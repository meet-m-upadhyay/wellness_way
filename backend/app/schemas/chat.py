from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class MessageBase(BaseModel):
    role: str
    content: str
    metadata_json: Optional[dict] = None


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: UUID
    chat_id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ChatBase(BaseModel):
    title: Optional[str] = None


class ChatCreate(ChatBase):
    pass


class ChatResponse(ChatBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ChatDetailResponse(ChatResponse):
    messages: List[MessageResponse] = []
    
    model_config = ConfigDict(from_attributes=True)
