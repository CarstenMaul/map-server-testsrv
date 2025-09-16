# API Key Authentication Implementation Guide

This document explains how to implement and configure API key authentication for the FastMCP server.

## Overview

The FastMCP server includes a custom middleware (`ApiKeyMiddleware`) that provides secure API key authentication compatible with Microsoft Copilot Studio and other HTTP clients.

## Architecture

### Authentication Flow

```
1. Client Request → 2. ApiKeyMiddleware → 3. Validation → 4. FastMCP Server
                                           ↓
                      401/403 ← Error Response (if invalid)
```

### Key Components

1. **ApiKeyMiddleware**: Custom Starlette middleware for authentication
2. **Header-based Authentication**: Multiple header formats supported
3. **Environment Configuration**: Flexible setup via env vars or CLI args
4. **Error Handling**: Proper JSON-RPC compatible error responses

## Implementation Details

### 1. Middleware Implementation

Located in `server.py`, the `ApiKeyMiddleware` class:

```python
class ApiKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, api_key: str = None, require_auth: bool = False):
        super().__init__(app)
        self.api_key = api_key
        self.require_auth = require_auth
        self.logger = logging.getLogger("mcp.auth")
```

**Key Features:**
- Inherits from `BaseHTTPMiddleware` for Starlette compatibility
- Configurable API key and authentication requirement
- Dedicated logging for authentication events

### 2. Authentication Logic

#### Header Extraction Priority

The middleware checks headers in this order:

1. **Primary**: `x-api-key` (Microsoft Copilot Studio standard)
2. **Alternative**: `X-API-Key` (case variation)
3. **Alternative**: `Authorization: Bearer <key>` (OAuth-style)
4. **Alternative**: `api-key` (lowercase)

```python
client_api_key = request.headers.get("x-api-key")

if not client_api_key:
    client_api_key = (
        request.headers.get("X-API-Key") or
        request.headers.get("Authorization", "").replace("Bearer ", "") or
        request.headers.get("api-key")
    )
```

#### Path Exemptions

Certain endpoints bypass authentication:
- `/` (root)
- `/health` (health check)
- `/ping` (ping endpoint)

```python
if request.url.path in ["/", "/health", "/ping"]:
    return await call_next(request)
```

#### Validation Process

1. **Skip if not required**: When `require_auth=False`
2. **Missing key check**: Return 401 if required but missing
3. **Invalid key check**: Return 403 if provided but incorrect
4. **Success logging**: Log successful authentication

### 3. Error Responses

#### 401 Unauthorized (Missing API Key)

```json
{
  "error": "Unauthorized",
  "message": "API key required. Please provide x-api-key header.",
  "details": "This MCP server requires authentication via x-api-key header for Microsoft Copilot Studio compatibility."
}
```

#### 403 Forbidden (Invalid API Key)

```json
{
  "error": "Forbidden",
  "message": "Invalid API key provided.",
  "details": "The API key provided does not match the expected value."
}
```

## Configuration

### 1. Command Line Arguments

```bash
python server.py \
  --api-key "your-secret-key-123" \
  --require-auth \
  --host 0.0.0.0 \
  --port 8000
```

**Arguments:**
- `--api-key`: Set the expected API key
- `--require-auth`: Enable authentication requirement

### 2. Environment Variables

```bash
export MCP_API_KEY="your-secret-key-123"
export MCP_REQUIRE_AUTH="true"
./start.sh
```

**Variables:**
- `MCP_API_KEY`: API key (overridden by `--api-key`)
- `MCP_REQUIRE_AUTH`: Enable auth (`true`, `1`, `yes`)

### 3. Startup Script

```bash
# With authentication
MCP_API_KEY=secret123 MCP_REQUIRE_AUTH=true ./start.sh

# Without authentication (default)
./start.sh
```

### 4. Middleware Registration

The middleware is registered before other middleware to ensure authentication happens first:

```python
# Add API key authentication middleware (must be added first)
app.add_middleware(ApiKeyMiddleware, api_key=api_key, require_auth=require_auth)

# Add debug middleware if debug is enabled (should be last to log everything)
if args.debug:
    app.add_middleware(DebugMiddleware, debug_enabled=True)
```

## Microsoft Copilot Studio Integration

### Custom Connector Setup

1. **Create Custom Connector** in Power Apps
2. **Set Authentication Type**: `API Key`
3. **Configure API Key**:
   - **Parameter Label**: `API Key`
   - **Parameter Name**: `x-api-key`
   - **Parameter Location**: `Header`

