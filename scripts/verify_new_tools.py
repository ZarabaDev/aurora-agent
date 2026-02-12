import sys
import os

# Adiciona o diretório do projeto ao path para importar o tool_loader
sys.path.append(os.getcwd())

from agent_core.utils.tool_loader import load_dynamic_tools

tools_dir = os.path.join(os.getcwd(), "tools_library")
tools = load_dynamic_tools(tools_dir)

print(f"\n--- Relatório de Carregamento de Ferramentas ---")
print(f"Total de ferramentas dinâmicas: {len(tools)}")

for t in tools:
    print(f"\n[OK] Ferramenta: {t.name}")
    print(f"     Descrição: {t.description}")

# Verifica especificamente as novas
novas = ["github_manager", "github_pr", "devops_automation"]
carregadas = [t.name for t in tools]

faltando = [n for n in novas if n not in carregadas]

if not faltando:
    print("\n✅ Todas as novas ferramentas foram carregadas com sucesso!")
else:
    print(f"\n❌ Algumas ferramentas falharam: {faltando}")
