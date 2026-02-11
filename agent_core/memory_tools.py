"""
MemoryTools v4.0 — LangChain StructuredTools that wrap MemoryManager.
These are loaded by the Orchestrator and made available to the LLM.
"""

from typing import List
from langchain_core.tools import StructuredTool


class MemoryTools:
    def __init__(self, memory_manager):
        self.memory = memory_manager

    def save_interaction(self, content: str) -> str:
        """
        Salva uma informação importante, fato ou aprendizado na memória de longo prazo.
        Use quando o usuário pedir para lembrar algo, ou quando aprender uma preferência.

        Args:
            content: O texto a ser salvo. Seja específico e inclua contexto.
        """
        try:
            self.memory.save(content)
            return f"✓ Memória salva: '{content}'"
        except Exception as e:
            return f"Erro ao salvar memória: {e}"

    def search_history(self, query: str) -> str:
        """
        Busca por memórias antigas, fatos ou preferências salvas no passado.
        Use quando precisar lembrar algo que não está no contexto atual.

        Args:
            query: A pergunta ou termo de busca para encontrar a memória.
        """
        try:
            results = self.memory.recall(query)
            if not results:
                return "Nenhuma memória relevante encontrada."
            return results
        except Exception as e:
            return f"Erro ao buscar memória: {e}"

    def forget_interaction(self, query: str) -> str:
        """
        Apaga memórias sobre um tópico. Use se o usuário disser que algo mudou.

        Args:
            query: O conteúdo ou tópico a ser esquecido.
        """
        try:
            return self.memory.forget(query)
        except Exception as e:
            return f"Erro ao esquecer memória: {e}"

    def get_tools(self) -> List[StructuredTool]:
        """Returns LangChain tools for the Orchestrator to load."""
        return [
            StructuredTool.from_function(
                func=self.save_interaction,
                name="save_memory",
                description="Salva uma informação importante na memória permanente.",
            ),
            StructuredTool.from_function(
                func=self.search_history,
                name="search_memory",
                description="Pesquisa na memória de longo prazo. Para melhores resultados, use perguntas naturais e específicas em vez de palavras-chave soltas. Exemplo: 'O que o usuário gosta de comer?' ou 'Resumo do projeto Aurora'.",
            ),
            StructuredTool.from_function(
                func=self.forget_interaction,
                name="forget_memory",
                description="Apaga informações da memória de longo prazo.",
            ),
        ]
