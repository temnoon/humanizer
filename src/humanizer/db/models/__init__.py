# src/humanizer/db/models/__init__.py
from humanizer.db.models.base import Base
from humanizer.db.models.content import Content, Message

__all__ = ['Base', 'Content', 'Message']
