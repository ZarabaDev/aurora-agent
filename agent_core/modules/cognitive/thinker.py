"""
Thinker v4.1 — Deep reasoning module using Groq Llama.

Generates structured inner monologue + actionable plan.
Soul is injected into the thinking prompt.
"""

import json
import re
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
            memory_block = f"\n[MEMÓRIAS RELEVANTES]\n{memory}\n"

        system_prompt = """{soul}

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
{{
    "thought_stream": "Seu monólogo interno. Comente sobre a tarefa, critique a abordagem, pense alto como uma voz na cabeça.",
    "plan": [
        "Passo 1: Descrição clara da ação",
        "Passo 2: Próxima ação..."
    ],
    "self_notes": "Notas para sua própria evolução ou lembretes (opcional)"
}}"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        chain = prompt | self.llm

        try:
            response = chain.invoke({
                "input": user_input,
                "soul": soul,
                "cwd": cwd,
                "memory_block": memory_block,
                "tools_desc": tools_desc
            })
            content = response.content.strip()
            result = self._extract_json(content)

            if result:
                # Garante que as chaves obrigatórias existam
                result.setdefault("thought_stream", "")
                result.setdefault("plan", [user_input])
                result.setdefault("self_notes", "")
                return result

            # Fallback: não conseguiu parsear, mas retorna o conteúdo bruto
            return {
                "thought_stream": content[:800],
                "plan": [user_input],
                "self_notes": "LLM retornou texto livre em vez de JSON",
            }

        except Exception as e:
            return {
                "thought_stream": f"Erro durante pensamento profundo: {e}",
                "plan": [f"Responder diretamente: {user_input}"],
                "self_notes": f"Erro no Thinker: {e}",
            }

    def _extract_json(self, content: str) -> dict | None:
        """
        Tenta extrair JSON estruturado do output do LLM usando múltiplas estratégias.
        Retorna dict se encontrar, None se falhar.
        """
        # Estratégia 1: Regex para code block ```json ... ```
        code_block_match = re.search(r'```(?:json)?\s*\n?(\{.*?\})\s*```', content, re.DOTALL)
        if code_block_match:
            try:
                return json.loads(code_block_match.group(1))
            except json.JSONDecodeError:
                pass

        # Estratégia 2: JSON object solto { ... } (mais externo)
        brace_match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})', content, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(1))
            except json.JSONDecodeError:
                pass

        # Estratégia 3: Limpeza agressiva e retry
        cleaned = self._clean_json_string(content)
        if cleaned:
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass

        return None

    @staticmethod
    def _clean_json_string(content: str) -> str | None:
        """Remove artefatos comuns que quebram o JSON parse."""
        # Tenta encontrar o bloco JSON mais externo
        start = content.find('{')
        end = content.rfind('}')
        if start == -1 or end == -1 or end <= start:
            return None

        raw = content[start:end + 1]

        # Remove trailing commas antes de } ou ]
        raw = re.sub(r',\s*([}\]])', r'\1', raw)
        # Remove comments single-line
        raw = re.sub(r'//.*?$', '', raw, flags=re.MULTILINE)

        return raw

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
