import importlib.util
import os
import sys

TOOL_DESC = "Ferramenta para testar outras ferramentas da tools_library. Formato: 'nome_da_ferramenta|input_de_teste'"

def run(input_str):
    try:
        if '|' not in input_str:
            return "Erro: Use o formato 'nome_da_ferramenta|input_de_teste'"
        
        tool_name, test_input = input_str.split('|', 1)
        tool_name = tool_name.strip()
        test_input = test_input.strip()
        
        # Caminho da biblioteca
        lib_path = "/home/zarabatana/Documentos/aurora/tools_library"
        file_path = os.path.join(lib_path, f"{tool_name}.py")
        
        if not os.path.exists(file_path):
            return f"Erro: Ferramenta '{tool_name}' não encontrada em {lib_path}"
        
        # Importação dinâmica
        spec = importlib.util.spec_from_file_location(tool_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if not hasattr(module, 'run'):
            return f"Erro: A ferramenta '{tool_name}' não possui a função 'run(input_str)'"
            
        # Execução do teste
        result = module.run(test_input)
        return f"--- Teste da Ferramenta: {tool_name} ---\nInput: {test_input}\nResultado: {result}"
        
    except Exception as e:
        return f"Erro durante a execução do teste: {str(e)}"
