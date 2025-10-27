"""
Project Database Manager

Handles project-level database isolation using PostgreSQL schemas.
Each project gets its own schema for safe multi-tenancy.

Architecture:
- Main database contains system tables (public schema)
- Each project gets a dedicated schema: project_{user_hash}_{timestamp}
- Backend agents can safely create/modify tables within their project schema
"""

import os
import hashlib
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ProjectMetadata
from database import get_session
from utils.telemetry import log_event, log_error, trace_operation


class ProjectDatabaseManager:
    """
    Manages project database schemas for multi-tenant isolation

    Each user's project gets its own PostgreSQL schema, enabling:
    - Safe table creation/modification per project
    - Data isolation between projects
    - Easy cleanup and archival
    - Database-level security
    """

    def __init__(self):
        """Initialize project database manager"""
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL not configured")

    @staticmethod
    def _generate_project_id(user_id: str) -> str:
        """
        Generate unique project ID

        Args:
            user_id: User identifier (phone number, repo#issue, etc.)

        Returns:
            Unique project ID with timestamp
        """
        timestamp = int(time.time())
        return f"proj_{timestamp}"

    @staticmethod
    def _generate_schema_name(user_id: str, project_id: str) -> str:
        """
        Generate schema name for project isolation

        Format: project_{user_hash}_{project_id}

        Args:
            user_id: User identifier
            project_id: Project ID

        Returns:
            Schema name (safe for PostgreSQL)
        """
        # Hash user_id for privacy and PostgreSQL naming compliance
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:12]

        # Schema name: project_{hash}_{id}
        # Example: project_a1b2c3d4e5f6_proj_1730000001
        schema_name = f"project_{user_hash}_{project_id}"

        return schema_name

    async def create_project(
        self,
        user_id: str,
        platform: str,
        project_name: str,
        project_description: Optional[str] = None
    ) -> ProjectMetadata:
        """
        Create a new project with dedicated database schema

        Steps:
        1. Generate project ID and schema name
        2. Create PostgreSQL schema
        3. Grant permissions to application user
        4. Create ProjectMetadata record
        5. Return project metadata

        Args:
            user_id: User identifier
            platform: Platform (whatsapp, github, etc.)
            project_name: Human-readable project name
            project_description: Optional description

        Returns:
            ProjectMetadata object with schema information
        """
        with trace_operation(
            "create_project_database",
            user_id=user_id,
            platform=platform,
            project_name=project_name
        ):
            # Generate IDs
            project_id = self._generate_project_id(user_id)
            user_hash = hashlib.sha256(user_id.encode()).hexdigest()
            schema_name = self._generate_schema_name(user_id, project_id)

            print(f"🏗️  Creating project: {project_name}")
            print(f"   Project ID: {project_id}")
            print(f"   Schema: {schema_name}")

            try:
                # Create database schema
                async for db_session in get_session():
                    # Create schema
                    await db_session.execute(
                        text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
                    )

                    # Grant permissions (assuming app runs as current user)
                    # In production, you'd grant to a specific role
                    await db_session.execute(
                        text(f"GRANT ALL ON SCHEMA {schema_name} TO CURRENT_USER")
                    )

                    # Set search_path default for schema
                    await db_session.execute(
                        text(f"ALTER SCHEMA {schema_name} OWNER TO CURRENT_USER")
                    )

                    # Create project metadata record
                    project = ProjectMetadata(
                        project_id=project_id,
                        user_id=user_id,
                        user_id_hash=user_hash,
                        platform=platform,
                        project_name=project_name,
                        project_description=project_description,
                        schema_name=schema_name,
                        deployment_status="pending",
                        status="active"
                    )

                    db_session.add(project)
                    await db_session.commit()
                    await db_session.refresh(project)

                    print(f"   ✅ Project database created successfully")

                    # Log success
                    log_event(
                        "project.database_created",
                        project_id=project_id,
                        schema_name=schema_name,
                        user_id=user_id,
                        platform=platform
                    )

                    return project

            except Exception as e:
                print(f"   ❌ Failed to create project database: {e}")
                log_error(e, "create_project_database",
                         project_id=project_id,
                         schema_name=schema_name)
                raise

    async def get_project(self, project_id: str) -> Optional[ProjectMetadata]:
        """
        Get project metadata by ID

        Args:
            project_id: Project identifier

        Returns:
            ProjectMetadata or None if not found
        """
        async for db_session in get_session():
            stmt = select(ProjectMetadata).where(
                ProjectMetadata.project_id == project_id
            )
            result = await db_session.execute(stmt)
            project = result.scalar_one_or_none()

            # Update last_accessed
            if project:
                project.last_accessed = datetime.utcnow()
                await db_session.commit()

            return project

    async def get_user_projects(
        self,
        user_id: str,
        platform: str,
        status: str = "active"
    ) -> List[ProjectMetadata]:
        """
        Get all projects for a user

        Args:
            user_id: User identifier
            platform: Platform filter
            status: Status filter (active, archived, deleted)

        Returns:
            List of ProjectMetadata objects
        """
        async for db_session in get_session():
            stmt = select(ProjectMetadata).where(
                ProjectMetadata.user_id == user_id,
                ProjectMetadata.platform == platform,
                ProjectMetadata.status == status
            ).order_by(ProjectMetadata.created_at.desc())

            result = await db_session.execute(stmt)
            projects = result.scalars().all()

            return list(projects)

    async def update_neon_connection(
        self,
        project_id: str,
        neon_project_id: str,
        database_url: str,
        database_url_pooled: str,
        region: str,
        branch_id: Optional[str] = None,
        database_name: str = "neondb"
    ) -> ProjectMetadata:
        """
        Update Neon PostgreSQL connection information for a project

        This method persists the Neon connection strings so they survive:
        - Server restarts
        - Agent cleanups
        - Conversation resumptions

        Args:
            project_id: Project identifier
            neon_project_id: Neon project ID (e.g., "ep-cool-meadow-123456")
            database_url: Regular connection string (for migrations)
            database_url_pooled: Pooled connection string (for serverless)
            region: Neon region (e.g., "aws-us-east-1")
            branch_id: Neon branch ID (optional)
            database_name: Database name (default: "neondb")

        Returns:
            Updated ProjectMetadata
        """
        async for db_session in get_session():
            stmt = select(ProjectMetadata).where(
                ProjectMetadata.project_id == project_id
            )
            result = await db_session.execute(stmt)
            project = result.scalar_one_or_none()

            if not project:
                raise ValueError(f"Project not found: {project_id}")

            # Update Neon connection fields
            project.neon_project_id = neon_project_id
            project.neon_database_url = database_url
            project.neon_database_url_pooled = database_url_pooled
            project.neon_region = region
            project.neon_branch_id = branch_id
            project.neon_database_name = database_name
            project.updated_at = datetime.utcnow()

            await db_session.commit()
            await db_session.refresh(project)

            print(f"✅ Saved Neon connection for project {project_id}")
            print(f"   Neon Project: {neon_project_id}")
            print(f"   Region: {region}")

            # Log event
            log_event(
                "project.neon_connection_saved",
                project_id=project_id,
                neon_project_id=neon_project_id,
                region=region
            )

            return project

    async def get_neon_connection(self, project_id: str) -> Optional[Dict[str, str]]:
        """
        Retrieve Neon connection information for a project

        This enables conversation resumption after restarts/cleanups

        Args:
            project_id: Project identifier

        Returns:
            Dict with connection info or None if not set
        """
        project = await self.get_project(project_id)

        if not project or not project.neon_project_id:
            return None

        return {
            "neon_project_id": project.neon_project_id,
            "database_url": project.neon_database_url,
            "database_url_pooled": project.neon_database_url_pooled,
            "region": project.neon_region,
            "branch_id": project.neon_branch_id,
            "database_name": project.neon_database_name
        }

    async def update_project_spec(
        self,
        project_id: str,
        design_spec: Optional[Dict] = None,
        backend_spec: Optional[Dict] = None,
        frontend_spec: Optional[Dict] = None
    ) -> ProjectMetadata:
        """
        Update project specifications

        Args:
            project_id: Project identifier
            design_spec: Design specification from DesignerAgent
            backend_spec: Backend specification from BackendAgent
            frontend_spec: Frontend specification from FrontendAgent

        Returns:
            Updated ProjectMetadata
        """
        async for db_session in get_session():
            stmt = select(ProjectMetadata).where(
                ProjectMetadata.project_id == project_id
            )
            result = await db_session.execute(stmt)
            project = result.scalar_one()

            if design_spec:
                project.design_spec = design_spec
            if backend_spec:
                project.backend_spec = backend_spec
            if frontend_spec:
                project.frontend_spec = frontend_spec

            project.updated_at = datetime.utcnow()
            await db_session.commit()
            await db_session.refresh(project)

            return project

    async def update_deployment_info(
        self,
        project_id: str,
        deployment_url: str,
        deployment_status: str = "deployed"
    ) -> ProjectMetadata:
        """
        Update deployment information

        Args:
            project_id: Project identifier
            deployment_url: Deployed URL
            deployment_status: Deployment status

        Returns:
            Updated ProjectMetadata
        """
        async for db_session in get_session():
            stmt = select(ProjectMetadata).where(
                ProjectMetadata.project_id == project_id
            )
            result = await db_session.execute(stmt)
            project = result.scalar_one()

            project.deployment_url = deployment_url
            project.deployment_status = deployment_status
            project.updated_at = datetime.utcnow()

            await db_session.commit()
            await db_session.refresh(project)

            log_event(
                "project.deployed",
                project_id=project_id,
                deployment_url=deployment_url
            )

            return project

    async def get_project_connection_string(
        self,
        project_id: str
    ) -> str:
        """
        Get database connection string for a specific project schema

        This connection string can be used by the BackendAgent to safely
        operate within the project's isolated schema.

        Args:
            project_id: Project identifier

        Returns:
            PostgreSQL connection string with schema set
        """
        project = await self.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Parse base DATABASE_URL and add search_path
        base_url = self.database_url

        # Add options to set search_path to project schema
        if "?" in base_url:
            connection_string = f"{base_url}&options=-c search_path={project.schema_name}"
        else:
            connection_string = f"{base_url}?options=-c search_path={project.schema_name}"

        return connection_string

    async def execute_in_project_schema(
        self,
        project_id: str,
        sql_statements: List[str]
    ) -> Dict[str, Any]:
        """
        Execute SQL statements within a project's schema

        This is used by BackendAgent to create/modify tables safely.

        Args:
            project_id: Project identifier
            sql_statements: List of SQL statements to execute

        Returns:
            Execution results
        """
        project = await self.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        schema_name = project.schema_name

        with trace_operation(
            "execute_project_sql",
            project_id=project_id,
            schema_name=schema_name,
            statement_count=len(sql_statements)
        ):
            results = []

            try:
                async for db_session in get_session():
                    # Set search_path to project schema
                    await db_session.execute(
                        text(f"SET search_path TO {schema_name}, public")
                    )

                    # Execute statements
                    for sql in sql_statements:
                        print(f"   Executing: {sql[:100]}...")
                        result = await db_session.execute(text(sql))
                        results.append({
                            "sql": sql,
                            "success": True,
                            "rowcount": result.rowcount if hasattr(result, 'rowcount') else 0
                        })

                    await db_session.commit()

                    # Update project metadata with table info
                    # (you could introspect schema here)
                    project.updated_at = datetime.utcnow()
                    await db_session.commit()

                    log_event(
                        "project.sql_executed",
                        project_id=project_id,
                        schema_name=schema_name,
                        statements=len(sql_statements)
                    )

                    return {
                        "success": True,
                        "results": results,
                        "schema": schema_name
                    }

            except Exception as e:
                log_error(e, "execute_project_sql",
                         project_id=project_id,
                         schema_name=schema_name)
                return {
                    "success": False,
                    "error": str(e),
                    "schema": schema_name
                }

    async def archive_project(self, project_id: str) -> ProjectMetadata:
        """
        Archive a project (soft delete)

        Args:
            project_id: Project identifier

        Returns:
            Updated ProjectMetadata
        """
        async for db_session in get_session():
            stmt = select(ProjectMetadata).where(
                ProjectMetadata.project_id == project_id
            )
            result = await db_session.execute(stmt)
            project = result.scalar_one()

            project.status = "archived"
            project.updated_at = datetime.utcnow()

            await db_session.commit()

            log_event("project.archived", project_id=project_id)

            return project

    async def delete_project(self, project_id: str, hard_delete: bool = False):
        """
        Delete a project and its database schema

        Args:
            project_id: Project identifier
            hard_delete: If True, permanently delete schema and data
        """
        project = await self.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        schema_name = project.schema_name

        with trace_operation(
            "delete_project",
            project_id=project_id,
            schema_name=schema_name,
            hard_delete=hard_delete
        ):
            async for db_session in get_session():
                if hard_delete:
                    # DANGER: Permanently delete schema and all data
                    print(f"⚠️  HARD DELETE: Dropping schema {schema_name}")
                    await db_session.execute(
                        text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE")
                    )

                    # Delete metadata
                    await db_session.delete(project)

                    log_event("project.deleted_permanently",
                             project_id=project_id,
                             schema_name=schema_name)
                else:
                    # Soft delete: mark as deleted
                    project.status = "deleted"
                    project.updated_at = datetime.utcnow()

                    log_event("project.deleted_soft",
                             project_id=project_id)

                await db_session.commit()
                print(f"   ✅ Project deleted: {project_id}")


# Global project manager instance
project_manager = ProjectDatabaseManager()
