#!/usr/bin/env python3
"""
Aurora HUD - Web Interface for Agent Monitoring
Sci-Fi / Retro-Futurism / Pixel Art HUD
"""

import eventlet
eventlet.monkey_patch()

import os
import sys
import time
import json
import requests
import uuid
from dotenv import load_dotenv
from flask import Flask, render_template, send_from_directory, request, jsonify
from flask_socketio import SocketIO, emit

# Load env vars
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_ALLOWED_CHAT_ID = os.getenv("TELEGRAM_DEFAULT_CHAT_ID")

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_core.core.orchestrator import Orchestrator

app = Flask(__name__, static_folder='static', template_folder='static')
app.config['SECRET_KEY'] = 'aurora-hud-secret'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global engine instance
engine = None
engine_lock = eventlet.semaphore.Semaphore()

# --- TELEGRAM HELPER FUNCTIONS ---
def tg_send_message(chat_id, text):
    if not TELEGRAM_TOKEN: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"Telegram Error: {e}")

def tg_send_action(chat_id, action="typing"):
    if not TELEGRAM_TOKEN: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendChatAction"
    try:
        requests.post(url, json={"chat_id": chat_id, "action": action})
    except:
        pass

# --- CORE PROCESSING (Shared by Web & Telegram) ---
def process_engine_request(user_input, source="web", chat_id=None):
    """
    Unified processor that runs the engine and broadcasts events to WebSocket.
    Returns the final answer text.
    """
    global engine
    if engine is None:
        with engine_lock:
            if engine is None:
                engine = Orchestrator()
                engine.initialize()
    
    if source == "telegram":
        socketio.emit('user_message', {'content': f"[Telegram] {user_input}"})
    
    final_response = ""
    
    try:
        for event in engine.process_message(user_input):
            socketio.emit(event.type, {
                'content': event.content,
                'metadata': event.metadata or {},
                'steps': event.content if event.type == 'plan' else None,
                'mode': event.metadata.get('mode', 'UNKNOWN') if event.type == 'plan' else None,
                'step': event.content if event.type == 'step_start' else None,
                'index': event.metadata.get('step_index') if event.type == 'step_start' else None,
                'total': event.metadata.get('total_steps') if event.type == 'step_start' else None,
                'name': event.content if event.type == 'tool_call' else None,
                'args': event.metadata.get('args', {}) if event.type == 'tool_call' else None,
                'preview': event.content if event.type == 'tool_result' else None,
                'full': event.metadata.get('full_content', '') if event.type == 'tool_result' else None,
                'message': event.content if event.type in ['error', 'log', 'thought'] else None
            })
            
            if source == "telegram" and chat_id:
                if event.type == "final_answer":
                    final_response = event.content
                elif event.type in ["plan", "tool_call"]:
                    tg_send_action(chat_id, "typing")
                    
            socketio.sleep(0.02)
            
    except Exception as e:
        error_msg = f"Error processing: {e}"
        socketio.emit('error', {'message': error_msg})
        return error_msg

    socketio.emit('processing_complete', {})
    return final_response


