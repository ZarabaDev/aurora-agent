# agent_core/tool_loader.py
import importlib.util
import os
import sys
from langchain_core.tools import StructuredTool

def load_dynamic_tools(tools_directory: str):
    """
    Escaneia a pasta, carrega módulos Python e retorna uma lista de Tools.
    O agente deve escrever scripts que tenham uma função 'run' e uma variável 'TOOL_DESC'.
    """
    tools = []
    
    # Garante que o diretório está no path
    if tools_directory not in sys.path:
        sys.path.append(tools_directory)

    for filename in os.listdir(tools_directory):
        if filename.endswith(".py") and not filename.startswith("_"):
            module_name = filename[:-3]
            file_path = os.path.join(tools_directory, filename)
            
            try:
                # Carregamento dinâmico do módulo
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Verifica se o módulo segue o contrato (tem função run e descrição)
                if hasattr(module, 'run') and hasattr(module, 'TOOL_DESC'):
                    new_tool = StructuredTool.from_function(
                        func=module.run,
                        name=module_name,
                        description=module.TOOL_DESC
                    )
                    tools.append(new_tool)
                    print(f"✅ Ferramenta carregada: {module_name}")
            except Exception as e:
                print(f"❌ Erro ao carregar {filename}: {e}")
                
    return tools