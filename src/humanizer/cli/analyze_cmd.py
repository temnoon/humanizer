# src/humanizer/cli/analyze_cmd.py
import click
import asyncio
from uuid import UUID
from humanizer.core.content.analyzer import ConversationAnalyzer

@click.group(name='analyze')
def analyze_cmd():
    """Analyze conversations and documents"""
    pass

@analyze_cmd.command(name='conversation')
@click.argument('conversation_id')
def analyze_conversation(conversation_id: str):
    """Analyze a single conversation for its characteristic message."""
    async def run():
        analyzer = ConversationAnalyzer()
        # Convert string to UUID
        cid = UUID(conversation_id)
        msg, sim = await analyzer.find_most_characteristic_message(cid)
        click.echo("Most Characteristic Message:")
        click.echo(f"Similarity: {sim:.3f}")
        click.echo(f"Content: {msg[:500]}...")  # Show first 500 chars

    asyncio.run(run())
