# 🍽️ Restaurant Multi-Agent System

A demonstration of **Agent-to-Agent (A2A)** communication using Google's Agent Development Kit (ADK). This system simulates a restaurant with three cooperating AI agents that communicate via JSON-RPC, featuring both CLI and web interfaces.

## 📐 System Architecture

### High-Level Overview

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                          RESTAURANT MULTI-AGENT SYSTEM                             │
│                                                                                    │
│  ┌──────────────┐         ┌──────────────┐         ┌──────────────┐               │
│  │    WAITER    │  A2A    │     CHEF     │  A2A    │   SUPPLIER   │               │
│  │   (Web+A2A)  │────────▶│  (Web+A2A)   │────────▶│  (Web+A2A)   │               │
│  │  Port 8001   │         │  Port 8002   │         │  Port 8003   │               │
│  └──┬────────┬──┘         └──┬────────┬──┘         └──────┬───────┘               │
│     │        │               │        │                   │                       │
│     │ MCP    │ MCP           │ MCP    │ MCP               │ MCP                   │
│     ▼        ▼               ▼        ▼                   ▼                       │
│  ┌─────┐  ┌─────┐     ┌─────────┐ ┌──────────┐    ┌──────────┐                  │
│  │Order│  │Menu │     │Order Up │ │ Recipes  │    │  Pantry  │                  │
│  │ MCP │  │ MCP │     │   MCP   │ │   MCP    │    │   MCP    │                  │
│  └──┬──┘  └─┬───┘     └────┬────┘ └────┬─────┘    └────┬─────┘                  │
│     │       │              │           │               │                         │
│     │r/w    │reads         │r/w        │hardcoded      │r/w      reads           │
│     ▼       ▼              ▼           │               ▼           ▼             │
│  ┌──────┐ ┌─────┐    ┌─────────┐      │        ┌──────────┐ ┌──────────┐        │
│  │orders│ │menu │    │  chef   │      │        │  pantry  │ │   food   │        │
│  │.json │ │.json│    │_orders  │      │        │  .json   │ │  .json   │        │
│  │      │ │     │    │  .json  │      │        │(Food IDs)│ │(Food DB) │        │
│  └──────┘ └─────┘    └─────────┘      └───────────────────┘ └──────────┘        │
│                                                                                    │
│  Features:                                                                        │
│  • Unified Web + A2A endpoints on ports 8001-8003                                 │
│  • A2A sessions visible in browser                                                │
│  • Food ID system for ingredient tracking                                         │
│  • Disk-reload for multi-process pantry consistency                               │
│  • Duration tracking for agent responses                                          │
│  • Normalized pantry view for debugging                                           │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### Component Details

#### 1. **Waiter Agent** (Web + A2A on port 8001)
- **Purpose**: Takes customer orders
- **Communication**: Calls Chef via A2A (port 8002)
- **Interface**:
  - Web: Flask app with dual exposure (GET for UI, POST for A2A)
  - A2A sessions visible in browser
- **MCP Connections**:
  - Orders MCP (stdio) - Customer order management
  - Menu MCP (stdio) - Artisanal menu descriptions
- **Tools**:
  - `save_order` - Save customer orders (via Orders MCP)
  - `list_orders` - List outstanding orders (via Orders MCP)
  - `set_order_status` - Update order status (via Orders MCP)
  - `get_order_status` - Check order status (via Orders MCP)
  - `list_menu` - Browse menu items (via Menu MCP)
  - `get_menu_item` - Get menu item details (via Menu MCP)
  - `list_categories` - Get menu categories (via Menu MCP)
  - `search_menu` - Search menu by keyword (via Menu MCP)
  - Chef agent (via RemoteA2aAgent)

#### 2. **Chef Agent** (Web + A2A on port 8002)
- **Purpose**: Prepares dishes based on orders
- **Communication**:
  - Receives orders from Waiter (A2A)
  - Calls Supplier when ingredients needed (A2A port 8003)
- **Interface**: Web + A2A dual exposure
- **MCP Connections**:
  - Recipes MCP (stdio) - Recipe database (hardcoded recipes)
  - Order Up MCP (stdio) - Chef's order completion tracking (auto-incrementing IDs)
  - Pantry MCP (stdio) - Ingredient inventory (disk-reload enabled)
