# 🍽️ Restaurant Multi-Agent System

A demonstration of **Agent-to-Agent (A2A)** communication using Google's Agent Development Kit (ADK). This system simulates a restaurant with three cooperating AI agents that communicate via JSON-RPC, featuring both CLI and web interfaces.

## 📐 System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        RESTAURANT MULTI-AGENT SYSTEM                    │
│                                                                         │
│  ┌──────────────┐         ┌──────────────┐         ┌──────────────┐     │
│  │    WAITER    │  A2A    │     CHEF     │  A2A    │   SUPPLIER   │     │
│  │   (CLI/Web)  │────────▶│  (Port 8002) │────────▶│  (Port 8003) │     │
│  │  Port 5001   │         │              │         │              │     │
│  └──────────────┘         └───────┬──────┘         └────────┬─────┘     │
│                                   │                         │           │
│                                   │ MCP                     │ MCP       │
│                                   ▼                         ▼           │
│                          ┌─────────────────┐      ┌─────────────────┐   │
│                          │  Recipes MCP    │      │  Pantry MCP     │   │
│                          │  (stdio)        │      │  (stdio)        │   │
│                          └─────────────────┘      └─────────────────┘   │
│                                   │                         │           │
│                                   │ MCP                     │           │
│                                   ▼                         │           │
│                          ┌─────────────────┐                │           │
│                          │  Pantry MCP     │◀───────────────┘           │
│                          │  (stdio)        │                            │
│                          └─────────────────┘                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Details

#### 1. **Waiter Agent** (CLI or Web Interface)
- **Purpose**: Takes customer orders
- **Communication**: Calls Chef via A2A (port 8002)
- **Interface**:
  - CLI: Interactive REPL
  - Web: Flask app on port 5001
- **Tools**: Chef agent (via RemoteA2aAgent)

#### 2. **Chef Agent** (A2A Server on port 8002)
- **Purpose**: Prepares dishes based on orders
- **Communication**:
  - Receives orders from Waiter (A2A)
  - Calls Supplier when ingredients needed (A2A port 8003)
- **MCP Connections**:
  - Recipes MCP (stdio) - Recipe database
  - Pantry MCP (stdio) - Ingredient inventory
- **Tools**:
  - `list_recipes` - Browse available recipes
  - `get_recipe` - Get recipe details
  - `check_pantry` - Check ingredient availability
  - `take_ingredients` - Remove ingredients from pantry
  - Supplier agent (via RemoteA2aAgent)

#### 3. **Supplier Agent** (A2A Server on port 8003)
- **Purpose**: Supplies ingredients to the restaurant
- **Communication**: Receives orders from Chef (A2A)
- **MCP Connections**:
  - Pantry MCP (stdio) - Restocks ingredients
- **Tools**:
  - `wait_time` - Simulates delivery (2-5 seconds)
  - `add_ingredients` - Adds to pantry inventory

### Data Flow Example

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          ORDER FLOW: "Greek Salad"                       │
└─────────────────────────────────────────────────────────────────────────┘

1. Customer → Waiter: "I'd like the Greek Salad please"
   │
   ▼
2. Waiter → Chef (A2A): "Order: Greek Salad"
   │
   ▼
3. Chef → Recipes MCP: list_recipes() → get_recipe("Greek Salad")
   │
   ▼
4. Chef → Pantry MCP: check_pantry(["tomatoes", "cucumbers", "feta", ...])
   │
   ▼
5. Chef → Pantry MCP: take_ingredients({"tomatoes": 4, "cucumbers": 2, ...})
   │
   ├─── IF MISSING ───┐
   │                  ▼
   │         Chef → Supplier (A2A): Order missing ingredients
   │                  │
   │                  ▼
   │         Supplier → wait_time(item, qty) [2-5 sec delay]
   │                  │
   │                  ▼
   │         Supplier → Pantry MCP: add_ingredients({...})
   │                  │
   │                  ▼
   │         Supplier → Chef: "Delivered!"
   │                  │
   └──────────────────┘
   │
   ▼
6. Chef → Waiter: "Ready in 15 minutes (prep: 15min, cook: 0min)"
   │
   ▼
7. Waiter → Customer: "Excellent choice! Your Greek Salad will be ready in 15 minutes."
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- `uv` package manager
- Terminal/shell access

