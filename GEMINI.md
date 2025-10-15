# ♊️ Using the Restaurant Project with Gemini CLI

This document provides instructions for using the Restaurant Multi-Agent System with the Gemini CLI, which uses Google's ADK (Agent Development Kit).

## 📋 Overview

The Restaurant Multi-Agent System demonstrates **Agent-to-Agent (A2A)** communication using Google's ADK. It simulates a restaurant with three cooperating AI agents:

- **Waiter Agent** - Takes customer orders (ports: 8001 A2A, 5001 web)
- **Chef Agent** - Prepares dishes based on orders (ports: 8002 A2A, 5002 web)
- **Supplier Agent** - Supplies ingredients (ports: 8003 A2A, 5003 web)

## 🚀 Quick Start with Gemini CLI

The easiest way to get started is to use the `make` commands.

### 1. Start the A2A Servers

In separate terminals, start the `supplier` and `chef` A2A servers:

```bash
# Terminal 1: Start supplier A2A server (port 8003)
make supplier-cli
```

```bash
# Terminal 2: Start chef A2A server (port 8002, requires supplier)
make chef-cli
```

### 2. Start the Waiter Interface

Once the `supplier` and `chef` are running, you can start the waiter:

**Option A: Web Interface (Recommended)**
```bash
# Terminal 3: Start waiter web UI (port 5001)
make waiter-web

# Then open http://localhost:5001 in your browser
```

**Option B: Interactive CLI**
```bash
# Terminal 3: Start waiter CLI
make waiter-cli
```

**Option C: Multi-Agent CLI**
```bash
# Terminal 3: Interactive CLI to chat with any agent
make cli
```

This will drop you into an interactive session with the waiter agent (or selected agent).

### 3. (Optional) Run the Automated Test

To run an automated test of the CLI, you can use the `test` make command:

```bash
make test
```

## 🤖 Interacting with the Agents

You can interact with the agents directly through the Gemini CLI.

### Waiter Agent

The waiter agent is the primary interface for placing orders.

**Example:**

```
> I'd like to order a Greek Salad
```

### Chef Agent

The chef agent can be used to get information about recipes.

**Example:**

```
> What ingredients are in the Grilled Salmon?
```

### Supplier Agent

The supplier agent can be used to check on ingredient availability.

**Example:**

```
> Do you have any tomatoes in stock?
```

## 🛠️ Makefile Commands for Gemini CLI

The following `make` commands are the most relevant for using this project with the Gemini CLI:

### A2A Servers (JSON-RPC)
| Command | Description |
|---|---|
| `make supplier-cli` | Start supplier A2A server (port 8003) |
| `make chef-cli` | Start chef A2A server (port 8002, requires supplier) |
| `make waiter-cli` | Start waiter A2A server (port 8001, requires chef) |

### Web Interfaces
| Command | Description |
|---|---|
| `make supplier-web` | Start supplier web UI (port 5003) |
| `make chef-web` | Start chef web UI (port 5002, requires supplier-cli) |
| `make waiter-web` | Start waiter web UI (port 5001, requires chef-cli) |

### Interactive CLI
| Command | Description |
|---|---|
| `make cli` | Start interactive CLI to chat with any agent |

### Utilities
| Command | Description |
|---|---|
| `make status` | Check which agents are running |
| `make stop` | Stop all agents |
| `make clean` | Clean up logs and temp files |
| `make test` | Run automated test suite |

### Shortcuts (defaults to web interface)
| Command | Description |
|---|---|
| `make supplier` | Same as `make supplier-web` |
| `make chef` | Same as `make chef-web` |
| `make waiter` | Same as `make waiter-web` |

## 🔗 Related Documentation

For more detailed information, see:

- **README.md** - Complete system overview and architecture
- **CLAUDE.md** - Using this project with Claude Code (Anthropic's AI pair programmer)
- **WEBAPP.md** - Web interface implementation details
- **CLI_DEMO.md** - Interactive CLI usage guide
- **SUMMARY.md** - Quick reference and project summary
- **ORDERS_SPEC.md** - Customer orders feature specification

## 💡 Tips

1. **Port Conflicts**: If you get "port already in use" errors, run `make stop` first
2. **Dependencies**: Always start agents in order: supplier → chef → waiter
3. **Status Check**: Use `make status` to see which agents are running
4. **Web vs CLI**: Web interface (`make waiter-web`) is recommended for beginners
5. **Interactive Mode**: Use `make cli` to chat with any running agent

---

**Built with ❤️ using Google ADK, A2A Protocol, and MCP**
