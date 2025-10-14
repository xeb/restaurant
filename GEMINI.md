# ♊️ Using the Restaurant Project with Gemini CLI

This document provides instructions on how to interact with the Restaurant Multi-Agent System using the Gemini CLI.

## 🚀 Quick Start with Gemini CLI

The easiest way to get started is to use the `make` commands.

### 1. Start the A2A Servers

In separate terminals, start the `supplier` and `chef` A2A servers:

```bash
make supplier
```

```bash
make chef
```

### 2. Start the Waiter CLI

Once the `supplier` and `chef` are running, you can start the interactive waiter CLI:

```bash
make waiter
```

This will drop you into an interactive session with the waiter agent.

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

| Command | Description |
|---|---|
| `make supplier` | Start supplier A2A server (port 8003) |
| `make chef` | Start chef A2A server (port 8002, requires supplier) |
| `make waiter` | Start waiter CLI (requires chef) |
| `make status` | Check which agents are running |
| `make stop` | Stop all agents |
| `make clean` | Clean up logs and temp files |
| `make test` | Run automated test suite |
