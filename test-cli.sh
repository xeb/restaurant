#!/bin/bash
# Test the interactive CLI with automated input

set -e

echo "=== Testing Interactive CLI ==="
echo ""

# Clean up first
echo "Cleaning up..."
pkill -f "a2a_server.py" 2>/dev/null || true
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
lsof -ti:8002 | xargs kill -9 2>/dev/null || true
lsof -ti:8003 | xargs kill -9 2>/dev/null || true
sleep 2

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Start supplier A2A server
echo "Starting supplier A2A server..."
(cd "$SCRIPT_DIR/supplier" && uv run a2a_server.py > /tmp/supplier_cli_test.log 2>&1) &
SUPPLIER_PID=$!
sleep 5

# Verify supplier is running
curl -s http://localhost:8003/.well-known/agent-card.json > /dev/null && echo "✅ Supplier ready" || { echo "❌ Supplier failed"; cat /tmp/supplier_cli_test.log; exit 1; }

echo ""
echo "Testing CLI connection to supplier..."
echo ""

# Create a test script that simulates user interaction
# This will send one message and then exit
timeout 15 python3 << 'EOF'
import sys
import asyncio
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.genai.types import Part, UserContent

print("Connecting to supplier agent...")

try:
    # Connect to supplier
    remote_agent = RemoteA2aAgent(
        name="supplier_agent",
        agent_card="http://localhost:8003/.well-known/agent-card.json"
    )
    print("✅ Connected to supplier")

    # Test sending a message
    print("\nSending test message...")
    user_content = UserContent([Part(text="hi")])

    async def test_message():
        response_parts = []
        async for event in remote_agent.run_async(new_message=user_content):
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_parts.append(part.text)
        return "".join(response_parts)

    response = asyncio.run(test_message())

    if response:
        print(f"✅ Got response: {response[:100]}...")
        print("\n✅ CLI test PASSED!")
        sys.exit(0)
    else:
        print("❌ No response received")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

TEST_RESULT=$?

# Clean up
echo ""
echo "Cleaning up test processes..."
kill $SUPPLIER_PID 2>/dev/null || true
sleep 1

if [ $TEST_RESULT -eq 0 ]; then
    echo ""
    echo "✅ All CLI tests passed!"
    exit 0
else
    echo ""
    echo "❌ CLI tests failed!"
    exit 1
fi
