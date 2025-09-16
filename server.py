#!/usr/bin/env python3
"""
MCP Server for Quote of the Day
Provides a tool to get a random quote from a static list of quotes.
"""

import random
import logging
from typing import Literal
from fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.routing import Route
import json
import time
import os

class DebugMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all HTTP requests and responses with headers."""

    def __init__(self, app, debug_enabled: bool = False):
        super().__init__(app)
        self.debug_enabled = debug_enabled
        self.logger = logging.getLogger("mcp.debug")

    async def dispatch(self, request: Request, call_next):
        if not self.debug_enabled:
            return await call_next(request)

        start_time = time.time()

        # Log request
        self.logger.info("=" * 80)
        self.logger.info(f"🔵 INCOMING REQUEST: {request.method} {request.url}")
        self.logger.info(f"📍 Path: {request.url.path}")
        self.logger.info(f"🔗 Query: {request.url.query}")

        # Log request headers
        self.logger.info("📥 REQUEST HEADERS:")
        for name, value in request.headers.items():
            self.logger.info(f"  {name}: {value}")

        # For MCP requests, try to log the body but don't interfere with streaming
        body_logged = False
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Only read body for non-streaming requests or initial MCP requests
                content_type = request.headers.get("content-type", "")
                accept = request.headers.get("accept", "")

                # Check if this is likely a streaming request
                is_streaming_request = (
                    "text/event-stream" in accept or
                    "stream" in content_type.lower()
                )

                if not is_streaming_request:
                    # Safe to read body for non-streaming requests
                    body = await request.body()
                    if body:
                        try:
                            # Try to parse as JSON for pretty printing
                            json_body = json.loads(body.decode())
                            self.logger.info("📝 REQUEST BODY (JSON):")
                            self.logger.info(json.dumps(json_body, indent=2))
                            body_logged = True
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            # Fall back to raw body
                            self.logger.info("📝 REQUEST BODY (RAW):")
                            self.logger.info(f"  {body}")
                            body_logged = True
                else:
                    self.logger.info("📝 REQUEST BODY: (streaming request - body not logged to avoid interference)")

            except Exception as e:
                self.logger.error(f"❌ Error reading request body: {e}")

        if not body_logged and request.method in ["POST", "PUT", "PATCH"]:
            self.logger.info("📝 REQUEST BODY: (not logged)")

        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log response
            self.logger.info(f"🟢 RESPONSE: {response.status_code}")
            self.logger.info(f"⏱️  Processing time: {process_time:.3f}s")

            # Log response headers
            self.logger.info("📤 RESPONSE HEADERS:")
            for name, value in response.headers.items():
                self.logger.info(f"  {name}: {value}")

            # For streaming responses, don't try to read the body
            response_content_type = response.headers.get("content-type", "")
            if "text/event-stream" in response_content_type:
                self.logger.info("📋 RESPONSE BODY: (Server-Sent Events stream - not logged)")
            elif hasattr(response, 'body') and response.body:
                try:
                    body_str = response.body.decode() if isinstance(response.body, bytes) else str(response.body)
                    try:
                        # Try to parse as JSON for pretty printing
                        json_body = json.loads(body_str)
                        self.logger.info("📋 RESPONSE BODY (JSON):")
                        self.logger.info(json.dumps(json_body, indent=2))
                    except json.JSONDecodeError:
                        # Fall back to raw body (truncated if too long)
                        if len(body_str) > 1000:
                            body_str = body_str[:1000] + "... (truncated)"
                        self.logger.info("📋 RESPONSE BODY (RAW):")
                        self.logger.info(f"  {body_str}")
                except Exception as e:
                    self.logger.info(f"📋 RESPONSE BODY: (unable to read: {e})")
            else:
                self.logger.info("📋 RESPONSE BODY: (empty or no body)")

            self.logger.info("=" * 80)
            return response

        except Exception as e:
            process_time = time.time() - start_time
            self.logger.error(f"❌ REQUEST FAILED after {process_time:.3f}s: {e}")
            self.logger.info("=" * 80)
            raise

class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication compatible with Microsoft Copilot Studio."""

    def __init__(self, app, api_key: str = None, require_auth: bool = False):
        super().__init__(app)
        self.api_key = api_key
        self.require_auth = require_auth
        self.logger = logging.getLogger("mcp.auth")

    async def dispatch(self, request: Request, call_next):
        # Skip authentication for health checks and non-MCP endpoints
        if request.url.path in ["/", "/health", "/ping"]:
            return await call_next(request)

        # Skip authentication if not required
        if not self.require_auth:
            return await call_next(request)

        # Extract API key from x-api-key header (Copilot Studio standard)
        client_api_key = request.headers.get("x-api-key")

        if not client_api_key:
            # Also check alternative header names for compatibility
            client_api_key = (
                request.headers.get("X-API-Key") or
                request.headers.get("Authorization", "").replace("Bearer ", "") or
                request.headers.get("api-key")
            )

        # Check if API key is required but missing
        if self.require_auth and not client_api_key:
            self.logger.warning(f"Missing API key for request to {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "message": "API key required. Please provide x-api-key header.",
                    "details": "This MCP server requires authentication via x-api-key header for Microsoft Copilot Studio compatibility."
                }
            )

        # Validate API key if provided and required
        if self.require_auth and self.api_key and client_api_key != self.api_key:
            self.logger.warning(f"Invalid API key for request to {request.url.path}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Forbidden",
                    "message": "Invalid API key provided.",
                    "details": "The API key provided does not match the expected value."
                }
            )

        # Log successful authentication
        if client_api_key:
            self.logger.info(f"Authenticated request to {request.url.path}")

        return await call_next(request)

