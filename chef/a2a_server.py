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
"""A2A Server for Chef Agent.

Exposes the chef agent via JSON-RPC A2A protocol on port 8002.
"""

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from agent import root_agent

print("[CHEF A2A] Starting chef agent server...")

# Create the A2A-compatible application
a2a_app = to_a2a(
    root_agent,
    port=8002,
)

print("[CHEF A2A] Server configured on port 8002")
print("[CHEF A2A] Agent card will be available at: http://localhost:8002/.well-known/agent-card.json")
print("[CHEF A2A] JSON-RPC endpoint: http://localhost:8002/")

if __name__ == "__main__":
    import uvicorn
    print("[CHEF A2A] 🚀 Launching uvicorn server...")
    uvicorn.run(a2a_app, host="0.0.0.0", port=8002)
