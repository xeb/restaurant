#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["flask", "google-adk[a2a]", "markdown"]
# ///

import argparse
import asyncio
import json
import logging
import os
import sys
import warnings
from flask import Flask, render_template_string, request, jsonify
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.genai.types import Part, UserContent
import threading
import uuid
from datetime import datetime
import concurrent.futures
import markdown

# Suppress warnings
warnings.filterwarnings("ignore", message=".*auth_config or auth_config.auth_scheme is missing.*")
warnings.filterwarnings("ignore", message=".*BaseAuthenticatedTool.*")
warnings.filterwarnings("ignore", message=".*there are non-text parts in the response.*")
warnings.filterwarnings("ignore", message=".*EXPERIMENTAL.*")

logging.getLogger('google.adk.tools').setLevel(logging.ERROR)
logging.getLogger('google.adk').setLevel(logging.ERROR)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Global storage
sessions = {}
agent_module = None
agent_name = ""
agent_port = 0

# HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Restaurant - {{ agent_name }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        body { font-family: 'Inter', sans-serif; background-color: white; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #f9fafb; }
        ::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #9ca3af; }
        .chat-message { margin-bottom: 1rem; padding: 1rem; border-radius: 0.5rem; font-size: 0.875rem; }
        .user-message { background-color: #f3f4f6; margin-left: 2rem; }
        .agent-message { background-color: #f0f9ff; margin-right: 2rem; }
        .tool-message { background-color: #fdf2f8; margin-right: 2rem; border-left: 4px solid #ec4899; }
        .a2a-message { background-color: #fef3c7; margin-right: 2rem; border-left: 4px solid #f59e0b; }
        .banner-gradient { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    </style>
</head>
<body class="bg-white text-gray-800 antialiased">
    <div class="flex flex-col h-screen">
        <header class="banner-gradient text-white border-b border-gray-200">
            <div class="px-8 py-6">
                <h1 class="text-4xl font-bold tracking-tight">🍽️ Restaurant - {{ agent_name }}</h1>
                <p class="text-sm opacity-90 mt-1">Multi-Agent System on port {{ agent_port }}</p>
            </div>
        </header>

        <div class="flex-1 flex overflow-hidden bg-white">
            <main class="flex-1 p-6 overflow-hidden">
                <div class="h-full flex gap-6 max-w-7xl mx-auto">
                    <!-- Left: Chat -->
                    <div class="flex-1 bg-white rounded-lg border border-gray-200 shadow-sm flex flex-col h-full">
                        <div class="flex items-center justify-between p-4 border-b border-gray-200">
                            <h2 class="text-lg font-semibold">Chat with {{ agent_name }}</h2>
                            <button class="text-gray-500 hover:text-gray-700 p-2 rounded-full hover:bg-gray-100" onclick="clearChat()" title="Clear Chat">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                            </button>
                        </div>

                        <div id="chatContainer" class="p-6 flex-1 overflow-y-auto"></div>

                        <div class="p-6 flex-shrink-0">
                            <div class="relative">
                                <textarea id="userInput" rows="3" class="w-full p-4 pr-16 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 resize-none" placeholder="Send message..." onkeypress="handleKeyPress(event)"></textarea>
                                <button onclick="sendMessage()" class="absolute top-1/2 right-4 -translate-y-1/2 p-2 rounded-full bg-gray-200 hover:bg-gray-300">
                                   <svg class="w-6 h-6 text-gray-600" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
                                   </svg>
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Right: Sessions List -->
                    <div class="w-1/3 bg-white rounded-lg border border-gray-200 flex flex-col h-full">
                        <div class="p-4 border-b border-gray-200">
                            <h3 class="text-lg font-semibold">Active Sessions</h3>
                        </div>
                        <div id="sessionsList" class="flex-1 p-6 overflow-y-auto">
                            <div id="sessionsPlaceholder" class="text-center text-gray-500 mt-8">
                                <svg class="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
                                </svg>
                                <p class="text-sm">No active sessions</p>
                                <p class="text-xs text-gray-400 mt-1">Start chatting to create a session</p>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    </div>

    <script>
        let sessionId = localStorage.getItem('sessionId') || generateSessionId();

        function generateSessionId() {
            const id = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('sessionId', id);
            return id;
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }

        function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            if (!message) return;

            input.value = '';
            addMessage('user', message);

            fetch('/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message, session_id: sessionId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    addMessage('system', 'Error: ' + data.error);
                    return;
                }

                // Add tool calls
                if (data.tool_calls && data.tool_calls.length > 0) {
                    data.tool_calls.forEach(toolCall => {
                        addToolMessage(toolCall.name, toolCall.arguments, toolCall.result);
                    });
                }

                // Add A2A calls
                if (data.a2a_calls && data.a2a_calls.length > 0) {
                    data.a2a_calls.forEach(a2aCall => {
                        addA2AMessage(a2aCall);
                    });
                }

                // Add response
                if (data.response) {
                    addMessage('agent', data.response);
                }

                refreshSessions();
            })
            .catch(error => {
                addMessage('system', 'Connection error: ' + error.message);
            });
        }

        function addMessage(type, content) {
            const container = document.getElementById('chatContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${type}-message`;

            const label = type === 'user' ? 'You' : type === 'agent' ? '{{ agent_name }}' : 'System';
            let formattedContent = type === 'agent' ? marked.parse(content) : content;

            messageDiv.innerHTML = `
                <div class="font-medium mb-2">${label}</div>
                <div class="whitespace-pre-wrap">${formattedContent}</div>
                <div class="text-xs text-gray-500 mt-2">${new Date().toLocaleTimeString()}</div>
            `;

            container.appendChild(messageDiv);
            container.scrollTop = container.scrollHeight;
        }

        function addToolMessage(name, args, result) {
            const container = document.getElementById('chatContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'chat-message tool-message';

            const argsStr = JSON.stringify(args, null, 2);
            const resultStr = JSON.stringify(result, null, 2);
            const toolId = `tool-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

            messageDiv.innerHTML = `
                <div class="font-medium mb-2">
                    <button onclick="toggleToolDetails('${toolId}')" class="flex items-center space-x-2 text-left w-full hover:text-pink-700">
                        <span>🔧 Tool Call: ${name}</span>
                        <svg id="${toolId}-arrow" class="w-4 h-4 transform transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                        </svg>
                    </button>
                </div>
                <div id="${toolId}-details" class="hidden space-y-2">
                    <div>
                        <div class="font-medium text-sm text-gray-700">Arguments:</div>
                        <div class="text-xs bg-gray-100 p-2 rounded max-h-32 overflow-y-auto whitespace-pre-wrap font-mono">${argsStr}</div>
                    </div>
                    <div>
                        <div class="font-medium text-sm text-gray-700">Result:</div>
                        <div class="text-xs bg-gray-100 p-2 rounded max-h-48 overflow-y-auto whitespace-pre-wrap font-mono">${resultStr}</div>
                    </div>
                </div>
                <div class="text-xs text-gray-500 mt-2">${new Date().toLocaleTimeString()}</div>
            `;

            container.appendChild(messageDiv);
            container.scrollTop = container.scrollHeight;
        }

        function addA2AMessage(call) {
            const container = document.getElementById('chatContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'chat-message a2a-message';

            const a2aId = `a2a-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

            messageDiv.innerHTML = `
                <div class="font-medium mb-2">
                    <button onclick="toggleToolDetails('${a2aId}')" class="flex items-center space-x-2 text-left w-full hover:text-yellow-700">
                        <span>🔄 A2A Call: ${call.target_agent}</span>
                        <svg id="${a2aId}-arrow" class="w-4 h-4 transform transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                        </svg>
                    </button>
                </div>
                <div id="${a2aId}-details" class="hidden space-y-2">
                    <div>
                        <div class="font-medium text-sm text-gray-700">Request:</div>
                        <div class="text-xs bg-gray-100 p-2 rounded max-h-32 overflow-y-auto whitespace-pre-wrap font-mono">${call.request}</div>
                    </div>
                    <div>
                        <div class="font-medium text-sm text-gray-700">Response:</div>
                        <div class="text-xs bg-gray-100 p-2 rounded max-h-48 overflow-y-auto whitespace-pre-wrap font-mono">${call.response || 'Processing...'}</div>
                    </div>
                </div>
                <div class="text-xs text-gray-500 mt-2">${new Date().toLocaleTimeString()}</div>
            `;

            container.appendChild(messageDiv);
            container.scrollTop = container.scrollHeight;
        }

        function toggleToolDetails(id) {
            const details = document.getElementById(`${id}-details`);
            const arrow = document.getElementById(`${id}-arrow`);
            if (details.classList.contains('hidden')) {
                details.classList.remove('hidden');
                arrow.classList.add('rotate-180');
            } else {
                details.classList.add('hidden');
                arrow.classList.remove('rotate-180');
            }
        }

        function clearChat() {
            document.getElementById('chatContainer').innerHTML = '';
            sessionId = generateSessionId();
            fetch('/clear', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            });
        }

        function refreshSessions() {
            fetch('/sessions')
            .then(response => response.json())
            .then(data => {
                displaySessions(data.sessions || []);
            });
        }

        function displaySessions(sessions) {
            const container = document.getElementById('sessionsList');
            const placeholder = document.getElementById('sessionsPlaceholder');

            if (sessions.length === 0) {
                if (placeholder) placeholder.style.display = 'block';
                return;
            }

            if (placeholder) placeholder.style.display = 'none';

            const sessionsList = sessions.map(session => {
                const isActive = session.id === sessionId;
                return `
                    <div class="border ${isActive ? 'border-blue-500 bg-blue-50' : 'border-gray-200'} rounded-lg p-3 mb-2">
                        <div class="flex items-start justify-between">
                            <div class="flex-1">
                                <h4 class="font-medium text-gray-900 text-sm">${session.id.substring(0, 20)}...</h4>
                                <p class="text-xs text-gray-500 mt-1">${session.message_count} messages</p>
                                <p class="text-xs text-gray-400">${new Date(session.created_at).toLocaleString()}</p>
                            </div>
                            ${isActive ? '<span class="text-xs font-semibold text-blue-600">ACTIVE</span>' : ''}
                        </div>
                    </div>
                `;
            }).join('');

            container.innerHTML = `
                <div class="space-y-2">
                    <h3 class="text-sm font-semibold text-gray-700 mb-4">Sessions (${sessions.length})</h3>
                    ${sessionsList}
                </div>
            `;
        }

        window.onload = function() {
            document.getElementById('userInput').focus();
            refreshSessions();

            fetch('/history', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.history) {
                    data.history.forEach(entry => {
                        if (entry.type === 'user') {
                            addMessage('user', entry.content);
                        } else if (entry.type === 'agent') {
                            if (entry.tool_calls) {
                                entry.tool_calls.forEach(tc => addToolMessage(tc.name, tc.arguments, tc.result));
                            }
                            if (entry.a2a_calls) {
                                entry.a2a_calls.forEach(ac => addA2AMessage(ac));
                            }
                            addMessage('agent', entry.content);
                        }
                    });
                }
            });
        };

        setInterval(refreshSessions, 5000);
    </script>
</body>
</html>
'''

def run_agent_async(agent, runner, session, message):
    """Run the agent and extract events."""
    try:
        content = UserContent(parts=[Part(text=message)])

        events = []
        for event in runner.run(
            user_id=session.user_id,
            session_id=session.id,
            new_message=content
        ):
            events.append(event)

        response_text = ""
        tool_calls = []
        a2a_calls = []

        for event in events:
            # Extract text
            if hasattr(event, 'content') and hasattr(event.content, 'parts'):
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text

                    # Extract function calls (tools)
                    if hasattr(part, 'function_call') and part.function_call:
                        func_call = part.function_call
                        tool_name = getattr(func_call, 'name', 'unknown')

                        # Detect A2A calls (agent tools)
                        if 'agent' in tool_name.lower():
                            a2a_calls.append({
                                'target_agent': tool_name,
                                'request': str(getattr(func_call, 'args', {})),
                                'response': None,
                                'id': getattr(func_call, 'id', '')
                            })
                        else:
                            tool_calls.append({
                                'name': tool_name,
                                'arguments': getattr(func_call, 'args', {}),
                                'result': None,
                                'id': getattr(func_call, 'id', '')
                            })

                    # Extract function responses
                    if hasattr(part, 'function_response') and part.function_response:
                        func_response = part.function_response
                        response_name = getattr(func_response, 'name', '')
                        response_id = getattr(func_response, 'id', '')
                        response_data = getattr(func_response, 'response', {})

                        # Match to A2A call
                        for ac in a2a_calls:
                            if ac['response'] is None and (ac['target_agent'] == response_name or ac['id'] == response_id):
                                ac['response'] = str(response_data)
                                break

                        # Match to tool call
                        for tc in tool_calls:
                            if tc['result'] is None and (tc['name'] == response_name or tc['id'] == response_id):
                                tc['result'] = response_data
                                break

        return {
            'response': response_text.strip(),
            'tool_calls': tool_calls,
            'a2a_calls': a2a_calls
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'error': str(e)}

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, agent_name=agent_name, agent_port=agent_port)

@app.route('/send', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        session_id = data.get('session_id', '')

        if not message:
            return jsonify({'error': 'Empty message'})

        if session_id not in sessions:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            session_service = InMemorySessionService()
            artifact_service = InMemoryArtifactService()

            runner = Runner(
                app_name=f"restaurant-{agent_name}",
                agent=agent_module.root_agent,
                artifact_service=artifact_service,
                session_service=session_service
            )

            session = loop.run_until_complete(
                session_service.create_session(
                    app_name=runner.app_name,
                    user_id="user"
                )
            )

            sessions[session_id] = {
                'session': session,
                'runner': runner,
                'loop': loop,
                'history': [],
                'created_at': datetime.now().isoformat()
            }

        session_data = sessions[session_id]
        session = session_data['session']
        runner = session_data['runner']

        session_data['history'].append({
            'type': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_agent_async, agent_module.root_agent, runner, session, message)
            result = future.result(timeout=120)

        if 'error' in result:
            return jsonify(result)

        agent_entry = {
            'type': 'agent',
            'content': result.get('response', ''),
            'timestamp': datetime.now().isoformat()
        }

        if result.get('tool_calls'):
            agent_entry['tool_calls'] = result['tool_calls']

        if result.get('a2a_calls'):
            agent_entry['a2a_calls'] = result['a2a_calls']

        session_data['history'].append(agent_entry)

        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)})

@app.route('/history', methods=['POST'])
def get_history():
    try:
        data = request.get_json()
        session_id = data.get('session_id', '')

        if session_id in sessions:
            return jsonify({'history': sessions[session_id]['history']})
        else:
            return jsonify({'history': []})

    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/clear', methods=['POST'])
def clear_session():
    try:
        data = request.get_json()
        session_id = data.get('session_id', '')

        if session_id in sessions:
            session_data = sessions[session_id]
            if session_data.get('loop'):
                try:
                    session_data['loop'].close()
                except:
                    pass
            del sessions[session_id]

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/sessions')
def get_sessions():
    try:
        session_list = []
        for sid, sdata in sessions.items():
            session_list.append({
                'id': sid,
                'created_at': sdata.get('created_at', datetime.now().isoformat()),
                'message_count': len(sdata.get('history', []))
            })

        session_list.sort(key=lambda x: x['created_at'], reverse=True)
        return jsonify({'sessions': session_list})

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Restaurant Multi-Agent Web Interface')
    parser.add_argument('--agent', type=str, required=True,
                       choices=['waiter', 'chef', 'supplier'],
                       help='Which agent to run (waiter, chef, or supplier)')
    parser.add_argument('--port', type=int, help='Port to run on (auto-assigned if not specified)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')

    args = parser.parse_args()

    # Import the appropriate agent module
    import importlib.util

    if args.agent == 'waiter':
        agent_file = os.path.join(os.path.dirname(__file__), 'waiter_standalone.py')
    else:
        agent_dir = os.path.join(os.path.dirname(__file__), args.agent)
        agent_file = os.path.join(agent_dir, 'agent.py')

    spec = importlib.util.spec_from_file_location(f"{args.agent}_agent", agent_file)
    agent_module = importlib.util.module_from_spec(spec)
    sys.modules[f"{args.agent}_agent"] = agent_module

    # Change to appropriate directory for relative imports
    original_dir = os.getcwd()
    if args.agent != 'waiter':
        os.chdir(os.path.join(os.path.dirname(__file__), args.agent))

    try:
        spec.loader.exec_module(agent_module)
    finally:
        os.chdir(original_dir)

    agent_name = args.agent.capitalize()
    default_port = {'waiter': 5001, 'chef': 5002, 'supplier': 5003}[args.agent]
    agent_port = args.port or default_port

    print(f"Starting {agent_name} agent web interface on {args.host}:{agent_port}")
    app.run(host=args.host, port=agent_port, debug=args.debug)
