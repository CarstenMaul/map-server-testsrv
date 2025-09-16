#!/usr/bin/env python3
"""
MCP Server for Quote of the Day
Provides a tool to get a random quote from a static list of quotes.
"""

import random
from typing import Literal
from fastmcp import FastMCP

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

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="MCP Server for Quote of the Day")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--ssl-cert", help="Path to SSL certificate file")
    parser.add_argument("--ssl-key", help="Path to SSL private key file")

    args = parser.parse_args()

    # Configure SSL if certificates are provided
    ssl_context = None
    if args.ssl_cert and args.ssl_key:
        import ssl
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(args.ssl_cert, args.ssl_key)
        print(f"Starting MCP server with SSL on https://{args.host}:{args.port}")
    else:
        print(f"Starting MCP server on http://{args.host}:{args.port}")

    try:
        mcp.run(
            transport="streamable-http",
            host=args.host,
            port=args.port,
            ssl_context=ssl_context
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)