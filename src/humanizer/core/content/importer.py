# src/humanizer/core/content/importer.py
from datetime import datetime
from typing import List
from uuid import UUID, uuid4
from pathlib import Path
from humanizer.parsers.openai import OpenAIConversationParser
from humanizer.db.models import Content, Message
from humanizer.db.session import get_session
from humanizer.utils.logging import get_logger

logger = get_logger(__name__)

def sanitize_text(text: str | None) -> str:
    """Sanitize text content for PostgreSQL."""
    if text is None:
        return ''
    # Remove null bytes
    text = text.replace('\x00', '')
    # Replace invalid UTF-8 sequences
    text = text.encode('utf-8', 'replace').decode('utf-8')
    return text

class ConversationImporter:
    """Handles importing OpenAI conversation archives"""

    async def import_file(self, path: Path) -> List[UUID]:
        """Import conversations from file"""
        parser = OpenAIConversationParser(path)
        imported_ids = []

        try:
            async with get_session() as session:
                for conversation in parser.parse_file():
                    # Create content record
                    content = Content(
                        id=uuid4(),
                        title=sanitize_text(conversation['title']),
                        create_time=datetime.fromtimestamp(conversation['create_time']),
                        update_time=datetime.fromtimestamp(conversation['update_time']),
                        content_type='conversation',
                        meta_info={
                            'original_id': conversation['id'],
                            'source': 'openai_export'
                        }
                    )
                    session.add(content)

                    # Create message records
                    for pos, msg in enumerate(conversation['messages']):
                        message = Message(
                            id=uuid4(),
                            conversation_id=content.id,
                            role=sanitize_text(msg['role']),
                            content=sanitize_text(msg['content']),
                            name=sanitize_text(msg.get('name')),
                            tool_call_id=sanitize_text(msg.get('tool_call_id')),
                            position=pos,
                            create_time=datetime.fromtimestamp(msg['create_time'])
                        )
                        session.add(message)

                    imported_ids.append(content.id)
                    logger.info(f"Importing conversation: {content.title}")

                    # Commit after each conversation to avoid large transactions
                    await session.commit()

                logger.info(f"Successfully imported {len(imported_ids)} conversations")

        except Exception as e:
            logger.error(f"Import failed: {str(e)}")
            raise

        return imported_ids
