#!/bin/bash
# Test the waiter orders feature via make cli

set -e

echo "=== Testing Waiter Orders Feature ==="
echo ""

# Clean up any existing orders.json
if [ -f orders.json ]; then
    echo "Removing existing orders.json..."
    rm -f orders.json
fi

# Clean up any running processes
echo "Cleaning up any running agents..."
pkill -f "a2a_server.py" 2>/dev/null || true
lsof -ti:8002 | xargs kill -9 2>/dev/null || true
lsof -ti:8003 | xargs kill -9 2>/dev/null || true

sleep 2

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Start supplier A2A server
echo "Starting supplier A2A server (port 8003)..."
(cd "$SCRIPT_DIR/supplier" && uv run a2a_server.py > /tmp/supplier_orders_test.log 2>&1) &
SUPPLIER_PID=$!
sleep 10

# Check supplier
if curl -s http://localhost:8003/.well-known/agent-card.json > /dev/null; then
    echo "✅ Supplier ready"
else
    echo "❌ Supplier failed to start"
    cat /tmp/supplier_orders_test.log
    exit 1
fi

# Start chef A2A server
echo "Starting chef A2A server (port 8002)..."
(cd "$SCRIPT_DIR/chef" && uv run a2a_server.py > /tmp/chef_orders_test.log 2>&1) &
CHEF_PID=$!
sleep 10

# Check chef
if curl -s http://localhost:8002/.well-known/agent-card.json > /dev/null; then
    echo "✅ Chef ready"
else
    echo "❌ Chef failed to start"
    cat /tmp/chef_orders_test.log
    kill $SUPPLIER_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "=== Agents are ready! ==="
echo ""
echo "Now test the orders feature with the interactive CLI:"
echo ""
echo "  1. Run: make cli"
echo "  2. Select 'Waiter' from the menu"
echo "  3. Test the following workflow:"
echo ""
echo "     a) Say: Hi there!"
echo "        → Waiter should ask for your name"
echo ""
echo "     b) Provide name: Alice"
echo "        → Waiter should ask what you want to order"
echo ""
echo "     c) Order: I'd like the Greek Salad please"
echo "        → Waiter should:"
echo "          - Save order (status: RECEIVED)"
echo "          - Send to chef (status → COOKING)"
echo "          - Get time estimate from chef (status → READY)"
echo "          - Tell you the order # and wait time"
echo ""
echo "     d) Ask: Where is my food?"
echo "        → Waiter should:"
echo "          - Check order status"
echo "          - If READY, serve it (status → SERVED)"
echo ""
echo "     e) Order again with name: Bob"
echo "        → Test multiple orders"
echo ""
echo "     f) Ask: What are the outstanding orders?"
echo "        → Waiter should list all non-SERVED orders"
echo ""
echo "  4. Exit the CLI (type 'exit')"
echo ""
echo "  5. Check orders.json to see saved orders:"
echo "     cat orders.json"
echo ""
echo "When done testing, press Enter to clean up..."
read -r

echo ""
echo "Cleaning up..."
kill $CHEF_PID $SUPPLIER_PID 2>/dev/null || true
sleep 2

echo ""
echo "=== Test setup complete! ==="
echo ""
echo "To view the orders that were saved:"
echo "  cat orders.json | python3 -m json.tool"
echo ""
