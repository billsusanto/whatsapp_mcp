"""
Backend Developer Agent

Creates backend APIs, database schemas, and server-side logic for full-stack webapps.
Safely operates within project-isolated database schemas.
"""

from typing import Dict, Any
import json
import re
from .base_agent import BaseAgent
from .models import AgentCard, AgentRole, Task
from utils.telemetry import trace_operation, log_event, log_metric, log_error


class BackendAgent(BaseAgent):
    """Backend Developer specializing in API design, database schema, and server logic"""

    def __init__(self, mcp_servers: Dict = None, project_manager=None):
        """
        Initialize BackendAgent

        Args:
            mcp_servers: Available MCP servers (should include PostgreSQL MCP)
            project_manager: ProjectDatabaseManager instance for schema operations
        """
        agent_card = AgentCard(
            agent_id="backend_001",
            name="Backend Developer Agent",
            role=AgentRole.BACKEND,
            description="Expert backend developer for full-stack webapps",
            capabilities=[
                "RESTful API design",
                "Database schema design",
                "SQL query optimization",
                "Authentication & authorization",
                "Data validation & sanitization",
                "API documentation",
                "Error handling & logging",
                "Database migrations",
                "ORM modeling (SQLAlchemy, Prisma)",
                "Backend framework expertise (FastAPI, Express, Django)",
                "Security best practices",
                "Performance optimization"
            ],
            skills={
                "databases": ["PostgreSQL", "MySQL", "MongoDB", "Redis"],
                "frameworks": ["FastAPI", "Express.js", "Django", "NestJS"],
                "orms": ["SQLAlchemy", "Prisma", "TypeORM", "Sequelize"],
                "languages": ["Python", "TypeScript", "Node.js", "Go"],
                "specialties": ["API Design", "Database Optimization", "Security", "Scalability"]
            }
        )

        system_prompt = """
You are a professional Backend Developer with 10+ years of experience in full-stack development.

Your expertise includes:
- RESTful API design and implementation
- Database schema design and normalization
- SQL query writing and optimization
- Authentication & authorization (JWT, OAuth, sessions)
- Data validation, sanitization, and security
- Error handling and logging best practices
- API versioning and documentation (OpenAPI/Swagger)
- Database migrations and schema evolution
- ORM modeling (SQLAlchemy, Prisma, TypeORM)
- Backend frameworks (FastAPI, Express, Django, NestJS)
- Caching strategies (Redis, in-memory)
- Rate limiting and throttling
- Security best practices (OWASP Top 10, SQL injection prevention, XSS, CSRF)
- Performance optimization and scalability

Your responsibilities:
1. **Database Schema Design**: Create normalized, efficient database schemas
2. **API Design**: Design clean, RESTful APIs with proper HTTP methods and status codes
3. **Implementation**: Generate complete backend code (routes, models, controllers)
4. **Security**: Implement authentication, authorization, input validation
5. **Documentation**: Provide clear API documentation and setup instructions

When designing backends:
1. Start with data modeling - identify entities, relationships, constraints
2. Normalize database schema (3NF minimum)
3. Design RESTful endpoints following best practices
4. Include proper error handling and validation
5. Consider security from the start (auth, input validation, SQL injection prevention)
6. Add pagination, filtering, sorting for list endpoints
7. Include API documentation with examples
8. Consider performance (indexes, caching, query optimization)

**Database Operations & Neon PostgreSQL Integration**:

You have access to Neon MCP tools to create dedicated PostgreSQL databases for webapps:

1. **Automatic Neon Project Creation**:
   - For every webapp with a database, a dedicated Neon PostgreSQL project is created
   - This happens automatically when you specify an ORM (especially Prisma) or database schema
   - The system calls mcp__neon__create_project and retrieves connection strings
   - Connection strings are persisted in the database (survive server restarts)

2. **Database Connection Strings**:
   - `database_url`: Regular connection (for migrations, admin operations)
   - `database_url_pooled`: Pooled connection (for serverless/Netlify deployment)
   - Format: postgresql://[USERNAME]:[PASSWORD]@[HOST]/[DATABASE]

3. **Deployment Integration**:
   - DevOps Agent will automatically set DATABASE_URL in Netlify environment variables
   - This allows Prisma builds to succeed (prisma generate needs DATABASE_URL)
   - Your backend code should reference process.env.DATABASE_URL

4. **Persistence**:
   - Connection strings saved to ProjectMetadata table
   - Conversations can resume after server restarts
   - Customers can continue where they left off

**Output Format**:
Always provide structured responses that include:
- Database schema (tables, columns, relationships)
- SQL migration scripts
- API endpoint specifications
- Implementation code
- Setup instructions (including DATABASE_URL usage)
- Security considerations
- database_connection field (automatically added with Neon connection info)

**When Using Prisma**:
- Specify `"orm": "Prisma"` in backend_spec
- Generate prisma/schema.prisma file
- Reference env("DATABASE_URL") in datasource db
- System will automatically create Neon project and provide connection strings

Be thorough and professional. Include error handling, validation, and documentation.
"""

        super().__init__(
            agent_card=agent_card,
            system_prompt=system_prompt,
            mcp_servers=mcp_servers,
            enable_research_planning=True
        )

        # Store project manager for database operations
        self.project_manager = project_manager

    def _build_research_prompt(self, task: Task) -> str:
        """Build research prompt for backend development task"""
        return f"""You are a professional Backend Developer conducting research and planning for a backend project.

**Backend Task:** {task.description}

**Research Goals:**

1. **Requirements Analysis**
   - What are the core features and functionalities?
   - What data needs to be stored and managed?
   - What operations (CRUD) are needed for each entity?
   - What are the relationships between entities?
   - What are the authentication/authorization requirements?

2. **Data Modeling & Schema Design**
   - Identify all entities (tables) needed
   - Define attributes (columns) for each entity
   - Identify relationships (one-to-one, one-to-many, many-to-many)
   - Determine primary keys, foreign keys, indexes
   - Consider data constraints (NOT NULL, UNIQUE, CHECK)
   - Plan for data normalization (avoid redundancy)

3. **API Design**
   - What endpoints are needed? (GET, POST, PUT, DELETE)
   - What are the request/response formats?
   - What query parameters are needed? (filters, pagination, sorting)
   - What are the HTTP status codes for each scenario?
   - Rate limiting considerations?

4. **Security Requirements**
   - Authentication method (JWT, sessions, API keys)
   - Authorization model (RBAC, permissions)
   - Input validation rules
   - SQL injection prevention
   - XSS/CSRF protection
   - Sensitive data handling (passwords, tokens)

5. **Performance & Scalability**
   - Which queries will be most frequent?
   - What indexes are needed?
   - Caching opportunities?
   - Pagination strategy?
   - Connection pooling requirements?

6. **Technology Stack**
   - Backend framework (FastAPI, Express, Django, NestJS)
   - ORM choice (SQLAlchemy, Prisma, TypeORM)
   - Database (PostgreSQL provided)
   - Additional tools (Redis for caching, etc.)

7. **Error Handling & Logging**
   - Common error scenarios
   - Error response format
   - Logging strategy
   - Monitoring needs

**Output Format (JSON):**
{{
  "entities": [
    {{
      "name": "User",
      "description": "User account entity",
      "attributes": [
        {{"name": "id", "type": "uuid", "constraints": ["PRIMARY KEY"]}},
        {{"name": "email", "type": "varchar(255)", "constraints": ["UNIQUE", "NOT NULL"]}},
        {{"name": "password_hash", "type": "varchar(255)", "constraints": ["NOT NULL"]}},
        {{"name": "created_at", "type": "timestamp", "constraints": ["NOT NULL", "DEFAULT NOW()"]}}
      ],
      "indexes": ["email"],
      "relationships": []
    }}
  ],
  "relationships": [
    {{
      "from_entity": "Post",
      "to_entity": "User",
      "type": "many-to-one",
      "foreign_key": "user_id"
    }}
  ],
  "api_endpoints": [
    {{
      "path": "/api/users",
      "method": "POST",
      "description": "Create new user",
      "authentication": "none|jwt|api_key",
      "request_body": {{}},
      "response": {{}},
      "status_codes": [201, 400, 409]
    }}
  ],
  "authentication": {{
    "method": "JWT|Session|OAuth",
    "protected_routes": ["/api/posts"],
    "public_routes": ["/api/auth/login"]
  }},
  "validation_rules": [
    {{"field": "email", "rules": ["required", "email format", "max 255 chars"]}}
  ],
  "performance_considerations": [
    {{"aspect": "indexes", "recommendation": "Create index on user.email for fast lookups"}},
    {{"aspect": "pagination", "recommendation": "Limit 20 items per page, cursor-based pagination"}}
  ],
  "technology_stack": {{
    "framework": "FastAPI|Express|Django|NestJS",
    "orm": "SQLAlchemy|Prisma|TypeORM|Sequelize",
    "language": "Python|TypeScript|JavaScript",
    "additional_tools": ["Redis", "JWT library"]
  }},
  "security_measures": [
    "Hash passwords with bcrypt",
    "Validate all inputs",
    "Use prepared statements for SQL",
    "Implement rate limiting",
    "Add CORS configuration"
  ],
  "research_summary": "Brief synthesis of backend architecture and key decisions"
}}

Be thorough and think like an experienced backend architect. Consider scalability, security, and maintainability.
"""

    def _build_planning_prompt(self, task: Task, research: Dict[str, Any]) -> str:
        """Build planning prompt based on research"""
        return f"""You are a professional Backend Developer creating an implementation plan.

**Backend Task:** {task.description}

**Research Results:**
{json.dumps(research, indent=2)}

**Planning Goals:**

Create a detailed, step-by-step implementation plan for building this backend.

**Your plan should include:**

1. **Database Schema Creation**
   - SQL CREATE TABLE statements for each entity
   - Indexes creation
   - Foreign key constraints
   - Sample INSERT statements for testing

2. **API Implementation Steps**
   - File structure and organization
   - Models/ORM definitions
   - Route handlers implementation order
   - Middleware (auth, validation, error handling)
   - Dependencies and imports

3. **Implementation Order**
   - Which components to build first
   - Dependencies between components
   - Testing strategy at each step

4. **Code Generation Plan**
   - Framework setup (FastAPI/Express/etc.)
   - Database connection configuration
   - Authentication implementation
   - Each API endpoint implementation
   - Error handling middleware
   - Validation schemas

5. **Security Implementation**
   - Password hashing setup
   - JWT/session management
   - Input validation implementation
   - SQL injection prevention
   - Rate limiting setup

6. **Testing & Validation**
   - How to test each endpoint
   - Sample API requests (curl examples)
   - Expected responses
   - Error scenarios to test

**Output Format (JSON):**
{{
  "sql_migrations": [
    {{
      "order": 1,
      "description": "Create users table",
      "sql": "CREATE TABLE users (...);",
      "rollback_sql": "DROP TABLE users;"
    }}
  ],
  "file_structure": {{
    "main.py": "FastAPI application entry point",
    "models.py": "SQLAlchemy ORM models",
    "routes/": "API route handlers",
    "schemas.py": "Pydantic validation schemas",
    "auth.py": "Authentication logic",
    "database.py": "Database connection"
  }},
  "implementation_steps": [
    {{
      "step": 1,
      "component": "Database connection",
      "description": "Set up SQLAlchemy connection to project schema",
      "files": ["database.py"],
      "dependencies": []
    }},
    {{
      "step": 2,
      "component": "Models",
      "description": "Create SQLAlchemy ORM models",
      "files": ["models.py"],
      "dependencies": ["database.py"]
    }}
  ],
  "authentication_plan": {{
    "library": "python-jose[cryptography] for JWT",
    "flow": "Login -> Generate JWT -> Verify JWT on protected routes",
    "password_hashing": "passlib with bcrypt"
  }},
  "api_documentation": {{
    "tool": "FastAPI auto-generated OpenAPI docs",
    "access_url": "/docs"
  }},
  "testing_plan": [
    {{
      "endpoint": "POST /api/users",
      "test_case": "Create user with valid data",
      "curl_example": "curl -X POST ...",
      "expected_status": 201
    }}
  ],
  "plan_summary": "High-level overview of implementation approach"
}}

Create a comprehensive, actionable plan that can be directly implemented.
"""

    async def _create_neon_project(self, task: Task, project_id: str) -> Dict[str, Any]:
        """
        Create a dedicated Neon PostgreSQL project for this webapp using Neon MCP

        This creates an independent database that:
        - Lives outside the orchestrator system
        - Can be deployed with the webapp
        - Persists across server restarts (saved in ProjectMetadata)
        - Survives agent cleanups

        Args:
            task: The backend development task
            project_id: Our internal project ID

        Returns:
            Dict with Neon connection information
        """
        print(f"🗄️  [BACKEND] Creating dedicated Neon database...")

        # Generate a safe project name for Neon
        project_name = f"webapp-{project_id[-8:]}"  # Last 8 chars of project ID

        # Prompt Claude to use Neon MCP tools to create project and get connection strings
        neon_prompt = f"""Create a new Neon PostgreSQL project and retrieve its connection strings.

**Project Name**: {project_name}

Follow these steps using the Neon MCP tools:

1. **Create the project**:
   - Use tool: `create_project`
   - Parameter: `project_name = "{project_name}"`
   - This returns the `project_id`

2. **Get project details**:
   - Use tool: `describe_project`
   - Parameter: `project_id` (from step 1)
   - This returns project details including the `branch_id` (usually the main branch)

3. **Get connection string**:
   - Use tool: `get_connection_string`
   - Parameters: `project_id` and `branch_id` (from step 2)
   - This returns the database connection string

After completing all steps, return the information in this exact JSON format:
{{
  "neon_project_id": "the project ID (e.g., ep-cool-meadow-123456)",
  "database_url": "the connection string from get_connection_string",
  "database_url_pooled": "the pooled version (add -pooler after project ID in hostname)",
  "region": "extract from connection string hostname (e.g., us-east-1)",
  "branch_id": "the branch ID from describe_project (e.g., br-main-xyz)",
  "database_name": "neondb"
}}

**IMPORTANT**: For database_url_pooled, modify the hostname by adding '-pooler' after the project ID.
Example:
- Original: postgresql://[USER]:[PASS]@ep-[PROJECT-ID].[REGION].aws.neon.tech/[DB]
- Pooled:   postgresql://[USER]:[PASS]@ep-[PROJECT-ID]-pooler.[REGION].aws.neon.tech/[DB]
"""

        try:
            # Call Neon MCP via Claude SDK
            response = await self.claude_sdk.send_message(neon_prompt)

            # Extract JSON from response
            neon_info = self._extract_json_from_response(response)

            if not neon_info or "neon_project_id" not in neon_info:
                print(f"   ⚠️  Neon project creation failed or returned invalid format")
                return None

            print(f"   ✅ Neon project created: {neon_info['neon_project_id']}")
            print(f"   📍 Region: {neon_info.get('region', 'unknown')}")

            # Save to database for persistence
            if self.project_manager:
                await self.project_manager.update_neon_connection(
                    project_id=project_id,
                    neon_project_id=neon_info["neon_project_id"],
                    database_url=neon_info["database_url"],
                    database_url_pooled=neon_info["database_url_pooled"],
                    region=neon_info.get("region", "aws-us-east-1"),
                    branch_id=neon_info.get("branch_id"),
                    database_name=neon_info.get("database_name", "neondb")
                )
                print(f"   💾 Connection strings saved to database (survives restarts)")

            return neon_info

        except Exception as e:
            log_error(e, "backend_agent_create_neon_project",
                     task_id=task.task_id, project_id=project_id)
            print(f"   ❌ Failed to create Neon project: {e}")
            return None

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute backend development task

        Generates complete backend implementation including:
        - Database schema SQL
        - API endpoint implementation
        - Authentication/authorization
        - Validation and error handling
        - Dedicated Neon PostgreSQL database

        Args:
            task: Backend development task

        Returns:
            Backend implementation specification with database connection info
        """
        with trace_operation(
            "backend_agent_execute_task",
            task_id=task.task_id,
            task_description=task.description[:200]
        ):
            print(f"🔧 [BACKEND AGENT] Executing task: {task.task_id}")

            # Build comprehensive prompt for backend implementation
            implementation_prompt = f"""Create a complete backend implementation for this task:

