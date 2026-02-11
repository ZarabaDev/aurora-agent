import os
import sys
import time
import requests
import json
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_core.core.orchestrator import Orchestrator
try:
    from tools_library.vision_analyzer import vision_analyzer
except ImportError:
    # Add project root to path for tool import if needed
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tools_library.vision_analyzer import vision_analyzer

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_CHAT_ID = os.getenv("TELEGRAM_DEFAULT_CHAT_ID")

if not TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN not found for bot script.")
    sys.exit(1)

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"
    params = {"timeout": 30, "offset": offset}
    try:
        response = requests.get(url, params=params)
        return response.json()
    except Exception as e:
        print(f"Error getting updates: {e}")
        return None

def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending message: {e}")

def send_chat_action(chat_id, action="typing"):
    url = f"{BASE_URL}/sendChatAction"
    payload = {"chat_id": chat_id, "action": action}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending chat action: {e}")

def main():
    print("🤖 Aurora Telegram Bot Online (Standalone)...")
    engine = Orchestrator()
    
    # Initialize Engine
    init_event = engine.initialize()
    if init_event.type == "error":
        print(f"Engine Init Error: {init_event.content}")
        return
    
    print(f"Engine Ready: {init_event.content}")

    offset = None
    
    while True:
        updates = get_updates(offset)
        
        if updates and updates.get("ok"):
            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                
                if "message" not in update:
                    continue
                    
                message = update["message"]
                chat_id = str(message.get("chat", {}).get("id"))
                
                # Security Check
                if ALLOWED_CHAT_ID and chat_id != str(ALLOWED_CHAT_ID):
                    continue
                
                text = message.get("text")
                photo = message.get("photo")
                
                if not text and not photo:
                    continue

                print(f"📩 Received from {chat_id}")
                send_chat_action(chat_id, "typing")
                
                full_input = ""
                
                # Handle Photo
                if photo:
                    # Get largest photo
                    file_id = photo[-1]["file_id"]
                    try:
                        # Get file path
                        f_info = requests.get(f"{BASE_URL}/getFile?file_id={file_id}").json()
                        f_path = f_info["result"]["file_path"]
                        # Download
                        img_url = f"https://api.telegram.org/file/bot{TOKEN}/{f_path}"
                        img_data = requests.get(img_url).content
                        
                        # Save temp
                        temp_dir = os.path.join(os.getcwd(), "temp_downloads")
                        os.makedirs(temp_dir, exist_ok=True)
                        import uuid
                        local_path = os.path.join(temp_dir, f"tg_{uuid.uuid4().hex}.jpg")
                        with open(local_path, "wb") as f:
                            f.write(img_data)
                            
                        # Analyze
                        description = vision_analyzer(local_path)
                        full_input += f"[CONTEXTO VISUAL DA IMAGEM]\n{description}\n[Caminho: {local_path}]\n\n"
                        
                        send_message(chat_id, "Imagem analisada. Processando contexto...")
                        
                    except Exception as e:
                        print(f"Photo Error: {e}")
                        full_input += f"[ERRO IMAGEM]: {e}\n\n"

                # Handle Text (Caption or Message)
                caption = message.get("caption")
                if text:
                    full_input += text
                elif caption:
                    full_input += caption
                
                if not full_input.strip():
                    full_input = "Analise esta imagem."

                # Process
                try:
                    for event in engine.process_message(full_input):
                        if event.type == "final_answer":
                            send_message(chat_id, event.content)
                        elif event.type == "error":
                            send_message(chat_id, f"⚠️ Error: {event.content}")
                        
                        if event.type in ["plan", "tool_call"]:
                            send_chat_action(chat_id, "typing")
                            
                except Exception as e:
                    print(f"❌ Error processing message: {e}")
                    send_message(chat_id, "Erro interno.")

        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBot stopped.")
