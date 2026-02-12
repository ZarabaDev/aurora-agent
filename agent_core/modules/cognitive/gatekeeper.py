"""
Gatekeeper v4.0 — Intent classifier with memory context awareness.

Classifies user input into SHALLOW (quick thought) or DEEP (deep reasoning).
Now receives memory context to make smarter decisions.
"""

from agent_core.interfaces.module import AgentModule
from agent_core.utils.llm_factory import LLMFactory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class Gatekeeper(AgentModule):
    def __init__(self):
        self.llm = LLMFactory.get_fast_thinking_model()

    @property
    def name(self) -> str:
        return "Gatekeeper"

    def process(self, user_input: str, context: dict = None) -> str:
        """
        Classifies intent: MODE_SHALLOW or MODE_DEEP.
        Context may contain 'memory_context' for smarter decisions.
        """
        memory_hint = ""
        if context and context.get("memory_context"):
            memory_hint = f"\n[MEMÓRIAS RELEVANTES]\n{context['memory_context']}\n"

        system_prompt = """You are the Gatekeeper of an AI Agent called Aurora.
Classify the User Input into one of two modes:

1. MODE_SHALLOW: Simple greetings, quick factual questions, thanks, small talk.
   Examples: "Oi", "Obrigado", "Que horas são?"

2. MODE_DEEP: ANY of these triggers → MODE_DEEP:
   - Tasks requiring tools (file operations, code, search)
   - Identity questions ("Quem é você?", "O que você sabe fazer?")
   - Complex reasoning, analysis, planning
   - Multi-step problems
   - Self-improvement or tool creation requests
   - Anything referencing memory or past interactions
   
   Examples: "Escreva um script", "Quem é você?", "Crie uma ferramenta", "O que conversamos ontem?"

{memory_hint}
OUTPUT ONLY: MODE_SHALLOW or MODE_DEEP"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])

        try:
            chain = prompt | self.llm | StrOutputParser()
            result = chain.invoke({"input": user_input, "memory_hint": memory_hint})
            decision = result.strip().upper() if isinstance(result, str) else str(result).strip().upper()

            if "DEEP" in decision:
                return "MODE_DEEP"
            return "MODE_SHALLOW"
        except Exception as e:
            print(f"[Gatekeeper] Error: {e}")
            # Default to DEEP on error (safer — thinks more, not less)
            return "MODE_DEEP"