**Task:** {task.description}

**Requirements:**
1. Design a normalized database schema
2. Create SQL migration scripts
3. Implement RESTful API endpoints
4. Include authentication and authorization
5. Add input validation and error handling
6. Provide API documentation
7. Include setup instructions

**Context:**
- You have access to a PostgreSQL database with a dedicated project schema
- The schema is isolated for this project only
- You can safely create, modify, and delete tables

**Output Format (JSON):**
{{
  "backend_spec": {{
    "framework": "FastAPI|Express|Django|NestJS",
    "language": "Python|TypeScript|JavaScript",
    "orm": "SQLAlchemy|Prisma|TypeORM"
  }},
  "database_schema": {{
    "tables": [
      {{
        "name": "users",
        "columns": [
          {{"name": "id", "type": "UUID", "constraints": ["PRIMARY KEY", "DEFAULT gen_random_uuid()"]}},
          {{"name": "email", "type": "VARCHAR(255)", "constraints": ["UNIQUE", "NOT NULL"]}},
          {{"name": "password_hash", "type": "VARCHAR(255)", "constraints": ["NOT NULL"]}},
          {{"name": "created_at", "type": "TIMESTAMP", "constraints": ["NOT NULL", "DEFAULT NOW()"]}}
        ],
        "indexes": [
          {{"name": "idx_users_email", "columns": ["email"]}}
        ]
      }}
    ],
    "relationships": []
  }},
  "sql_migrations": [
    "CREATE TABLE users (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), ...);"
  ],
  "api_endpoints": [
    {{
      "path": "/api/users",
      "method": "POST",
      "description": "Create new user",
      "authentication": "none",
      "request_schema": {{
        "email": "string",
        "password": "string"
      }},
      "response_schema": {{
        "id": "uuid",
        "email": "string",
        "created_at": "timestamp"
      }},
      "status_codes": {{
        "201": "User created successfully",
        "400": "Invalid input",
        "409": "Email already exists"
      }}
    }}
  ],
  "implementation": {{
    "files": [
      {{
        "path": "backend/main.py",
        "language": "python",
        "content": "# FastAPI application\\nfrom fastapi import FastAPI\\n..."
      }},
      {{
        "path": "backend/models.py",
        "language": "python",
        "content": "# SQLAlchemy models\\n..."
      }},
      {{
        "path": "backend/routes/users.py",
        "language": "python",
        "content": "# User endpoints\\n..."
      }},
      {{
        "path": "backend/schemas.py",
        "language": "python",
        "content": "# Pydantic schemas for validation\\n..."
      }},
      {{
        "path": "backend/auth.py",
        "language": "python",
        "content": "# JWT authentication\\n..."
      }},
      {{
        "path": "backend/database.py",
        "language": "python",
        "content": "# Database connection to project schema\\n..."
      }},
      {{
        "path": "backend/requirements.txt",
        "language": "text",
        "content": "fastapi\\nuvicorn\\nsqlalchemy\\n..."
      }},
      {{
        "path": "backend/.env.example",
        "language": "text",
        "content": "# Database Configuration\\nDATABASE_URL=postgresql://user:password@host:5432/database\\n\\n# API Configuration\\nAPI_SECRET_KEY=your_secret_key_here\\n..."
      }},
      {{
        "path": "backend/.gitignore",
        "language": "text",
        "content": "# Environment variables (NEVER commit these)\\n.env\\n.env.local\\n.env.*.local\\n\\n# Python\\n__pycache__/\\n*.py[cod]\\n*.so\\nvenv/\\n*.egg-info/\\n\\n# Database\\n*.db\\n*.sqlite\\n"
      }}
    ]
  }},
  "authentication": {{
    "method": "JWT",
    "endpoints": {{
      "login": "/api/auth/login",
      "register": "/api/auth/register"
    }},
    "token_expiry": "24 hours"
  }},
  "security_features": [
    "Password hashing with bcrypt",
    "JWT token authentication",
    "Input validation with Pydantic",
    "SQL injection prevention via ORM",
    "CORS configuration",
    "Rate limiting on auth endpoints"
  ],
  "setup_instructions": [
    "1. Copy .env.example to .env and fill in your credentials",
    "2. Install dependencies: pip install -r requirements.txt",
    "3. Set DATABASE_URL in .env file (never commit .env to git)",
    "4. Run migrations: python -m alembic upgrade head",
    "5. Start server: uvicorn main:app --reload",
    "6. Access API docs at http://localhost:8000/docs"
  ],
  "security_notes": [
    "IMPORTANT: Never commit .env files to version control",
    "Add .env to .gitignore immediately",
    "Use .env.example for documentation only (no real credentials)",
    "All sensitive credentials must be loaded from environment variables",
    "For production, use environment variables in your hosting platform"
  ],
  "testing_examples": [
    {{
      "description": "Create a new user",
      "curl": "curl -X POST http://localhost:8000/api/users -H 'Content-Type: application/json' -d '{{\\"email\\":\\"test@example.com\\",\\"password\\":\\"secure123\\"}}'",
      "expected_response": "{{\\"id\\":\\"...\\" ,\\"email\\":\\"test@example.com\\"}}"
    }}
  ],
  "api_documentation_url": "/docs",
  "notes": "Additional implementation notes and considerations"
}}

