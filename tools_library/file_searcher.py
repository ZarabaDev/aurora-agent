import os

TOOL_DESC = "Busca arquivos recursivamente a partir do diretório atual. Uso: 'nome_do_arquivo' ou '*.extensao'"

def run(input_str):
    search_term = input_str.strip()
    matches = []
    
    # Define o ponto de partida (root do projeto)
    start_dir = "/home/zarabatana/Documentos/aurora"
    
    try:
        for root, dirs, files in os.walk(start_dir):
            for file in files:
                # Busca simples (contém o termo ou padrão básico de asterisco)
                if search_term.startswith('*.'):
                    extension = search_term[2:]
                    if file.endswith(extension):
                        matches.append(os.path.join(root, file))
                elif search_term in file:
                    matches.append(os.path.join(root, file))
        
        if not matches:
            return f"Nenhum arquivo encontrado para: '{search_term}'"
            
        return "Arquivos encontrados:\n" + "\n".join(matches)
        
    except Exception as e:
        return f"Erro na busca: {str(e)}"