### Installation

```bash
# Clone or navigate to the restaurant directory
cd /path/to/restaurant

# All dependencies are managed by uv (no manual installation needed)
```

### Option 1: Web Interface (Recommended)

**Step 1: Start A2A Servers** (in separate terminals)

```bash
# Terminal 1: Supplier A2A Server
make supplier
# Or: cd supplier && uv run a2a_server.py

# Terminal 2: Chef A2A Server
make chef
# Or: cd chef && uv run a2a_server.py
```

**Step 2: Start Web Interfaces** (in separate terminals)

```bash
# Terminal 3: Waiter Web UI
make waiter-web
# Opens on http://localhost:5001

# Optional: Chef Web UI
make chef-web
# Opens on http://localhost:5002

# Optional: Supplier Web UI
make supplier-web
# Opens on http://localhost:5003
```

**Step 3: Open Browser**

Navigate to http://localhost:5001 and start chatting with the waiter!

### Option 2: CLI Interface

```bash
# Terminal 1: Start supplier
make supplier

# Terminal 2: Start chef
make chef

# Terminal 3: Start waiter CLI
make waiter
# Interactive REPL - type your orders!
```

### Option 3: Automated Test

```bash
# Run full system test
make test

# Or manually:
bash test.sh
```

## 🤖 Gemini CLI Integration

This project can also be used with the Gemini CLI. For detailed instructions, please see the [GEMINI.md](GEMINI.md) file.

## 📋 Make Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| **A2A Servers** | |
| `make supplier` | Start supplier A2A server (port 8003) |
| `make chef` | Start chef A2A server (port 8002, requires supplier) |
| **Web Interfaces** | |
| `make waiter-web` | Start waiter web UI (port 5001, requires chef) |
| `make chef-web` | Start chef web UI (port 5002, requires supplier) |
| `make supplier-web` | Start supplier web UI (port 5003) |
| **CLI Interface** | |
| `make waiter` | Start waiter CLI (requires chef) |
| **Utilities** | |
| `make status` | Check which agents are running |
| `make stop` | Stop all agents |
| `make clean` | Clean up logs and temp files |
| `make test` | Run automated test suite |
| `make test-simple` | Run simple order test |

## 🖥️ Web Interface Features

The web interface (`webapp.py`) provides a rich, interactive experience:

### Features

- **🎯 Multi-Agent Support**: Single webapp handles all agents via `--agent` flag
- **💬 Real-time Chat**: Interactive chat interface with markdown rendering
- **📊 Session Management**: View all active sessions with message counts
- **🔧 Tool Call Inspection**: Expandable UI showing tool arguments and results
- **🔄 A2A Call Tracking**: Special highlighting for inter-agent communication
- **💾 Persistent History**: Sessions survive page refreshes
- **🎨 Clean UI**: Tailwind CSS, responsive design, Inter font

### Visual Elements

**Tool Calls** (Pink highlight):
```
🔧 Tool Call: check_pantry
  Arguments: {"ingredients": ["tomatoes", "feta", "cucumbers"]}
  Result: {"available": true, "quantities": {...}}
```

**A2A Calls** (Yellow highlight):
```
🔄 A2A Call: supplier_agent
  Request: "Order: 2 tomatoes, 1 feta cheese"
  Response: "Delivered in 4 seconds"
```

**Session List** (Right panel):
```
Active Sessions (3)
├── session_1234... [ACTIVE]
│   └── 12 messages
├── session_5678...
│   └── 8 messages
└── session_9012...
    └── 3 messages
```

## 🧪 Testing

### Automated Tests

```bash
# Full system test (A2A servers + CLI)
bash test.sh

# Web interface test
bash test_webapp.sh
```

### Manual Testing

**Web Interface:**
1. Start supplier A2A: `make supplier`
2. Start chef A2A: `make chef`
3. Start waiter web: `make waiter-web`
4. Visit http://localhost:5001
5. Try ordering: "I'd like the Greek Salad please"

**CLI Interface:**
1. Start supplier: `make supplier`
2. Start chef: `make chef`
3. Start waiter: `make waiter`
4. Type: `I'd like the Grilled Salmon`
5. Observe the full workflow in the terminal

## 📦 Project Structure

