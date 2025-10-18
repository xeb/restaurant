.PHONY: help supplier supplier-cli supplier-web chef chef-cli chef-web waiter waiter-cli waiter-web cli test test-webapp test-all test-orders clean clear stop check-supplier check-chef check-waiter all logs status

.DEFAULT_GOAL := help

# Port configuration
WAITER_PORT := 8001
CHEF_PORT := 8002
SUPPLIER_PORT := 8003
WAITER_WEB_PORT := 5001
CHEF_WEB_PORT := 5002
SUPPLIER_WEB_PORT := 5003

help: ## Show this help menu
	@echo "Restaurant Multi-Agent System Commands"
	@echo "======================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Supplier targets
supplier: supplier-web ## Start supplier (defaults to web interface on port 5003)

supplier-cli: ## Start supplier A2A server on port 8003
	@if lsof -i:$(SUPPLIER_PORT) > /dev/null 2>&1; then \
		echo "⚠️  Port $(SUPPLIER_PORT) is already in use!"; \
		echo ""; \
		echo "The supplier may already be running. Check with:"; \
		echo "  make status"; \
		echo ""; \
		echo "To stop existing agents:"; \
		echo "  make stop"; \
		echo ""; \
		exit 1; \
	fi
	@echo "🚀 Starting supplier A2A server on port $(SUPPLIER_PORT)..."
	@cd supplier && uv run a2a_server.py

supplier-cli-dev: ## Start supplier A2A server with auto-reload (development mode)
	@if lsof -i:$(SUPPLIER_PORT) > /dev/null 2>&1; then \
		echo "⚠️  Port $(SUPPLIER_PORT) is already in use!"; \
		echo ""; \
		echo "The supplier may already be running. Check with:"; \
		echo "  make status"; \
		echo ""; \
		echo "To stop existing agents:"; \
		echo "  make stop"; \
		echo ""; \
		exit 1; \
	fi
	@echo "🚀 Starting supplier A2A server on port $(SUPPLIER_PORT) with auto-reload..."
	@cd supplier && uvicorn a2a_server:a2a_app --host 0.0.0.0 --port $(SUPPLIER_PORT) --reload

supplier-web: ## Start supplier with web + A2A on port 8003 (sessions visible in browser!)
	@echo "🚀 Starting supplier with dual exposure (web + A2A)..."
	@echo "📝 Logging to supplier.log"
	@uv run webapp.py --agent=supplier --with-a2a 2>&1 | tee supplier.log

# Chef targets
chef: chef-web ## Start chef (defaults to web interface on port 5002)

chef-cli: check-supplier ## Start chef A2A server on port 8002 (requires supplier)
	@if lsof -i:$(CHEF_PORT) > /dev/null 2>&1; then \
		echo "⚠️  Port $(CHEF_PORT) is already in use!"; \
		echo ""; \
		echo "The chef may already be running. Check with:"; \
		echo "  make status"; \
		echo ""; \
		echo "To stop existing agents:"; \
		echo "  make stop"; \
		echo ""; \
		exit 1; \
	fi
	@echo "🚀 Starting chef A2A server on port $(CHEF_PORT)..."
	@cd chef && uv run a2a_server.py

chef-cli-dev: check-supplier ## Start chef A2A server with auto-reload (development mode)
	@if lsof -i:$(CHEF_PORT) > /dev/null 2>&1; then \
		echo "⚠️  Port $(CHEF_PORT) is already in use!"; \
		echo ""; \
		echo "The chef may already be running. Check with:"; \
		echo "  make status"; \
		echo ""; \
		echo "To stop existing agents:"; \
		echo "  make stop"; \
		echo ""; \
		exit 1; \
	fi
	@echo "🚀 Starting chef A2A server on port $(CHEF_PORT) with auto-reload..."
	@cd chef && uvicorn a2a_server:a2a_app --host 0.0.0.0 --port $(CHEF_PORT) --reload

chef-web: check-supplier ## Start chef with web + A2A on port 8002 (sessions visible in browser!, requires supplier A2A)
	@echo "🚀 Starting chef with dual exposure (web + A2A)..."
	@echo "📝 Logging to chef.log"
	@uv run webapp.py --agent=chef --with-a2a 2>&1 | tee chef.log

# Waiter targets
waiter: waiter-web ## Start waiter (defaults to web interface on port 5001)

waiter-cli: check-chef ## Start waiter A2A server on port 8001 (requires chef)
	@if lsof -i:$(WAITER_PORT) > /dev/null 2>&1; then \
		echo "⚠️  Port $(WAITER_PORT) is already in use!"; \
		echo ""; \
		echo "The waiter may already be running. Check with:"; \
		echo "  make status"; \
		echo ""; \
		echo "To stop existing agents:"; \
		echo "  make stop"; \
		echo ""; \
		exit 1; \
	fi
	@echo "🚀 Starting waiter A2A server on port $(WAITER_PORT)..."
	@cd waiter && uv run a2a_server.py

