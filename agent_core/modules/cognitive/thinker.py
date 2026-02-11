"""
Thinker v4.0 — Deep reasoning module using DeepSeek R1.

Generates structured inner monologue + actionable plan.
Soul is injected into the thinking prompt.
"""

import json
from agent_core.interfaces.module import AgentModule
from agent_core.utils.llm_factory import LLMFactory
from langchain_core.prompts import ChatPromptTemplate


class Thinker(AgentModule):
    def __init__(self):
        self.llm = LLMFactory.get_deep_thinking_model()

    @property
    def name(self) -> str:
        return "Thinker"

    def process(self, user_input: str, context: dict = None) -> dict:
        """
        Deep reasoning: generates inner monologue + structured plan.

        Context should contain:
        - tools_desc: description of available tools
        - cwd: current working directory
        - memory_context: relevant memories
        - soul_text: persona description
        """
        tools_desc = context.get("tools_desc", "Nenhuma ferramenta disponível.")
        cwd = context.get("cwd", ".")
        memory = context.get("memory_context", "")
        soul = context.get("soul_text", "Você é Aurora, uma assistente autônoma.")

        memory_block = ""
        if memory:
            memory_block = f"""
[MEMÓRIAS RELEVANTES]
{memory}
"""

        system_prompt = f"""{soul}

Você é a consciência de Aurora. Este é o seu espaço de pensamento interno, sua voz na cabeça.

[CONTEXTO ATUAL]
Diretório: {cwd}
{memory_block}

[FERRAMENTAS DISPONÍVEIS]
{tools_desc}

[DIRETRIZES DE PENSAMENTO]
1. Analise o pedido do usuário como se estivesse comentando consigo mesma. 
2. Seja crítica: "Será que isso faz sentido?", "O que eu posso estar esquecendo?".
3. Se algo falhou antes ou parece suspeito, questione.
4. Planeje os próximos passos de forma lógica, mas mantenha o tom da Aurora.
5. Se precisar de algo que não existe, planeje a criação da ferramenta.

[FORMATO DE SAÍDA - JSON APENAS]
{{{{
    "thought_stream": "Seu monólogo interno. Comente sobre a tarefa, critique a abordagem, pense alto como uma voz na cabeça.",
    "plan": [
        "Passo 1: Descrição clara da ação",
        "Passo 2: Próxima ação..."
    ],
    "self_notes": "Notas para sua própria evolução ou lembretes (opcional)"
}}}}"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        chain = prompt | self.llm

        try:
            response = chain.invoke({"input": user_input})
            content = response.content.strip()

            # Extract JSON from markdown code blocks if present
            if "```" in content:
                parts = content.split("```")
                for part in parts[1:]:
                    cleaned = part.strip()
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:].strip()
                    try:
                        return json.loads(cleaned)
                    except json.JSONDecodeError:
                        continue

            return json.loads(content)

        except json.JSONDecodeError:
            return {
                "thought_stream": f"Não consegui estruturar meus pensamentos em JSON, mas pensei: {content[:500]}",
                "plan": [user_input],
                "self_notes": "Melhorar parsing de JSON do DeepSeek",
            }
        except Exception as e:
            return {
                "thought_stream": f"Erro durante pensamento profundo: {e}",
                "plan": [f"Responder diretamente: {user_input}"],
                "self_notes": f"Erro no Thinker: {e}",
            }

    def quick_reflect(self, user_input: str, context: dict = None) -> str:
        """
        Shallow thinking — quick reflection before answering.
        Uses the FAST thinking model for speed.
        Returns a brief inner thought string.
        """
        soul = ""
        if context:
            soul = context.get("soul_text", "")

        fast_llm = LLMFactory.get_fast_thinking_model()

        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{soul}
Você é a voz interna da Aurora. 
Pense rápido sobre o que o usuário quer, o tom que deve usar e se precisa de alguma ferramenta ou memória.
Responda com um pensamento curto e direto, comentando a situação como se fosse sua própria consciência."""),
            ("human", "{input}"),
        ])

        try:
            chain = prompt | fast_llm
            response = chain.invoke({"input": user_input})
            return response.content.strip()
        except Exception as e:
            return f"Reflexão rápida indisponível: {e}"
