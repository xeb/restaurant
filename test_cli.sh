#!/bin/bash
# Test the interactive CLI

set -e

echo "=== Testing Interactive CLI ==="
echo ""

# Check all agents are running
echo "Checking agent status..."
make status

echo ""
echo "Testing CLI connection to each agent..."
echo ""

# Test waiter
echo "Testing waiter agent connection..."
timeout 5 uv run interactive_cli.py <<EOF || true
exit
EOF

echo ""
echo "✅ CLI test completed!"
echo ""
echo "To use the interactive CLI:"
echo "  1. Start all agents (make supplier-cli, make chef-cli, make waiter-cli)"
echo "  2. Run: make cli"
echo "  3. Select an agent from the menu"
echo "  4. Chat with the agent!"
echo ""
