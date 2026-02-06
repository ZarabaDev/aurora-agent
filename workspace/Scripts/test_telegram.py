import os
import requests
from dotenv import load_dotenv

def test_telegram_connection():
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Erro: TELEGRAM_BOT_TOKEN não encontrado no .env")
        return

    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(f"Sucesso! Bot conectado: @{data['result']['username']}")
        else:
            print(f"Erro na API do Telegram: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Erro ao tentar conectar: {e}")

if __name__ == '__main__':
    test_telegram_connection()
