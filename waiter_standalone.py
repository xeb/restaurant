#!/usr/bin/env python3
"""Standalone waiter agent for webapp - uses chef via A2A."""

import io
import sys
from contextlib import redirect_stdout, redirect_stderr
from google.adk import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.tools.agent_tool import AgentTool

print("[WAITER STANDALONE] Connecting to chef agent via A2A...")

try:
    chef_agent = RemoteA2aAgent(
        name="chef_agent",
        agent_card="http://localhost:8002/.well-known/agent-card.json"
    )

    chef_tool = AgentTool(agent=chef_agent)

    print("[WAITER STANDALONE] ✅ Connected to chef agent (port 8002)")

except Exception as e:
    print(f"[WAITER STANDALONE] ⚠️  Could not connect to chef agent: {e}")
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
