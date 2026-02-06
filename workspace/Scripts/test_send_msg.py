import os
import requests
from dotenv import load_dotenv

def send_test_message(chat_id, text):
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Erro: TELEGRAM_BOT_TOKEN não encontrado no .env")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"Sucesso! Mensagem enviada para {chat_id}")
        else:
            print(f"Erro na API do Telegram: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Erro ao tentar enviar: {e}")

if __name__ == '__main__':
    # ID fornecido pelo usuário: 5735708010
    send_test_message("5735708010", "Oi! Aqui é a Aurora. Testando a conexão direta com você. Chegou aí? 🚀")
