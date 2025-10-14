#!/bin/bash
# Test the webapp

set -e

echo "=== Testing Restaurant Webapp ==="

# Clean up
echo "Cleaning up..."
pkill -f "webapp.py" 2>/dev/null || true
pkill -f "a2a_server.py" 2>/dev/null || true
lsof -ti:8002 | xargs kill -9 2>/dev/null || true
lsof -ti:8003 | xargs kill -9 2>/dev/null || true
lsof -ti:5001 | xargs kill -9 2>/dev/null || true
lsof -ti:5002 | xargs kill -9 2>/dev/null || true
lsof -ti:5003 | xargs kill -9 2>/dev/null || true

sleep 3

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Start supplier A2A server
echo "Starting supplier A2A server..."
(cd "$SCRIPT_DIR/supplier" && uv run a2a_server.py > /tmp/supplier_test.log 2>&1) &
SUPPLIER_PID=$!
sleep 10

# Check supplier
curl -s http://localhost:8003/.well-known/agent-card.json > /dev/null && echo "✅ Supplier ready" || { echo "❌ Supplier failed"; cat /tmp/supplier_test.log; exit 1; }

# Start chef A2A server
echo "Starting chef A2A server..."
(cd "$SCRIPT_DIR/chef" && uv run a2a_server.py > /tmp/chef_test.log 2>&1) &
CHEF_PID=$!
sleep 10

# Check chef
curl -s http://localhost:8002/.well-known/agent-card.json > /dev/null && echo "✅ Chef ready" || { echo "❌ Chef failed"; cat /tmp/chef_test.log; exit 1; }

# Start waiter webapp
echo "Starting waiter webapp on port 5001..."
uv run webapp.py --agent=waiter --port=5001 > /tmp/waiter_webapp.log 2>&1 &
WAITER_PID=$!
sleep 8

# Test waiter webapp
echo "Testing waiter webapp..."
curl -s http://localhost:5001/ | grep -q "Restaurant" && echo "✅ Waiter webapp accessible" || { echo "❌ Waiter webapp failed"; cat /tmp/waiter_webapp.log; exit 1; }

echo ""
echo "=== All webapps tested successfully! ==="
echo ""
echo "To use:"
echo "  Supplier webapp: make supplier-web"
echo "  Chef webapp:     make chef-web"
echo "  Waiter webapp:   make waiter-web"
echo ""
echo "Cleaning up test processes..."
kill $WAITER_PID $CHEF_PID $SUPPLIER_PID 2>/dev/null || true
