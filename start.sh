#!/bin/bash
# Start script for mcp-server-testsrv with SSL support
# This script assumes SSL certificates are in the ./ssl/ directory
#
# Usage:
#   ./start.sh                    # Start normally
#   DEBUG=true ./start.sh         # Start with debug logging
#   HOST=127.0.0.1 PORT=9000 ./start.sh  # Custom host/port
#   MCP_API_KEY=secret123 MCP_REQUIRE_AUTH=true ./start.sh  # With authentication
#
# Environment variables:
#   HOST         - Server host (default: 0.0.0.0)
#   PORT         - Server port (default: 8000)
#   DEBUG        - Enable debug logging (default: false)
#   MCP_API_KEY  - API key for authentication (optional)
#   MCP_REQUIRE_AUTH - Require authentication (default: false)
#   SSL_CERT_PATH - Path to SSL certificate (default: ./ssl/fullchain.pem)
#   SSL_KEY_PATH  - Path to SSL private key (default: ./ssl/privkey.pem)

set -e

# Configuration
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
SSL_CERT_PATH="${SSL_CERT_PATH:-./ssl/fullchain.pem}"
SSL_KEY_PATH="${SSL_KEY_PATH:-./ssl/privkey.pem}"
DEBUG="${DEBUG:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting mcp-server-testsrv...${NC}"

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}Warning: Virtual environment not detected. Attempting to activate...${NC}"
    if [[ -f "./bin/activate" ]]; then
        source ./bin/activate
        echo -e "${GREEN}Virtual environment activated.${NC}"
    else
        echo -e "${RED}Error: Virtual environment not found. Please activate your virtual environment first.${NC}"
        exit 1
    fi
fi

# Check if FastMCP is installed
if ! python -c "import fastmcp" 2>/dev/null; then
    echo -e "${YELLOW}FastMCP not found. Installing...${NC}"
    pip install fastmcp
fi

# Prepare debug argument
DEBUG_ARG=""
if [[ "$DEBUG" == "true" ]]; then
    DEBUG_ARG="--debug"
    echo -e "${YELLOW}🐛 Debug mode enabled - HTTP requests/responses will be logged${NC}"
fi

# Check if SSL certificates exist
if [[ -f "$SSL_CERT_PATH" && -f "$SSL_KEY_PATH" ]]; then
    echo -e "${GREEN}SSL certificates found. Starting server with HTTPS...${NC}"
    echo -e "${GREEN}Server will be available at: https://${HOST}:${PORT}${NC}"

    # Start server with SSL
    python server.py \
        --host "$HOST" \
        --port "$PORT" \
        --ssl-cert "$SSL_CERT_PATH" \
        --ssl-key "$SSL_KEY_PATH" \
        $DEBUG_ARG
else
    echo -e "${YELLOW}SSL certificates not found at:${NC}"
    echo -e "${YELLOW}  - Certificate: $SSL_CERT_PATH${NC}"
    echo -e "${YELLOW}  - Private Key: $SSL_KEY_PATH${NC}"
    echo -e "${YELLOW}Starting server without SSL (HTTP only)...${NC}"
    echo -e "${GREEN}Server will be available at: http://${HOST}:${PORT}${NC}"

    # Start server without SSL
    python server.py \
        --host "$HOST" \
        --port "$PORT" \
        $DEBUG_ARG
fi