# Microsoft Copilot Studio Integration Guide

This MCP server is compatible with Microsoft Copilot Studio via Power Automate custom connectors.

## Authentication Setup

### Server Configuration

The server supports API key authentication compatible with Copilot Studio:

```bash
# Start with authentication enabled
MCP_API_KEY=your-secret-key MCP_REQUIRE_AUTH=true ./start.sh

# Or use command line parameters
python server.py --api-key your-secret-key --require-auth
```

### Environment Variables

- `MCP_API_KEY`: Your API key for authentication
- `MCP_REQUIRE_AUTH`: Set to `true` to require authentication

## Copilot Studio Custom Connector Setup

### 1. Create Custom Connector

1. In Power Apps, go to **Data** > **Custom connectors**
2. Click **New custom connector** > **Import from blank**
3. Set the connector name: `MCP Quote Server`

### 2. General Configuration

- **Host**: Your server host (e.g., `your-domain.com`)
- **Base URL**: `/mcp`
- **Scheme**: `HTTPS` (recommended)

### 3. Security Configuration

1. Go to the **Security** tab
2. Select **Authentication type**: `API Key`
3. Configure the API key:
   - **Parameter label**: `API Key`
   - **Parameter name**: `x-api-key`
   - **Parameter location**: `Header`

### 4. Definition

The server automatically exposes these MCP tools:

- `get_quote_of_the_day`: Get a quote with optional category
- `get_random_quote`: Get a random quote
- `get_quotes_count`: Get total number of available quotes

### 5. Test Connection

Use the test feature with your API key to verify the connection works.

## Headers Required

When connecting from Copilot Studio, the following header must be included:

```
x-api-key: your-secret-key
```

The server also accepts these alternative header formats for compatibility:
- `X-API-Key`
- `Authorization: Bearer your-secret-key`
- `api-key`

## Health Check

Monitor server status via the health endpoint:

```bash
curl -H "x-api-key: your-secret-key" https://your-server.com/health
```

Response:
```json
{
  "status": "healthy",
  "service": "mcp-server-testsrv",
  "version": "1.0.0",
  "protocol": "streamable-http",
  "authentication": "x-api-key header supported",
  "copilot_studio_compatible": true
}
```

## Security Best Practices

1. Use HTTPS in production
2. Generate strong, unique API keys
3. Rotate API keys regularly
4. Monitor authentication logs
5. Use environment variables for sensitive configuration

## Testing the MCP Server

### Manual Testing

Use the included test script:

```bash
# Test with default settings
./test_mcp.sh

# Test with custom host and API key
./test_mcp.sh your-server.com:8000 your-api-key
```

### Correct MCP Request Format

MCP requires JSON-RPC 2.0 format. **Do not send empty requests!**

#### 1. Initialize Connection
```bash
curl -X POST "https://your-server.com/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "x-api-key: your-api-key" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-06-18",
      "capabilities": {},
      "clientInfo": {
        "name": "copilot-studio",
        "version": "1.0.0"
      }
    }
  }'
```

#### 2. List Available Tools
```bash
curl -X POST "https://your-server.com/mcp" \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list"
  }'
```

#### 3. Call a Tool
```bash
curl -X POST "https://your-server.com/mcp" \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "get_quote_of_the_day",
      "arguments": {
        "category": "random"
      }
    }
  }'
```

## Troubleshooting

### Common Issues

1. **"Load failed" / TypeError**: Empty request body - MCP requires proper JSON-RPC format
2. **401 Unauthorized**: Missing `x-api-key` header
3. **403 Forbidden**: Invalid API key
4. **Connection Failed**: Check host, port, and SSL configuration

### Microsoft Copilot Studio Specific

- Ensure custom connector is configured with **Base URL**: `/mcp`
- Use **Authentication Type**: `API Key` in header `x-api-key`
- The server supports the `x-ms-agentic-protocol: "mcp-streamable-1.0"` header

### Debug Mode

Enable debug logging to troubleshoot:

```bash
DEBUG=true MCP_API_KEY=your-key MCP_REQUIRE_AUTH=true ./start.sh
```

This will log all HTTP requests and responses, including headers.