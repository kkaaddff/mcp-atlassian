# MCP Confluence

![PyPI Version](https://img.shields.io/pypi/v/mcp-confluence)
![PyPI - Downloads](https://img.shields.io/pypi/dm/mcp-confluence)
![PePy - Total Downloads](https://static.pepy.tech/personalized-badge/mcp-confluence?period=total&units=international_system&left_color=grey&right_color=blue&left_text=Total%20Downloads)
[![Run Tests](https://github.com/sooperset/mcp-confluence/actions/workflows/tests.yml/badge.svg)](https://github.com/sooperset/mcp-confluence/actions/workflows/tests.yml)
![License](https://img.shields.io/github/license/sooperset/mcp-confluence)

Model Context Protocol (MCP) server for Confluence. This integration supports both Confluence Cloud and Server/Data Center deployments.

## Example Usage

Ask your AI assistant to:

- **🔍 AI-Powered Confluence Search** - "Find our OKR guide in Confluence and summarize it"
- **📄 Content Creation & Management** - "Create a tech design doc for XYZ feature"
- **📚 Space Management** - "List all spaces in our Confluence instance"
- **🏷️ Page Organization** - "Update the project documentation with meeting notes"

### Feature Demo

https://github.com/user-attachments/assets/7fe9c488-ad0c-4876-9b54-120b666bb785

### Compatibility

| Product        | Deployment Type    | Support Status              |
|----------------|--------------------|-----------------------------|
| **Confluence** | Cloud              | ✅ Fully supported           |
| **Confluence** | Server/Data Center | ✅ Supported (version 6.0+)  |

## Quick Start Guide

### 🔐 1. Authentication Setup

MCP Confluence supports three authentication methods:

#### A. API Token Authentication (Cloud) - **Recommended**

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **Create API token**, name it
3. Copy the token immediately

#### B. Personal Access Token (Server/Data Center)

1. Go to your profile (avatar) → **Profile** → **Personal Access Tokens**
2. Click **Create token**, name it, set expiry
3. Copy the token immediately

#### C. OAuth 2.0 Authentication (Cloud) - **Advanced**

> [!NOTE]
> OAuth 2.0 is more complex to set up but provides enhanced security features. For most users, API Token authentication (Method A) is simpler and sufficient.

1. Go to [Atlassian Developer Console](https://developer.atlassian.com/console/myapps/)
2. Create an "OAuth 2.0 (3LO) integration" app
3. Configure **Permissions** (scopes) for Confluence
4. Set **Callback URL** (e.g., `http://localhost:8080/callback`)
5. Run setup wizard:
   ```bash
   mcp-confluence --oauth-setup -v
   ```
6. Follow prompts for `Client ID`, `Secret`, `URI`, and `Scope`
7. Complete browser authorization
8. Add obtained credentials to `.env` or IDE config:
   - `CONFLUENCE_OAUTH_CLOUD_ID` (from wizard)
   - `CONFLUENCE_OAUTH_CLIENT_ID`
   - `CONFLUENCE_OAUTH_CLIENT_SECRET`
   - `CONFLUENCE_OAUTH_REDIRECT_URI`
   - `CONFLUENCE_OAUTH_SCOPE`

> [!IMPORTANT]
> For the standard OAuth flow described above, include `offline_access` in your scope (e.g., `read:confluence-content.all write:confluence-content offline_access`). This allows the server to refresh the access token automatically.

<details>
<summary>Alternative: Using a Pre-existing OAuth Access Token (BYOT)</summary>

If you are running mcp-confluence part of a larger system that manages Atlassian OAuth 2.0 access tokens externally (e.g., through a central identity provider or another application), you can provide an access token directly to this MCP server. This method bypasses the interactive setup wizard and the server's internal token management (including refresh capabilities).

**Requirements:**
- A valid Atlassian OAuth 2.0 Access Token with the necessary scopes for the intended operations.
- The corresponding `CONFLUENCE_OAUTH_CLOUD_ID` for your Atlassian instance.

**Configuration:**
To use this method, set the following environment variables (or use the corresponding command-line flags when starting the server):
- `CONFLUENCE_OAUTH_CLOUD_ID`: Your Atlassian Cloud ID. (CLI: `--oauth-cloud-id`)
- `CONFLUENCE_OAUTH_ACCESS_TOKEN`: Your pre-existing OAuth 2.0 access token. (CLI: `--oauth-access-token`)

**Important Considerations for BYOT:**
- **Token Lifecycle Management:** When using BYOT, the MCP server **does not** handle token refresh. The responsibility for obtaining, refreshing (before expiry), and revoking the access token lies entirely with you or the external system providing the token.
- **Token Expiry:** If the provided token expires during a session, the MCP server will fail all subsequent API calls until a fresh token is provided.
- **Security:** Ensure your token is stored and transmitted securely, as it grants access to your Confluence instance.
- **Scope Compatibility:** The scopes associated with your token must be compatible with the operations you intend to perform through the MCP server.

</details>

### ⚙️ 2. Environment Configuration

Create a `.env` file in your project root:

```bash
# For Confluence Cloud (API Token)
CONFLUENCE_URL=https://your-company.atlassian.net/wiki
CONFLUENCE_USERNAME=your.email@company.com
CONFLUENCE_API_TOKEN=your_api_token_here

# For Confluence Server/Data Center (Personal Access Token)
CONFLUENCE_URL=https://confluence.your-company.com
CONFLUENCE_PERSONAL_TOKEN=your_personal_access_token_here

# Optional: Filter by specific spaces (comma-separated)
CONFLUENCE_SPACES_FILTER=DEV,TEAM,DOC
```

### 🚀 3. Run the Server

#### Standard MCP Mode
```bash
# Using uv (recommended)
uv run mcp-confluence

# Using pip
pip install mcp-confluence
mcp-confluence
```

#### HTTP Service Mode
For use as a standalone HTTP service with configurable base URL and request-based authentication:

```bash
# Start HTTP service
mcp-confluence --http-service --host 0.0.0.0 --port 8000

# The service will be available at:
# - http://localhost:8000/confluence/execute - Execute operations
# - http://localhost:8000/health - Health check
```

#### HTTP Service API
The HTTP service accepts POST requests to `/confluence/execute` with the following structure:

```json
{
  "base_url": "https://your-company.atlassian.net/wiki",
  "auth_type": "basic|pat|oauth",
  "username": "your.email@company.com",  # For basic auth
  "api_token": "your_api_token",        # For basic auth
  "personal_token": "your_pat",          # For PAT auth
  "oauth_token": "your_oauth_token",      # For OAuth
  "cloud_id": "your_cloud_id",           # For OAuth
  "operation": "get_page|search_pages|get_space|list_spaces|create_page|update_page",
  "parameters": {
    "page_id": "12345",
    "query": "search term",
    "space_key": "TEAM",
    "limit": 50,
    "title": "Page Title",
    "content": "Page content",
    "parent_id": "123"
  }
}
```

## Configuration Options

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `CONFLUENCE_URL` | Base URL for Confluence instance | ✅ |
| `CONFLUENCE_USERNAME` | Email/username for Cloud auth | ✅ (Cloud) |
| `CONFLUENCE_API_TOKEN` | API token for Cloud auth | ✅ (Cloud) |
| `CONFLUENCE_PERSONAL_TOKEN` | Personal Access Token for Server/DC | ✅ (Server/DC) |
| `CONFLUENCE_SPACES_FILTER` | Comma-separated space keys to filter | ❌ |
| `CONFLUENCE_SSL_VERIFY` | Verify SSL certificates (true/false) | ❌ |
| `CONFLUENCE_OAUTH_*` | OAuth configuration variables | ❌ |

### Command Line Options

```bash
mcp-confluence [OPTIONS]

Options:
  -v, --verbose                       Increase verbosity
  --env-file PATH                     Path to .env file
  --confluence-url TEXT                Confluence URL
  --confluence-username TEXT           Confluence username/email
  --confluence-token TEXT               Confluence API token
  --confluence-personal-token TEXT      Confluence Personal Access Token
  --confluence-spaces-filter TEXT       Space filter
  --read-only                         Run in read-only mode
  --transport [stdio\|sse\|streamable-http]  Transport type
  --port INTEGER                       Port for HTTP transports
  --host TEXT                          Host for HTTP transports
  --http-service                       Run as HTTP service
  --help                              Show help message
```

## Available Operations

### Confluence Operations
- **Search Content**: Find pages, blogs, and attachments
- **Page Management**: Create, read, update pages
- **Space Operations**: List spaces, get space details
- **Comments**: Add and retrieve page comments
- **Labels**: Manage page labels
- **Attachments**: Handle page attachments
- **User Information**: Get user details and permissions

## Features

### 🔒 Security
- Multiple authentication methods
- Token validation and refresh
- SSL certificate verification
- Request-based authentication (HTTP service mode)

### 🚀 Performance
- Connection pooling
- Response caching
- Efficient data models
- Batch operations support

### 🛠️ Extensibility
- Tool filtering system
- Read-only mode
- Configurable spaces filter
- HTTP service mode for integration

## Development

### Setup Development Environment
```bash
# Clone repository
git clone https://github.com/sooperset/mcp-confluence.git
cd mcp-confluence

# Install dependencies
uv sync

# Set up pre-commit hooks
pre-commit install

# Copy environment template
cp .env.example .env
```

### Running Tests
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=mcp_confluence

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

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Verify your API token is valid and not expired
   - Check that your Confluence URL is correct
   - Ensure proper permissions for your user/token

2. **SSL Certificate Issues**
   - For self-signed certificates, set `CONFLUENCE_SSL_VERIFY=false`
   - Ensure your certificate chain is complete

3. **Permission Denied**
   - Verify your user has necessary permissions in Confluence
   - Check space and page-level permissions

4. **HTTP Service Issues**
   - Ensure all required authentication parameters are provided
   - Check that the base URL is accessible
   - Verify the operation and parameters are correct

### Debug Mode
Enable verbose logging to troubleshoot issues:

```bash
mcp-confluence -vv --env-file .env
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📚 [Documentation](https://github.com/sooperset/mcp-confluence/wiki)
- 🐛 [Report Issues](https://github.com/sooperset/mcp-confluence/issues)
- 💬 [Discussions](https://github.com/sooperset/mcp-confluence/discussions)

---

**Built with ❤️ for the Confluence community**