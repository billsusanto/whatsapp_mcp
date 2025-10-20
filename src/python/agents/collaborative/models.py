"""
A2A Protocol Data Models
Based on Google's A2A specification
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


class AgentRole(str, Enum):
    """Agent roles in the system"""
    DESIGNER = "ui_ux_designer"
    FRONTEND = "frontend_developer"
    BACKEND = "backend_developer"
    QA = "qa_engineer"
    DEVOPS = "devops_engineer"


class MessageType(str, Enum):
    """Types of messages agents can send"""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    REVIEW_REQUEST = "review_request"
    REVIEW_RESPONSE = "review_response"
    QUESTION = "question"
    ANSWER = "answer"
    STATUS_UPDATE = "status_update"


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


# Agent Card (Discovery)
class AgentCard(BaseModel):
    """Agent capabilities and metadata (A2A discovery)"""
    agent_id: str
    name: str
    role: AgentRole
    description: str
    version: str = "1.0.0"
    capabilities: List[str]
    skills: Dict[str, List[str]]
    endpoint: Optional[str] = None

    class Config:
        use_enum_values = True


# A2A Message
class A2AMessage(BaseModel):
    """Standardized message format for agent-to-agent communication"""
    message_id: str = Field(default_factory=lambda: f"msg_{datetime.now().timestamp()}")
    from_agent: str
    to_agent: str
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        use_enum_values = True


# Task Models
class Task(BaseModel):
    """A2A Task model"""
    task_id: str = Field(default_factory=lambda: f"task_{datetime.now().timestamp()}")
    description: str
    from_agent: str
    to_agent: str
    priority: str = "medium"
    status: TaskStatus = TaskStatus.PENDING
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        use_enum_values = True


class TaskResponse(BaseModel):
    """A2A Task Response model"""
    task_id: str
    status: TaskStatus
    result: Any
    agent_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    error: Optional[str] = None

    class Config:
        use_enum_values = True


# Design-specific models
class DesignSpecification(BaseModel):
    """Design specification from UI/UX Designer"""
    style: str  # "modern", "minimal", "bold", "playful"
    colors: Dict[str, str]  # {"primary": "#hex", ...}
    typography: Dict[str, Any]  # Font families, scales
    components: List[Dict[str, Any]]  # Component structure
    layout_description: str
    design_tokens: Dict[str, str]  # CSS custom properties
    accessibility_notes: List[str]


class WebappImplementation(BaseModel):
    """Implementation from Frontend Developer"""
    framework: str  # "react", "vue"
    files: List[Dict[str, str]]  # [{"path": "...", "content": "..."}]
    dependencies: Dict[str, str]  # package.json dependencies
    build_command: str
    output_directory: str


class DesignReview(BaseModel):
    """Design review from UI/UX Designer"""
    approved: bool
    feedback: List[str]
    iteration: int
    suggestions: Optional[List[str]] = None
