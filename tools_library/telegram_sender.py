import os
import requests
from dotenv import load_dotenv

def run(input_str):
    """
    Envia uma mensagem via Telegram.
    Formato do input: 'chat_id|mensagem' ou apenas 'mensagem' (usa o ID padrão se configurado).
    """
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    # Tenta pegar um ID padrão do .env se não for passado no input
    default_chat_id = os.getenv("TELEGRAM_DEFAULT_CHAT_ID", "5735708010")

    if not token:
        return "Erro: TELEGRAM_BOT_TOKEN não encontrado no .env"

    if "|" in input_str:
        chat_id, message = input_str.split("|", 1)
    else:
        chat_id = default_chat_id
        message = input_str

    if not chat_id:
        return "Erro: chat_id não fornecido e TELEGRAM_DEFAULT_CHAT_ID não definido."

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return f"Mensagem enviada com sucesso para {chat_id}."
        else:
            return f"Erro na API do Telegram: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Erro ao enviar mensagem: {str(e)}"

TOOL_DESC = "Envia mensagens de texto via Telegram. Input: 'chat_id|mensagem' ou apenas 'mensagem'."
