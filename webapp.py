#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["flask", "google-adk[a2a]", "markdown", "uvicorn"]
# ///

import argparse
import asyncio
import json
import logging
import os
import sys
import warnings
from pathlib import Path
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
from a2a_logging import log_a2a_traffic

# Suppress warnings
warnings.filterwarnings("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

# Suppress all Google ADK logging except critical errors
logging.getLogger('google').setLevel(logging.CRITICAL)
logging.getLogger('google.adk').setLevel(logging.CRITICAL)
logging.getLogger('google.adk.tools').setLevel(logging.CRITICAL)
logging.getLogger('google.genai').setLevel(logging.CRITICAL)
logging.getLogger('werkzeug').setLevel(logging.WARNING)  # Flask's logger

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Global storage
sessions = {}
agent_module = None
agent_name = ""
agent_port = 0
agent_type = ""  # waiter, chef, or supplier
agent_emoji = ""  # emoji for the agent

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
        .dropdown { position: relative; display: inline-block; }
        .dropdown-content { display: none; position: absolute; right: 0; background-color: white; min-width: 200px; box-shadow: 0px 8px 16px rgba(0,0,0,0.1); z-index: 1000; border-radius: 0.5rem; margin-top: 0.125rem; padding-top: 0.25rem; }
        .dropdown:hover .dropdown-content { display: block; }
        .dropdown-content a { color: #374151; padding: 12px 16px; text-decoration: none; display: block; transition: background 0.2s; }
        .dropdown-content a:hover { background-color: #f3f4f6; }
    </style>
</head>
<body class="bg-white text-gray-800 antialiased">
    <div class="flex flex-col h-screen">
        <header class="banner-gradient text-white border-b border-gray-200">
            <div class="px-8 py-4 flex justify-between items-center">
                <div>
                    <h1 class="text-4xl font-bold tracking-tight">{{ agent_emoji }} Restaurant - {{ agent_name }}</h1>
                    <p class="text-sm opacity-90 mt-1">Multi-Agent System on port {{ agent_port }}</p>
                </div>
                <div class="flex items-center space-x-4">
                    <!-- Agents Menu -->
                    <div class="dropdown">
                        <button class="bg-white bg-opacity-20 hover:bg-opacity-30 px-4 py-2 rounded-lg font-medium transition-all">
                            Agents ▾
                        </button>
                        <div class="dropdown-content">
                            <a href="https://waiter.xeb.ai" target="_blank">Waiter</a>
                            <a href="https://chef.xeb.ai" target="_blank">Chef</a>
                            <a href="https://supplier.xeb.ai" target="_blank">Supplier</a>
                        </div>
                    </div>

                    <!-- Data Menu -->
                    <div class="dropdown">
                        <button class="bg-white bg-opacity-20 hover:bg-opacity-30 px-4 py-2 rounded-lg font-medium transition-all">
                            Data ▾
                        </button>
                        <div class="dropdown-content">
                            <a href="/data/menu.json" target="_blank">Menu</a>
                            <a href="/data/food.json" target="_blank">Food Database</a>
                            <a href="/data/pantry.json" target="_blank">Pantry Inventory</a>
                            <a href="/data/pantry-normalized" target="_blank">Pantry (Normalized)</a>
                            <a href="/data/orders.json" target="_blank">Waiter Orders</a>
                            <a href="/data/chef_orders.json" target="_blank">Chef Orders</a>
                        </div>
                    </div>

                    <!-- A2A Menu -->
                    <div class="dropdown">
                        <button class="bg-white bg-opacity-20 hover:bg-opacity-30 px-4 py-2 rounded-lg font-medium transition-all">
                            A2A ▾
                        </button>
                        <div class="dropdown-content">
                            <a href="/a2a/architecture" target="_blank">View Architecture</a>
                            <a href="/a2a/logs/waiter" target="_blank">View Waiter Logs</a>
                            <a href="/a2a/logs/chef" target="_blank">View Chef Logs</a>
                            <a href="/a2a/logs/supplier" target="_blank">View Supplier Logs</a>
                        </div>
                    </div>
                </div>
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
                        <div class="p-4 border-b border-gray-200 flex justify-between items-center">
                            <h3 class="text-lg font-semibold">Active Sessions</h3>
                            <button onclick="createNewSession()" class="bg-blue-500 hover:bg-blue-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-xl font-bold" title="Create New Session">
                                +
                            </button>
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
        let thinkingBubbleId = null;

        function generateSessionId() {
            const id = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('sessionId', id);
            return id;
        }

        function formatDuration(milliseconds) {
            const seconds = Math.floor(milliseconds / 1000);
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;

            if (minutes === 0) {
                return `${remainingSeconds} sec`;
            } else {
                return `${minutes} min, ${remainingSeconds} sec`;
            }
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }

        function showThinkingIndicator() {
            const container = document.getElementById('chatContainer');
            const thinkingDiv = document.createElement('div');
            thinkingBubbleId = 'thinking-' + Date.now();
            thinkingDiv.id = thinkingBubbleId;
            thinkingDiv.className = 'chat-message agent-message';
            thinkingDiv.innerHTML = `
                <div class="font-medium mb-2">{{ agent_name }}</div>
                <div class="flex items-center space-x-2">
                    <div class="animate-pulse">💭</div>
                    <div class="text-gray-500 italic">Thinking...</div>
                </div>
            `;
            container.appendChild(thinkingDiv);
            container.scrollTop = container.scrollHeight;
            return thinkingBubbleId;
        }

        function removeThinkingIndicator(bubbleId) {
            if (bubbleId) {
                const bubble = document.getElementById(bubbleId);
                if (bubble) bubble.remove();
            }
        }

        function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            if (!message) return;

            input.value = '';
            addMessage('user', message);

            const thinkingId = showThinkingIndicator();
            const startTime = Date.now();

            fetch('/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message, session_id: sessionId })
            })
            .then(response => response.json())
            .then(data => {
                const duration = Date.now() - startTime;
                removeThinkingIndicator(thinkingId);

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

                // Add response with duration
                if (data.response) {
                    addMessage('agent', data.response, duration);
                }

                refreshSessions();
            })
            .catch(error => {
                removeThinkingIndicator(thinkingId);
                addMessage('system', 'Connection error: ' + error.message);
            });
        }

        function addMessage(type, content, duration) {
            const container = document.getElementById('chatContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${type}-message`;

            const label = type === 'user' ? 'You' : type === 'agent' ? '{{ agent_name }}' : 'System';
            let formattedContent = type === 'agent' ? marked.parse(content) : content;

            // Build footer with time and optional duration
            let footer = new Date().toLocaleTimeString();
            if (type === 'agent' && duration !== undefined) {
                footer += ` • Duration: ${formatDuration(duration)}`;
            }

            messageDiv.innerHTML = `
                <div class="font-medium mb-2">${label}</div>
                <div class="whitespace-pre-wrap">${formattedContent}</div>
                <div class="text-xs text-gray-500 mt-2">${footer}</div>
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

        function createNewSession() {
            document.getElementById('chatContainer').innerHTML = '';
            sessionId = generateSessionId();
            refreshSessions();
            document.getElementById('userInput').focus();
        }

        function refreshSessions() {
            fetch('/sessions')
            .then(response => response.json())
            .then(data => {
                displaySessions(data.sessions || []);
            });
        }

        function loadSession(sid) {
            // Clear current chat
            document.getElementById('chatContainer').innerHTML = '';

            // Update active session
            sessionId = sid;
            localStorage.setItem('sessionId', sid);

            // Load history for this session
            fetch('/history', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sid })
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
                refreshSessions();
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
                    <div onclick="loadSession('${session.id}')" class="border ${isActive ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-400 cursor-pointer'} rounded-lg p-3 mb-2 transition-colors">
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

def serialize_response_data(data):
    """Convert complex response objects to JSON-serializable format."""
    if data is None:
        return None

    # If it's already a simple type, return as-is
    if isinstance(data, (str, int, float, bool)):
        return data

    # If it's a dict, recursively serialize
    if isinstance(data, dict):
        return {k: serialize_response_data(v) for k, v in data.items()}

    # If it's a list, recursively serialize
    if isinstance(data, (list, tuple)):
        return [serialize_response_data(item) for item in data]

    # For complex objects, try to extract data or convert to string
    if hasattr(data, '__dict__'):
        try:
            return serialize_response_data(data.__dict__)
        except:
            return str(data)

    # Fallback to string representation
    return str(data)

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
                                'arguments': serialize_response_data(getattr(func_call, 'args', {})),
                                'result': None,
                                'id': getattr(func_call, 'id', '')
                            })

                    # Extract function responses
                    if hasattr(part, 'function_response') and part.function_response:
                        func_response = part.function_response
                        response_name = getattr(func_response, 'name', '')
                        response_id = getattr(func_response, 'id', '')
                        response_data = getattr(func_response, 'response', {})

                        # Serialize the response data
                        serialized_data = serialize_response_data(response_data)

                        # Match to A2A call
                        for ac in a2a_calls:
                            if ac['response'] is None and (ac['target_agent'] == response_name or ac['id'] == response_id):
                                ac['response'] = str(serialized_data)
                                break

                        # Match to tool call
                        for tc in tool_calls:
                            if tc['result'] is None and (tc['name'] == response_name or tc['id'] == response_id):
                                tc['result'] = serialized_data
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

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE, agent_name=agent_name, agent_port=agent_port, agent_emoji=agent_emoji)

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

@app.route('/data/<filename>')
def serve_json_data(filename):
    """Serve JSON data files with formatted display."""
    try:
        # Security: only allow specific JSON files
        allowed_files = ['menu.json', 'food.json', 'pantry.json', 'orders.json', 'chef_orders.json']

        if filename not in allowed_files:
            return f"<html><body><h1>Error</h1><p>File '{filename}' not allowed</p></body></html>", 403

        # Try to read the JSON file
        if not os.path.exists(filename):
            return f"""
            <html>
            <head>
                <title>{filename}</title>
                <style>
                    body {{ font-family: 'Inter', sans-serif; margin: 40px; background: #f9fafb; }}
                    .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
                    h1 {{ color: #374151; }}
                    .warning {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px; border-radius: 4px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>{filename}</h1>
                    <div class="warning">
                        <strong>File not found</strong><br>
                        The file <code>{filename}</code> does not exist yet. It will be created once the system generates data.
                    </div>
                </div>
            </body>
            </html>
            """, 404

        with open(filename, 'r') as f:
            json_data = json.load(f)

        # Format JSON for display
        formatted_json = json.dumps(json_data, indent=2)

        # Return HTML page with formatted JSON
        html = f"""
        <html>
        <head>
            <title>{filename}</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
            <style>
                body {{
                    font-family: 'Inter', sans-serif;
                    margin: 40px;
                    background: #f9fafb;
                }}
                .container {{
                    max-width: 900px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #374151;
                    margin-bottom: 20px;
                }}
                .json-display {{
                    background: #1f2937;
                    color: #f3f4f6;
                    padding: 20px;
                    border-radius: 6px;
                    overflow-x: auto;
                    font-family: 'Monaco', 'Courier New', monospace;
                    font-size: 14px;
                    line-height: 1.5;
                    white-space: pre;
                }}
                .back-link {{
                    display: inline-block;
                    margin-bottom: 20px;
                    color: #667eea;
                    text-decoration: none;
                    font-weight: 500;
                }}
                .back-link:hover {{
                    text-decoration: underline;
                }}
                .meta {{
                    color: #6b7280;
                    font-size: 14px;
                    margin-bottom: 16px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <a href="javascript:history.back()" class="back-link">← Back</a>
                <h1>{filename}</h1>
                <div class="meta">
                    Last modified: {datetime.fromtimestamp(os.path.getmtime(filename)).strftime('%Y-%m-%d %H:%M:%S')}
                </div>
                <div class="json-display">{formatted_json}</div>
            </div>
        </body>
        </html>
        """

        return html

    except json.JSONDecodeError as e:
        return f"""
        <html>
        <body>
            <h1>Error</h1>
            <p>Failed to parse {filename} as JSON: {str(e)}</p>
        </body>
        </html>
        """, 500
    except Exception as e:
        return f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>", 500

@app.route('/data/pantry-normalized')
def serve_normalized_pantry():
    """Serve normalized pantry view - merges pantry.json and food.json."""
    try:
        # Load food database
        food_data = {}
        if os.path.exists('food.json'):
            with open('food.json', 'r') as f:
                food_json = json.load(f)
                food_data = food_json.get('foods', {})

        # Load pantry inventory
        pantry_data = {}
        if os.path.exists('pantry.json'):
            with open('pantry.json', 'r') as f:
                pantry_data = json.load(f)

        # Merge the data
        merged_items = []

        # Get all food IDs from both sources
        all_food_ids = set(food_data.keys()) | set(pantry_data.keys())

        for food_id in sorted(all_food_ids, key=lambda x: int(x)):
            food_info = food_data.get(food_id, {})
            food_name = food_info.get('name', f'Unknown (ID {food_id})')
            quantity = pantry_data.get(food_id, 0)

            merged_items.append({
                'id': int(food_id),
                'name': food_name,
                'quantity': quantity
            })

        # Generate HTML table rows
        table_rows = ''
        for item in merged_items:
            # Color code based on quantity
            if item['quantity'] == 0:
                row_class = 'bg-red-50'
                quantity_class = 'text-red-700 font-bold'
            elif item['quantity'] <= 3:
                row_class = 'bg-yellow-50'
                quantity_class = 'text-yellow-700 font-semibold'
            else:
                row_class = ''
                quantity_class = 'text-gray-900'

            table_rows += f'''
                <tr class="{row_class}">
                    <td class="px-4 py-2 text-sm text-gray-700">{item['id']}</td>
                    <td class="px-4 py-2 text-sm text-gray-900 font-medium">{item['name']}</td>
                    <td class="px-4 py-2 text-sm {quantity_class} text-right">{item['quantity']}</td>
                </tr>
            '''

        # Return HTML page
        html = f'''
        <html>
        <head>
            <title>Pantry (Normalized)</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                body {{
                    font-family: 'Inter', sans-serif;
                    background: #f9fafb;
                }}
            </style>
        </head>
        <body class="p-8">
            <div class="max-w-4xl mx-auto">
                <a href="javascript:history.back()" class="text-blue-600 hover:text-blue-800 mb-4 inline-block">← Back</a>

                <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                    <div class="px-6 py-4 border-b border-gray-200">
                        <h1 class="text-2xl font-bold text-gray-900">Pantry Inventory (Normalized)</h1>
                        <p class="text-sm text-gray-600 mt-1">Merged view of Food Database and Pantry Inventory</p>
                        <div class="mt-3 flex items-center space-x-4 text-xs">
                            <div class="flex items-center space-x-2">
                                <div class="w-4 h-4 bg-red-50 border border-red-200 rounded"></div>
                                <span class="text-gray-600">Out of stock (0)</span>
                            </div>
                            <div class="flex items-center space-x-2">
                                <div class="w-4 h-4 bg-yellow-50 border border-yellow-200 rounded"></div>
                                <span class="text-gray-600">Low stock (≤ 3)</span>
                            </div>
                        </div>
                    </div>

                    <div class="overflow-x-auto">
                        <table class="min-w-full divide-y divide-gray-200">
                            <thead class="bg-gray-50">
                                <tr>
                                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Food ID</th>
                                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Food Name</th>
                                    <th class="px-4 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">Quantity</th>
                                </tr>
                            </thead>
                            <tbody class="bg-white divide-y divide-gray-200">
                                {table_rows}
                            </tbody>
                        </table>
                    </div>

                    <div class="px-6 py-4 bg-gray-50 border-t border-gray-200">
                        <p class="text-xs text-gray-500">
                            Total items in database: {len(merged_items)} |
                            Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''

        return html

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"<html><body><h1>Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre></body></html>", 500

# A2A Protocol Endpoints (JSON-RPC 2.0)
@app.route('/.well-known/agent-card.json', methods=['GET'])
def agent_card():
    """Return agent card for A2A discovery."""
    try:
        # Construct agent card from the agent
        root_agent = agent_module.root_agent

        card = {
            "name": getattr(root_agent, 'name', f"{agent_type}_agent"),
            "description": getattr(root_agent, 'description', f"{agent_name} agent"),
            "url": f"http://localhost:{agent_port}",
            "version": "0.0.1",
            "protocolVersion": "0.3.0",
            "capabilities": {},
            "preferredTransport": "JSONRPC",
            "supportsAuthenticatedExtendedCard": False,
            "defaultInputModes": ["text/plain"],
            "defaultOutputModes": ["text/plain"],
            "skills": [
                {
                    "id": getattr(root_agent, 'name', f"{args.agent}_agent"),
                    "name": "model",
                    "description": getattr(root_agent, 'instruction', f"{agent_name} agent"),
                    "tags": ["llm"]
                }
            ]
        }

        # Add tool skills if available
        if hasattr(root_agent, 'tools') and root_agent.tools:
            for tool in root_agent.tools:
                tool_name = getattr(tool, 'name', str(tool))
                tool_desc = getattr(tool, 'description', f"Tool: {tool_name}")
                card["skills"].append({
                    "id": f"{card['name']}-{tool_name}",
                    "name": tool_name,
                    "description": tool_desc,
                    "tags": ["llm", "tools"]
                })

        return jsonify(card)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['POST'])
def a2a_jsonrpc():
    """Handle A2A JSON-RPC 2.0 requests."""
    request_data = None
    response_data = None

    try:
        print(f"\n[A2A] ========== POST REQUEST RECEIVED ==========", flush=True)
        data = request.get_json()
        request_data = data  # Store for logging
        print(f"[A2A] Request data type: {type(data)}", flush=True)
        print(f"[A2A] Request data keys: {data.keys() if isinstance(data, dict) else 'N/A'}", flush=True)
        print(f"[A2A] Full request data: {data}", flush=True)

        # Check if this is a JSON-RPC request
        if not isinstance(data, dict) or 'jsonrpc' not in data:
            # Not a JSON-RPC request, return error
            print(f"[A2A] ❌ Not a valid JSON-RPC request (missing 'jsonrpc' field)", flush=True)
            response_data = {
                'jsonrpc': '2.0',
                'error': {'code': -32600, 'message': 'Invalid Request'},
                'id': data.get('id') if isinstance(data, dict) else None
            }
            # Log the failed request
            try:
                log_a2a_traffic(agent_type, request_data, response_data)
            except:
                pass
            return jsonify(response_data)

        method = data.get('method')
        params = data.get('params', {})
        request_id = data.get('id')

        print(f"[A2A] ✅ Valid JSON-RPC request - method: {method}, id: {request_id}", flush=True)

        # Handle both invoke and message/send methods (Google ADK uses both)
        if method in ['invoke', 'message/send']:
            # Extract message text based on method format
            if method == 'invoke':
                message_text = params.get('message', {}).get('text', '')
            else:  # message/send
                message_obj = params.get('message', {})
                parts = message_obj.get('parts', [])
                # Get text from first text part
                message_text = next((p.get('text', '') for p in parts if p.get('kind') == 'text'), '')

            print(f"[A2A] 📨 {method} method called with message: {message_text[:80]}...", flush=True)

            # Create a NEW session for each A2A call
            # This makes each A2A interaction visible as a separate session in the web UI
            a2a_session_id = f"a2a_session_{int(datetime.now().timestamp() * 1000)}_{uuid.uuid4().hex[:8]}"

            print(f"[A2A] 📝 Creating new session ID: {a2a_session_id}", flush=True)

            # Always create a new session for each A2A call
            print(f"[A2A] 🆕 Creating new session: {a2a_session_id}", flush=True)
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
                    user_id="a2a_agent"
                )
            )

            sessions[a2a_session_id] = {
                'session': session,
                'runner': runner,
                'loop': loop,
                'history': [],
                'created_at': datetime.now().isoformat()
            }
            print(f"[A2A] ✅ Session created: {a2a_session_id}, Total sessions: {len(sessions)}", flush=True)

            session_data = sessions[a2a_session_id]
            session = session_data['session']
            runner = session_data['runner']

            print(f"[A2A] 📝 Adding user message to history", flush=True)
            session_data['history'].append({
                'type': 'user',
                'content': f"[A2A Request] {message_text}",
                'timestamp': datetime.now().isoformat(),
                'source': 'a2a'
            })
            print(f"[A2A] 📊 Session now has {len(session_data['history'])} history entries", flush=True)

            print(f"[A2A] 🤖 Running agent...", flush=True)
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_agent_async, agent_module.root_agent, runner, session, message_text)
                result = future.result(timeout=120)

            if 'error' in result:
                response_data = {
                    'jsonrpc': '2.0',
                    'error': {'code': -32603, 'message': result['error']},
                    'id': request_id
                }
                # Log the error response
                try:
                    log_a2a_traffic(agent_type, request_data, response_data)
                except:
                    pass
                return jsonify(response_data)

            print(f"[A2A] ✅ Agent finished, response: {result.get('response', '')[:80]}...", flush=True)

            agent_entry = {
                'type': 'agent',
                'content': result.get('response', ''),
                'timestamp': datetime.now().isoformat(),
                'source': 'a2a'
            }

            if result.get('tool_calls'):
                agent_entry['tool_calls'] = result['tool_calls']
                print(f"[A2A] 🔧 Tool calls: {len(result['tool_calls'])}", flush=True)

            if result.get('a2a_calls'):
                agent_entry['a2a_calls'] = result['a2a_calls']
                print(f"[A2A] 🔄 A2A calls: {len(result['a2a_calls'])}", flush=True)

            session_data['history'].append(agent_entry)
            print(f"[A2A] 📊 Session now has {len(session_data['history'])} history entries (after agent response)", flush=True)
            print(f"[A2A] 💾 Sessions dict now has {len(sessions)} total sessions", flush=True)

            # Return JSON-RPC response with format based on method
            print(f"[A2A] 📤 Returning JSON-RPC response for method: {method}", flush=True)

            if method == 'invoke':
                # Simple format for invoke
                response_data = {
                    'jsonrpc': '2.0',
                    'result': {
                        'message': {
                            'text': result.get('response', '')
                        }
                    },
                    'id': request_id
                }
            else:  # message/send - use Google ADK format
                response_data = {
                    'jsonrpc': '2.0',
                    'result': {
                        'messageId': str(uuid.uuid4()),
                        'parts': [
                            {
                                'kind': 'text',
                                'text': result.get('response', '')
                            }
                        ],
                        'role': 'agent'
                    },
                    'id': request_id
                }

            # Log A2A traffic
            try:
                log_a2a_traffic(agent_type, request_data, response_data)
            except Exception as log_error:
                print(f"[A2A] ⚠️  Failed to log A2A traffic: {log_error}", flush=True)

            return jsonify(response_data)

        # Unknown method
        response_data = {
            'jsonrpc': '2.0',
            'error': {'code': -32601, 'message': 'Method not found'},
            'id': request_id
        }
        # Log the error response
        try:
            log_a2a_traffic(agent_type, request_data, response_data)
        except:
            pass
        return jsonify(response_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        response_data = {
            'jsonrpc': '2.0',
            'error': {'code': -32603, 'message': str(e)},
            'id': request_id if 'request_id' in locals() else None
        }
        # Log the error response
        try:
            if request_data:  # Only log if we captured request data
                log_a2a_traffic(agent_type, request_data, response_data)
        except:
            pass
        return jsonify(response_data)

@app.route('/a2a/architecture')
def view_architecture():
    """Display the system architecture diagram."""
    try:
        architecture_ascii = """
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
"""

        html = f"""
        <html>
        <head>
            <title>A2A Architecture</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                body {{
                    font-family: 'Inter', sans-serif;
                    background: #f9fafb;
                }}
                .banner-gradient {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
                .dropdown {{ position: relative; display: inline-block; }}
                .dropdown-content {{ display: none; position: absolute; right: 0; background-color: white; min-width: 200px; box-shadow: 0px 8px 16px rgba(0,0,0,0.1); z-index: 1000; border-radius: 0.5rem; margin-top: 0.125rem; padding-top: 0.25rem; }}
                .dropdown:hover .dropdown-content {{ display: block; }}
                .dropdown-content a {{ color: #374151; padding: 12px 16px; text-decoration: none; display: block; transition: background 0.2s; }}
                .dropdown-content a:hover {{ background-color: #f3f4f6; }}
            </style>
        </head>
        <body class="bg-white text-gray-800">
            <header class="banner-gradient text-white border-b border-gray-200">
                <div class="px-8 py-4 flex justify-between items-center">
                    <div>
                        <h1 class="text-4xl font-bold tracking-tight">{agent_emoji} Restaurant - {agent_name}</h1>
                        <p class="text-sm opacity-90 mt-1">Multi-Agent System on port {agent_port}</p>
                    </div>
                    <div class="flex items-center space-x-4">
                        <!-- Agents Menu -->
                        <div class="dropdown">
                            <button class="bg-white bg-opacity-20 hover:bg-opacity-30 px-4 py-2 rounded-lg font-medium transition-all">
                                Agents ▾
                            </button>
                            <div class="dropdown-content">
                                <a href="https://waiter.xeb.ai" target="_blank">Waiter</a>
                                <a href="https://chef.xeb.ai" target="_blank">Chef</a>
                                <a href="https://supplier.xeb.ai" target="_blank">Supplier</a>
                            </div>
                        </div>

                        <!-- Data Menu -->
                        <div class="dropdown">
                            <button class="bg-white bg-opacity-20 hover:bg-opacity-30 px-4 py-2 rounded-lg font-medium transition-all">
                                Data ▾
                            </button>
                            <div class="dropdown-content">
                                <a href="/data/menu.json" target="_blank">Menu</a>
                                <a href="/data/food.json" target="_blank">Food Database</a>
                                <a href="/data/pantry.json" target="_blank">Pantry Inventory</a>
                                <a href="/data/pantry-normalized" target="_blank">Pantry (Normalized)</a>
                                <a href="/data/orders.json" target="_blank">Waiter Orders</a>
                                <a href="/data/chef_orders.json" target="_blank">Chef Orders</a>
                            </div>
                        </div>

                        <!-- A2A Menu -->
                        <div class="dropdown">
                            <button class="bg-white bg-opacity-20 hover:bg-opacity-30 px-4 py-2 rounded-lg font-medium transition-all">
                                A2A ▾
                            </button>
                            <div class="dropdown-content">
                                <a href="/a2a/architecture" target="_blank">View Architecture</a>
                                <a href="/a2a/logs/waiter" target="_blank">View Waiter Logs</a>
                                <a href="/a2a/logs/chef" target="_blank">View Chef Logs</a>
                                <a href="/a2a/logs/supplier" target="_blank">View Supplier Logs</a>
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            <div class="p-8">
                <div class="max-w-7xl mx-auto">
                    <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                        <div class="px-6 py-4 border-b border-gray-200">
                            <h1 class="text-2xl font-bold text-gray-900">System Architecture</h1>
                            <p class="text-sm text-gray-600 mt-1">Agent-to-Agent Communication Flow</p>
                        </div>

                        <div class="p-6">
                            <div class="bg-gray-900 text-green-400 p-6 rounded-lg overflow-x-auto">
                                <pre class="font-mono text-sm">{architecture_ascii}</pre>
                            </div>
                        </div>

                        <div class="px-6 py-4 bg-gray-50 border-t border-gray-200">
                            <h3 class="font-semibold text-gray-900 mb-2">Key Features:</h3>
                            <ul class="text-sm text-gray-700 space-y-1 list-disc list-inside">
                                <li>Unified Web + A2A endpoints on ports 8001-8003</li>
                                <li>A2A sessions visible in browser interface</li>
                                <li>Food ID system for precise ingredient tracking</li>
                                <li>Disk-reload for multi-process pantry consistency</li>
                                <li>Duration tracking for agent responses</li>
                                <li>Normalized pantry view for debugging</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"<html><body><h1>Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre></body></html>", 500

@app.route('/a2a/logs/<agent_name>')
def view_a2a_logs(agent_name):
    """Display A2A traffic logs for a specific agent."""
    try:
        # Validate agent name
        if agent_name not in ['waiter', 'chef', 'supplier']:
            return f"<html><body><h1>Error</h1><p>Invalid agent name: {agent_name}</p></body></html>", 400

        # Get log files from a2a_traffic directory
        log_dir = Path("a2a_traffic")
        if not log_dir.exists():
            log_files = []
        else:
            # Get all log files for this agent
            pattern = f"{agent_name}_*.json"
            log_files = sorted(log_dir.glob(pattern), key=lambda x: x.stat().st_mtime, reverse=True)

        # Build file list HTML
        if not log_files:
            file_list_html = '<p class="text-gray-500 text-center py-8">No log files found</p>'
        else:
            file_items = []
            for log_file in log_files:
                # Read log file to get metadata
                try:
                    with open(log_file, 'r') as f:
                        log_data = json.load(f)

                    timestamp = log_data.get('timestamp_human', 'Unknown')
                    method = log_data.get('request', {}).get('method', 'N/A')

                    file_items.append(f'''
                        <div class="border border-gray-200 rounded-lg p-4 hover:border-blue-500 cursor-pointer transition-colors" onclick="loadLogFile('{log_file.name}')">
                            <div class="flex items-start justify-between">
                                <div class="flex-1">
                                    <h4 class="font-medium text-gray-900 text-sm">{log_file.name}</h4>
                                    <p class="text-xs text-gray-500 mt-1">Method: {method}</p>
                                    <p class="text-xs text-gray-400">{timestamp}</p>
                                </div>
                                <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                                </svg>
                            </div>
                        </div>
                    ''')
                except Exception:
                    # Skip files that can't be read
                    continue

            file_list_html = '\n'.join(file_items)

        html = f"""
        <html>
        <head>
            <title>A2A Logs - {agent_name.capitalize()}</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                body {{
                    font-family: 'Inter', sans-serif;
                    background: #f9fafb;
                }}
                .banner-gradient {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
                .dropdown {{ position: relative; display: inline-block; }}
                .dropdown-content {{ display: none; position: absolute; right: 0; background-color: white; min-width: 200px; box-shadow: 0px 8px 16px rgba(0,0,0,0.1); z-index: 1000; border-radius: 0.5rem; margin-top: 0.125rem; padding-top: 0.25rem; }}
                .dropdown:hover .dropdown-content {{ display: block; }}
                .dropdown-content a {{ color: #374151; padding: 12px 16px; text-decoration: none; display: block; transition: background 0.2s; }}
                .dropdown-content a:hover {{ background-color: #f3f4f6; }}
            </style>
        </head>
        <body class="bg-white text-gray-800">
            <header class="banner-gradient text-white border-b border-gray-200">
                <div class="px-8 py-4 flex justify-between items-center">
                    <div>
                        <h1 class="text-4xl font-bold tracking-tight">{agent_emoji} Restaurant - {agent_name}</h1>
                        <p class="text-sm opacity-90 mt-1">Multi-Agent System on port {agent_port}</p>
                    </div>
                    <div class="flex items-center space-x-4">
                        <!-- Agents Menu -->
                        <div class="dropdown">
                            <button class="bg-white bg-opacity-20 hover:bg-opacity-30 px-4 py-2 rounded-lg font-medium transition-all">
                                Agents ▾
                            </button>
                            <div class="dropdown-content">
                                <a href="https://waiter.xeb.ai" target="_blank">Waiter</a>
                                <a href="https://chef.xeb.ai" target="_blank">Chef</a>
                                <a href="https://supplier.xeb.ai" target="_blank">Supplier</a>
                            </div>
                        </div>

                        <!-- Data Menu -->
                        <div class="dropdown">
                            <button class="bg-white bg-opacity-20 hover:bg-opacity-30 px-4 py-2 rounded-lg font-medium transition-all">
                                Data ▾
                            </button>
                            <div class="dropdown-content">
                                <a href="/data/menu.json" target="_blank">Menu</a>
                                <a href="/data/food.json" target="_blank">Food Database</a>
                                <a href="/data/pantry.json" target="_blank">Pantry Inventory</a>
                                <a href="/data/pantry-normalized" target="_blank">Pantry (Normalized)</a>
                                <a href="/data/orders.json" target="_blank">Waiter Orders</a>
                                <a href="/data/chef_orders.json" target="_blank">Chef Orders</a>
                            </div>
                        </div>

                        <!-- A2A Menu -->
                        <div class="dropdown">
                            <button class="bg-white bg-opacity-20 hover:bg-opacity-30 px-4 py-2 rounded-lg font-medium transition-all">
                                A2A ▾
                            </button>
                            <div class="dropdown-content">
                                <a href="/a2a/architecture" target="_blank">View Architecture</a>
                                <a href="/a2a/logs/waiter" target="_blank">View Waiter Logs</a>
                                <a href="/a2a/logs/chef" target="_blank">View Chef Logs</a>
                                <a href="/a2a/logs/supplier" target="_blank">View Supplier Logs</a>
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            <div class="p-8">
                <div class="max-w-7xl mx-auto">
                    <div class="flex gap-6">
                        <!-- Left: File List -->
                        <div class="w-1/3 bg-white rounded-lg shadow-sm border border-gray-200">
                            <div class="px-6 py-4 border-b border-gray-200">
                                <h2 class="text-lg font-semibold">{agent_name.capitalize()} A2A Logs</h2>
                                <p class="text-sm text-gray-600 mt-1">{len(log_files)} log files</p>
                            </div>
                            <div class="p-4 overflow-y-auto" style="max-height: calc(100vh - 250px);">
                                <div class="space-y-2">
                                    {file_list_html}
                                </div>
                            </div>
                        </div>

                        <!-- Right: Log Content -->
                        <div class="flex-1 bg-white rounded-lg shadow-sm border border-gray-200">
                            <div class="px-6 py-4 border-b border-gray-200">
                                <h2 class="text-lg font-semibold">Log Details</h2>
                                <p class="text-sm text-gray-600 mt-1">Select a log file to view details</p>
                            </div>
                            <div id="logContent" class="p-6 overflow-y-auto" style="max-height: calc(100vh - 250px);">
                                <div class="text-center text-gray-500 mt-8">
                                    <svg class="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                    </svg>
                                    <p class="text-sm">No log file selected</p>
                                    <p class="text-xs text-gray-400 mt-1">Click a log file on the left to view details</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                function loadLogFile(filename) {{
                    fetch(`/a2a/logs/{agent_name}/${{filename}}`)
                        .then(response => response.json())
                        .then(data => {{
                            const content = document.getElementById('logContent');

                            const requestStr = JSON.stringify(data.request, null, 2);
                            const responseStr = JSON.stringify(data.response, null, 2);

                            content.innerHTML = `
                                <div class="space-y-4">
                                    <div>
                                        <h3 class="font-semibold text-gray-900 mb-2">Metadata</h3>
                                        <div class="bg-gray-50 p-4 rounded-lg text-sm">
                                            <div class="grid grid-cols-2 gap-2">
                                                <div><span class="font-medium">File:</span> ${{filename}}</div>
                                                <div><span class="font-medium">Timestamp:</span> ${{data.timestamp_human}}</div>
                                                <div><span class="font-medium">Agent:</span> ${{data.agent}}</div>
                                                <div><span class="font-medium">Method:</span> ${{data.request.method || 'N/A'}}</div>
                                            </div>
                                        </div>
                                    </div>

                                    <div>
                                        <h3 class="font-semibold text-gray-900 mb-2">Request</h3>
                                        <div class="bg-gray-900 text-green-400 p-4 rounded-lg overflow-auto">
                                            <pre class="font-mono text-xs whitespace-pre-wrap break-all">${{requestStr}}</pre>
                                        </div>
                                    </div>

                                    <div>
                                        <h3 class="font-semibold text-gray-900 mb-2">Response</h3>
                                        <div class="bg-gray-900 text-blue-400 p-4 rounded-lg overflow-auto">
                                            <pre class="font-mono text-xs whitespace-pre-wrap break-all">${{responseStr}}</pre>
                                        </div>
                                    </div>
                                </div>
                            `;
                        }})
                        .catch(error => {{
                            console.error('Error loading log file:', error);
                            document.getElementById('logContent').innerHTML = `
                                <div class="text-center text-red-500 mt-8">
                                    <p>Error loading log file</p>
                                    <p class="text-sm mt-2">${{error.message}}</p>
                                </div>
                            `;
                        }});
                }}
            </script>
        </body>
        </html>
        """

        return html

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"<html><body><h1>Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre></body></html>", 500

@app.route('/a2a/logs/<agent_name>/<filename>')
def get_log_file(agent_name, filename):
    """Return the contents of a specific log file."""
    try:
        # Validate agent name
        if agent_name not in ['waiter', 'chef', 'supplier']:
            return jsonify({'error': 'Invalid agent name'}), 400

        # Security: ensure filename matches expected pattern
        if not filename.startswith(f"{agent_name}_") or not filename.endswith('.json'):
            return jsonify({'error': 'Invalid filename'}), 400

        log_file = Path("a2a_traffic") / filename

        if not log_file.exists():
            return jsonify({'error': 'Log file not found'}), 404

        with open(log_file, 'r') as f:
            log_data = json.load(f)

        return jsonify(log_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Restaurant Multi-Agent Web Interface')
    parser.add_argument('--agent', type=str, required=True,
                       choices=['waiter', 'chef', 'supplier'],
                       help='Which agent to run (waiter, chef, or supplier)')
    parser.add_argument('--port', type=int, help='Port to run on (auto-assigned if not specified)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    parser.add_argument('--with-a2a', action='store_true', default=False,
                       help='Also expose A2A server on the agent port (8001-8003)')

    args = parser.parse_args()

    # Import the appropriate agent module
    import importlib.util

    # All agents now use the same pattern: {agent}/agent.py
    agent_dir = os.path.join(os.path.dirname(__file__), args.agent)
    agent_file = os.path.join(agent_dir, 'agent.py')

    spec = importlib.util.spec_from_file_location(f"{args.agent}_agent", agent_file)
    agent_module = importlib.util.module_from_spec(spec)
    sys.modules[f"{args.agent}_agent"] = agent_module

    # Change to appropriate directory for relative imports
    original_dir = os.getcwd()
    os.chdir(os.path.join(os.path.dirname(__file__), args.agent))

    try:
        spec.loader.exec_module(agent_module)
    finally:
        os.chdir(original_dir)

    # Set module-level variables
    agent_type = args.agent
    agent_name = args.agent.capitalize()
    agent_emoji = {'waiter': '🙋', 'chef': '👨‍🍳', 'supplier': '🚚'}[args.agent]
    default_web_port = {'waiter': 5001, 'chef': 5002, 'supplier': 5003}[args.agent]
    default_a2a_port = {'waiter': 8001, 'chef': 8002, 'supplier': 8003}[args.agent]

    # Use A2A port if --with-a2a is enabled, otherwise use web port
    if args.with_a2a:
        agent_port = args.port or default_a2a_port
        print(f"🚀 Starting {agent_name} agent with dual exposure (Web + A2A):")
        print(f"   - Unified endpoint: http://{args.host}:{agent_port}")
        print(f"   - Web interface: http://{args.host}:{agent_port}/ (GET)")
        print(f"   - A2A JSON-RPC: http://{args.host}:{agent_port}/ (POST)")
        print(f"   - Agent card: http://{args.host}:{agent_port}/.well-known/agent-card.json")
        print(f"")
        print(f"   💡 A2A sessions will be visible in the web interface!")
    else:
        agent_port = args.port or default_web_port
        print(f"🚀 Starting {agent_name} agent web interface on {args.host}:{agent_port}")

    app.run(host=args.host, port=agent_port, debug=args.debug)
