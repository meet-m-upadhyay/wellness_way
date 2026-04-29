from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.database.connection import get_db
from app.models.chat import Chat, Message
from app.schemas.chat import (
    ChatCreate, 
    ChatResponse, 
    ChatDetailResponse, 
    MessageCreate, 
    MessageResponse
)
from app.api.endpoints.diet_plans_ml import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_in: ChatCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Start a new conversation session"""
    chat = Chat(
        user_id=current_user_id,
        title=chat_in.title
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@router.get("/", response_model=List[ChatResponse])
async def list_chats(
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """List all conversations for the current user"""
    chats = db.query(Chat).filter(Chat.user_id == current_user_id).order_by(Chat.created_at.desc()).all()
    return chats


@router.get("/{chat_id}", response_model=ChatDetailResponse)
async def get_chat(
    chat_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Get a specific conversation with all its messages"""
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user_id
    ).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    return chat


@router.post("/{chat_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_message(
    chat_id: UUID,
    message_in: MessageCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Add a new message to a conversation"""
    # Verify chat ownership
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user_id
    ).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    message = Message(
        chat_id=chat_id,
        role=message_in.role,
        content=message_in.content,
        metadata_json=message_in.metadata_json
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
