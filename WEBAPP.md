# Restaurant Multi-Agent Web Interface

## Overview

The restaurant project now includes a comprehensive web interface (`webapp.py`) that allows you to interact with each agent through a browser-based chat UI. The webapp displays:

- **Real-time chat** with the agent
- **Session management** - see all active sessions
- **Tool call inspection** - view arguments and results
- **A2A call tracking** - monitor inter-agent communication

## Architecture

```
┌─────────────────────┐
│   Waiter Webapp     │  Port 5001
│  (Flask + Jinja2)   │
└──────────┬──────────┘
           │ A2A
           ▼
┌─────────────────────┐
│   Chef A2A Server   │  Port 8002
│   (JSON-RPC/HTTP)   │
└──────────┬──────────┘
           │ A2A
           ▼
┌─────────────────────┐
│ Supplier A2A Server │  Port 8003
│   (JSON-RPC/HTTP)   │
└─────────────────────┘
```

## Features

### 1. Multi-Agent Support

Run any agent with the `--agent` flag:

```bash
uv run webapp.py --agent=waiter --port=5001
uv run webapp.py --agent=chef --port=5002
uv run webapp.py --agent=supplier --port=5003
```

### 2. Session Listing

The right panel shows all active sessions:
- Session ID (truncated)
- Message count
- Creation timestamp
- Active session highlight

### 3. Tool Call Inspection

Tool calls are displayed with:
- Collapsible details (click to expand)
- JSON-formatted arguments
- JSON-formatted results
- Timestamp
- Pink highlight

### 4. A2A Call Tracking

A2A calls between agents are shown with:
- Target agent name
- Request message
- Response message
- Yellow/amber highlight

### 5. Chat History

- Persists across page refreshes
- Clear chat button to start new session
- Markdown rendering for agent responses
- Timestamps for all messages

## Usage

### Starting the System

**Method 1: Using Make (Recommended)**

```bash
# Terminal 1: Start supplier A2A server
make supplier

# Terminal 2: Start chef A2A server
make chef

# Terminal 3: Start waiter webapp
make waiter-web
```

**Method 2: Direct Commands**

```bash
# Terminal 1
cd supplier && uv run a2a_server.py

# Terminal 2
cd chef && uv run a2a_server.py

# Terminal 3
uv run webapp.py --agent=waiter --port=5001
```

### Accessing the Web Interface

Open your browser to:
- Waiter: http://localhost:5001
- Chef: http://localhost:5002 (if running chef-web)
- Supplier: http://localhost:5003 (if running supplier-web)

## Implementation Details

### Agent Loading

The webapp dynamically loads agents using Python's `importlib`:

```python
# For waiter: uses waiter_standalone.py (connects to chef via A2A)
# For chef: uses chef/agent.py (direct instantiation)
# For supplier: uses supplier/agent.py (direct instantiation)
```

### Session Management

- Uses `InMemorySessionService` from Google ADK
- Each browser session gets a unique ID (stored in localStorage)
- Sessions are tracked server-side in a global dict
- Real-time session list updates every 5 seconds

### Event Processing

Tool calls and A2A calls are extracted from ADK events:

```python
# Function calls (tools)
if hasattr(part, 'function_call'):
    tool_calls.append({...})

# Function responses
if hasattr(part, 'function_response'):
    # Match response to call and update
```

### UI Components

- **Header**: Agent name and port
- **Left Panel**: Chat interface with message history
- **Right Panel**: Active sessions list
- **Tool Messages**: Collapsible with args/results
- **A2A Messages**: Yellow highlight for agent calls

## Testing

Run the test script to verify everything works:

```bash
bash test_webapp.sh
```

This will:
1. Start supplier A2A server
2. Start chef A2A server
3. Start waiter webapp
4. Verify HTTP connectivity
5. Clean up processes

## Troubleshooting

### Webapp won't start

**Error**: Port already in use
```bash
# Check what's using the port
lsof -i :5001

# Kill it
kill -9 <PID>
```

**Error**: Can't connect to chef/supplier
```bash
# Make sure A2A servers are running
make status

# Start them if needed
make supplier
make chef
```

### Tool calls not showing

The webapp extracts tool calls from ADK events. If they're not showing:
1. Check console logs for errors
2. Verify agent has tools configured
3. Check that `function_call` events are being emitted

### A2A calls not tracked

A2A calls are detected by looking for 'agent' in the tool name:

```python
if 'agent' in tool_name.lower():
    # Treat as A2A call
```

If using different naming, update this logic.

## Files

```
restaurant/
├── webapp.py                 # Main web interface
├── waiter_standalone.py      # Standalone waiter agent for webapp
├── test_webapp.sh           # Webapp test script
└── Makefile                 # Updated with *-web targets
```

## Next Steps

Possible enhancements:
- [ ] Streaming responses (SSE or WebSocket)
- [ ] Multi-session support (switch between sessions)
- [ ] Export chat history
- [ ] Agent performance metrics
- [ ] Visual graph of A2A calls
- [ ] MCP tool visualization