# --- TELEGRAM POLLING THREAD ---
def telegram_poll_loop():
    if not TELEGRAM_TOKEN:
        print("[System] Telegram Token not found. Polling disabled.")
        return

    print("[System] Telegram Polling Started.")
    offset = None
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    
    while True:
        try:
            params = {"timeout": 30, "offset": offset}
            resp = requests.get(url, params=params)
            data = resp.json()
            
            if data.get("ok"):
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    
                    if "message" in update:
                        msg = update["message"]
                        chat_id = str(msg["chat"]["id"])
                        
                        if TELEGRAM_ALLOWED_CHAT_ID and chat_id != str(TELEGRAM_ALLOWED_CHAT_ID):
                            continue

                        # Handle Text
                        if "text" in msg:
                            text = msg["text"]
                            process_engine_request(text, source="telegram", chat_id=chat_id)
                            response_text = process_engine_request(text, source="telegram", chat_id=chat_id)
                            if response_text:
                                tg_send_message(chat_id, response_text)
                        
                        # Handle Photo
                        elif "photo" in msg:
                            photo = msg["photo"][-1] # Get largest size
                            file_id = photo["file_id"]
                            # Get file path
                            file_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}").json()
                            file_path = file_info["result"]["file_path"]
                            # Download
                            img_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
                            img_data = requests.get(img_url).content
                            
                            local_filename = f"tg_{uuid.uuid4().hex}.jpg"
                            local_path = os.path.join(app.config['UPLOAD_FOLDER'], local_filename)
                            with open(local_path, "wb") as f:
                                f.write(img_data)
                            
                            send_chat_action(chat_id, "typing")
                            
                            # Vision Analysis
                            try:
                                from tools_library.vision_analyzer import vision_analyzer
                                description = vision_analyzer(local_path)
                                vision_context = f"[CONTEXTO VISUAL DA IMAGEM]\n{description}\n[Caminho: {local_path}]"
                            except Exception as ve:
                                vision_context = f"[ERRO NA VISÃO]: {ve}"
                            
                            caption = msg.get("caption", "")
                            full_prompt = f"{vision_context}\n\n{caption}".strip()
                            
                            # Log for user
                            if not caption:
                                send_message(chat_id, "Recebi sua imagem. Analisando...")
                            
                            response_text = process_engine_request(full_prompt, source="telegram", chat_id=chat_id)
                            if response_text:
                                tg_send_message(chat_id, response_text)
                            
        except Exception as e:
            print(f"[Telegram] Polling Error: {e}")
            time.sleep(5)
            
        time.sleep(1)

# --- FLASK ROUTES ---
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/style.css')
def styles():
    return send_from_directory('static', 'style.css')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = f"web_{uuid.uuid4().hex}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({'filepath': os.path.abspath(filepath)})

# --- SOCKET EVENTS ---
@socketio.on('connect')
def handle_connect():
    print('[HUD] Client connected')
    emit('system', {'message': 'Conexão estabelecida com Aurora HUD'})

@socketio.on('init_engine')
def handle_init():
    global engine
    with engine_lock:
        if engine is None:
            emit('system', {'message': 'Inicializando Aurora Engine...'})
            engine = Orchestrator()
            init_event = engine.initialize()
            if init_event.type == "error":
                emit('error', {'message': init_event.content})
            else:
                emit('system', {'message': init_event.content})
                emit('ready', {'tools': len(engine.all_tools)})
        else:
            emit('ready', {'tools': len(engine.all_tools)})


@socketio.on('reset_engine')
def handle_reset():
    global engine
    with engine_lock:
        if engine is None:
            engine = Orchestrator()
            init_event = engine.initialize()
        else:
            init_event = engine.reset_session()
        
        if init_event.type == "error":
             emit('error', {'message': f"Erro no reset: {init_event.content}"})
        else:
             emit('reset_complete', {})
             emit('system', {'message': 'Sessão reiniciada.'})
             emit('ready', {'tools': len(engine.all_tools)})

from tools_library.vision_analyzer import vision_analyzer

@socketio.on('send_message')
def handle_message(data):
    user_input = data.get('message', '')
    image_path = data.get('image_path', None)
    
    context_prefix = ""

    if image_path:
        emit('system', {'message': 'Analysando imagem com visão computacional...'})
        try:
            # Run vision analysis
            description = vision_analyzer(image_path)
            context_prefix = f"[CONTEXTO VISUAL DA IMAGEM]\n{description}\n[Caminho: {image_path}]\n\n"
            emit('system', {'message': 'Análise visual concluída.'})
        except Exception as e:
            print(f"Vision Error: {e}")
            context_prefix = f"[ERRO NA VISÃO]: Não foi possível analisar a imagem ({str(e)}). O usuário enviou: {image_path}\n\n"
    
    # Combine context with user input
    final_input = f"{context_prefix}{user_input}".strip()
    
    if not final_input: return
    
    # Show user what we are sending (conceptually)
    display_msg = user_input
    if image_path:
        display_msg = f"[Imagem Anexada] {user_input}"

    emit('user_message', {'content': display_msg})
    
    # Process with the engine
    process_engine_request(final_input, source="web")


if __name__ == '__main__':
    if TELEGRAM_TOKEN:
        import eventlet
        eventlet.spawn(telegram_poll_loop)
    
    socketio.run(app, host='0.0.0.0', port=5001, debug=False)
