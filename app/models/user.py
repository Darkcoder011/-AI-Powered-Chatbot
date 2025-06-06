from pydantic import BaseModel, EmailStr, Field
from typing import Dict, Optional
from datetime import datetime
import uuid

class UserBase(BaseModel):
    email: EmailStr
    preferences: Optional[Dict] = Field(default_factory=dict)

class UserCreate(UserBase):
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    preferences: Optional[Dict] = None
    last_active: Optional[datetime] = None

class User(UserBase):
    user_id: str
    created_at: datetime
    last_active: datetime
    interaction_count: int = 0

    class Config:
        from_attributes = True

class UserPreferences(BaseModel):
    language: str = "en"
    theme: str = "light"
    notification_enabled: bool = True
    response_length: str = "medium"  # short, medium, long
    technical_level: str = "intermediate"  # beginner, intermediate, advanced

class UserStats(BaseModel):
    total_sessions: int
    total_interactions: int
    average_sentiment: float
    most_common_intents: Dict[str, int]
    average_response_time: float
    satisfaction_score: float

class UserSession(BaseModel):
    session_id: str
    user_id: str
    created_at: datetime
    last_active: datetime
    message_count: int
    is_active: bool
    context: Dict = Field(default_factory=dict)

    class Config:
        from_attributes = True

class UserInteraction(BaseModel):
    interaction_id: str
    session_id: str
    user_id: str
    timestamp: datetime
    message: str
    response: str
    sentiment: str
    confidence: float
    intent: str

    class Config:
        from_attributes = True 