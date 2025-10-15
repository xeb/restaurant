# Testing the Customer Orders Feature

## What Was Updated

### 1. Orders MCP Server (orders_mcp_server.py)
- Enhanced with better logging
- Tools: `save_order`, `set_order_status`, `get_order_status`, `list_orders`
- Saves to `orders.json` with timestamps

### 2. Waiter Agents (Both Files Updated!)
- **waiter_standalone.py** - Used by web interface (`make waiter-web`)
- **waiter/a2a_server.py** - Used by CLI (`make cli`)

Both now:
- Connect to orders MCP server with smart path detection
- Have explicit instructions to use MCP tools
- ALWAYS ask for customer name first
- Only mention order ID when customer asks

### 3. Updated Instructions
The waiter now:
- Lists available tools clearly
- Has step-by-step workflow
- Provides concrete examples
- Uses tools explicitly (not recursively calling itself)

### 4. Fixed MCP Path Issues (All Agents!)
All agents now use smart path detection to work from both root and subdirectories:
- **supplier/agent.py** - Fixed pantry MCP path
- **chef/agent.py** - Fixed recipes and pantry MCP paths
- **waiter_standalone.py** - Fixed orders MCP path
- **waiter/a2a_server.py** - Fixed orders MCP path

This fixes the error: `Failed to spawn: ../pantry_mcp_server.py` when using web interfaces

## How to Test

### Option 1: Using Make CLI (Recommended)

```bash
# Clean up any old orders
rm -f orders.json

# Terminal 1: Start supplier
make supplier-cli

# Terminal 2: Start chef
make chef-cli

# Terminal 3: Start interactive CLI
make cli
# Select "Waiter" from the menu
```

### Option 2: Using Test Script

```bash
make test-orders
# Follow the on-screen instructions
```

### Option 3: Using Web Interface

```bash
# Terminal 1: Start supplier
make supplier-cli

# Terminal 2: Start chef
make chef-cli

# Terminal 3: Start waiter web UI
make waiter-web

# Open http://localhost:5001 in browser
```

## Test Conversation

```
You: Hi
Waiter: Welcome! May I have your name please?

You: Alice
Waiter: Nice to meet you, Alice! What would you like to order?

You: Greek Salad
Waiter: [Calls chef_agent, save_order, set_order_status]
        Excellent choice! Your Greek Salad will be ready in 15 minutes.

You: Where is my food?
Waiter: [Calls list_orders, set_order_status to SERVED]
        Your Greek Salad is ready! Here you go, Alice. Enjoy!

You: What is my order ID?
Waiter: [Calls list_orders]
        Your order ID is #1.
```

## Expected Tool Calls

When you order "Greek Salad", you should see:

1. `chef_agent` - Send order to chef
2. `save_order` - Save order (returns order_id)
3. `set_order_status` - Update to COOKING
4. `set_order_status` - Update to READY

When you ask "Where is my food?":

1. `list_orders` - Find your order
2. `set_order_status` - Update to SERVED

## Verifying Orders

Check the saved orders file:

```bash
cat orders.json | python3 -m json.tool
```

Expected structure:
```json
{
  "next_order_id": 2,
  "orders": {
    "1": {
      "order_id": 1,
      "name": "Alice",
      "order_details": "Greek Salad",
      "estimated_wait_time": "15 minutes",
      "status": "SERVED",
      "created_at": "2025-10-14T...",
      "updated_at": "2025-10-14T..."
    }
  }
}
```

## Troubleshooting

### Issue: Waiter not using tools
**Symptom**: Waiter says "I don't have a way to provide order ID"

**Solution**: 
1. Stop all agents: `make stop`
2. Remove old orders: `rm -f orders.json`
3. Restart agents
4. Make sure you're using the updated version

### Issue: MCP connection failed
**Symptom**: `[WAITER] ⚠️ Could not connect to orders MCP`

**Solution**: Check that orders_mcp_server.py exists and has correct syntax:
```bash
python3 -m py_compile orders_mcp_server.py
```

### Issue: Tools not showing up
**Symptom**: No tool calls visible in CLI output

**Solution**: The waiter should show tool calls like:
```
🔧 Tool Call: chef_agent
🔧 Tool Call: save_order
🔧 Tool Call: set_order_status
```

If you see `🔧 Tool Call: waiter_agent` (calling itself), restart the waiter.

## Status Transitions

```
RECEIVED  →  COOKING  →  READY  →  SERVED
   ↑           ↑          ↑         ↑
save_order  to chef   chef done  customer
                                  receives
```

- **RECEIVED**: Order saved, not yet sent to chef
- **COOKING**: Order sent to chef, being prepared
- **READY**: Chef finished, waiting for customer
- **SERVED**: Delivered to customer

## Clean Up

```bash
# Stop all agents
make stop

# Remove orders file
rm -f orders.json

# Remove logs
make clean
```
