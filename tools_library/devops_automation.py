import os
import subprocess
import json

TOOL_DESC = "Executa testes ou build detectando o tipo de projeto (Python/Node). Input: JSON com 'action' (test|build) e 'target_dir' (opcional)."

def run(input_str):
    try:
        try:
            params = json.loads(input_str)
        except:
            params = {"action": input_str.strip()}
            
        action = params.get("action")
        target_dir = params.get("target_dir") or os.path.join(os.getcwd(), "workspace")
        
        if not os.path.exists(target_dir):
            return f"Erro: Diretório {target_dir} não existe."

        is_python = os.path.exists(os.path.join(target_dir, "requirements.txt")) or os.path.exists(os.path.join(target_dir, "pyproject.toml"))
        is_node = os.path.exists(os.path.join(target_dir, "package.json"))
        
        cmds = []
        if action == "test":
            if is_python: cmds = [["pytest"], ["python", "-m", "unittest"]]
            elif is_node: cmds = [["npm", "test"], ["yarn", "test"]]
        elif action == "build":
            if is_node: cmds = [["npm", "run", "build"], ["yarn", "build"]]
            elif is_python: return "Aviso: Projeto Python não possui build step padrão."
            
        for cmd in cmds:
            try:
                res = subprocess.run(cmd, cwd=target_dir, capture_output=True, text=True)
                if res.returncode == 0:
                    return f"Sucesso: {action} ok.\nOutput: {res.stdout}"
            except: continue
            
        return f"Erro: Falha ao rodar {action}."
        
    except Exception as e:
        return f"Erro: {str(e)}"
