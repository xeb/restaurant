#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-adk[a2a]",
#     "simple-term-menu",
#     "colorama",
#     "rich",
# ]
# ///
"""Interactive CLI for Restaurant Multi-Agent System.

Allows user to select which agent to chat with and provides a colored REPL interface.
"""

import sys
import warnings
import requests
import asyncio
import logging
from simple_term_menu import TerminalMenu
from colorama import Fore, Style, init
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
import json

# Suppress experimental warnings from Google ADK
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message="Deprecated. Please migrate to the async method.")
warnings.filterwarnings("ignore", message=".*there are non-text parts in the response.*")

# Suppress logger warnings from google.genai and google.adk
logging.getLogger('google.genai.types').setLevel(logging.ERROR)
logging.getLogger('google.adk').setLevel(logging.ERROR)
logging.getLogger('google.adk.tools').setLevel(logging.ERROR)
logging.getLogger('google.adk.sessions').setLevel(logging.ERROR)

from google.adk import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai.types import Part, UserContent

# Initialize colorama
init(autoreset=True)
console = Console()

AGENTS = {
    "waiter": {
        "name": "Waiter",
        "port": 8001,
        "color": Fore.CYAN,
        "rich_color": "cyan",
        "agent_card": "http://localhost:8001/.well-known/agent-card.json",
    },
    "chef": {
        "name": "Chef",
        "port": 8002,
        "color": Fore.YELLOW,
        "rich_color": "yellow",
        "agent_card": "http://localhost:8002/.well-known/agent-card.json",
    },
    "supplier": {
        "name": "Supplier",
        "port": 8003,
        "color": Fore.GREEN,
        "rich_color": "green",
        "agent_card": "http://localhost:8003/.well-known/agent-card.json",
    },
}


def check_agent_status(agent_key):
    """Check if an agent is running."""
    agent = AGENTS[agent_key]
    try:
        response = requests.get(agent["agent_card"], timeout=2)
        return response.status_code == 200
    except:
        return False


def show_status():
    """Display status of all agents."""
    console.print("\n[bold]Agent Status:[/bold]")
    console.print("=" * 40)

    all_running = True
    for key, agent in AGENTS.items():
        status = check_agent_status(key)
        status_icon = "✅" if status else "❌"
        status_text = "Running" if status else "Not running"
        color = "green" if status else "red"
        console.print(f"  {agent['name']:10} (port {agent['port']}): [{color}]{status_icon} {status_text}[/{color}]")
        if not status:
            all_running = False

    console.print("=" * 40 + "\n")
    return all_running


def select_agent():
    """Show menu to select an agent."""
    console.print("\n[bold cyan]🍽️  Restaurant Multi-Agent CLI[/bold cyan]\n")

    # Check status first
    all_running = show_status()

    # Get list of running agents
    running_agents = []
    for key in AGENTS.keys():
        if check_agent_status(key):
            running_agents.append(key)

    if not running_agents:
        console.print("[bold red]⚠️  No agents are running![/bold red]")
        console.print("\nStart at least one agent:")
        console.print("  [cyan]make supplier-cli[/cyan]  # Terminal 1")
        console.print("  [cyan]make chef-cli[/cyan]      # Terminal 2")
        console.print("  [cyan]make waiter-cli[/cyan]    # Terminal 3")
        console.print("\nThen run: [cyan]make cli[/cyan]\n")
        return None

    if not all_running:
        console.print("[yellow]ℹ️  Some agents are not running. Only running agents are available for chat.[/yellow]\n")

    # Build menu options - only show running agents
    menu_items = []
    available_keys = []
    for key, agent in AGENTS.items():
        if key in running_agents:
            menu_items.append(f"{agent['name']} (port {agent['port']})")
            available_keys.append(key)
    menu_items.append("Exit")

    console.print("[bold]Select an agent to chat with:[/bold]")
    terminal_menu = TerminalMenu(menu_items, title="")
    menu_index = terminal_menu.show()

    if menu_index is None or menu_index == len(menu_items) - 1:
        return None

    # Return the agent key
    return available_keys[menu_index]


def print_tool_call(tool_name, args, result=None):
    """Print a tool call with colored formatting."""
    console.print()
    if result is None:
        # Tool call start
        console.print(f"[bold magenta]🔧 Tool Call:[/bold magenta] {tool_name}")
        if args:
            console.print(Panel(
                Syntax(json.dumps(args, indent=2), "json", theme="monokai"),
                title="Arguments",
                border_style="magenta"
            ))
    else:
        # Tool result
        console.print(f"[bold green]✓ Tool Result:[/bold green] {tool_name}")
        if result:
            result_str = str(result)
            if len(result_str) > 500:
                result_str = result_str[:500] + "..."
            console.print(Panel(
                result_str,
                title="Result",
                border_style="green"
            ))


