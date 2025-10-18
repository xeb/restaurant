#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-adk[a2a]",
#     "fastmcp",
#     "fire",
#     "uvicorn",
# ]
# ///
"""A2A Server for Supplier Agent.

Exposes the supplier agent via JSON-RPC A2A protocol on port 8003.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from agent import root_agent
from a2a_logging import A2ALoggingMiddleware

print("[SUPPLIER A2A] Starting supplier agent server...")

# Create the A2A-compatible application
a2a_app = to_a2a(
    root_agent,
    port=8003,
)

# Add logging middleware
a2a_app.add_middleware(A2ALoggingMiddleware, agent_name="supplier")
print("[SUPPLIER A2A] ✅ A2A traffic logging enabled")

print("[SUPPLIER A2A] Server configured on port 8003")
print("[SUPPLIER A2A] Agent card will be available at: http://localhost:8003/.well-known/agent-card.json")
print("[SUPPLIER A2A] JSON-RPC endpoint: http://localhost:8003/")

if __name__ == "__main__":
    import uvicorn
    print("[SUPPLIER A2A] 🚀 Launching uvicorn server...")
    uvicorn.run(a2a_app, host="0.0.0.0", port=8003)
