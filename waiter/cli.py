#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-adk[a2a]",
# ]
# ///
"""Waiter CLI - Interactive REPL for taking customer orders.

This is the main interface for the restaurant system.
The waiter takes orders from customers and delegates to the chef via A2A.
"""

import sys
from google.adk import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Part, UserContent

print("=" * 80)
print("🍽️  RESTAURANT ORDER SYSTEM")
print("=" * 80)
print()

# Connect to chef agent via A2A
try:
    print("[WAITER] Connecting to chef agent via A2A...")

    chef_agent = RemoteA2aAgent(
        name="chef_agent",
        agent_card="http://localhost:8002/.well-known/agent-card.json"
    )

    chef_tool = AgentTool(agent=chef_agent)

    print("[WAITER] ✅ Connected to chef agent (port 8002)")
    print()

except Exception as e:
    print(f"[WAITER] ❌ Could not connect to chef agent: {e}")
    print("[WAITER] Make sure the chef server is running:")
    print("         cd chef && uv run a2a_server.py")
    sys.exit(1)

# Create the waiter agent
waiter_agent = Agent(
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
- Log all interactions with [WAITER] prefix

Example interaction:
Customer: "I'd like the Greek Salad please"
You: [Use chef_agent tool to order "Greek Salad"]
You: "Excellent choice! The chef says your Greek Salad will be ready in 15 minutes."
""",
    tools=[chef_tool]
)

# Create runner
session_service = InMemorySessionService()
runner = Runner(
    agent=waiter_agent,
    session_service=session_service,
    app_name="waiter_cli"
)

# Create persistent session
user_id = "customer_1"
session_id = "table_1"

print("🍽️  Welcome to the Restaurant!")
print("=" * 80)
print()
print("I'm your waiter. What would you like to order today?")
print("(Type 'menu' to see available dishes, 'quit' to exit)")
print()

# REPL loop
while True:
    try:
        # Get user input
        user_input = input("Customer: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n[WAITER] Thank you for dining with us! Goodbye! 👋\n")
            break

        if user_input.lower() == 'menu':
            print("\n[WAITER] Let me check our menu...")
            user_input = "What dishes do you have available?"

        print()
        print("[WAITER] 📝 Taking order...")
        print()

        # Create message
        content = UserContent([Part(text=user_input)])

        # Call the waiter agent
        events = list(runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        ))

        # Extract and print response
        for event in events:
            if hasattr(event, 'content') and hasattr(event.content, 'parts'):
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        print(f"Waiter: {part.text}")
                        print()

    except KeyboardInterrupt:
        print("\n\n[WAITER] Interrupted. Thank you for dining with us! 👋\n")
        break
    except Exception as e:
        print(f"\n[WAITER] ❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
