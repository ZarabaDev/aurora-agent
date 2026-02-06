import subprocess

def run(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    except Exception as e:
        return str(e)

TOOL_DESC = "Executa comandos do sistema (shell) e retorna a saída."
