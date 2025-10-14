#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-adk[a2a]",
#     "fire",
#     "uvicorn",
# ]
# ///
"""A2A Server for Waiter Agent.

Exposes the waiter agent via JSON-RPC A2A protocol on port 8001.
"""

import warnings
import logging

# Suppress warnings from Google ADK and GenAI
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message="Deprecated. Please migrate to the async method.")
warnings.filterwarnings("ignore", message=".*there are non-text parts in the response.*")

# Suppress logger warnings
logging.getLogger('google.genai.types').setLevel(logging.ERROR)
logging.getLogger('google.adk').setLevel(logging.ERROR)
logging.getLogger('google.adk.tools').setLevel(logging.ERROR)
logging.getLogger('google.adk.sessions').setLevel(logging.ERROR)

from google.adk import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.a2a.utils.agent_to_a2a import to_a2a

print("[WAITER A2A] Starting waiter agent server...")
print("[WAITER A2A] Connecting to chef agent...")

try:
    chef_agent = RemoteA2aAgent(
        name="chef_agent",
        agent_card="http://localhost:8002/.well-known/agent-card.json"
    )
    chef_tool = AgentTool(agent=chef_agent)
    print("[WAITER A2A] ✅ Connected to chef agent")
except Exception as e:
    print(f"[WAITER A2A] ⚠️  Could not connect to chef agent: {e}")
    chef_tool = None

# Create the waiter agent
root_agent = Agent(
    name="waiter_agent",
    model="gemini-2.5-flash",
    description="Waiter agent that takes customer orders and coordinates with the chef",
    instruction="""You are a friendly waiter in a restaurant.

Your job is to:
1. Greet customers warmly
2. Take their food orders
3. Send orders to the chef using the chef_agent tool
4. Relay the chef's time estimate back to the customer
5. Provide excellent customer service

IMPORTANT:
- When a customer orders a dish, immediately use the chef_agent tool to place the order
- The chef will check ingredients, coordinate with suppliers if needed, and give you a time estimate
- Report back to the customer with the time estimate
- Be friendly, professional, and clear

Example interaction:
Customer: "I'd like the Greek Salad please"
You: [Use chef_agent tool to order "Greek Salad"]
You: "Excellent choice! The chef says your Greek Salad will be ready in 15 minutes."
""",
    tools=[chef_tool] if chef_tool else []
)

# Create the A2A-compatible application
a2a_app = to_a2a(
    root_agent,
    port=8001,
)

print("[WAITER A2A] Server configured on port 8001")
print("[WAITER A2A] Agent card will be available at: http://localhost:8001/.well-known/agent-card.json")
print("[WAITER A2A] JSON-RPC endpoint: http://localhost:8001/")

if __name__ == "__main__":
    import uvicorn
    print("[WAITER A2A] 🚀 Launching uvicorn server...")
    uvicorn.run(a2a_app, host="0.0.0.0", port=8001)
