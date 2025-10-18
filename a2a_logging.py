#!/usr/bin/env python3
"""A2A Traffic Logging Utility.

Logs all A2A JSON-RPC requests and responses to individual files
in the a2a_traffic/ directory for debugging and analysis.

Provides both a direct logging function and ASGI middleware for automatic logging.
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict


LOG_DIR = Path("a2a_traffic")


def ensure_log_dir():
    """Create the a2a_traffic directory if it doesn't exist."""
    LOG_DIR.mkdir(exist_ok=True)


def log_a2a_traffic(agent_name: str, request_data: Dict[str, Any], response_data: Dict[str, Any]):
    """Log an A2A request/response pair to a JSON file.

    Args:
        agent_name: Name of the agent handling the request (e.g., "supplier", "chef", "waiter")
        request_data: The JSON-RPC request data
        response_data: The JSON-RPC response data
    """
    ensure_log_dir()

    # Generate timestamp-based filename
    timestamp = int(time.time() * 1000000)  # Microsecond precision for uniqueness
    filename = f"{agent_name}_{timestamp}.json"
    filepath = LOG_DIR / filename

    # Create log entry with both request and response
    log_entry = {
        "timestamp": time.time(),
        "timestamp_human": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "agent": agent_name,
        "request": request_data,
        "response": response_data
    }

    # Write to file with pretty formatting
    with open(filepath, 'w') as f:
        json.dump(log_entry, f, indent=2, sort_keys=False)

    print(f"[A2A LOG] Logged traffic to {filepath}")


# ASGI Middleware for standalone A2A servers
try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response

    class A2ALoggingMiddleware(BaseHTTPMiddleware):
        """Middleware to log A2A JSON-RPC requests and responses."""

        def __init__(self, app, agent_name: str):
            super().__init__(app)
            self.agent_name = agent_name

        async def dispatch(self, request: Request, call_next: Callable):
            # Only log POST requests to the JSON-RPC endpoint (not agent card)
            if request.method == "POST" and not request.url.path.startswith("/.well-known/"):
                # Read request body
                body = await request.body()

                try:
                    request_data = json.loads(body) if body else {}
                except json.JSONDecodeError:
                    request_data = {"raw_body": body.decode('utf-8', errors='replace')}

                # Re-create request with body (since we consumed it)
                from starlette.datastructures import Headers
                async def receive():
                    return {"type": "http.request", "body": body}

                request = Request(request.scope, receive)

                # Call the next middleware/endpoint
                response = await call_next(request)

                # Read response body
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk

                try:
                    response_data = json.loads(response_body) if response_body else {}
                except json.JSONDecodeError:
                    response_data = {"raw_body": response_body.decode('utf-8', errors='replace')}

                # Log the traffic
                try:
                    log_a2a_traffic(self.agent_name, request_data, response_data)
                except Exception as e:
                    print(f"[A2A LOG] Error logging traffic: {e}")

                # Return new response with the body we read
                return Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
            else:
                # Don't log agent card requests
                return await call_next(request)

except ImportError:
    # Starlette not available - middleware won't work but logging function will
    A2ALoggingMiddleware = None
