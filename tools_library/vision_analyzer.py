import os
import base64
import requests

def vision_analyzer(image_path: str) -> str:
    """
    Analisa uma imagem local usando um modelo multimodal via OpenRouter.
    Recebe o caminho do arquivo da imagem.
    Retorna a descrição textual do conteúdo da imagem.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return "Erro: OPENROUTER_API_KEY não configurada no ambiente."

    image_path = image_path.strip("'").strip('"')

    if not os.path.exists(image_path):
        return f"Erro: Arquivo {image_path} não encontrado."

    try:
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        extension = image_path.split('.')[-1].lower()
        mime_type = f"image/{extension}" if extension in ['png', 'jpg', 'jpeg', 'webp'] else "image/jpeg"

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "google/gemini-flash-1.5-exp", # Usando a versão experimental que costuma estar disponível
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Descreva esta imagem em detalhes para que eu possa entender o contexto."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ]
            }
        )

        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            # Tenta outro modelo se o primeiro falhar
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "openai/gpt-4o-mini",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Descreva esta imagem em detalhes."},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime_type};base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ]
                }
            )
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            
            return f"Erro na API OpenRouter: {response.status_code} - {response.text}"

    except Exception as e:
        return f"Erro ao processar imagem: {str(e)}"

def run(input_str: str) -> str:
    return vision_analyzer(input_str)
