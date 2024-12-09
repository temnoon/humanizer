from sqlalchemy import Column, String, DateTime, Text, JSON, Integer, ForeignKey, event, text
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from humanizer.db.models.base import Base
from humanizer.config import get_settings

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    raise ImportError(
        "pgvector is required. Install it with: pip install pgvector"
    )

class Content(Base):
    __tablename__ = 'content'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String)
    create_time = Column(DateTime, nullable=False)
    update_time = Column(DateTime, nullable=False)
    content_type = Column(String, nullable=False)
    meta_info = Column(JSON)  # Changed from metadata to meta_info

class Message(Base):
    __tablename__ = 'messages'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('content.id'), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    name = Column(String)
    function_call = Column(JSON)
    tool_calls = Column(JSON)
    tool_call_id = Column(String)
    position = Column(Integer, nullable=False)
    create_time = Column(DateTime, nullable=False)
    embedding = Column(Vector(get_settings().embedding_dimensions))
    embedding_model = Column(String)

# Add the vector normalization trigger after table creation
def create_vector_triggers(target, connection, **kw):
    connection.execute(text("""
        CREATE OR REPLACE FUNCTION normalize_vector()
        RETURNS trigger AS $$
        BEGIN
            IF NEW.embedding IS NOT NULL THEN
                NEW.embedding = NEW.embedding / sqrt(NEW.embedding <#> NEW.embedding);
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """))

    connection.execute(text("""
        DROP TRIGGER IF EXISTS normalize_embedding ON messages;
        CREATE TRIGGER normalize_embedding
            BEFORE INSERT OR UPDATE ON messages
            FOR EACH ROW
            EXECUTE FUNCTION normalize_vector();
    """))

# Register the event listener
event.listen(Message.__table__, 'after_create', create_vector_triggers)