# Static list of quotes
QUOTES = [
    {
        "quote": "The only way to do great work is to love what you do.",
        "author": "Steve Jobs"
    },
    {
        "quote": "Innovation distinguishes between a leader and a follower.",
        "author": "Steve Jobs"
    },
    {
        "quote": "Life is what happens to you while you're busy making other plans.",
        "author": "John Lennon"
    },
    {
        "quote": "The future belongs to those who believe in the beauty of their dreams.",
        "author": "Eleanor Roosevelt"
    },
    {
        "quote": "It is during our darkest moments that we must focus to see the light.",
        "author": "Aristotle"
    },
    {
        "quote": "The only impossible journey is the one you never begin.",
        "author": "Tony Robbins"
    },
    {
        "quote": "Success is not final, failure is not fatal: it is the courage to continue that counts.",
        "author": "Winston Churchill"
    },
    {
        "quote": "The way to get started is to quit talking and begin doing.",
        "author": "Walt Disney"
    },
    {
        "quote": "Don't be afraid to give up the good to go for the great.",
        "author": "John D. Rockefeller"
    },
    {
        "quote": "If you really look closely, most overnight successes took a long time.",
        "author": "Steve Jobs"
    },
    {
        "quote": "The greatest glory in living lies not in never falling, but in rising every time we fall.",
        "author": "Nelson Mandela"
    },
    {
        "quote": "Your time is limited, don't waste it living someone else's life.",
        "author": "Steve Jobs"
    },
    {
        "quote": "Spread love everywhere you go. Let no one ever come to you without leaving happier.",
        "author": "Mother Teresa"
    },
    {
        "quote": "When you reach the end of your rope, tie a knot in it and hang on.",
        "author": "Franklin D. Roosevelt"
    },
    {
        "quote": "Tell me and I forget. Teach me and I remember. Involve me and I learn.",
        "author": "Benjamin Franklin"
    },
    {
        "quote": "The best and most beautiful things in the world cannot be seen or even touched - they must be felt with the heart.",
        "author": "Helen Keller"
    },
    {
        "quote": "You will face many defeats in life, but never let yourself be defeated.",
        "author": "Maya Angelou"
    },
    {
        "quote": "In the end, we will remember not the words of our enemies, but the silence of our friends.",
        "author": "Martin Luther King Jr."
    },
    {
        "quote": "Whether you think you can or you think you can't, you're right.",
        "author": "Henry Ford"
    },
    {
        "quote": "The only person you are destined to become is the person you decide to be.",
        "author": "Ralph Waldo Emerson"
    }
]

# Initialize FastMCP server
mcp = FastMCP("mcp-server-testsrv")

