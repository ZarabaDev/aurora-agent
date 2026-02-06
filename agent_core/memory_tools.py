from langchain_core.tools import tool
from typing import List
from langchain_core.tools import StructuredTool

class MemoryTools:
    def __init__(self, brain):
        self.brain = brain

    def save_interaction(self, content: str) -> str:
        """
        Salva uma informação importante, fato ou aprendizado na memória de longo prazo (permanente).
        Use isso quando o usuário pedir para lembrar algo, ou quando você aprender uma preferência do usuário.
        
        Args:
            content: O texto a ser salvo. Seja específico e inclua contexto.
        """
        try:
            self.brain.save_memory(content)
            return f"Memória salva com sucesso: '{content}'"
        except Exception as e:
            return f"Erro ao salvar memória: {e}"

    def search_history(self, query: str) -> str:
        """
        Busca explicitamente por memórias antigas, fatos ou preferências salvas no passado.
        Use isso quando precisar lembrar de algo que não está no contexto atual.
        
        Args:
            query: A pergunta ou termo de busca para encontrar a memória.
        """
        try:
            results = self.brain.recall_memories(query)
            if not results:
                return "Nenhuma memória relevante encontrada para essa busca."
            return results
        except Exception as e:
            return f"Erro ao buscar memória: {e}"



    def forget_interaction(self, query: str) -> str:
        """
        Apaga memórias antigas. Use isso se o usuário disser que algo mudou ou pedir para esquecer.
        
        Args:
            query: O conteúdo ou tópico a ser esquecido.
        """
        try:
            return self.brain.forget_memory(query)
        except Exception as e:
            return f"Erro ao esquecer memória: {e}"

    def get_tools(self) -> List[StructuredTool]:
        return [
            StructuredTool.from_function(
                func=self.save_interaction,
                name="save_memory",
                description="Salva uma informação importante na memória permanente (longo prazo)."
            ),
            StructuredTool.from_function(
                func=self.search_history,
                name="search_memory",
                description="Pesquisa na memória de longo prazo por informações salvas anteriormente."
            ),
            StructuredTool.from_function(
                 func=self.forget_interaction,
                 name="forget_memory",
                 description="Apaga informações da memória de longo prazo."
            )
        ]