### Request Format

Copilot Studio will automatically include the header:

```http
POST /mcp HTTP/1.1
Host: your-server.com
Content-Type: application/json
Accept: application/json, text/event-stream
x-api-key: your-configured-key
x-ms-agentic-protocol: mcp-streamable-1.0

{
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
}
```

## Security Considerations

### 1. API Key Generation

Generate strong API keys:

```bash
# Using openssl (32 characters)
openssl rand -hex 16

# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Using uuidgen
uuidgen | tr -d '-'
```

### 2. Storage and Management

**Production Best Practices:**
- Store API keys in environment variables or secure vaults
- Use different keys for development/staging/production
- Rotate keys regularly
- Never commit keys to version control
- Use strong, unpredictable values

### 3. Transport Security

**HTTPS Requirements:**
- Always use HTTPS in production
- API keys in headers are transmitted with each request
- HTTP exposes keys in plain text

### 4. Logging and Monitoring

**Security Logging:**
```python
# Success
self.logger.info(f"Authenticated request to {request.url.path}")

# Failure
self.logger.warning(f"Missing API key for request to {request.url.path}")
self.logger.warning(f"Invalid API key for request to {request.url.path}")
```

**Monitoring Recommendations:**
- Monitor authentication failure rates
- Alert on unusual access patterns
- Log client IP addresses for suspicious activity

## Testing

### 1. Manual Testing

```bash
# Test with valid key
curl -H "x-api-key: your-key" https://your-server.com/mcp

# Test without key (should fail)
curl https://your-server.com/mcp

# Test with invalid key (should fail)
curl -H "x-api-key: wrong-key" https://your-server.com/mcp
```

### 2. Automated Testing

Use the included test script:

```bash
# Test with authentication
./test_mcp.sh your-server.com:8000 your-api-key

# Test locally
./test_mcp.sh localhost:8000 test123
```

### 3. Health Check Verification

```bash
# Health endpoint (no auth required)
curl https://your-server.com/health

# Should return authentication status
{
  "status": "healthy",
  "authentication": "x-api-key header supported",
  "copilot_studio_compatible": true
}
```

## Troubleshooting

### Common Issues

1. **"Missing API key"**: Client not sending `x-api-key` header
2. **"Invalid API key"**: Key mismatch between client and server
3. **Still getting 401**: Check if authentication is actually enabled
4. **Middleware not working**: Ensure middleware is registered correctly

### Debug Mode

Enable detailed logging:

```bash
DEBUG=true MCP_API_KEY=key123 MCP_REQUIRE_AUTH=true ./start.sh
```

This will log all requests including headers and authentication attempts.

### Configuration Verification

Check server startup messages:

```
🔐 API key authentication enabled
💡 Clients must provide x-api-key header for Copilot Studio compatibility
```

Or without authentication:

```
🔓 Authentication disabled - server accepts all requests
```

## Advanced Configuration

### Custom Header Names

To support additional header names, modify the middleware:

```python
# Add custom header check
client_api_key = (
    request.headers.get("x-api-key") or
    request.headers.get("X-API-Key") or
    request.headers.get("Authorization", "").replace("Bearer ", "") or
    request.headers.get("api-key") or
    request.headers.get("custom-auth-header")  # Add custom header
)
```

### Multiple API Keys

For multiple valid keys, modify validation:

```python
valid_keys = [self.api_key, "backup-key", "admin-key"]
if self.require_auth and self.api_key and client_api_key not in valid_keys:
    # Return 403 error
```

### Rate Limiting

Consider adding rate limiting middleware after authentication:

```python
app.add_middleware(ApiKeyMiddleware, api_key=api_key, require_auth=require_auth)
app.add_middleware(RateLimitMiddleware, calls_per_minute=60)  # Custom implementation
```

## Summary

The API key authentication implementation provides:

- **Secure**: Header-based authentication with proper error handling
- **Compatible**: Optimized for Microsoft Copilot Studio integration
- **Flexible**: Multiple header formats and configuration options
- **Observable**: Comprehensive logging and health check integration
- **Production-ready**: SSL support and security best practices

For production deployment, ensure you:
1. Generate strong API keys
2. Use HTTPS/SSL
3. Set appropriate authentication requirements
4. Monitor authentication logs
5. Follow security best practices for key management