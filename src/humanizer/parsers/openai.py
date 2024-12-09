# src/humanizer/parsers/openai.py
import ijson
from typing import Generator, Dict, Any
from zipfile import ZipFile
from decimal import Decimal
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class OpenAIConversationParser:
    """Enhanced OpenAI conversation parser"""

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        logger.info(f"Initialized parser for {file_path}")

    def _safe_float(self, value: Any) -> float:
        """Safely convert various types to float"""
        try:
            if isinstance(value, (float, int)):
                return float(value)
            if isinstance(value, Decimal):
                return float(value)
            if isinstance(value, str):
                return float(value)
            if isinstance(value, dict):
                for k in ['timestamp', 'time', 'create_time', 'date']:
                    if k in value and value[k]:
                        return self._safe_float(value[k])
            return 0.0
        except (ValueError, TypeError):
            return 0.0

    def _safe_str(self, value: Any) -> str:
        """Safely convert various types to string"""
        if value is None:
            return ''
        if isinstance(value, (dict, list)):
            return str(value)
        return str(value)

    def _extract_content(self, obj: Any) -> str:
        """Recursively extract content from various structures"""
        try:
            if obj is None:
                return ''
            if isinstance(obj, str):
                return obj
            if isinstance(obj, (list, tuple)):
                return ' '.join(self._extract_content(item) for item in obj)
            if isinstance(obj, dict):
                if 'content' in obj:
                    return self._extract_content(obj['content'])
                if 'parts' in obj:
                    return self._extract_content(obj['parts'])
                if 'text' in obj:
                    return self._extract_content(obj['text'])
                if 'value' in obj:
                    return self._extract_content(obj['value'])
                if 'message' in obj:
                    return self._extract_content(obj['message'])
                return ' '.join(self._extract_content(v) for v in obj.values())
            return self._safe_str(obj)
        except Exception as e:
            logger.error(f"Error extracting content: {str(e)}")
            return ''

    def _process_message(self, message: Any, conversation_id: str) -> Dict[str, Any]:
        """Process a message with flexible type handling"""
        base_message = {
            'id': str(conversation_id),
            'conversation_id': conversation_id,
            'role': 'unknown',
            'content': '',
            'create_time': 0
        }
        try:
            if not message or not isinstance(message, dict):
                return base_message

            msg_data = message.get('message', message)
            if not isinstance(msg_data, dict):
                return base_message

            author = msg_data.get('author', {})
            if isinstance(author, dict):
                role = author.get('role', msg_data.get('role', 'unknown'))
            else:
                role = msg_data.get('role', 'unknown')

            return {
                'id': self._safe_str(msg_data.get('id', base_message['id'])),
                'conversation_id': conversation_id,
                'role': self._safe_str(role),
                'content': self._extract_content(msg_data),
                'create_time': self._safe_float(msg_data.get('create_time', 0))
            }
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return base_message

    def _process_conversation(self, conversation: Any) -> Dict[str, Any]:
        """Process a conversation with flexible type handling"""
        try:
            if not isinstance(conversation, dict):
                return {
                    'id': 'unknown',
                    'title': 'Unknown',
                    'create_time': 0,
                    'update_time': 0,
                    'messages': []
                }

            conv_id = self._safe_str(conversation.get('id', 'unknown'))
            messages = []

            mapping = conversation.get('mapping', {})
            if isinstance(mapping, dict):
                for msg_id, msg_data in mapping.items():
                    try:
                        msg = self._process_message(msg_data, conv_id)
                        messages.append(msg)
                    except Exception as e:
                        logger.error(f"Error processing mapped message: {str(e)}")
                        continue

            messages.sort(key=lambda x: x['create_time'])

            return {
                'id': conv_id,
                'title': self._safe_str(conversation.get('title', 'Untitled')),
                'create_time': self._safe_float(conversation.get('create_time', 0)),
                'update_time': self._safe_float(conversation.get('update_time', 0)),
                'messages': messages
            }
        except Exception as e:
            logger.error(f"Error processing conversation: {str(e)}")
            raise

    def parse_file(self) -> Generator[Dict[str, Any], None, None]:
        """Parse conversations from file (either ZIP or JSON)"""
        if self.file_path.suffix == '.zip':
            yield from self._parse_zip()
        else:
            yield from self._parse_json()

    def _parse_zip(self) -> Generator[Dict[str, Any], None, None]:
        with ZipFile(self.file_path, 'r') as zip_ref:
            for file_name in zip_ref.namelist():
                if file_name.endswith('.json'):
                    with zip_ref.open(file_name) as f:
                        yield from self._parse_json_stream(f)

    def _parse_json(self) -> Generator[Dict[str, Any], None, None]:
        with open(self.file_path, 'rb') as f:
            yield from self._parse_json_stream(f)

    def _parse_json_stream(self, stream) -> Generator[Dict[str, Any], None, None]:
        parser = ijson.items(stream, 'item')
        for conversation in parser:
            try:
                processed = self._process_conversation(conversation)
                if processed['messages']:
                    yield processed
            except Exception as e:
                logger.error(f"Error processing conversation: {e}")
                continue
