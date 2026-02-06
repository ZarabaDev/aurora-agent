# scripts/verify_self_build.py
import sys
import os
import shutil

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_core.brain import AgentBrain
from agent_core.tool_loader import load_dynamic_tools

def verify_tool_creation():
    print("--- Teste de Self-Build ---")
    
    tools_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools_library")
    if not os.path.exists(tools_dir):
        os.makedirs(tools_dir)
        
    # 1. Simular o Agente criando um arquivo (por enquanto manual, para testar o LOADER)
    #    No futuro, isso virá de uma tool 'create_file' chamada pelo LLM.
    
    tool_code = """
# random_number.py
import random

TOOL_DESC = "Gera um numero aleatorio entre 0 e 100."

def run(input_str):
    return f"Numero Aleatorio: {random.randint(0, 100)}"
"""
    
    tool_path = os.path.join(tools_dir, "random_number.py")
    
    print(f"1. Criando ferramenta simulada em: {tool_path}")
    with open(tool_path, "w") as f:
        f.write(tool_code)
        
    # 2. Testar o Loader
    print("2. Recarregando ferramentas...")
    tools = load_dynamic_tools(tools_dir)
    
    # 3. Verificar se a ferramenta foi carregada
    loaded = False
    for t in tools:
        if t.name == "random_number":
            print(f"✅ Ferramenta 'random_number' carregada com sucesso!")
            # Testar execução
            result = t.run("teste")
            print(f"   Resultado da execução: {result}")
            loaded = True
            break
            
    if not loaded:
        print("❌ FALHA: Ferramenta não foi carregada.")
        
    # Limpeza
    if os.path.exists(tool_path):
        os.remove(tool_path)
        print("4. Limpeza concluída.")

if __name__ == "__main__":
    verify_tool_creation()
