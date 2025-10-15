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

**Manual startup process:**

```bash
# Terminal 1: Start supplier A2A server
make supplier-cli

# Terminal 2: Start chef A2A server
make chef-cli

# Terminal 3: Start waiter web interface
make waiter-web

# Then open http://localhost:5001 in your browser
```

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

- `waiter_standalone.py` - Standalone waiter agent for webapp (line 28-53: instructions)
- `chef/agent.py` - Chef agent definition (line 116-156: instructions)
- `supplier/agent.py` - Supplier agent definition (line 98-123: instructions)

### MCP Servers

- `pantry_mcp_server.py` - Shared inventory management
- `chef/recipes_mcp_server.py` - Recipe database
- `orders_mcp_server.py` - Customer orders tracking (if implemented)

### A2A Servers

- `supplier/a2a_server.py` - Supplier A2A server (port 8003)
- `chef/a2a_server.py` - Chef A2A server (port 8002)
- `waiter/a2a_server.py` - Waiter A2A server (port 8001)

### Web Interface

- `webapp.py` - Flask web interface for all agents
- Port allocation:
  - Waiter Web: 5001
  - Chef Web: 5002
  - Supplier Web: 5003

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
- `waiter_standalone.py:14-17` - RemoteA2aAgent connection
- Port configuration in Makefile
- Agent card endpoint verification

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
| `make supplier-cli` | Start supplier A2A server (8003) | None |
| `make chef-cli` | Start chef A2A server (8002) | Supplier |
| `make waiter-cli` | Start waiter A2A server (8001) | Chef, Supplier |
| `make supplier-web` | Start supplier web UI (5003) | None |
| `make chef-web` | Start chef web UI (5002) | Supplier (CLI) |
| `make waiter-web` | Start waiter web UI (5001) | Chef (CLI), Supplier (CLI) |
| `make cli` | Interactive CLI for any agent | At least one agent running |
| `make status` | Check all agent statuses | None |
| `make stop` | Stop all agents | None |
| `make clean` | Clean logs and temp files | None |
| `make test` | Run all test suites | None |

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
In waiter_standalone.py:42-45, update the example interaction to include
asking for the customer's name
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

Claude: Let me check the A2A connection in waiter_standalone.py:14-17...
[Examines connection code]
The issue is the chef A2A server needs to be running. Let me check:
[Runs make status]
Chef agent is not running. Start it with: make chef-cli

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
