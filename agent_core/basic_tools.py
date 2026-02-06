# agent_core/basic_tools.py
import os
from langchain_core.tools import tool

@tool
def read_file(file_path: str) -> str:
    """
    Lê o conteúdo de um arquivo.
    Args:
        file_path: Caminho absoluto ou relativo do arquivo.
    Returns:
        Conteúdo do arquivo ou mensagem de erro.
    """
    try:
        if not os.path.exists(file_path):
            return f"Erro: Arquivo '{file_path}' não encontrado."
        
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Erro ao ler arquivo: {e}"

@tool
def write_file(file_path: str, content: str) -> str:
    """
    Escreve conteúdo em um arquivo. Cria o arquivo se não existir.
    Args:
        file_path: Caminho para o arquivo.
        content: Conteúdo de texto a ser escrito.
    Returns:
        Mensagem de sucesso ou erro.
    """
    try:
        # Garante que o diretório existe
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Sucesso: Arquivo escrito em '{file_path}'."
    except Exception as e:
        return f"Erro ao escrever arquivo: {e}"

@tool
def list_directory(directory_path: str = ".") -> str:
    """
    Lista os arquivos e pastas em um diretório.
    """
    try:
        if not os.path.exists(directory_path):
            return f"Erro: Diretório '{directory_path}' não encontrado."
            
        items = os.listdir(directory_path)
        return "\n".join(items)
    except Exception as e:
        return f"Erro ao listar diretório: {e}"

# Lista para exportação fácil
BASIC_TOOLS = [read_file, write_file, list_directory]