waiter-cli-dev: check-chef ## Start waiter A2A server with auto-reload (development mode)
	@if lsof -i:$(WAITER_PORT) > /dev/null 2>&1; then \
		echo "⚠️  Port $(WAITER_PORT) is already in use!"; \
		echo ""; \
		echo "The waiter may already be running. Check with:"; \
		echo "  make status"; \
		echo ""; \
		echo "To stop existing agents:"; \
		echo "  make stop"; \
		echo ""; \
		exit 1; \
	fi
	@echo "🚀 Starting waiter A2A server on port $(WAITER_PORT) with auto-reload..."
	@cd waiter && uvicorn a2a_server:a2a_app --host 0.0.0.0 --port $(WAITER_PORT) --reload

waiter-web: check-chef ## Start waiter with web + A2A on port 8001 (sessions visible in browser!, requires chef A2A)
	@echo "🚀 Starting waiter with dual exposure (web + A2A)..."
	@uv run webapp.py --agent=waiter --with-a2a

cli: ## Start interactive CLI to chat with any agent (at least one agent must be running)
	@echo "🚀 Starting interactive CLI..."
	@uv run interactive_cli.py

check-supplier: ## Check if supplier agent is running
	@echo "🔍 Checking if supplier is running on port $(SUPPLIER_PORT)..."
	@if ! curl -s http://localhost:$(SUPPLIER_PORT)/.well-known/agent-card.json > /dev/null 2>&1; then \
		echo "❌ Error: Supplier agent is not running!"; \
		echo ""; \
		echo "Please start the supplier first:"; \
		echo "  Terminal 1: make supplier-cli"; \
		echo ""; \
		exit 1; \
	fi
	@echo "✅ Supplier is running"

check-chef: check-supplier ## Check if chef agent is running
	@echo "🔍 Checking if chef is running on port $(CHEF_PORT)..."
	@if ! curl -s http://localhost:$(CHEF_PORT)/.well-known/agent-card.json > /dev/null 2>&1; then \
		echo "❌ Error: Chef agent is not running!"; \
		echo ""; \
		echo "Please start the chef:"; \
		echo "  Terminal 1: make supplier-cli"; \
		echo "  Terminal 2: make chef-cli"; \
		echo ""; \
		exit 1; \
	fi
	@echo "✅ Chef is running"

check-waiter: check-chef ## Check if waiter agent is running
	@echo "🔍 Checking if waiter is running on port $(WAITER_PORT)..."
	@if ! curl -s http://localhost:$(WAITER_PORT)/.well-known/agent-card.json > /dev/null 2>&1; then \
		echo "❌ Error: Waiter agent is not running!"; \
		echo ""; \
		echo "Please start all agents:"; \
		echo "  Terminal 1: make supplier-cli"; \
		echo "  Terminal 2: make chef-cli"; \
		echo "  Terminal 3: make waiter-cli"; \
		echo ""; \
		exit 1; \
	fi
	@echo "✅ Waiter is running"

test: test-all ## Run all tests (CLI + webapp + interactive)

test-cli: ## Run interactive CLI test suite
	@echo "🧪 Running interactive CLI tests..."
	@bash test-cli.sh

test-old-cli: ## Run old CLI test suite
	@echo "🧪 Running old CLI tests..."
	@bash test.sh

test-webapp: ## Run webapp test suite
	@echo "🧪 Running webapp tests..."
	@bash test_webapp.sh

test-all: ## Run all automated tests
	@echo "🧪 Running all test suites..."
	@echo ""
	@echo "=== Interactive CLI Tests ==="
	@bash test-cli.sh
	@echo ""
	@echo "=== Old CLI Tests ==="
	@bash test.sh
	@echo ""
	@echo "=== Webapp Tests ==="
	@bash test_webapp.sh
	@echo ""
	@echo "✅ All tests completed!"

test-simple: check-chef ## Run simple order test (requires chef and supplier running)
	@echo "🧪 Running simple order test..."
	@cd waiter && uv run simple_client.py

test-orders: ## Setup and test waiter orders feature via make cli
	@echo "🧪 Setting up waiter orders test..."
	@bash test_waiter_orders.sh

