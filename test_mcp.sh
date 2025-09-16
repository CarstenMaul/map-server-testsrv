#!/bin/bash
# Test script for MCP server with proper JSON-RPC initialization

HOST="${1:-localhost:8000}"
API_KEY="${2:-test123}"

echo "Testing MCP server at $HOST with API key: $API_KEY"
echo "=================================================="

# Test 1: Health check (should work without authentication)
echo "1. Testing health endpoint..."
curl -s "http://$HOST/health" | jq . || echo "Health endpoint failed"
echo ""

# Test 2: MCP Initialize (requires proper JSON-RPC)
echo "2. Testing MCP initialization..."
curl -X POST "http://$HOST/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "x-api-key: $API_KEY" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-06-18",
      "capabilities": {
        "sampling": {},
        "elicitation": {},
        "roots": {
          "listChanged": true
        }
      },
      "clientInfo": {
        "name": "test-client",
        "version": "1.0.0"
      }
    }
  }' --no-buffer
echo ""

# Test 3: List tools (after initialization)
echo "3. Testing tools/list..."
curl -X POST "http://$HOST/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list"
  }' | jq . || echo "Tools list failed"
echo ""

# Test 4: Call quote tool
echo "4. Testing get_quote_of_the_day tool..."
curl -X POST "http://$HOST/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "x-api-key: $API_KEY" \
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
  }' | jq . || echo "Quote tool failed"
echo ""

echo "Testing complete!"