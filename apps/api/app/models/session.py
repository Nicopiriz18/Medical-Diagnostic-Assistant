from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

# Request/Response Models
class SessionCreate(BaseModel):
    user_id: Optional[str] = None
    patient_info: Optional[Dict[str, Any]] = Field(default_factory=dict)

class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    images: Optional[List[str]] = Field(default_factory=list)  # Image URLs/paths

class MessageResponse(BaseModel):
    id: int
    session_id: str
    role: MessageRole
    content: str
    images: List[str]
    message_metadata: Dict[str, Any]
    timestamp: datetime

    class Config:
        from_attributes = True

class SessionResponse(BaseModel):
    id: str
    user_id: Optional[str]
    status: SessionStatus
    patient_info: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[MessageResponse]] = None

    class Config:
        from_attributes = True

class ImageUploadResponse(BaseModel):
    url: str
    filename: str
    size: int
    content_type: str