@mcp.tool
def get_quote_of_the_day(category: Literal["random", "inspirational"] = "random") -> dict:
    """
    Get a quote of the day from a curated collection of inspirational quotes.

    Args:
        category: Type of quote to retrieve. Currently only supports 'random' and 'inspirational' (both return the same pool).

    Returns:
        A dictionary containing the quote text and author information.
    """
    selected_quote = random.choice(QUOTES)
    return {
        "quote": selected_quote["quote"],
        "author": selected_quote["author"],
        "category": category,
        "total_quotes_available": len(QUOTES)
    }

@mcp.tool
def get_random_quote() -> dict:
    """
    Get a random quote from the collection.

    Returns:
        A dictionary containing the quote text and author information.
    """
    return get_quote_of_the_day("random")

@mcp.tool
def get_quotes_count() -> dict:
    """
    Get the total number of quotes available in the collection.

    Returns:
        A dictionary containing the count of available quotes.
    """
    return {
        "total_quotes": len(QUOTES),
        "description": "Total number of quotes available in the collection"
    }

def setup_logging(debug_enabled: bool = False):
    """Configure logging for the application."""
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Configure debug logger if debug is enabled
    if debug_enabled:
        debug_logger = logging.getLogger("mcp.debug")
        debug_logger.setLevel(logging.INFO)

        # Create console handler with a different format for debug logs
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - DEBUG - %(message)s', datefmt='%H:%M:%S')
        console_handler.setFormatter(formatter)

        # Remove any existing handlers and add our custom one
        debug_logger.handlers.clear()
        debug_logger.addHandler(console_handler)
        debug_logger.propagate = False  # Don't propagate to root logger

if __name__ == "__main__":
    import argparse
    import sys
    import uvicorn

    parser = argparse.ArgumentParser(description="MCP Server for Quote of the Day")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--ssl-cert", help="Path to SSL certificate file")
    parser.add_argument("--ssl-key", help="Path to SSL private key file")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging of all HTTP requests and responses")
    parser.add_argument("--api-key", help="API key for authentication (can also be set via MCP_API_KEY environment variable)")
    parser.add_argument("--require-auth", action="store_true", help="Require API key authentication for all MCP requests")

    args = parser.parse_args()

    # Get API key from command line or environment variable
    api_key = args.api_key or os.getenv("MCP_API_KEY")
    require_auth = args.require_auth or os.getenv("MCP_REQUIRE_AUTH", "").lower() in ("true", "1", "yes")

    # Set up logging
    setup_logging(debug_enabled=args.debug)

    if args.debug:
        print("🐛 Debug mode enabled - all HTTP requests and responses will be logged")

    # Display authentication status
    if require_auth:
        if api_key:
            print("🔐 API key authentication enabled")
            print("💡 Clients must provide x-api-key header for Copilot Studio compatibility")
        else:
            print("⚠️  Authentication required but no API key configured!")
            print("💡 Set MCP_API_KEY environment variable or use --api-key parameter")
    else:
        print("🔓 Authentication disabled - server accepts all requests")

    # Configure SSL if certificates are provided
    if args.ssl_cert and args.ssl_key:
        print(f"Starting MCP server with SSL on https://{args.host}:{args.port}")
        uvicorn_kwargs = {
            "ssl_keyfile": args.ssl_key,
            "ssl_certfile": args.ssl_cert
        }
    else:
        print(f"Starting MCP server on http://{args.host}:{args.port}")
        uvicorn_kwargs = {}

    try:
        # Get the FastMCP HTTP app
        app = mcp.http_app()

        # Create health check endpoint function
        async def health_check(request):
            """Health check endpoint for monitoring and load balancers."""
            _ = request  # Starlette requires request parameter
            return JSONResponse({
                "status": "healthy",
                "service": "mcp-server-testsrv",
                "version": "1.0.0",
                "protocol": "streamable-http",
                "authentication": "x-api-key header supported" if require_auth else "disabled",
                "copilot_studio_compatible": True
            })

        # Add health route to the app's router
        health_route = Route("/health", health_check, methods=["GET"])
        app.router.routes.append(health_route)

        # Add API key authentication middleware (must be added first)
        app.add_middleware(ApiKeyMiddleware, api_key=api_key, require_auth=require_auth)

        # Add debug middleware if debug is enabled (should be last to log everything)
        if args.debug:
            app.add_middleware(DebugMiddleware, debug_enabled=True)

        # Run with uvicorn directly for SSL support
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            **uvicorn_kwargs
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)