```
restaurant/
├── README.md                    # This file
├── GEMINI.md                    # Gemini CLI instructions
├── WEBAPP.md                    # Web interface documentation
├── Makefile                     # Build commands
├── webapp.py                    # Flask web interface (all agents)
├── waiter_standalone.py         # Waiter agent for webapp
├── test.sh                      # Automated CLI test
├── test_webapp.sh              # Automated webapp test
├── pantry_mcp_server.py        # Shared pantry MCP server
│
├── supplier/
│   ├── agent.py                # Supplier agent definition
│   └── a2a_server.py           # A2A server wrapper (port 8003)
│
├── chef/
│   ├── agent.py                # Chef agent definition
│   ├── a2a_server.py           # A2A server wrapper (port 8002)
│   └── recipes_mcp_server.py   # Recipes MCP server
│
└── waiter/
    ├── cli.py                  # Interactive CLI (ADK Runner)
    └── simple_client.py        # Direct A2A test client
```

## 🔧 Technical Details

### Technologies Used

- **Google ADK** - Agent Development Kit for building AI agents
- **A2A Protocol** - Agent-to-Agent communication (JSON-RPC 2.0)
- **MCP (Model Context Protocol)** - Tool server protocol
- **FastMCP** - Python MCP server framework
- **Flask** - Web framework for UI
- **UV** - Python package manager
- **Gemini 2.5 Flash** - LLM model

### A2A Communication

Agents expose themselves via the A2A protocol:

```python
from google.adk.a2a.utils.agent_to_a2a import to_a2a

# Wrap agent with A2A server
a2a_app = to_a2a(root_agent, port=8003)

# Auto-generates agent card at:
# http://localhost:8003/.well-known/agent-card.json
```

Remote agents are consumed as tools:

```python
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.tools.agent_tool import AgentTool

# Connect to remote agent
remote_agent = RemoteA2aAgent(
    name="chef_agent",
    agent_card="http://localhost:8002/.well-known/agent-card.json"
)

# Wrap as tool
chef_tool = AgentTool(agent=remote_agent)

# Add to agent
waiter_agent = Agent(
    name="waiter_agent",
    tools=[chef_tool]  # Chef is now a tool
)
```

### MCP Integration

Agents connect to MCP servers via stdio:

```python
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StdioConnectionParams,
    StdioServerParameters
)

# Connect to MCP server
recipes_connection = StdioConnectionParams(
    server_params=StdioServerParameters(
        command="uv",
        args=["run", "recipes_mcp_server.py"]
    )
)

recipes_toolset = McpToolset(
    connection_params=recipes_connection
)

# Add to agent
chef_agent = Agent(
    name="chef_agent",
    tools=[recipes_toolset]
)
```

### Agent Instructions

Each agent has specific instructions for behavior:

**Waiter:**
- Greet customers warmly
- Take food orders
- Use chef_agent tool for all orders
- Relay time estimates

**Chef:**
- Receive orders from waiter
- Look up recipes using MCP
- Check pantry for ingredients
- Order from supplier if ingredients missing
- Calculate total time (prep + cook + delivery)

**Supplier:**
- Receive ingredient orders
- Use wait_time to simulate delivery (2-5 sec)
- Add ingredients to pantry
- Report completion

## 🐛 Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Check what's using the port
lsof -i :8002

# Kill the process
kill -9 <PID>

# Or use make
make stop
```

**Agent Can't Connect**
```bash
# Check status
make status

# Expected output:
# Supplier (8003): ✅ Running
# Chef (8002):     ✅ Running

# If not running, start them:
make supplier
make chef
```

**MCP Connection Errors**
```bash
# Check that MCP server files exist
ls pantry_mcp_server.py
ls chef/recipes_mcp_server.py

# Check relative paths in agent files
# Should use: "../pantry_mcp_server.py" from supplier/chef
```

**Webapp Won't Start**
```bash
# Check Python version
python3 --version  # Should be 3.10+

# Check uv is installed
uv --version

# Try with debug flag
uv run webapp.py --agent=waiter --port=5001 --debug
```

### Debug Logs

Log files are written to `/tmp/`:
- `/tmp/supplier.log` - Supplier A2A server
- `/tmp/chef.log` - Chef A2A server
- `/tmp/waiter_test.log` - Test output

View logs:
```bash
tail -f /tmp/supplier.log
tail -f /tmp/chef.log
```

## 📚 Example Sessions

### CLI Example

```bash
$ make waiter