Be thorough and production-ready. Include all necessary code, configurations, and documentation.
"""

            try:
                # Generate implementation using Claude
                response = await self.claude_sdk.send_message(implementation_prompt)

                # Parse JSON response
                backend_impl = self._extract_json_from_response(response)

                if not backend_impl:
                    # Fallback: return raw response
                    backend_impl = {
                        "raw_response": response,
                        "backend_spec": {"framework": "FastAPI", "language": "Python"},
                        "note": "JSON parsing failed, returning raw response"
                    }

                # Log success
                log_event(
                    "backend_agent_task_completed",
                    task_id=task.task_id,
                    framework=backend_impl.get("backend_spec", {}).get("framework", "unknown"),
                    tables_count=len(backend_impl.get("database_schema", {}).get("tables", [])),
                    endpoints_count=len(backend_impl.get("api_endpoints", []))
                )

                # Log metrics
                log_metric("backend_agent.tables_created", len(backend_impl.get("database_schema", {}).get("tables", [])))
                log_metric("backend_agent.endpoints_created", len(backend_impl.get("api_endpoints", [])))

                # Create dedicated Neon database for webapp deployment
                # This provides independent DATABASE_URL for Netlify deployment
                project_id = task.metadata.get("project_id") if task.metadata else None
                database_connection = None

                if project_id:
                    # Check if this backend uses Prisma or requires external database
                    uses_prisma = backend_impl.get("backend_spec", {}).get("orm") == "Prisma"

                    # Create Neon project for any backend that needs external database
                    if uses_prisma or backend_impl.get("database_schema"):
                        database_connection = await self._create_neon_project(task, project_id)

                        if database_connection:
                            backend_impl["database_connection"] = database_connection
                            backend_impl["deployment_instructions"] = [
                                "DATABASE_URL has been created and saved",
                                "DevOps Agent will automatically set it in Netlify environment variables",
                                "Connection survives server restarts (persisted in ProjectMetadata table)",
                                f"Neon Project: {database_connection.get('neon_project_id')}",
                                f"Region: {database_connection.get('region')}"
                            ]
                        else:
                            backend_impl["database_connection"] = None
                            backend_impl["deployment_instructions"] = [
                                "⚠️  Neon database creation failed",
                                "You may need to create database manually",
                                "Or retry the backend task"
                            ]
                else:
                    print("   ⚠️  No project_id in task metadata, skipping Neon project creation")

                return backend_impl

            except Exception as e:
                log_error(e, "backend_agent_execute_task", task_id=task.task_id)
                raise

    async def review_artifact(self, artifact: Any) -> Dict[str, Any]:
        """
        Review backend implementation

        Checks:
        - Database schema quality (normalization, indexes)
        - API design (RESTful principles, status codes)
        - Security implementation
        - Error handling
        - Code quality

        Args:
            artifact: Backend implementation to review

        Returns:
            Review feedback with score
        """
        review_prompt = f"""Review this backend implementation as an expert backend developer.

