# src/humanizer/core/types.py
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel

class Message(BaseModel):
    """OpenAI chat message format"""
    role: str
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None

class Conversation(BaseModel):
    """Single conversation with messages"""
    id: UUID
    title: Optional[str] = None
    create_time: datetime
    update_time: datetime
    messages: List[Message]
    meta_info: Optional[Dict[str, Any]] = None  # Changed from metadata to meta_info

class ConversationFile(BaseModel):
    """OpenAI conversation export format"""
    conversations: List[Conversation]
