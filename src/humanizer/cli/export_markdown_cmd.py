# src/humanizer/cli/export_markdown_cmd.py
import click
import asyncio
import json
from uuid import UUID
from typing import List
from sqlalchemy import select
from humanizer.db.session import get_session
from humanizer.db.models import Message, Content

@click.group(name='export')
def export_cmd():
    """Export content in various formats"""
    pass

@export_cmd.command(name='markdown')
@click.argument('uuids', nargs=-1)
@click.option('--show-tools', is_flag=True, default=False, help='Include tool outputs and function calls')
@click.option('--show-json', is_flag=True, default=False, help='Include raw JSON fields (function_call, tool_calls)')
def export_markdown(uuids: List[str], show_tools: bool, show_json: bool):
    """Export messages or conversations as Markdown given their UUIDs."""
    async def run():
        async with get_session() as session:
            for uid_str in uuids:
                uid = UUID(uid_str)

                # Check if this UUID is a message or a conversation
                # Try message first
                msg_result = await session.execute(
                    select(Message, Content)
                    .join(Content, Content.id == Message.conversation_id)
                    .where(Message.id == uid)
                )
                msg_row = msg_result.one_or_none()

                if msg_row:
                    # It's a message
                    message, content = msg_row
                    await print_message_markdown(message, content, show_tools, show_json)
                else:
                    # Not a message, maybe a conversation?
                    conv_result = await session.execute(
                        select(Content).where(Content.id == uid)
                    )
                    conv = conv_result.scalar_one_or_none()
                    if conv:
                        # It's a conversation: print all messages in it
                        msg_list_result = await session.execute(
                            select(Message).where(Message.conversation_id == uid).order_by(Message.position)
                        )
                        msgs = msg_list_result.scalars().all()
                        # Print each message
                        for m in msgs:
                            # We have conv already
                            await print_message_markdown(m, conv, show_tools, show_json)
                    else:
                        click.echo(f"UUID {uid} not found as message or conversation.", err=True)

    asyncio.run(run())

async def print_message_markdown(message: Message, conversation: Content, show_tools: bool, show_json: bool):
    # Extract role
    role = str(message.role) or "unknown"

    # Start printing
    click.echo("\n## Message")
    click.echo(f"**Role:** {role}")

    # Show metadata
    if str(conversation.title).strip():
        click.echo(f"**From Conversation:** {conversation.title}")
    if message.create_time is not None:
        click.echo(f"**Created:** {message.create_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Model info
    model_info = str(message.embedding_model) if message.embedding_model is not None else None
    if model_info is None and conversation.meta_info is not None:
        model_info = conversation.meta_info.get('model', conversation.meta_info.get('tool', None))
    if model_info is not None:
        click.echo(f"**Model:** {model_info}")

    # Content
    click.echo("\n### Content")
    click.echo(message.content)

    # Optionally show tool outputs or JSON fields
    if show_tools and message.tool_calls is not None:
        click.echo("\n### Tool Calls")
        click.echo("```json")
        click.echo(json.dumps(message.tool_calls, indent=2))
        click.echo("```")

    if show_json and message.function_call is not None:
        click.echo("\n### Function Call")
        click.echo("```json")
        click.echo(json.dumps(message.function_call, indent=2))
        click.echo("```")

    click.echo("\n---")  # Separator between messages
