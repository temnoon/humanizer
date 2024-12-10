# Humanizer

A tool for processing and analyzing (LLM and more) conversational content using PostgreSQL and vector operations.

## Features

- Import OpenAI chat archives
- Generate and store embeddings using Ollama
- Semantic search across conversations
- PostgreSQL + pgvector for vector operations
- CLI tools for management and search
- Secure credential handling

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL with pgvector extension
- Ollama for embeddings

```bash
# Install PostgreSQL and pgvector (MacOS)
brew install postgresql
brew install pgvector

# Start PostgreSQL
brew services start postgresql

# Create a conda environment
conda create -n humanizer python=3.9
conda activate humanizer

# Clone and install
git clone https://github.com/yourusername/humanizer.git
cd humanizer
pip install -e .
```

### Environment Setup

Create a `.env` file in the project root:

```env
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSIONS=512
HUMANIZER_DB_HOST=localhost
HUMANIZER_DB_PORT=5432
HUMANIZER_DB_NAME=humanizer
HUMANIZER_LOG_LEVEL=INFO
```

## Quick Start

1. Initialize database:
```bash
humanizer db init
```

2. Import conversations:
```bash
humanizer import /path/to/conversations.json
```

3. Generate embeddings:
```bash
humanizer embeddings update
```

## Common Commands

### Database Management

```bash
# Initialize database
humanizer db init

# Verify database setup
humanizer db verify

# Fix vector dimensions
humanizer db fix-dimensions
```

### Content Management

```bash
# Import conversations
humanizer import /path/to/file.json

# List conversations
humanizer list conversations --sort messages

# Update embeddings
humanizer embeddings update --batch-size 50
```

### Search Operations

```bash
# Semantic search
humanizer search semantic "your query here" --limit 5

# Find similar conversations
humanizer search conversation <conversation_id>

# Text search
humanizer search text "exact phrase"
```

### Configuration

```bash
# Show current config
humanizer config show

# Verify setup
humanizer config verify

# Test embedding model
humanizer embeddings test
```

## Project Status Commands

```bash
# Show embedding status
humanizer embeddings status

# Show project overview
humanizer project status

# Verify project setup
humanizer project verify
```

## Development

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=humanizer
```


## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## License

CC0 1.0 Universal


Release Notes for Humanizer 0.1.1:

# Humanizer 0.1.1 Release Notes

## New Features

### Search and Export Improvements
- Added `--uuids-only` flag to semantic search command for piping to export
- New `export markdown` command for formatted content display
- Improved markdown formatting with clear message structure and metadata

### Content Display
- Enhanced message display with role, conversation title, and timestamps
- Optional display of tool calls and function calls with `--show-tools` and `--show-json` flags
- Cleaner markdown formatting with proper section headers and content separation

### Search Refinements
- Added filters to remove search-only messages from results
- Improved message content filtering for more relevant results
- Added minimum content length filter to avoid short, non-substantive matches

## Technical Improvements
- Fixed command hierarchy for export functionality
- Added proper error handling for UUID parsing
- Improved metadata extraction and display

## Usage Example
```bash
# Search and export workflow
humanizer search semantic "your query" --uuids-only > results.txt
humanizer export markdown $(cat results.txt)

# Direct UUID export
humanizer export markdown UUID1 UUID2 UUID3

# Include tool and function calls
humanizer export markdown --show-tools --show-json UUID1
```

## Installation
```bash
pip install -e .
```

## Known Issues
- Need to implement conversation-level embeddings persistence
- Tool calls and function calls might need better formatting in markdown output

## Next Steps
- Implement conversation embedding storage
- Add date range filtering to search
- Improve search result relevance scoring
- Add support for custom markdown templates