def run_repl(agent_key):
    """Run the REPL for the selected agent."""
    agent_config = AGENTS[agent_key]
    color = agent_config["color"]
    rich_color = agent_config["rich_color"]
    name = agent_config["name"]

    console.print(f"\n[bold {rich_color}]🤖 Connected to {name} Agent[/bold {rich_color}]")
    console.print(f"[dim]Type your message or 'exit' to quit[/dim]\n")

    # Connect to the remote agent and wrap it as a tool
    try:
        remote_agent = RemoteA2aAgent(
            name=f"{agent_key}_agent",
            agent_card=agent_config["agent_card"]
        )

        # Wrap the remote agent as a tool
        agent_tool = AgentTool(agent=remote_agent)

        # Create a simple Agent that uses the remote agent as its only tool
        # This allows us to chat "with" the remote agent by having a pass-through
        wrapper_agent = Agent(
            name=f"{agent_key}_wrapper",
            model="gemini-2.5-flash",
            description=f"Direct pass-through to {name} agent",
            instruction=f"""You are a pass-through agent that ALWAYS calls the {agent_key}_agent tool with the user's message.

IMPORTANT: For EVERY user message, immediately call the {agent_key}_agent tool with that exact message.
Do not add any commentary or explanation. Just relay the tool's response directly.""",
            tools=[agent_tool]
        )

    except Exception as e:
        console.print(f"[bold red]Error connecting to {name}: {e}[/bold red]")
        return

    # Create runner with the wrapper agent
    session_service = InMemorySessionService()
    runner = Runner(
        agent=wrapper_agent,
        session_service=session_service,
        app_name=f"restaurant_cli_{agent_key}"
    )

    # Session identifiers
    user_id = "cli_user"
    session_id = f"cli_session_{agent_key}"

    async def chat_loop():
        """Async chat loop to properly handle event loop."""
        # Create the session explicitly before using it
        session_service.create_session_sync(
            app_name=f"restaurant_cli_{agent_key}",
            user_id=user_id,
            session_id=session_id
        )

        while True:
            try:
                # Get user input with colored prompt
                user_input = input(f"{color}{name.lower()}> {Style.RESET_ALL}").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['exit', 'quit', 'q']:
                    console.print(f"\n[dim]Goodbye from {name}![/dim]\n")
                    break

                # Send message to agent
                console.print()
                with console.status(f"[bold cyan]Thinking...[/bold cyan]", spinner="dots"):
                    content = UserContent([Part(text=user_input)])
                    events = []
                    async for event in runner.run_async(
                        user_id=user_id,
                        session_id=session_id,
                        new_message=content
                    ):
                        events.append(event)

                # Process events
                tool_calls = {}
                response_text = ""

                for event in events:
                    if hasattr(event, 'content') and event.content:
                        for part in event.content.parts:
                            # Handle function calls
                            if hasattr(part, 'function_call') and part.function_call:
                                func_call = part.function_call
                                call_id = getattr(func_call, 'id', '')
                                tool_name = getattr(func_call, 'name', 'unknown')
                                args = getattr(func_call, 'args', {})

                                tool_calls[call_id] = {
                                    'name': tool_name,
                                    'args': args
                                }
                                print_tool_call(tool_name, args)

                            # Handle function responses
                            if hasattr(part, 'function_response') and part.function_response:
                                func_response = part.function_response
                                call_id = getattr(func_response, 'id', '')
                                result = getattr(func_response, 'response', {})

                                if call_id in tool_calls:
                                    tool_name = tool_calls[call_id]['name']
                                    print_tool_call(tool_name, None, result)

                            # Handle text responses
                            if hasattr(part, 'text') and part.text:
                                response_text += part.text

                # Display final response
                if response_text:
                    console.print()
                    console.print(Panel(
                        Markdown(response_text),
                        title=f"{name} Response",
                        border_style=rich_color,
                        padding=(1, 2)
                    ))
                    console.print()

            except KeyboardInterrupt:
                console.print(f"\n\n[dim]Goodbye from {name}![/dim]\n")
                break
            except Exception as e:
                console.print(f"\n[bold red]Error: {e}[/bold red]\n")

    # Run the async chat loop
    asyncio.run(chat_loop())


def main():
    """Main entry point."""
    agent_key = select_agent()

    if agent_key:
        run_repl(agent_key)
    else:
        console.print("[dim]Exiting...[/dim]\n")


if __name__ == "__main__":
    main()