stop: ## Stop all agent servers (A2A and web)
	@echo "🛑 Stopping all agents..."
	@echo "  Killing processes on agent ports..."
	@-lsof -ti:$(WAITER_PORT) 2>/dev/null | xargs -r kill -9 2>/dev/null
	@-lsof -ti:$(CHEF_PORT) 2>/dev/null | xargs -r kill -9 2>/dev/null
	@-lsof -ti:$(SUPPLIER_PORT) 2>/dev/null | xargs -r kill -9 2>/dev/null
	@-lsof -ti:$(WAITER_WEB_PORT) 2>/dev/null | xargs -r kill -9 2>/dev/null
	@-lsof -ti:$(CHEF_WEB_PORT) 2>/dev/null | xargs -r kill -9 2>/dev/null
	@-lsof -ti:$(SUPPLIER_WEB_PORT) 2>/dev/null | xargs -r kill -9 2>/dev/null
	@echo "  Cleaning up any remaining agent processes..."
	@-pgrep -f "bin/python3 webapp.py" 2>/dev/null | grep -v $$$$ | xargs -r kill -9 2>/dev/null
	@-pgrep -f "bin/python3.*a2a_server.py" 2>/dev/null | grep -v $$$$ | xargs -r kill -9 2>/dev/null
	@-pgrep -f "uv run webapp.py" 2>/dev/null | grep -v $$$$ | xargs -r kill -9 2>/dev/null
	@-pgrep -f "uv run.*a2a_server.py" 2>/dev/null | grep -v $$$$ | xargs -r kill -9 2>/dev/null
	@-pgrep -f "interactive_cli.py" 2>/dev/null | grep -v $$$$ | xargs -r kill -9 2>/dev/null
	@sleep 1
	@echo "✅ All agents stopped"

clean: stop ## Clean up logs and temporary files
	@echo "🧹 Cleaning up..."
	@rm -f /tmp/supplier.log /tmp/chef.log /tmp/waiter_test.log
	@rm -rf a2a_traffic
	@echo "✅ Cleanup complete"

clear: ## Clear all order data (resets orders.json and chef_orders.json)
	@echo "🗑️  Clearing order data..."
	@echo '{"orders": {}, "next_order_id": 1}' > orders.json
	@echo '{"orders": {}, "next_order_id": 1}' > chef_orders.json
	@echo "✅ Order data cleared:"
	@echo "  - orders.json reset to empty state"
	@echo "  - chef_orders.json reset to empty state"

status: ## Check status of all agents (unified web + A2A on ports 8001-8003)
	@echo "Agent Status (Unified Web + A2A Endpoints)"
	@echo "==========================================="
	@echo ""
	@echo -n "  Waiter ($(WAITER_PORT)):   "
	@if curl -s http://localhost:$(WAITER_PORT)/.well-known/agent-card.json > /dev/null 2>&1; then \
		echo "✅ Running (web + A2A on http://localhost:$(WAITER_PORT))"; \
	else \
		echo "❌ Not running"; \
	fi
	@echo -n "  Chef ($(CHEF_PORT)):     "
	@if curl -s http://localhost:$(CHEF_PORT)/.well-known/agent-card.json > /dev/null 2>&1; then \
		echo "✅ Running (web + A2A on http://localhost:$(CHEF_PORT))"; \
	else \
		echo "❌ Not running"; \
	fi
	@echo -n "  Supplier ($(SUPPLIER_PORT)): "
	@if curl -s http://localhost:$(SUPPLIER_PORT)/.well-known/agent-card.json > /dev/null 2>&1; then \
		echo "✅ Running (web + A2A on http://localhost:$(SUPPLIER_PORT))"; \
	else \
		echo "❌ Not running"; \
	fi
	@echo ""
	@echo "Note: All agents now expose BOTH web interface AND A2A protocol on the same port!"
	@echo "      View in browser or communicate via A2A - sessions are shared! 🎉"

all: ## Start all agents in background with logging (use 'make logs' to view output)
	@echo "Starting all agents in background..."
	@if lsof -i:$(SUPPLIER_PORT) > /dev/null 2>&1 || lsof -i:$(CHEF_PORT) > /dev/null 2>&1 || lsof -i:$(WAITER_PORT) > /dev/null 2>&1; then \
		echo "⚠️  Some ports are already in use!"; \
		echo ""; \
		make status; \
		echo ""; \
		echo "To stop existing agents: make stop"; \
		exit 1; \
	fi
	@(uv run webapp.py --agent=supplier --with-a2a > supplier.log 2>&1 &) && sleep 3 && echo "  Supplier started (port $(SUPPLIER_PORT), logging to supplier.log)"
	@(uv run webapp.py --agent=chef --with-a2a > chef.log 2>&1 &) && sleep 3 && echo "  Chef started (port $(CHEF_PORT), logging to chef.log)"
	@(uv run webapp.py --agent=waiter --with-a2a > waiter.log 2>&1 &) && sleep 3 && echo "  Waiter started (port $(WAITER_PORT), logging to waiter.log)"
	@echo ""
	@echo "All agents started! 🎉"
	@echo ""
	@make status
	@echo ""
	@echo "To view all logs: make logs"
	@echo "To stop all agents: make stop"

logs: ## Tail all agent logs in real-time
	@echo "Tailing all agent logs (Ctrl+C to stop)..."
	@echo "=========================================="
	@tail -f supplier.log chef.log waiter.log 2>/dev/null || echo "⚠️  No log files found yet. Start agents with 'make all'"
