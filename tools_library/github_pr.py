import os
import requests
import json

TOOL_DESC = "Cria um Pull Request no GitHub. Input: JSON com 'repo' (usuario/repo), 'title', 'body', 'head' (branch-origem) e 'base' (branch-destino)."

def run(input_str):
    try:
        params = json.loads(input_str)
        repo = params.get("repo")
        token = os.getenv("GITHUB_TOKEN")
        
        if not token:
            return "Erro: GITHUB_TOKEN não configurado no .env."
        
        url = f"https://api.github.com/repos/{repo}/pulls"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "title": params.get("title"),
            "body": params.get("body"),
            "head": params.get("head"),
            "base": params.get("base", "main")
        }
        
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 201:
            return f"Sucesso: PR criado em {response.json().get('html_url')}"
        else:
            return f"Erro ({response.status_code}): {response.text}"
            
    except Exception as e:
        return f"Erro: {str(e)}"