🍽️  Welcome to the Restaurant!
================================================================================

I'm your waiter. What would you like to order today?
(Type 'menu' to see available dishes, 'quit' to exit)

Customer: What's on the menu?

Waiter: Let me check our menu...

[CHEF] Looking up available recipes...
[CHEF] Found 10 recipes: Greek Salad, Grilled Salmon, ...

Customer: I'd like the Greek Salad please

Waiter: Taking order...

[CHEF] Checking recipe for Greek Salad...
[CHEF] Ingredients: tomatoes (4), cucumbers (2), feta (100g), ...
[CHEF] Checking pantry...
[CHEF] Missing: cucumbers (2), feta (100g)
[CHEF] Ordering from supplier...

[SUPPLIER] 📦 Preparing 2 units of cucumbers... (will take 3 seconds)
[SUPPLIER] ✅ cucumbers ready for delivery!
[SUPPLIER] 📦 Preparing 100 units of feta cheese... (will take 4 seconds)
[SUPPLIER] ✅ feta cheese ready for delivery!

[CHEF] Ingredients restocked!
[CHEF] Prep: 15min, Cook: 0min, Delivery: 7sec
[CHEF] Total: 15 minutes

Waiter: Excellent choice! Your Greek Salad will be ready in about 15 minutes!

Customer: quit

[WAITER] Thank you for dining with us! Goodbye! 👋
```

### Web Interface Example

**Browser: http://localhost:5001**

```
┌─────────────────────────────────────────────────────────┐
│  🍽️ Restaurant - Waiter                Port 5001        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  You: I'd like the Greek Salad please                   │
│                                                          │
│  🔧 Tool Call: chef_agent                    [▼]        │
│     Arguments: {"message": "Order: Greek Salad"}        │
│     Result: "Ready in 15 minutes..."                    │
│                                                          │
│  Waiter: Excellent choice! Your Greek Salad will be     │
│          ready in about 15 minutes. The chef is         │
│          preparing it now!                              │
│                                                          │
│  [Type your message...]                          [Send] │
└─────────────────────────────────────────────────────────┘
```

## 🚢 Deployment

### Local Development

```bash
# Current setup (development mode)
make supplier
make chef
make waiter-web
```

### Production Considerations

For production deployment:

1. **Use Production WSGI Server**
   ```bash
   # Instead of Flask dev server, use gunicorn
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5001 webapp:app
   ```

2. **Environment Variables**
   ```bash
   export SUPPLIER_PORT=8003
   export CHEF_PORT=8002
   export WAITER_PORT=5001
   ```

3. **Process Management**
   ```bash
   # Use systemd, supervisor, or pm2
   # Example systemd service:
   [Unit]
   Description=Restaurant Supplier A2A

   [Service]
   WorkingDirectory=/path/to/restaurant/supplier
   ExecStart=/usr/bin/uv run a2a_server.py
   Restart=always
   ```

4. **Reverse Proxy** (nginx/Apache)
   ```nginx
   location /waiter/ {
       proxy_pass http://localhost:5001/;
   }
   ```

## 🔐 Security Notes

**Development Only**: This is a demonstration system. For production:

- Add authentication/authorization
- Implement rate limiting
- Use HTTPS (TLS/SSL)
- Validate all inputs
- Implement proper error handling
- Add logging and monitoring
- Secure API keys (use environment variables)

## 🤝 Contributing

This is a demonstration project. To extend:

1. **Add New Agents**: Create new agent folder with `agent.py` and `a2a_server.py`
2. **Add New Tools**: Implement FunctionTool or MCP server
3. **Enhance UI**: Modify `webapp.py` HTML template
4. **Add Features**: Update agent instructions and tools

## 📄 License

This project is for educational and demonstration purposes.

## 🔗 References

- [Google ADK Documentation](https://googleapis.github.io/python-adk/)
- [A2A Protocol Specification](https://a2a.dev/)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)

## 📞 Support

For issues or questions:
- Check [WEBAPP.md](WEBAPP.md) for web interface details
- Review logs in `/tmp/`
- Run `make status` to check agent health
- Use `make clean` to reset state

---

**Built with ❤️ using Google ADK, A2A Protocol, and MCP**
