# How to Restart After Path Fixes

The MCP path detection code is evaluated when the agent module is first imported. If the webapp or servers were already running, they need to be restarted to pick up the changes.

## Complete Restart Process

```bash
# 1. Stop ALL running agents and webapps
make stop

# Wait a moment for processes to fully terminate
sleep 2

# 2. Verify nothing is running
make status
# All should show "❌ Not running"

# 3. Verify the changes are in place
grep -n "possible_paths" supplier/agent.py chef/agent.py waiter_standalone.py waiter/a2a_server.py

# 4. Start fresh
# For web interface:
make supplier       # Will use supplier/agent.py with smart paths
# OR for CLI:
make supplier-cli   # A2A server

# 5. Check the startup logs
# Look for:
# [SUPPLIER] ✅ Connected to pantry MCP server (using pantry_mcp_server.py)
```

## If Still Not Working

Check if there's a cached Python bytecode:

```bash
# Remove all .pyc files and __pycache__ directories
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Remove any uv cache for this project
rm -rf .venv 2>/dev/null || true

# Now restart
make stop
sleep 2
make supplier
```

## Debugging Path Detection

Run this to see what paths will be detected:

```bash
cd /path/to/restaurant
python3 -c "
import os
print('Current directory:', os.getcwd())
print('pantry_mcp_server.py exists:', os.path.exists('pantry_mcp_server.py'))
print('../pantry_mcp_server.py exists:', os.path.exists('../pantry_mcp_server.py'))
"
```

Expected output when in root:
```
Current directory: /path/to/restaurant
pantry_mcp_server.py exists: True
../pantry_mcp_server.py exists: False
```

## Alternative: Explicit Path Override

If the smart detection still fails, you can set an environment variable:

```bash
export RESTAURANT_ROOT="/full/path/to/restaurant"
make supplier
```

Then update the agents to use this variable (let me know if you need this).