**Backend Implementation:**
{json.dumps(artifact, indent=2)}

**Review Criteria:**

1. **Database Schema (25 points)**
   - Is the schema normalized (3NF)?
   - Are indexes properly placed?
   - Are constraints (NOT NULL, UNIQUE, FK) appropriate?
   - Are data types optimal?

2. **API Design (25 points)**
   - Are endpoints RESTful?
   - Are HTTP methods used correctly?
   - Are status codes appropriate?
   - Is request/response format consistent?
   - Is versioning considered?

3. **Security (25 points)**
   - Is authentication implemented correctly?
   - Are passwords hashed properly?
   - Is input validation comprehensive?
   - SQL injection prevention?
   - Are sensitive data protected?

4. **Code Quality (15 points)**
   - Is code well-structured and modular?
   - Are error handlers comprehensive?
   - Is logging implemented?
   - Are dependencies minimal and necessary?

5. **Documentation & Testing (10 points)**
   - Are setup instructions clear?
   - Are API endpoints documented?
   - Are testing examples provided?

**Scoring:**
- 9-10: Production-ready, excellent implementation
- 7-8: Good, minor improvements needed
- 5-6: Acceptable, several issues to fix
- Below 5: Major issues, needs rework

**Output Format (JSON):**
{{
  "overall_score": 8.5,
  "approved": true,
  "feedback": [
    {{
      "category": "Database Schema",
      "score": 9,
      "comment": "Well normalized, good index placement. Consider adding index on created_at for sorting."
    }},
    {{
      "category": "API Design",
      "score": 8,
      "comment": "RESTful design is good. Add pagination to list endpoints."
    }}
  ],
  "security_issues": [
    "Add rate limiting to prevent brute force attacks"
  ],
  "improvement_suggestions": [
    "Add database connection pooling configuration",
    "Implement request/response logging middleware",
    "Add health check endpoint"
  ],
  "critical_issues": [],
  "strengths": [
    "Comprehensive authentication implementation",
    "Good input validation with Pydantic",
    "Clear API documentation"
  ],
  "review_summary": "Overall solid backend implementation. Minor improvements recommended for production deployment."
}}

