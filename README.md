# Google Chat MCP Server

A Model Context Protocol (MCP) server that provides comprehensive Google Chat API integration. This server implements the [MCP specification](https://modelcontextprotocol.io/) over Streamable HTTP transport, enabling AI assistants and agents to interact with Google Chat spaces, messages, and members through a standardized interface.

## 🚀 Features

### 📧 Message Management (5 tools)
- **send_message**: Send text or rich card messages to spaces
- **list_messages**: List messages in a space with filtering options
- **get_message**: Retrieve specific message details by ID
- **update_message**: Edit existing messages
- **delete_message**: Remove messages from spaces

### 🏠 Space Management (5 tools)
- **list_spaces**: List accessible Chat spaces with filtering
- **get_space**: Get detailed information about a specific space
- **create_space**: Create new group chat spaces
- **update_space**: Modify space settings and properties
- **delete_space**: Remove spaces (admin only)

### 👥 Member Management (6 tools)
- **list_members**: List members in a space
- **get_member**: Get detailed member information
- **create_membership**: Add users to spaces
- **update_membership**: Change member roles and permissions
- **delete_membership**: Remove members from spaces
- **find_direct_message**: Find or create DM spaces with users

### 🔍 Search Capabilities (4 tools)
- **search_messages**: Search messages across spaces with query filters
- **search_spaces**: Find spaces by name or description
- **search_members**: Search for members across spaces
- **get_recent_activity**: Get recent activity across accessible spaces

### 🔗 Webhook Integration (5 tools)
- **send_webhook_message**: Send messages via incoming webhooks
- **create_card_message**: Create rich interactive card messages
- **parse_webhook_event**: Parse incoming webhook events
- **validate_webhook_signature**: Validate webhook security signatures
- **create_interactive_card**: Create cards with buttons and actions

## 📋 Prerequisites

### 1. Google Cloud Project Setup
1. Create or select a Google Cloud Project
2. Enable the Google Chat API:
   ```bash
   gcloud services enable chat.googleapis.com
   ```

### 2. Service Account Creation
1. Create a service account:
   ```bash
   gcloud iam service-accounts create google-chat-mcp-server \
     --description="Service account for Google Chat MCP Server" \
     --display-name="Google Chat MCP Server"
   ```

2. Download the service account key:
   ```bash
   gcloud iam service-accounts keys create google-chat-mcp-server-key.json \
     --iam-account=google-chat-mcp-server@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

### 3. Google Chat App Configuration
1. Go to [Google Cloud Console > APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials)
2. Create a new "Google Chat App" credential
3. Configure the Chat app with:
   - **App name**: Google Chat MCP Server
   - **Avatar URL**: (optional)
   - **Description**: MCP server for Google Chat integration
   - **Functionality**: Can be added to spaces and group conversations
   - **Connection settings**: HTTP endpoint (for webhooks, if needed)
   - **Visibility**: Available to specific people/groups in your domain

### 4. Required OAuth Scopes
The service account needs these OAuth 2.0 scopes:
- `https://www.googleapis.com/auth/chat.bot`
- `https://www.googleapis.com/auth/chat.spaces`
- `https://www.googleapis.com/auth/chat.messages`
- `https://www.googleapis.com/auth/chat.memberships`

## 🛠️ Installation

### 1. Clone and Setup
```bash
git clone https://github.com/pueteam/google-chat-mcp-server.git
cd google-chat-mcp-server
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy the example environment file and configure:
```bash
cp .env.example .env
```

Edit `.env` with your settings:
```bash
# Required: Path to service account JSON file
GOOGLE_APPLICATION_CREDENTIALS=/path/to/google-chat-mcp-server-key.json

# Optional: Default space for operations (can be overridden per tool call)
GOOGLE_CHAT_DEFAULT_SPACE=spaces/AAAA1234567

# Optional: Logging level
LOG_LEVEL=INFO
```

### 3. Verify Setup
Test authentication and basic functionality:
```bash
source venv/bin/activate
python -c "
from src.google_chat_mcp.auth.google_auth import GoogleChatAuth
import asyncio

async def test():
    auth = GoogleChatAuth('google-chat-mcp-server-key.json')
    await auth.initialize()
    print('✅ Authentication successful')

asyncio.run(test())
"
```

## 🚀 Running the Server

### MCP Streamable HTTP Server (Recommended)
The server supports both SSE streaming and JSON response modes:

```bash
# Start with SSE streaming (default)
python stateless_streamable_server.py --port 8004 --response sse

# Start with JSON responses
python stateless_streamable_server.py --port 8004 --response json

# With custom log level
python stateless_streamable_server.py --port 8004 --log-level DEBUG --response sse
```

**Server Options:**
- `--port, -p`: Port to listen on (default: 8004)
- `--log-level, -l`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `--response, -r`: Response type (sse, json)

### MCP Endpoint
The server will be available at:
- **Endpoint**: `http://localhost:8004/mcp`
- **Protocol**: MCP Streamable HTTP
- **Transport**: HTTP with JSON-RPC 2.0

## 🔧 MCP Client Integration

### Configuration
To use this server with an MCP client, add the following configuration:

```json
{
  "name": "google_chat_mcp_server",
  "endpoint": "http://localhost:8004/mcp",
  "transport_type": "http",
  "enabled": true,
  "auth_type": "none",
  "description": "Google Chat API integration with 25 tools for messaging, spaces, members, search, and webhooks"
}
```

### Connection Details
Connect to the server using:
- **URL**: `http://localhost:8004/mcp`
- **Protocol**: MCP Streamable HTTP
- **Headers**:
  - `Accept: application/json, text/event-stream`
  - `Content-Type: application/json`

### Available JSON-RPC Methods
- `initialize`: Initialize MCP session
- `tools/list`: List all 25 available tools
- `tools/call`: Execute a specific tool
- `ping`: Health check

## 📚 Tool Usage Examples

### Send a Message
```json
{
  "jsonrpc": "2.0",
  "id": "msg1",
  "method": "tools/call",
  "params": {
    "name": "send_message",
    "arguments": {
      "space": "spaces/AAAA1234567",
      "text": "Hello from MCP!"
    }
  }
}
```

### Create a Rich Card
```json
{
  "jsonrpc": "2.0",
  "id": "card1",
  "method": "tools/call",
  "params": {
    "name": "create_card_message",
    "arguments": {
      "title": "Status Update",
      "subtitle": "System Health Check",
      "text": "All systems operational",
      "color": "#00FF00",
      "buttons": [
        {
          "text": "View Details",
          "url": "https://dashboard.example.com"
        }
      ]
    }
  }
}
```

### Search Messages
```json
{
  "jsonrpc": "2.0",
  "id": "search1",
  "method": "tools/call",
  "params": {
    "name": "search_messages",
    "arguments": {
      "query": "project status",
      "limit": 10,
      "order_by": "create_time desc"
    }
  }
}
```

## 🏗️ Architecture

### Project Structure
```
google-chat-mcp-server/
├── src/
│   └── google_chat_mcp/
│       ├── auth/
│       │   └── google_auth.py      # Google API authentication
│       ├── tools/
│       │   ├── __init__.py         # Tool exports
│       │   ├── base.py             # Base tool class
│       │   ├── messages.py         # Message management tools
│       │   ├── spaces.py           # Space management tools
│       │   ├── members.py          # Member management tools
│       │   ├── search.py           # Search tools
│       │   └── webhooks.py         # Webhook tools
│       └── server.py               # Legacy STDIO server
├── stateless_streamable_server.py  # MCP Streamable HTTP server
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment configuration template
├── Dockerfile                      # Container image definition
└── README.md                       # This file
```

### MCP Compliance
This server is fully compliant with the MCP specification:
- ✅ **Protocol Version**: 2024-11-05
- ✅ **Transport**: Streamable HTTP with SSE and JSON modes
- ✅ **JSON-RPC 2.0**: Proper request/response format
- ✅ **Error Handling**: Standard JSON-RPC error codes
- ✅ **Tool Schema**: OpenAPI-compatible tool definitions
- ✅ **Content Types**: Structured text content responses

## 🔍 Troubleshooting

### Common Issues

**Authentication Errors**
```
Error: Could not load the default credentials
```
- Verify `GOOGLE_APPLICATION_CREDENTIALS` path is correct
- Ensure service account key file exists and is readable
- Check service account has required OAuth scopes

**API Permission Errors**
```
Error: The caller does not have permission to access the Chat API
```
- Verify Google Chat API is enabled in your project
- Ensure Chat app is properly configured
- Check service account has been added to relevant spaces

**Connection Issues**
```
Error: Connection refused to localhost:8004
```
- Verify server is running: `ps aux | grep stateless_streamable_server`
- Check port availability: `lsof -i :8004`
- Review server logs for startup errors

**Tool Execution Errors**
```
Error: Invalid space name
```
- Ensure space names use format: `spaces/AAAA1234567`
- Verify bot has access to the target space
- Check space exists and is accessible

### Debug Mode
Run with debug logging for detailed troubleshooting:
```bash
python stateless_streamable_server.py --port 8004 --log-level DEBUG
```

### Health Check
Verify server health:
```bash
curl -H "Accept: application/json, text/event-stream" \
     -H "Content-Type: application/json" \
     -X POST http://localhost:8004/mcp \
     -d '{"jsonrpc":"2.0","id":"health","method":"ping","params":{}}'
```

## 📊 Monitoring & Logs

### Server Logs
Monitor server activity:
```bash
# Follow real-time logs
tail -f google_chat_mcp_*.log

# Search for errors
grep -i error google_chat_mcp_*.log

# View recent startup
head -20 google_chat_mcp_*.log
```

### Performance Metrics
- **Tools Available**: 25 total across 5 categories
- **Response Time**: Typically < 500ms for API calls
- **Concurrent Connections**: Supports multiple MCP clients
- **Memory Usage**: ~60-80MB baseline

## 🤝 Integration with AI Assistants

This MCP server follows the open MCP standard, making it compatible with any MCP-compliant client or AI assistant framework.

### Key Integration Features
- **Standard MCP Protocol**: Works with any MCP-compliant client
- **Tool Discovery**: Automatic tool discovery via the `tools/list` method
- **Error Handling**: Graceful error handling with standard JSON-RPC error codes
- **Schema Validation**: OpenAPI-compatible tool schemas for reliable integration

### Quick Start
1. Start the MCP server as shown above
2. Configure your MCP client to connect to `http://localhost:8004/mcp`
3. The client will automatically discover all 25 available tools
4. Begin using Google Chat tools in your AI workflows

## 🔒 Security Considerations

- **Service Account Keys**: Store securely, never commit to version control
- **Webhook Signatures**: Always validate webhook signatures when using webhook tools
- **Network Access**: Consider running on localhost or secure internal networks
- **Space Permissions**: Bot only has access to spaces it's been added to
- **Rate Limiting**: Google Chat API has rate limits; server handles backoff

## 🚀 Docker Support

Run the server using Docker:

```bash
# Build the image
docker build -t google-chat-mcp-server .

# Run the container
docker run -p 8004:8004 \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/google-chat-mcp-server-key.json \
  -v $(pwd)/credentials:/app/credentials \
  google-chat-mcp-server
```

## 📈 Roadmap

- [ ] **Event Streaming**: Real-time Chat events via webhooks
- [ ] **Batch Operations**: Bulk message and member operations
- [ ] **Advanced Filtering**: More sophisticated search and filtering options
- [ ] **Analytics**: Message and space usage analytics
- [ ] **Caching**: Intelligent caching for frequently accessed data
- [ ] **CLI Tool**: Command-line interface for direct tool invocation
- [ ] **Web UI**: Simple web interface for testing and debugging

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs, feature requests, or improvements.

### Development Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/google-chat-mcp-server.git
cd google-chat-mcp-server

# Setup development environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-asyncio black ruff mypy  # Dev dependencies

# Run tests
pytest tests/

# Format and lint
black src/ tests/
ruff src/ tests/
mypy src/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**🤖 Built with the Model Context Protocol**
This server implements the open [MCP standard](https://modelcontextprotocol.io) for AI-application integration.
