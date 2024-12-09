# src/humanizer/cli/list_cmd.py
import click
import asyncio
from sqlalchemy import select, func
from humanizer.db.session import get_session
from humanizer.db.models import Content, Message
from humanizer.utils.logging import get_logger
from tabulate import tabulate  # Add tabulate to your dependencies

logger = get_logger(__name__)

@click.group(name='list')
def list_cmd():
    """List and analyze conversations"""
    pass

@list_cmd.command(name='conversations')
@click.option('--sort', type=click.Choice(['title', 'messages', 'words']),
              default='title', help='Sort output by field')
@click.option('--limit', default=50, help='Maximum number of conversations to show')
@click.option('--format', type=click.Choice(['table', 'csv', 'json']),
              default='table', help='Output format')
def list_conversations(sort: str, limit: int, format: str):
    """List conversations with statistics"""
    async def run():
        async with get_session() as session:
            # Build query
            query = (
                select(
                    Content.title,
                    func.count(Message.id).label('message_count'),
                    func.sum(
                        func.array_length(
                            func.regexp_split_to_array(
                                func.coalesce(Message.content, ''),
                                '\\s+'
                            ),
                            1
                        )
                    ).label('word_count')
                )
                .join(Message, Content.id == Message.conversation_id)
                .group_by(Content.id, Content.title)
            )

            # Add sorting
            if sort == 'title':
                query = query.order_by(Content.title)
            elif sort == 'messages':
                query = query.order_by(func.count(Message.id).desc())
            elif sort == 'words':
                query = query.order_by(func.sum(
                    func.array_length(
                        func.regexp_split_to_array(
                            func.coalesce(Message.content, ''),
                            '\\s+'
                        ),
                        1
                    )
                ).desc())

            # Add limit
            query = query.limit(limit)

            # Execute query
            result = await session.execute(query)
            conversations = result.all()

            # Prepare output
            headers = ['Title', 'Messages', 'Words']
            rows = [
                (
                    title,
                    message_count,
                    word_count or 0  # Handle None values
                )
                for title, message_count, word_count in conversations
            ]

            # Format output
            if format == 'table':
                click.echo(tabulate(rows, headers=headers, tablefmt='psql'))
            elif format == 'csv':
                import csv
                import sys
                writer = csv.writer(sys.stdout)
                writer.writerow(headers)
                writer.writerows(rows)
            elif format == 'json':
                import json
                data = [
                    {
                        'title': title,
                        'messages': msg_count,
                        'words': word_count
                    }
                    for title, msg_count, word_count in rows
                ]
                click.echo(json.dumps(data, indent=2))

    # Run the async function
    asyncio.run(run())
