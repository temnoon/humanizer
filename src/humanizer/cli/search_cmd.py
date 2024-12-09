# src/humanizer/cli/search_cmd.py
import click
import asyncio
from humanizer.core.search.vector import VectorSearch
from humanizer.utils.logging import get_logger
from tabulate import tabulate

logger = get_logger(__name__)

@click.group()
def search():
    """Search conversations and messages"""
    pass

@search.command()
@click.argument('query')
@click.option('--limit', default=5, help='Number of results')
@click.option('--min-similarity', default=0.7, type=float, help='Minimum similarity score')
@click.option('--role', help='Filter by role (user/assistant)')
@click.option('--format', type=click.Choice(['text', 'json', 'table']), default='table')
def semantic(query: str, limit: int, min_similarity: float, role: str, format: str):
    """Semantic search using vector similarity"""
    async def run():
        searcher = VectorSearch()
        results = await searcher.search(
            query,
            limit=limit,
            min_similarity=min_similarity,
            role=role
        )

        if format == 'json':
            import json
            click.echo(json.dumps(results, indent=2))
        elif format == 'table':
            headers = ['Similarity', 'Role', 'Content', 'Conversation']
            rows = [
                (
                    f"{r['similarity']:.3f}",
                    r['role'],
                    r['content'][:100] + '...',
                    r['conversation_id']
                )
                for r in results
            ]
            click.echo(tabulate(rows, headers=headers, tablefmt='psql'))
        else:
            for r in results:
                click.echo(f"\nSimilarity: {r['similarity']:.3f}")
                click.echo(f"Role: {r['role']}")
                click.echo(f"Content: {r['content'][:200]}...")
                click.echo(f"Conversation: {r['conversation_id']}")
                click.echo("-" * 80)

    asyncio.run(run())

@search.command()
@click.argument('conversation_id')
@click.option('--similar/--no-similar', default=True, help='Find similar conversations')
@click.option('--limit', default=5, help='Number of results')
def conversation(conversation_id: str, similar: bool, limit: int):
    """Search for or find similar conversations"""
    async def run():
        searcher = VectorSearch()
        results = await searcher.find_similar_conversations(
            conversation_id,
            limit=limit
        )

        click.echo("\nSimilar Conversations:")
        for r in results:
            click.echo(f"\nTitle: {r['title']}")
            click.echo(f"Similarity: {r['similarity']:.3f}")
            click.echo(f"ID: {r['id']}")
            click.echo("-" * 80)

    asyncio.run(run())

@search.command()
@click.argument('text')
@click.option('--case-sensitive/--no-case-sensitive', default=False)
def text(text: str, case_sensitive: bool):
    """Search for text in conversation content"""
    async def run():
        from sqlalchemy import select
        from humanizer.db.models import Content, Message
        from humanizer.db.session import get_session

        async with get_session() as session:
            query = (
                select(Content.title, Message.role, Message.content)
                .join(Message, Content.id == Message.conversation_id)
            )

            if case_sensitive:
                query = query.where(Message.content.like(f'%{text}%'))
            else:
                query = query.where(Message.content.ilike(f'%{text}%'))

            results = await session.execute(query)
            rows = results.all()

            if rows:
                headers = ['Title', 'Role', 'Matching Content']
                table_rows = [
                    (title, role, content[:100] + '...')
                    for title, role, content in rows
                ]
                click.echo(tabulate(table_rows, headers=headers, tablefmt='psql'))
            else:
                click.echo("No matches found")

    asyncio.run(run())
