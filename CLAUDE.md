# 🤖 Using the Restaurant Project with Claude Code

This document provides instructions for using the Restaurant Multi-Agent System with Claude Code, Anthropic's official CLI for Claude.

## 📋 Overview

The Restaurant Multi-Agent System is a demonstration of **Agent-to-Agent (A2A)** communication using Google's Agent Development Kit (ADK). It simulates a restaurant with three cooperating AI agents that communicate via JSON-RPC:

- **Waiter Agent** - Takes customer orders
- **Chef Agent** - Prepares dishes based on orders
- **Supplier Agent** - Supplies ingredients to the restaurant

## 🚀 Quick Start with Claude Code

Claude Code can help you understand, modify, and extend this multi-agent system. Here are the most common workflows:

### 1. Understanding the System

Ask Claude Code to explain different aspects of the project:

```
Explain how the A2A communication works between the waiter and chef
```

```
Show me how the MCP servers are integrated with the agents
```

```
Walk me through the order flow when a customer orders a Greek Salad
```

### 2. Running the System

Claude Code can help you start the agents in the correct order:

```
Help me start all the agents for testing
```

```
Check which agents are currently running
```

```
Show me how to test the system with a sample order
```

**Manual startup process (Unified Web + A2A):**

```bash
# Terminal 1: Start supplier (web + A2A on port 8003)
make supplier

# Terminal 2: Start chef (web + A2A on port 8002)
make chef

# Terminal 3: Start waiter (web + A2A on port 8001)
make waiter

# Then open http://localhost:8001 in your browser
```

**Key Feature**: All agents now expose **both** web UI and A2A protocol on the same port!
- Browser sessions and A2A sessions are unified
- You can chat via web UI while agents communicate via A2A
- All sessions visible in the web interface
- Ports: 8001 (waiter), 8002 (chef), 8003 (supplier)

### 3. Debugging Issues

Claude Code can help troubleshoot common problems:

```
The chef agent can't connect to the supplier, help me debug this
```

```
Port 8002 is already in use, how do I fix this?
```

```
Check the logs to see why the waiter isn't getting responses
```

## 🛠️ Development with Claude Code

### Adding New Features

Claude Code excels at helping you extend the system:

```
Add a new menu item for "Vegetarian Lasagna" to the recipes MCP server
```

```
Create a new MCP server for tracking customer feedback
```

```
Add a function to the supplier agent to check low stock items
```

### Refactoring Code

Ask Claude Code to improve the codebase:

```
Refactor the chef agent to better handle missing ingredients
```

```
Add error handling to the A2A connections
```

```
Improve the logging in the supplier agent
```

### Creating New Agents

Claude Code can help you add new agents to the system:

```
Create a new "Host" agent that manages table reservations
```

```
Add a "Dishwasher" agent that tracks dirty dishes
```

## 📁 Key Files to Know

When working with Claude Code, you'll frequently reference these files:

### Agent Files

- `waiter/agent.py` - Waiter agent definition (line 115-207: instructions)
- `chef/agent.py` - Chef agent definition (line 184-227: instructions)
- `supplier/agent.py` - Supplier agent definition (line 113-173: instructions)

All agents use the **Gemini 2.5 Flash** model (`gemini-2.5-flash`)

### MCP Servers

