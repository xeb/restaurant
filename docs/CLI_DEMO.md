# Interactive CLI Demo

## Overview

The `interactive_cli.py` provides a terminal-based interface to chat with any of the restaurant agents (Waiter, Chef, or Supplier) using A2A communication.

## Features

- **Agent Selection Menu**: Choose which agent to talk to using arrow keys
- **Status Check**: Automatically verifies all agents are running before connecting
- **Colored REPL**: Agent-specific colored prompts (cyan for waiter, yellow for chef, green for supplier)
- **Tool Call Visualization**: See MCP tool calls and A2A agent calls in real-time with colored panels
- **Rich Formatting**: Markdown-rendered responses with syntax highlighting for JSON arguments

## Quick Start

### 1. Start One or More A2A Servers

You can start any combination of agents. The CLI will show only the running agents.

**Option A: Start all agents** (in separate terminals):

```bash
# Terminal 1
make supplier-cli

# Terminal 2
make chef-cli

# Terminal 3
make waiter-cli
```

**Option B: Start just one agent** (for testing):

```bash
make supplier-cli
```

**Option C: Start a subset**:

```bash
make supplier-cli  # Terminal 1
make chef-cli      # Terminal 2
```

### 2. Launch the Interactive CLI

```bash
make cli
```

The CLI will automatically detect which agents are running and show only those in the menu.

## Example Sessions

### All Agents Running

```
🍽️  Restaurant Multi-Agent CLI

Agent Status:
========================================
  Waiter     (port 8001): ✅ Running
  Chef       (port 8002): ✅ Running
  Supplier   (port 8003): ✅ Running
========================================

Select an agent to chat with:
  > Waiter (port 8001)
    Chef (port 8002)
    Supplier (port 8003)
    Exit
```

### Only Some Agents Running

```
🍽️  Restaurant Multi-Agent CLI

Agent Status:
========================================
  Waiter     (port 8001): ❌ Not running
  Chef       (port 8002): ✅ Running
  Supplier   (port 8003): ✅ Running
========================================

ℹ️  Some agents are not running. Only running agents are available for chat.

Select an agent to chat with:
  > Chef (port 8002)
    Supplier (port 8003)
    Exit
```

### No Agents Running

```
🍽️  Restaurant Multi-Agent CLI

Agent Status:
========================================
  Waiter     (port 8001): ❌ Not running
  Chef       (port 8002): ❌ Not running
  Supplier   (port 8003): ❌ Not running
========================================

⚠️  No agents are running!

Start at least one agent:
  make supplier-cli  # Terminal 1
  make chef-cli      # Terminal 2
  make waiter-cli    # Terminal 3

Then run: make cli
```

### Chatting with the Waiter

```
🤖 Connected to Waiter Agent
Type your message or 'exit' to quit

waiter> I'd like to order the Greek Salad please

⠋ Thinking...

🔧 Tool Call: chef_agent
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Arguments ━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ {                                                                   ┃
┃   "message": "Order: Greek Salad"                                   ┃
┃ }                                                                   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

✓ Tool Result: chef_agent
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Result ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Greek Salad will be ready in 15 minutes (prep: 15min, cook: 0min) ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

╭─────────────────────── Waiter Response ────────────────────────╮
│                                                                 │
│  Excellent choice! Your Greek Salad will be ready in           │
│  15 minutes!                                                    │
│                                                                 │
│  The chef is preparing it now. It should be fresh and          │
│  delicious!                                                     │
│                                                                 │
╰─────────────────────────────────────────────────────────────────╯

waiter> exit

Goodbye from Waiter!
```

### Chatting with the Chef