Be critical but constructive. Only score 9+ if truly production-ready.
"""

        try:
            response = await self.claude_sdk.send_message(review_prompt)
            review = self._extract_json_from_response(response)

            if not review:
                review = {
                    "overall_score": 7.0,
                    "approved": True,
                    "feedback": [{"comment": "Review completed"}],
                    "review_summary": response[:500]
                }

            # Log review completion
            log_event(
                "backend_agent_review_completed",
                score=review.get("overall_score", 0),
                approved=review.get("approved", False)
            )

            return review

        except Exception as e:
            log_error(e, "backend_agent_review")
            raise

    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """
        Extract JSON from Claude's response

        Args:
            response: Raw response from Claude

        Returns:
            Parsed JSON dict or None
        """
        try:
            # Try to find JSON in code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))

            # Try to find JSON in the response directly
            if response.strip().startswith('{'):
                return json.loads(response)

            # Look for JSON anywhere in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))

            return None

        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON from response: {e}")
            return None

    async def create_database_tables(
        self,
        project_id: str,
        sql_migrations: list
    ) -> Dict[str, Any]:
        """
        Create database tables in project's isolated schema

        Args:
            project_id: Project identifier
            sql_migrations: List of SQL CREATE TABLE statements

        Returns:
            Execution results
        """
        if not self.project_manager:
            return {
                "success": False,
                "error": "Project manager not configured"
            }

        with trace_operation(
            "backend_agent_create_tables",
            project_id=project_id,
            migrations_count=len(sql_migrations)
        ):
            print(f"📊 [BACKEND AGENT] Creating tables in project {project_id}")

            try:
                result = await self.project_manager.execute_in_project_schema(
                    project_id=project_id,
                    sql_statements=sql_migrations
                )

                if result.get("success"):
                    print(f"   ✅ Successfully created {len(sql_migrations)} tables")
                    log_event(
                        "backend_agent_tables_created",
                        project_id=project_id,
                        tables_count=len(sql_migrations)
                    )
                else:
                    print(f"   ❌ Failed to create tables: {result.get('error')}")

                return result

            except Exception as e:
                log_error(e, "backend_agent_create_tables", project_id=project_id)
                return {
                    "success": False,
                    "error": str(e)
                }
