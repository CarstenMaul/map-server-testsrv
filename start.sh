#!/bin/bash
# Start script for mcp-server-testsrv with SSL support
# This script assumes SSL certificates are in the ./ssl/ directory

set -e

# Configuration
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
SSL_CERT_PATH="${SSL_CERT_PATH:-./ssl/fullchain.pem}"
SSL_KEY_PATH="${SSL_KEY_PATH:-./ssl/privkey.pem}"

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

# Check if SSL certificates exist
if [[ -f "$SSL_CERT_PATH" && -f "$SSL_KEY_PATH" ]]; then
    echo -e "${GREEN}SSL certificates found. Starting server with HTTPS...${NC}"
    echo -e "${GREEN}Server will be available at: https://${HOST}:${PORT}${NC}"

    # Start server with SSL
    python server.py \
        --host "$HOST" \
        --port "$PORT" \
        --ssl-cert "$SSL_CERT_PATH" \
        --ssl-key "$SSL_KEY_PATH"
else
    echo -e "${YELLOW}SSL certificates not found at:${NC}"
    echo -e "${YELLOW}  - Certificate: $SSL_CERT_PATH${NC}"
    echo -e "${YELLOW}  - Private Key: $SSL_KEY_PATH${NC}"
    echo -e "${YELLOW}Starting server without SSL (HTTP only)...${NC}"
    echo -e "${GREEN}Server will be available at: http://${HOST}:${PORT}${NC}"

    # Start server without SSL
    python server.py \
        --host "$HOST" \
        --port "$PORT"
fi