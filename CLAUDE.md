# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync
uv sync --frozen --all-extras --dev

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate.ps1

# Set up pre-commit hooks
pre-commit install

# Copy environment template
cp .env.example .env
```

### Testing
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=mcp_atlassian

# Run specific test file
uv run pytest tests/unit/confluence/test_client.py

# Run with verbose output
uv run pytest -v
```

### Code Quality
```bash
# Run all pre-commit checks
pre-commit run --all-files

# Run specific tools
uv run ruff check .
uv run ruff format .
uv run mypy .
```

### Running the Server
```bash
# Run with stdio transport (default)
uv run mcp-confluence

# Run with HTTP transport
uv run mcp-confluence --transport sse --port 9000

# Run with verbose logging
uv run mcp-confluence -vv

# Run OAuth setup wizard
uv run mcp-confluence --oauth-setup

# Run as HTTP service
uv run mcp-confluence --http-service --host 0.0.0.0 --port 8000
```

## Architecture Overview

This is a Model Context Protocol (MCP) server that provides integration with Confluence. The architecture is modular with clear separation of concerns:

### Core Components

1. **Server Layer** (`src/mcp_atlassian/servers/`):
   - `main.py`: Main FastMCP server with lifespan management and tool filtering
   - `confluence.py`: Confluence-specific MCP server instance
   - `context.py`: Application context for managing configuration and state

2. **Service Clients** (`src/mcp_atlassian/confluence/`):
   - `client.py`: Base API client using atlassian-python-api library
   - `config.py`: Configuration management and authentication setup
   - Various feature modules (pages, spaces, search, comments, etc.)

3. **Models** (`src/mcp_atlassian/models/`):
   - Pydantic models for API responses and data structures
   - Confluence-specific models

4. **HTTP Service** (`src/mcp_atlassian/http_service.py`):
   - FastAPI-based HTTP service with configurable base URL
   - Request-based authentication system
   - REST API for Confluence operations

5. **Authentication Support**:
   - **Cloud**: API Token, OAuth 2.0, Personal Access Token
   - **Server/Data Center**: Personal Access Token, Basic Auth
   - Multi-user authentication with token extraction from HTTP headers
   - Request-based authentication for HTTP service mode

### Key Design Patterns

- **Configuration Management**: Environment-based configuration with fallbacks
- **Tool Filtering**: Dynamic tool availability based on configuration and permissions
- **Transport Agnostic**: Supports stdio, SSE, and streamable-http transports
- **Authentication Middleware**: HTTP middleware for multi-user token handling
- **Read-Only Mode**: Configurable mode to disable write operations

### Testing Structure

- **Unit Tests**: `tests/unit/` - Individual component testing
- **Integration Tests**: `tests/integration/` - End-to-end workflow testing
- **Fixtures**: `tests/fixtures/` - Mock data and test utilities
- **Conftest**: `tests/conftest.py` - Shared test configuration

### Environment Variables

Key configuration variables (see `.env.example` for complete list):

```bash
# Service URLs
CONFLUENCE_URL=https://your-company.atlassian.net/wiki

# Authentication (Cloud)
CONFLUENCE_USERNAME=your.email@company.com
CONFLUENCE_API_TOKEN=your_token

# Authentication (Server/Data Center)
CONFLUENCE_PERSONAL_TOKEN=your_pat

# OAuth 2.0 (Cloud)
CONFLUENCE_OAUTH_CLIENT_ID=your_client_id
CONFLUENCE_OAUTH_CLIENT_SECRET=your_client_secret
CONFLUENCE_OAUTH_REDIRECT_URI=http://localhost:8080/callback
CONFLUENCE_OAUTH_SCOPE=read:confluence-content.all write:confluence-content offline_access
CONFLUENCE_OAUTH_CLOUD_ID=your_cloud_id

# Feature Controls
READ_ONLY_MODE=false
ENABLED_TOOLS=confluence_search,confluence_get_page,confluence_get_space
CONFLUENCE_SPACES_FILTER=DEV,TEAM,DOC

# Logging
MCP_VERBOSE=true
MCP_VERY_VERBOSE=true
MCP_LOGGING_STDOUT=true
```

### Multi-Cloud OAuth Support

The server supports multi-tenant scenarios where users provide their own OAuth tokens:

1. **Minimal Configuration**: Set `CONFLUENCE_OAUTH_ENABLE=true`
2. **User Authentication**: Users provide tokens via HTTP headers:
   - `Authorization: Bearer <user_oauth_token>`
   - `X-Atlassian-Cloud-Id: <user_cloud_id>`
3. **Token Isolation**: Each request uses user-specific tokens with no cross-tenant leakage

### Development Notes

- Use `uv` for dependency management (not pip)
- Pre-commit hooks enforce code quality (ruff, mypy, formatting)
- Type hints are required with modern Python syntax (`str | None`)
- Use Google-style docstrings for public APIs
- Configuration is loaded from environment variables with CLI overrides
- The server uses FastMCP for MCP protocol implementation
- Authentication is handled with fallback to global config
- HTTP service mode provides REST API with request-based authentication