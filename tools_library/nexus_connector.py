import os
import requests
import json

TOOL_DESC = "Envia dados, logs ou aprendizados da Aurora para o Nexus2. Input: JSON com 'data' (objeto com o que enviar) e 'nexus_url' (opcional)."

def run(input_str):
    try:
        try:
            params = json.loads(input_str)
        except:
            params = {"data": {"message": input_str.strip()}}
            
        data_to_send = params.get("data")
        # Default local development port for Next.js
        nexus_url = params.get("nexus_url") or "http://localhost:3000"
        
        endpoint = f"{nexus_url}/api/partner/data"
        
        payload = {
            "partnerId": "Aurora-Agent",
            "data": data_to_send
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(endpoint, json=payload, headers=headers)
        
        if response.status_code == 201:
            return f"Sucesso: Dados sincronizados com Nexus2 ({nexus_url})."
        else:
            return f"Erro ao sincronizar com Nexus2 ({response.status_code}): {response.text}"
            
    except Exception as e:
        return f"Erro no conector: {str(e)}"
