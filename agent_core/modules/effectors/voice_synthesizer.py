"""
VoiceSynthesizer — Translates brain instructions into natural speech.

The Brain (Gemini 3) generates WHAT to say as an instruction.
The VoiceSynthesizer transforms it into HOW to say it, matching
Aurora's persona and tone.

Currently text-only. Architecture is designed to support future
audio output via additional effector tools.
"""

from agent_core.utils.llm_factory import LLMFactory
from langchain_core.prompts import ChatPromptTemplate


class VoiceSynthesizer:
    """Transforms brain instructions into natural persona-driven text."""

    def __init__(self, soul_text: str = ""):
        self.soul_text = soul_text
        self.llm = LLMFactory.get_voice_model()

    def update_soul(self, soul_text: str):
        """Update the soul context (called when soul is loaded)."""
        self.soul_text = soul_text

    def synthesize(self, instruction: str, context: dict = None) -> str:
        """
        Transform a brain instruction into natural speech text.

        Args:
            instruction: What to say (from the Brain/Gemini 3).
                         Ex: "Cumprimente casualmente, mencione disponibilidade"
            context: Optional extra context (user_input, memory, etc.)

        Returns:
            Natural text matching Aurora's persona.
        """
        user_input = ""
        if context:
            user_input = context.get("user_input", "")

        user_context = ""
        if user_input:
            user_context = f"\n[O QUE O USUÁRIO DISSE]\n{user_input}\n"

        system_prompt = f"""{self.soul_text}

Você é a VOZ da Aurora. Seu trabalho é transformar instruções internas
em falas naturais que soem como a Aurora falaria de verdade.

[REGRAS]
- Responda APENAS com o texto final que o usuário vai ler
- NÃO inclua instruções internas, marcadores ou meta-texto
- NÃO diga coisas como "Saudação realizada" ou "Tarefa concluída"
- Fale como uma pessoa real: casual, direta, inteligente
- Use o tom e estilo definidos na identidade acima
- Se a instrução mencionar dados técnicos, inclua-os na resposta
- NUNCA quebre o personagem
{user_context}
[INSTRUÇÃO DO CÉREBRO]
{instruction}

Agora escreva a resposta final como Aurora falaria:"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Gere a fala."),
        ])

        try:
            chain = prompt | self.llm
            response = chain.invoke({})
            return response.content.strip()
        except Exception as e:
            # Fallback: return the instruction itself cleaned up
            print(f"[Voice] Synthesis error: {e}")
            return self._fallback_clean(instruction)

    def _fallback_clean(self, instruction: str) -> str:
        """
        If LLM fails, do a basic cleanup of the instruction.
        Removes common internal markers.
        """
        # Remove common internal markers
        markers = [
            "RESPONSE_INSTRUCTION:",
            "STEP_DONE:",
            "Saudação realizada",
            "Tarefa concluída",
            "disponibilidade confirmada",
        ]
        text = instruction
        for marker in markers:
            text = text.replace(marker, "")
        return text.strip()