```
🤖 Connected to Chef Agent
Type your message or 'exit' to quit

chef> What's in the Greek Salad?

⠋ Thinking...

🔧 Tool Call: get_recipe
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Arguments ━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ {                                                                   ┃
┃   "name": "Greek Salad"                                             ┃
┃ }                                                                   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

✓ Tool Result: get_recipe
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Result ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ {                                                                   ┃
┃   "name": "Greek Salad",                                            ┃
┃   "ingredients": {                                                  ┃
┃     "cucumbers": 2,                                                 ┃
┃     "tomatoes": 3,                                                  ┃
┃     "feta": 8,                                                      ┃
┃     "olives": 12,                                                   ┃
┃     "olive oil": 3,                                                 ┃
┃     "lemon juice": 2                                                ┃
┃   },                                                                ┃
┃   "prep_time_minutes": 15,                                          ┃
┃   "cook_time_minutes": 0                                            ┃
┃ }                                                                   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

╭──────────────────────── Chef Response ─────────────────────────╮
│                                                                 │
│  The Greek Salad contains:                                      │
│                                                                 │
│  • 2 cucumbers                                                  │
│  • 3 tomatoes                                                   │
│  • 8 oz feta cheese                                             │
│  • 12 olives                                                    │
│  • 3 tbsp olive oil                                             │
│  • 2 tbsp lemon juice                                           │
│                                                                 │
│  Prep time: 15 minutes | Cook time: 0 minutes                   │
│                                                                 │
╰─────────────────────────────────────────────────────────────────╯

chef> exit

Goodbye from Chef!
```

### Chatting with the Supplier

```
🤖 Connected to Supplier Agent
Type your message or 'exit' to quit

supplier> What do you have in stock?

⠋ Thinking...

🔧 Tool Call: check_pantry
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Arguments ━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ {                                                                   ┃
┃   "items": []                                                       ┃
┃ }                                                                   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

✓ Tool Result: check_pantry
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Result ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ {                                                                   ┃
┃   "status": "success",                                              ┃
┃   "inventory": {                                                    ┃
┃     "tomatoes": 20,                                                 ┃
┃     "onions": 15,                                                   ┃
┃     "cheese": 10,                                                   ┃
┃     ...                                                             ┃
┃   }                                                                 ┃
┃ }                                                                   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

╭────────────────────── Supplier Response ───────────────────────╮
│                                                                 │
│  Current pantry inventory:                                      │
│                                                                 │
│  • Tomatoes: 20 units                                           │
│  • Onions: 15 units                                             │
│  • Cheese: 10 units                                             │
│  ...                                                            │
│                                                                 │
╰─────────────────────────────────────────────────────────────────╯

supplier> exit

Goodbye from Supplier!
```

## Color Scheme

- **Waiter**: Cyan prompts and borders
- **Chef**: Yellow prompts and borders
- **Supplier**: Green prompts and borders
- **Tool Calls**: Magenta borders
- **Tool Results**: Green borders
- **Status**: Blue text for running, red for errors

## Commands

| Command | Description |
|---------|-------------|
| `make cli` | Start the interactive CLI |
| `exit` or `quit` or `q` | Exit the current agent chat |
| `Ctrl+C` | Force quit |

## Error Handling

If any agents are not running, you'll see:

```
⚠️  Not all agents are running!

Start agents with:
  make supplier-cli  # Terminal 1
  make chef-cli      # Terminal 2
  make waiter-cli    # Terminal 3

Then run: make cli
```

## Technical Details

- Uses `simple-term-menu` for the agent selection interface
- Uses `colorama` for colored terminal output
- Uses `rich` for formatted panels and markdown rendering
- Connects to agents via `RemoteA2aAgent` over HTTP
- Extracts and displays tool calls from ADK events
- Session persists for the duration of the chat

## Tips

1. **See Tool Calls**: Every MCP tool call and A2A agent call is displayed with arguments and results
2. **Markdown Support**: Agent responses support markdown formatting
3. **Arrow Keys**: Use arrow keys to select agents in the menu
4. **Quick Exit**: Type 'exit', 'quit', or 'q' to leave an agent chat
5. **Switch Agents**: Exit current chat and run `make cli` again to talk to a different agent
