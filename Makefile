.PHONY: help supplier supplier-cli supplier-web chef chef-cli chef-web waiter waiter-cli waiter-web cli test test-webapp test-all clean stop check-supplier check-chef check-waiter all status

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

supplier-web: ## Start supplier web interface on port 5003
	@echo "🚀 Starting supplier web interface on port $(SUPPLIER_WEB_PORT)..."
	@uv run webapp.py --agent=supplier --port=$(SUPPLIER_WEB_PORT)

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

chef-web: check-supplier ## Start chef web interface on port 5002 (requires supplier A2A)
	@echo "🚀 Starting chef web interface on port $(CHEF_WEB_PORT)..."
	@uv run webapp.py --agent=chef --port=$(CHEF_WEB_PORT)

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

waiter-web: check-chef ## Start waiter web interface on port 5001 (requires chef A2A)
	@echo "🚀 Starting waiter web interface on port $(WAITER_WEB_PORT)..."
	@uv run webapp.py --agent=waiter --port=$(WAITER_WEB_PORT)

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

stop: ## Stop all agent servers (A2A and web)
	@echo "🛑 Stopping all agents..."
	@pkill -f "uv run.*a2a_server.py" || true
	@pkill -f "webapp.py" || true
	@pkill -f "interactive_cli.py" || true
	@lsof -ti:$(WAITER_PORT) | xargs kill -9 2>/dev/null || true
	@lsof -ti:$(CHEF_PORT) | xargs kill -9 2>/dev/null || true
	@lsof -ti:$(SUPPLIER_PORT) | xargs kill -9 2>/dev/null || true
	@lsof -ti:$(WAITER_WEB_PORT) | xargs kill -9 2>/dev/null || true
	@lsof -ti:$(CHEF_WEB_PORT) | xargs kill -9 2>/dev/null || true
	@lsof -ti:$(SUPPLIER_WEB_PORT) | xargs kill -9 2>/dev/null || true
	@sleep 1
	@echo "✅ All agents stopped (A2A servers and web interfaces)"

clean: stop ## Clean up logs and temporary files
	@echo "🧹 Cleaning up..."
	@rm -f /tmp/supplier.log /tmp/chef.log /tmp/waiter_test.log
	@echo "✅ Cleanup complete"

status: ## Check status of all agents (A2A and web)
	@echo "Agent Status"
	@echo "============"
	@echo ""
	@echo "A2A Servers:"
	@echo -n "  Waiter ($(WAITER_PORT)):   "
	@if curl -s http://localhost:$(WAITER_PORT)/.well-known/agent-card.json > /dev/null 2>&1; then \
		echo "✅ Running"; \
	else \
		echo "❌ Not running"; \
	fi
	@echo -n "  Chef ($(CHEF_PORT)):     "
	@if curl -s http://localhost:$(CHEF_PORT)/.well-known/agent-card.json > /dev/null 2>&1; then \
		echo "✅ Running"; \
	else \
		echo "❌ Not running"; \
	fi
	@echo -n "  Supplier ($(SUPPLIER_PORT)): "
	@if curl -s http://localhost:$(SUPPLIER_PORT)/.well-known/agent-card.json > /dev/null 2>&1; then \
		echo "✅ Running"; \
	else \
		echo "❌ Not running"; \
	fi
	@echo ""
	@echo "Web Interfaces:"
	@echo -n "  Waiter ($(WAITER_WEB_PORT)):   "
	@if curl -s http://localhost:$(WAITER_WEB_PORT)/ > /dev/null 2>&1; then \
		echo "✅ Running"; \
	else \
		echo "❌ Not running"; \
	fi
	@echo -n "  Chef ($(CHEF_WEB_PORT)):     "
	@if curl -s http://localhost:$(CHEF_WEB_PORT)/ > /dev/null 2>&1; then \
		echo "✅ Running"; \
	else \
		echo "❌ Not running"; \
	fi
	@echo -n "  Supplier ($(SUPPLIER_WEB_PORT)): "
	@if curl -s http://localhost:$(SUPPLIER_WEB_PORT)/ > /dev/null 2>&1; then \
		echo "✅ Running"; \
	else \
		echo "❌ Not running"; \
	fi

all: ## Start all agents in proper order (run in separate terminals)
	@echo "Starting all agents requires separate terminals:"
	@echo ""
	@echo "  Terminal 1: make supplier"
	@echo "  Terminal 2: make chef"
	@echo "  Terminal 3: make waiter"
	@echo ""
	@echo "Or run automated test: make test"
