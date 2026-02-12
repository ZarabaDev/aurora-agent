import os
import subprocess
import json

TOOL_DESC = "Gerencia repositórios Git (clone, pull, status). Input esperado: JSON com 'action' (clone|pull|status), 'repo_url' (opcional para clone) e 'branch' (opcional)."

def run(input_str):
    try:
        # Tenta parsear como JSON, se falhar tenta usar como string pura para ações simples
        try:
            params = json.loads(input_str)
        except:
            params = {"action": input_str.strip()}

        action = params.get("action")
        repo_url = params.get("repo_url")
        branch = params.get("branch", "main")
        workspace_dir = os.path.join(os.getcwd(), "workspace")

        if action == "clone":
            if not repo_url:
                return "Erro: 'repo_url' é necessário para clonar."
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            target_path = os.path.join(workspace_dir, repo_name)
            
            if os.path.exists(target_path):
                return f"Erro: {target_path} já existe."
            
            subprocess.run(["git", "clone", repo_url, target_path], check=True, capture_output=True, text=True)
            return f"Sucesso: Clonado em {target_path}"

        elif action == "pull":
            result = subprocess.run(["git", "pull", "origin", branch], capture_output=True, text=True)
            if result.returncode != 0:
                return f"Erro no pull: {result.stderr}"
            return f"Sucesso: Pull na branch {branch}.\nOutput: {result.stdout}"

        elif action == "status":
            result = subprocess.run(["git", "status"], capture_output=True, text=True)
            return result.stdout

        return f"Erro: Ação '{action}' não reconhecida."

    except Exception as e:
        return f"Erro na execução: {str(e)}"
