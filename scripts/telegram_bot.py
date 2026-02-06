import os
import sys
import time
import requests
import json
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_core.engine import AuroraEngine

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_CHAT_ID = os.getenv("TELEGRAM_DEFAULT_CHAT_ID") # Optional security

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
    print("🤖 Aurora Telegram Bot Online...")
    engine = AuroraEngine()
    
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
                text = message.get("text")
                
                # Security Check (Optional but recommended)
                if ALLOWED_CHAT_ID and chat_id != str(ALLOWED_CHAT_ID):
                    print(f"⚠️ Unauthorized access attempt from {chat_id}")
                    continue
                
                if not text:
                    continue

                print(f"📩 Received from {chat_id}: {text}")
                
                # Process with Aurora Engine
                send_chat_action(chat_id, "typing")
                
                # We can send a quick "thinking" reaction or message if needed, 
                # but user requested minimal noise. So we just wait.
                
                try:
                    current_response = ""
                    for event in engine.process_message(text):
                        # We ONLY care about the final answer for Telegram
                        if event.type == "final_answer":
                            current_response = event.content
                            send_message(chat_id, current_response)
                        elif event.type == "error":
                            send_message(chat_id, f"⚠️ Error: {event.content}")
                        
                        # Keep typing active during long think times
                        if event.type in ["plan", "tool_call"]:
                            send_chat_action(chat_id, "typing")
                            
                    print(f"✅ Set reply to {chat_id}")
                    
                except Exception as e:
                    print(f"❌ Error processing message: {e}")
                    send_message(chat_id, "Desculpe, ocorreu um erro interno ao processar sua mensagem.")

        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBot stopped.")