- **Tools**:
  - `list_recipes` - Browse available recipes (via Recipes MCP)
  - `get_recipe` - Get recipe details (via Recipes MCP)
  - `accept_order` - Accept and complete orders with auto-generated ID (via Order Up MCP)
  - `list_ready_orders` - List completed orders (via Order Up MCP)
  - `get_order_status` - Check order status (via Order Up MCP)
  - `check_pantry` - Check ingredient availability by Food ID (via Pantry MCP)
  - `take_ingredients` - Remove ingredients from pantry by Food ID (via Pantry MCP)
  - `list_foods` - Search food database (via Pantry MCP)
  - Supplier agent (via RemoteA2aAgent)

#### 3. **Supplier Agent** (Web + A2A on port 8003)
- **Purpose**: Supplies ingredients to the restaurant
- **Communication**: Receives orders from Chef (A2A)
- **Interface**: Web + A2A dual exposure
- **MCP Connections**:
  - Pantry MCP (stdio) - Restocks ingredients (disk-reload enabled)
- **Tools**:
  - `wait_time` - Simulates delivery (2-5 seconds)
  - `add_ingredients` - Adds to pantry inventory by Food ID (via Pantry MCP)
  - `check_pantry` - Check stock levels by Food ID (via Pantry MCP)
  - `get_low_stock_items` - Get items below threshold (via Pantry MCP)
  - `list_foods` - Search food database (via Pantry MCP)

#### 4. **MCP Servers**

##### Orders MCP Server (`orders_mcp_server.py`)
- **Purpose**: Manages customer orders for the waiter
- **Storage**: `orders.json`
- **Tools**:
  - `save_order(name, order_details, estimated_wait_time)` - Create new order
  - `list_orders()` - Get all outstanding orders (not SERVED)
  - `set_order_status(order_id, status)` - Update order status
  - `get_order_status(order_id)` - Check order status

##### Menu MCP Server (`menu_mcp_server.py`)
- **Purpose**: Provides artisanal menu descriptions for the waiter
- **Storage**: `menu.json` (read-only)
- **Tools**:
  - `list_menu(category)` - List all menu items, optionally filtered by category
  - `get_menu_item(item_name)` - Get detailed information about a specific menu item
  - `list_categories()` - List all available menu categories
  - `search_menu(query)` - Search menu items by keyword

##### Order Up MCP Server (`order_up_mcp_server.py`)
- **Purpose**: Tracks chef's order completion with auto-incrementing IDs
- **Storage**: `chef_orders.json`
- **Tools**:
  - `accept_order(recipe, prep_time, cook_time)` - Accept and complete order (auto-generates order ID)
  - `list_ready_orders()` - List all completed orders
  - `get_order_status(order_id)` - Check order status

##### Pantry MCP Server (`pantry_mcp_server.py`)
- **Purpose**: Manages ingredient inventory using Food IDs with multi-process support
- **Storage**: `pantry.json` (r/w), `food.json` (read-only)
- **Key Feature**: Reloads from disk before each operation to prevent stale data in multi-process environments
- **Tools**:
  - `list_foods(search)` - Search food database by name
  - `list_pantry()` - List all pantry items with names (reloads from disk)
  - `check_pantry(food_id)` - Check quantity of specific Food ID (reloads from disk)
  - `take_ingredients(ingredients)` - Remove ingredients by Food ID (reloads from disk)
  - `add_ingredients(ingredients)` - Add ingredients by Food ID (reloads from disk)
  - `get_low_stock_items(threshold)` - Get items below threshold (reloads from disk)

##### Recipes MCP Server (`chef/recipes_mcp_server.py`)
- **Purpose**: Provides recipe database for the chef
- **Storage**: Hardcoded recipes (no JSON file)
- **Tools**:
  - `list_recipes()` - Get all available recipes
  - `get_recipe(recipe_name)` - Get recipe details with ingredients

#### 5. **JSON Data Files**

##### `food.json` (Food Database)
- **Purpose**: Single source of truth for all foods in the system
- **Structure**: Maps Food ID → {id, name}
- **Used by**: Pantry MCP Server (read-only for name lookups)
- **Count**: 77 food items (IDs 1-77)
- **Example**: `"61": {"id": 61, "name": "pepper"}`

