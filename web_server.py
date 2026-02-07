#!/usr/bin/env python3
"""
Aurora HUD - Web Interface for Agent Monitoring
Sci-Fi / Retro-Futurism / Pixel Art HUD
"""

import os
import sys
import threading
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_core.engine import AuroraEngine

app = Flask(__name__, static_folder='static', template_folder='static')
app.config['SECRET_KEY'] = 'aurora-hud-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Global engine instance
engine = None
engine_lock = threading.Lock()


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/style.css')
def styles():
    return send_from_directory('static', 'style.css')


@socketio.on('connect')
def handle_connect():
    print('[HUD] Client connected')
    emit('system', {'message': 'Conexão estabelecida com Aurora HUD'})


@socketio.on('disconnect')
def handle_disconnect():
    print('[HUD] Client disconnected')


@socketio.on('init_engine')
def handle_init():
    """Initialize the Aurora Engine."""
    global engine
    
    with engine_lock:
        if engine is None:
            emit('system', {'message': 'Inicializando Aurora Engine...'})
            engine = AuroraEngine()
            init_event = engine.initialize()
            
            if init_event.type == "error":
                emit('error', {'message': init_event.content})
            else:
                emit('system', {'message': init_event.content})
                emit('ready', {'tools': len(engine.all_tools)})
        else:
            emit('ready', {'tools': len(engine.all_tools)})


@socketio.on('send_message')
def handle_message(data):
    """Process a user message through the engine."""
    global engine
    
    user_input = data.get('message', '')
    if not user_input.strip():
        return
    
    if engine is None:
        emit('error', {'message': 'Engine não inicializado. Recarregue a página.'})
        return
    
    emit('user_message', {'content': user_input})
    
    # Process message and emit events
    try:
        for event in engine.process_message(user_input):
            event_data = {
                'type': event.type,
                'content': event.content,
                'metadata': event.metadata or {}
            }
            
            if event.type == 'plan':
                emit('plan', {
                    'steps': event.content,
                    'mode': event.metadata.get('mode', 'UNKNOWN')
                })
            
            elif event.type == 'step_start':
                emit('step_start', {
                    'step': event.content,
                    'index': event.metadata.get('step_index'),
                    'total': event.metadata.get('total_steps')
                })
            
            elif event.type == 'tool_call':
                emit('tool_call', {
                    'name': event.content,
                    'args': event.metadata.get('args', {})
                })
            
            elif event.type == 'tool_result':
                emit('tool_result', {
                    'preview': event.content,
                    'full': event.metadata.get('full_content', '')
                })
            
            elif event.type == 'thought':
                emit('thought', {'content': event.content})
            
            elif event.type == 'final_answer':
                emit('final_answer', {'content': event.content})
            
            elif event.type == 'error':
                emit('error', {'message': event.content})
            
            elif event.type == 'log':
                emit('log', {'message': event.content})
            
            # Small delay to allow UI updates
            socketio.sleep(0.05)
    
    except Exception as e:
        emit('error', {'message': f'Erro no processamento: {str(e)}'})
    
    emit('processing_complete', {})


if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║           🌌 AURORA HUD - Interface Web 🌌                ║
    ║                                                           ║
    ║   Acesse: http://localhost:5001                          ║
    ║                                                           ║
    ║   Para acesso remoto, use um túnel SSH:                  ║
    ║   ssh -L 5001:localhost:5001 user@server                 ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    socketio.run(app, host='0.0.0.0', port=5001, debug=False)