- `pantry_mcp_server.py` - Shared inventory management (Food IDs, disk-reload support)
- `chef/recipes_mcp_server.py` - Recipe database (hardcoded recipes)
- `orders_mcp_server.py` - Customer orders tracking (waiter's order management)
- `order_up_mcp_server.py` - Chef's order completion tracking (auto-incrementing IDs)
- `menu_mcp_server.py` - Artisanal menu descriptions for customers

### A2A Servers

- `supplier/a2a_server.py` - Supplier A2A server (port 8003, legacy standalone)
- `chef/a2a_server.py` - Chef A2A server (port 8002, legacy standalone)
- `waiter/a2a_server.py` - Waiter A2A server (port 8001, legacy standalone)
- `a2a_logging.py` - A2A traffic logging utility (logs all JSON-RPC requests/responses to `a2a_traffic/` directory)

### Web Interface

- `webapp.py` - Flask web interface for all agents
- **Unified Architecture**: Web UI (GET) + A2A protocol (POST) on the same port!
- Port allocation:
  - Waiter: 8001 (unified web + A2A)
  - Chef: 8002 (unified web + A2A)
  - Supplier: 8003 (unified web + A2A)
- Features: Session management, tool call inspection, A2A session visibility, duration tracking

### Build & Test

- `Makefile` - All build commands
- `test.sh` - CLI test suite
- `test_webapp.sh` - Web interface tests
- `interactive_cli.py` - Interactive terminal interface

## 🧪 Testing with Claude Code

### Running Tests

```
Run the test suite and explain any failures
```

```
Create a new test case for ordering multiple dishes
```

```
Test the order flow with missing ingredients
```

### Automated Testing

```bash
# Run all tests
make test

# Run specific test suites
make test-cli        # Interactive CLI tests
make test-old-cli    # Legacy CLI tests
make test-webapp     # Web interface tests
```

## 🔍 Common Tasks with Claude Code

### 1. Examining Tool Calls

```
Show me all the MCP tools available to the chef agent
```

```
Explain how the chef uses the check_pantry tool
```

### 2. Understanding A2A Communication

```
Trace the A2A calls when ordering "Grilled Salmon"
```

```
Show me the JSON-RPC messages exchanged between waiter and chef
```

### 3. Modifying Agent Instructions

```
Update the waiter's instructions to ask for customer names
```

```
Make the chef more verbose about ingredient preparation
```

### 4. Adding MCP Tools

```
Add a new tool to the pantry server for inventory reports
```

```
Create a tool to list all recipes by category
```

### 5. Web Interface Customization

```
Add a new button to the web UI to clear the chat history
```

```
Show tool call timestamps in the web interface
```

### 6. Working with the Menu System

The waiter has access to an artisanal menu via the Menu MCP server:

```
Show me all menu items with dietary information
```

```
Add a new vegan dish to menu.json
```

```
How does the waiter use the menu tools to answer customer questions?
```

**Menu MCP Tools**:
- `list_menu(category)` - Browse menu by category
- `get_menu_item(item_name)` - Get detailed item info
- `list_categories()` - Get all categories
- `search_menu(query)` - Search by keyword (e.g., "vegan")

**Example interaction**:
```
Customer: What vegan options do you have?

Waiter: [Calls search_menu(query="vegan")]
        We have several delicious vegan options:
        - Greek Salad (Mediterranean delight...)
        - Vegetable Stir-Fry (Asian-inspired...)
        [Shows artisanal descriptions]
```

## 🔍 A2A Traffic Logging

The project includes a powerful A2A traffic logging system for debugging and analysis.

### Logging Feature

**File**: `a2a_logging.py`

This utility logs all A2A JSON-RPC requests and responses to the `a2a_traffic/` directory.

### How to Use

1. **Automatic Logging**: When using standalone A2A servers with the middleware:
   ```python
   from a2a_logging import A2ALoggingMiddleware

   # Add to your A2A app
   a2a_app.add_middleware(A2ALoggingMiddleware, agent_name="chef")
   ```

2. **Manual Logging**: Call the logging function directly:
   ```python
   from a2a_logging import log_a2a_traffic

   log_a2a_traffic("waiter", request_data, response_data)
   ```

3. **View Logs**: Each A2A call creates a timestamped JSON file:
   ```bash
   ls a2a_traffic/
   # chef_1234567890123456.json
   # waiter_1234567890234567.json
   ```

### Log File Format

Each log file contains:
```json
{
  "timestamp": 1234567890.123456,
  "timestamp_human": "2024-01-15 10:30:45",
  "agent": "chef",
  "request": {
    "jsonrpc": "2.0",
    "method": "invoke",
    "params": {...},
    "id": 1
  },
  "response": {
    "jsonrpc": "2.0",
    "result": {...},
    "id": 1
  }
}
```

### Debugging with A2A Logs

```
User: Show me the A2A traffic logs for the last order

Claude: Let me check the a2a_traffic/ directory...
[Reads recent log files]
[Shows request/response pairs with timing information]
```

### Clean Up Logs

```bash
# Remove all A2A traffic logs
make clean

# Or manually
rm -rf a2a_traffic/
```

## 📦 Order Delivery Tracking

The system supports tracking when orders are delivered to customers.

### The `mark_order_delivered` Feature

**Location**: `order_up_mcp_server.py:164-197`

This MCP tool allows the chef to mark orders as "delivered" once the waiter notifies them.

### How It Works

1. **Waiter serves the order** to the customer
2. **Waiter notifies chef**: "Order #3 has been delivered"
3. **Chef calls** `mark_order_delivered(order_id=3)`
4. **Status updates** from "ready" → "delivered"

### Chef Agent Instructions

The chef agent (chef/agent.py:213-214) includes instructions:
```
When the waiter notifies you that an order has been served/delivered:
1. Extract the order_id from the message
2. Use mark_order_delivered(order_id) to update the status
3. Respond with confirmation
```

### Example Interaction

```
Waiter: Order #5 has been served to the customer

Chef: [Calls mark_order_delivered(order_id=5)]
      Order #5 marked as delivered. Thanks for letting me know!
```

### Using with Claude Code

```
User: How does the order delivery tracking work?

Claude: The system tracks order delivery in two stages:
1. Chef marks orders as "ready" using accept_order()
2. Waiter marks orders as "delivered" by notifying the chef
   [Explains the mark_order_delivered flow]
```

## 📊 Architecture Deep Dives

Ask Claude Code to explain specific architectural patterns:

```
Explain the MCPToolset connection pattern used in chef/agent.py
```

```
How does the webapp.py handle multiple agent sessions?
```

```
Show me how RemoteA2aAgent wraps HTTP endpoints as tools
```

## 🐛 Debugging Scenarios

### Connection Issues

```
The waiter can't connect to the chef agent, show me the connection code
```

**Claude Code will point you to:**
- `waiter/agent.py:23-34` - RemoteA2aAgent connection to chef
- Port configuration in Makefile
- Agent card endpoint verification (http://localhost:8002/.well-known/agent-card.json)

### Missing Ingredients Flow

```
Walk me through what happens when ingredients are missing
```

**Claude Code will explain:**
1. Chef calls `take_ingredients` (line 82 in pantry_mcp_server.py)
2. Gets missing items in response (line 106-111)
3. Calls supplier_agent tool (chef/agent.py:107)
4. Supplier calls `wait_time` then `add_ingredients`
5. Chef retries `take_ingredients`

### MCP Server Issues

```
The pantry MCP server isn't responding, help me debug
```

**Claude Code will check:**
- StdioConnectionParams configuration
- Server command and args (e.g., "uv run pantry_mcp_server.py")
- Relative paths from agent directories
- Import errors in MCP server file

## 🌟 Advanced Features

### Streaming Responses

```
How would I add streaming responses to the web interface?
```

### Multi-Session Support

```
Add the ability to switch between different customer sessions
```

### Agent Performance Monitoring

```
Create a dashboard showing agent response times
```

### Custom MCP Servers

```
Build a new MCP server for managing table reservations
```

## 🛠️ Development Mode Features

### Auto-Reload with `-dev` Commands

For active development, use the `-dev` variants of the CLI commands:

```bash
# Terminal 1: Supplier with auto-reload
make supplier-cli-dev

# Terminal 2: Chef with auto-reload
make chef-cli-dev

# Terminal 3: Waiter with auto-reload
make waiter-cli-dev
```

**Benefits**:
- **Automatic reloading** when you edit agent files
- **Faster iteration** during development
- **Powered by uvicorn** with `--reload` flag

**When to use**:
- Developing new agent instructions
- Testing tool integrations
- Debugging A2A communication
- Refactoring agent code

### Background Execution with `make all`

Start all agents in the background with logging:

```bash
# Start all agents at once
make all

# View combined logs
make logs

# Check status
make status

# Stop all agents
make stop
```

**Log files created**:
- `supplier.log` - Supplier agent output
- `chef.log` - Chef agent output
- `waiter.log` - Waiter agent output

**Use case**: When you want all agents running without occupying multiple terminal windows.

### Clearing Order Data

Reset the order tracking systems:

```bash
# Clear all order data
make clear
```

This resets:
- `orders.json` (waiter's customer orders)
- `chef_orders.json` (chef's order completions)

**When to use**:
- Before running test suites
- After testing scenarios
- When order IDs get too high
- To start fresh

## 📚 Learning with Claude Code

### Understanding ADK Concepts

```
Explain the difference between FunctionTool and MCPToolset
```

```
What is the purpose of the Agent instruction field?
```

```
How does session management work in the webapp?
```

### A2A Protocol Details

```
Show me the agent card JSON structure
```

```
Explain the JSON-RPC 2.0 message format used in A2A
```

### Best Practices

```
What are best practices for error handling in A2A communication?
```

```
How should I structure agent instructions for optimal performance?
```

## 🔧 Make Commands Reference

Claude Code can help you understand and use these commands:

| Command | Purpose | Dependencies |
|---------|---------|--------------|
| `make supplier` | Start supplier (defaults to web, port 8003) | None |
| `make chef` | Start chef (defaults to web, port 8002) | Supplier |
| `make waiter` | Start waiter (defaults to web, port 8001) | Chef, Supplier |
| `make supplier-cli` | Start supplier A2A server (8003) | None |
| `make chef-cli` | Start chef A2A server (8002) | Supplier |
| `make waiter-cli` | Start waiter A2A server (8001) | Chef, Supplier |
| `make supplier-cli-dev` | Start supplier A2A with auto-reload | None |
| `make chef-cli-dev` | Start chef A2A with auto-reload | Supplier |
| `make waiter-cli-dev` | Start waiter A2A with auto-reload | Chef, Supplier |
| `make supplier-web` | Start supplier unified web+A2A (8003) | None |
| `make chef-web` | Start chef unified web+A2A (8002) | Supplier |
| `make waiter-web` | Start waiter unified web+A2A (8001) | Chef, Supplier |
| `make cli` | Interactive CLI for any agent | At least one agent running |
| `make all` | Start all agents in background | None |
| `make logs` | Tail all agent logs in real-time | Running agents |
| `make status` | Check all agent statuses | None |
| `make stop` | Stop all agents | None |
| `make clean` | Clean logs and temp files | None |
| `make clear` | Clear all order data | None |
| `make test` | Run all test suites | None |
| `make test-cli` | Run interactive CLI tests | None |
| `make test-webapp` | Run webapp tests | None |

## 💡 Tips for Working with Claude Code

### 1. Be Specific About Context

Instead of:
```
Fix the chef agent
```

Try:
```
The chef agent at chef/agent.py:145 isn't properly calculating cook time.
The instructions say to add prep + cook + delivery time, but it's only
using prep time. Fix this.
```

### 2. Reference Line Numbers

Claude Code works well with specific references:
```
In waiter/agent.py:177-200, update the example interaction to include
additional customer greeting variations
```

### 3. Ask for Explanations First

Before modifying code:
```
Explain how the supplier agent connects to the pantry MCP server
```

Then:
```
Now add error handling for when the pantry MCP connection fails
```

### 4. Use Claude Code for Documentation

```
Generate docstrings for all functions in pantry_mcp_server.py
```

```
Create inline comments explaining the A2A connection in chef/agent.py
```

### 5. Iterative Development

Build features step by step:
```
1. Show me where to add a new tool to the waiter agent
2. Create a simple function that returns the current time
3. Add it as a FunctionTool to the waiter's tools list
4. Update the waiter instructions to use this tool
```

## 🎯 Example Sessions with Claude Code

### Session 1: Adding a New Recipe

```
User: Add a new recipe for "Margherita Pizza" to the recipes MCP server

Claude: I'll add a new recipe for Margherita Pizza to the recipes database...
[Shows the recipes_mcp_server.py file]
[Adds new recipe with ingredients, prep time, cook time, etc.]

User: Now test this by ordering it through the waiter

Claude: I'll help you test the new recipe...
[Guides through starting agents and placing test order]
```

### Session 2: Debugging Connection Issues

```
User: The waiter web interface shows "chef_agent" tool failed

Claude: Let me check the A2A connection in waiter/agent.py:23-34...
[Examines connection code]
The issue is the chef A2A server needs to be running. Let me check:
[Runs make status]
Chef agent is not running. Start it with: make chef

User: Started it, still not working

Claude: Let me check the agent card endpoint...
[Verifies http://localhost:8002/.well-known/agent-card.json]
[Identifies specific error and provides fix]
```

### Session 3: Adding New Functionality

```
User: I want the waiter to track customer names with each order

Claude: I'll help you add customer name tracking. This requires:
1. Creating an orders MCP server (like pantry_mcp_server.py)
2. Connecting it to the waiter agent
3. Updating waiter instructions to ask for names
4. Adding save_order and list_orders tools

Let me start by creating the orders MCP server...
[Implements each step iteratively]
```

## 🔗 Related Documentation

For deeper dives, ask Claude Code to reference:

- **README.md** - Full system overview and architecture
- **WEBAPP.md** - Web interface implementation details
- **CLI_DEMO.md** - Interactive CLI usage guide
- **SUMMARY.md** - Quick reference and completion checklist
- **ORDERS_SPEC.md** - Customer orders feature specification

## 🆘 Getting Help

When working with Claude Code on this project:

1. **Start with Understanding**: Ask Claude to explain before modifying
2. **Reference Specific Files**: Point to files and line numbers
3. **Test Incrementally**: Make small changes and test frequently
4. **Use Make Commands**: Leverage the Makefile for consistency
5. **Check Status Often**: Use `make status` to verify agents are running

## 🎓 Learning Goals

Working with this project and Claude Code, you'll learn:

- ✅ Multi-agent system architecture
- ✅ A2A (Agent-to-Agent) communication patterns
- ✅ MCP (Model Context Protocol) integration
- ✅ Remote agent communication via JSON-RPC
- ✅ Flask web interface development
- ✅ Session management with ADK
- ✅ Tool creation and integration
- ✅ Debugging distributed agent systems
- ✅ Testing multi-agent workflows

## 🚀 Next Steps

After getting familiar with the basics, try these with Claude Code:

1. **Extend the Menu**: Add 5 new recipes
2. **Create Analytics**: Track order statistics
3. **Add Authentication**: Secure the web interface
4. **Implement Streaming**: Add real-time updates via WebSocket
5. **Build a Dashboard**: Visualize agent communication
6. **Add Error Recovery**: Handle network failures gracefully
7. **Create New Agents**: Add a host, delivery, or inventory manager
8. **Optimize Performance**: Profile and improve response times

---

**Built with ❤️ using Google ADK, A2A Protocol, and MCP**

**Enhanced for Claude Code - The AI pair programmer that understands your codebase**