##### `menu.json` (Customer Menu)
- **Purpose**: Artisanal menu descriptions for customer-facing interactions
- **Structure**: Maps menu item name → {name, category, description, price, dietary, prep_time, cook_time}
- **Used by**: Menu MCP Server (read-only)
- **Example**: `"Greek Salad": {"name": "Greek Salad", "category": "Salads", "description": "A taste of the Mediterranean...", ...}`

##### `pantry.json` (Inventory)
- **Purpose**: Tracks available ingredient quantities
- **Structure**: Maps Food ID → quantity
- **Used by**: Pantry MCP Server (read/write)
- **Example**: `"61": 1000` (1000 units of pepper)

##### `orders.json` (Customer Orders)
- **Purpose**: Tracks customer orders from the waiter
- **Structure**: Maps order_id → {order_id, name, order_details, estimated_wait_time, status, timestamps}
- **Used by**: Orders MCP Server (read/write)
- **Statuses**: RECEIVED, COOKING, READY, SERVED

##### `chef_orders.json` (Chef's Order Queue)
- **Purpose**: Tracks chef's order completion
- **Structure**: Maps order_id → {order_id, recipe, prep_time, cook_time, total_time, status, timestamps}
- **Used by**: Order Up MCP Server (read/write)
- **Status**: ready (orders complete instantly in this simulation)

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
| **Unified Web + A2A** | |
| `make supplier` | Start supplier (Web + A2A on port 8003) |
| `make chef` | Start chef (Web + A2A on port 8002, requires supplier) |
| `make waiter` | Start waiter (Web + A2A on port 8001, requires chef) |
| **Utilities** | |
| `make status` | Check which agents are running |
| `make stop` | Stop all agents |
| `make clean` | Clean up logs and temp files |
| `make clear` | Clear all order data (resets orders.json and chef_orders.json) |
| **Testing** | |
| `make test` | Run automated test suite |
| `make test-simple` | Run simple order test |

## 🖥️ Web Interface Features

The web interface (`webapp.py`) provides a rich, interactive experience:

### Features

- **🎯 Multi-Agent Support**: Single webapp handles all agents via `--agent` flag
- **🔄 Unified Endpoints**: Web UI (GET) and A2A protocol (POST) on the same port
- **💬 Real-time Chat**: Interactive chat interface with markdown rendering
- **⏱️ Duration Tracking**: Displays response time for each agent message (e.g., "5 min, 27 sec")
- **📊 Session Management**: View all active sessions (including A2A sessions!)
- **🔧 Tool Call Inspection**: Expandable UI showing tool arguments and results
- **🔄 A2A Call Tracking**: Special highlighting for inter-agent communication
- **💾 Persistent History**: Sessions survive page refreshes
- **🗂️ Data Views**: Browse JSON files (menu, food, pantry, orders) via Data menu
- **🐛 Normalized Pantry**: Debug view merging food.json and pantry.json
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
├── Makefile                     # Build commands (includes 'make clear')
├── webapp.py                    # Flask web interface (all agents, unified Web + A2A)
├── waiter_standalone.py         # Waiter agent for webapp
├── test.sh                      # Automated CLI test
├── test_webapp.sh              # Automated webapp test
│
├── MCP Servers:
├── pantry_mcp_server.py        # Pantry inventory MCP server (Food IDs, disk-reload)
├── menu_mcp_server.py          # Menu MCP server (artisanal descriptions)
├── orders_mcp_server.py        # Waiter orders MCP server
├── order_up_mcp_server.py      # Chef orders MCP server (auto-incrementing IDs)
│
├── JSON Data Files:
├── food.json                   # Food database (77 items, Food ID → name)
├── menu.json                   # Customer menu (artisanal descriptions)
├── pantry.json                 # Pantry inventory (Food ID → quantity)
├── orders.json                 # Customer orders (waiter)
├── chef_orders.json            # Chef's completed orders
│
├── supplier/
│   ├── agent.py                # Supplier agent definition
│   └── a2a_server.py           # A2A server wrapper (legacy, not used with webapp)
│
├── chef/
│   ├── agent.py                # Chef agent definition
│   ├── a2a_server.py           # A2A server wrapper (legacy, not used with webapp)
│   └── recipes_mcp_server.py   # Recipes MCP server (hardcoded recipes)
│
└── waiter/
    ├── cli.py                  # Interactive CLI (legacy)
    └── simple_client.py        # Direct A2A test client (legacy)
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
