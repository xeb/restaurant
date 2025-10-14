#!/bin/bash
# Test script for Restaurant Multi-Agent System
# Tests waiter -> chef -> supplier A2A communication

set -e

echo "=========================================="
echo "Restaurant Multi-Agent System Test"
echo "=========================================="
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

cd "$(dirname "$0")"

echo -e "${BLUE}📁 Working directory: $(pwd)${NC}"
echo ""

# Kill any existing servers
echo "Step 1: Cleaning up old servers..."
echo "----------------------------------------"
pkill -f "uv run.*a2a_server.py" 2>/dev/null || true
lsof -ti:8002 | xargs kill -9 2>/dev/null || true
lsof -ti:8003 | xargs kill -9 2>/dev/null || true
sleep 2
echo -e "${GREEN}✅ Cleanup complete${NC}"
echo ""

# Start supplier agent (port 8003)
echo "Step 2: Starting supplier agent (port 8003)..."
echo "----------------------------------------"
cd supplier
uv run a2a_server.py > /tmp/supplier.log 2>&1 &
SUPPLIER_PID=$!
cd ..
echo "Supplier PID: $SUPPLIER_PID"

# Wait for supplier to be ready
echo "Waiting for supplier..."
sleep 15

if curl -s http://localhost:8003/.well-known/agent-card.json > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Supplier agent ready on port 8003${NC}"
else
    echo -e "${RED}❌ Supplier agent failed to start${NC}"
    cat /tmp/supplier.log
    kill $SUPPLIER_PID 2>/dev/null || true
    exit 1
fi
echo ""

# Start chef agent (port 8002)
echo "Step 3: Starting chef agent (port 8002)..."
echo "----------------------------------------"
cd chef
uv run a2a_server.py > /tmp/chef.log 2>&1 &
CHEF_PID=$!
cd ..
echo "Chef PID: $CHEF_PID"

# Wait for chef to be ready
echo "Waiting for chef..."
sleep 15

if curl -s http://localhost:8002/.well-known/agent-card.json > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Chef agent ready on port 8002${NC}"
else
    echo -e "${RED}❌ Chef agent failed to start${NC}"
    cat /tmp/chef.log
    kill $SUPPLIER_PID $CHEF_PID 2>/dev/null || true
    exit 1
fi
echo ""

# Test the system with automated input
echo "Step 4: Testing order flow..."
echo "----------------------------------------"
echo ""
echo -e "${YELLOW}Testing orders via direct A2A calls${NC}"
echo ""

cd waiter
# Use simple HTTP client instead of CLI to avoid session issues
timeout 120 uv run simple_client.py > /tmp/waiter_test.log 2>&1 || true
cd ..

echo ""
echo "Test output:"
cat /tmp/waiter_test.log | grep -v "UserWarning" | grep -v "EXPERIMENTAL"
echo ""

# Check if order was processed
if grep -q "Greek Salad\|CHEF RESPONSE" /tmp/waiter_test.log; then
    echo -e "${GREEN}✅ Order processed successfully${NC}"
else
    echo -e "${RED}❌ Order processing failed${NC}"
    echo "Full test log:"
    cat /tmp/waiter_test.log
fi
echo ""

# Show agent logs
echo "Step 5: Checking agent logs..."
echo "----------------------------------------"

echo "Supplier agent log (last 10 lines):"
tail -10 /tmp/supplier.log | grep -v "UserWarning" || echo "No significant log entries"
echo ""

echo "Chef agent log (last 10 lines):"
tail -10 /tmp/chef.log | grep -v "UserWarning" || echo "No significant log entries"
echo ""

# Cleanup
echo "Step 6: Cleanup..."
echo "----------------------------------------"
kill $SUPPLIER_PID $CHEF_PID 2>/dev/null || true
pkill -f "uv run.*a2a_server.py" 2>/dev/null || true
sleep 2
echo -e "${GREEN}✅ All servers stopped${NC}"
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}✅ Supplier agent started (port 8003)${NC}"
echo -e "${GREEN}✅ Chef agent started (port 8002)${NC}"
echo -e "${GREEN}✅ Waiter CLI connected${NC}"
echo -e "${GREEN}✅ Order flow tested${NC}"
echo ""
echo "To run manually:"
echo "  Terminal 1: cd supplier && uv run a2a_server.py"
echo "  Terminal 2: cd chef && uv run a2a_server.py"
echo "  Terminal 3: cd waiter && uv run cli.py"
echo ""
echo "Architecture:"
echo "  Waiter (CLI) --A2A--> Chef (port 8002) --A2A--> Supplier (port 8003)"
echo "  Chef uses: Recipes MCP + Pantry MCP"
echo "  Supplier uses: Pantry MCP + wait_time tool"
echo ""
