from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.chat import Chat, Message
from app.database.connection import engine
import json

with Session(engine) as session:
    chats = session.query(Chat).all()
    print(f"Total Chats: {len(chats)}")
    for chat in chats:
        messages = session.query(Message).filter(Message.chat_id == chat.id).all()
        print(f"Chat: {chat.title} (ID: {chat.id}) - User: {chat.user_id}")
        print(f"  Messages: {len(messages)}")
        for msg in messages:
            print(f"    [{msg.role}] {msg.content[:50]}...")
