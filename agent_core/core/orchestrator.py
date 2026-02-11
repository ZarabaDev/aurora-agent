"""
Orchestrator v5.0 — "Brain + Voice" cognitive architecture.

The Brain (Gemini 3) thinks, decides, and commands.
The Voice (Groq) translates brain instructions into natural speech.
All interactions are logged for later consolidation.

Cognitive Flow:
1. Log Input → record user message
2. Memory Recall → retrieve relevant context
3. Gatekeeper → classify SHALLOW vs DEEP
4. Thinking → always think (depth varies)
5. Execution → tool calls with runtime critique
6. Voice Synthesis → transform brain output into natural speech
7. Log Output → record everything for sleep consolidation
"""

import os
from typing import Generator
from langchain_core.messages import (
    HumanMessage, AIMessage, SystemMessage, ToolMessage,
)

from agent_core.core.events import AuroraEvent
from agent_core.core.memory import MemoryManager
from agent_core.core.interaction_logger import InteractionLogger
from agent_core.modules.cognitive.gatekeeper import Gatekeeper
from agent_core.modules.cognitive.thinker import Thinker
from agent_core.modules.cognitive.critic import Critic
from agent_core.modules.effectors.voice_synthesizer import VoiceSynthesizer
from agent_core.utils.tool_loader import load_dynamic_tools
from agent_core.utils.llm_factory import LLMFactory
from agent_core.utils.soul_loader import load_soul
from agent_core.basic_tools import BASIC_TOOLS
from agent_core.memory_tools import MemoryTools


class Orchestrator:
    def __init__(self):
        self.memory = None
        self.gatekeeper = None
        self.thinker = None
        self.critic = None
        self.voice = None
        self.logger = None
        self.all_tools = []
        self.tools_map = {}
        self.chat_history = []
        self.soul_message = None

        self.tools_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "..", "tools_library"
        )

    def initialize(self) -> AuroraEvent:
        """Initialize all modules and inject soul."""
        try:
            # 1. Logger (first — so we can log init events)
            self.logger = InteractionLogger()

            # 2. Memory
            self.memory = MemoryManager()

            # 3. Tools (basic + dynamic + memory)
            dynamic_tools = load_dynamic_tools(self.tools_dir)
            memory_tools = self._build_memory_tools()
            self.all_tools = BASIC_TOOLS + dynamic_tools + memory_tools
            self.tools_map = {t.name: t for t in self.all_tools}

            # 4. Soul (needs tools list for description)
            self.soul_message = load_soul(
                tools_list=self.all_tools,
                cwd=os.getcwd(),
            )
            self.chat_history = [self.soul_message]

            # 5. Cognitive Modules
            self.gatekeeper = Gatekeeper()
            self.thinker = Thinker()
            self.critic = Critic()

            # 6. Voice Synthesizer (with soul context)
            soul_text = self.soul_message.content if self.soul_message else ""
            self.voice = VoiceSynthesizer(soul_text=soul_text)

            self.logger.log("system", "Aurora v5.0 initialized", {
                "tools_count": len(self.all_tools),
                "memory_available": self.memory.is_available if self.memory else False,
            })

            return AuroraEvent(
                type="setup_complete",
                content=f"Aurora v5.0 Online. {len(self.all_tools)} ferramentas carregadas.",
            )
        except Exception as e:
            return AuroraEvent(type="error", content=f"Init failed: {e}")

    def reset_session(self) -> AuroraEvent:
        """Efficiently resets the session state without reloading heavy modules."""
        try:
            # 1. Reset Chat History to Soul only
            self.chat_history = [self.soul_message] if self.soul_message else []
            
            # 2. Log the reset
            if self.logger:
                self.logger.log("system", "Session reset initiated", {"type": "soft_reset"})
            
            return AuroraEvent(
                type="setup_complete",
                content=f"Sessão reiniciada. {len(self.all_tools)} ferramentas prontas.",
            )
        except Exception as e:
            return AuroraEvent(type="error", content=f"Reset failed: {e}")

    def _build_memory_tools(self):
        """Build memory tools if memory is available."""
        if not self.memory or not self.memory.is_available:
            return []
        mem_tools = MemoryTools(self.memory)
        return mem_tools.get_tools()

    def process_message(self, user_input: str) -> Generator[AuroraEvent, None, None]:
        """Main cognitive loop."""

        # ── 0. Log Input ──
        self.logger.log("user_input", user_input)

        # ── 1. Memory Recall ──
        memory_context = ""
        if self.memory and self.memory.is_available:
            memory_context = self.memory.recall(user_input)
            if memory_context:
                self.logger.log("memory_recall", memory_context[:500])
                yield AuroraEvent(
                    type="log",
                    content="Memórias relevantes encontradas.",
                    metadata={"memory": memory_context},
                )

        # ── 2. Gatekeeper (Intent Classification) ──
        yield AuroraEvent(type="log", content="Classificando intenção...")
        mode = self.gatekeeper.process(
            user_input,
            context={"memory_context": memory_context},
        )
        self.logger.log("gatekeeper", mode)
        yield AuroraEvent(type="log", content=f"Modo: {mode}")

        # ── 3. Thinking (ALWAYS — depth varies) ──
        tools_desc = "\n".join(
            f"- {t.name}: {t.description}" for t in self.all_tools
        )
        soul_text = self.soul_message.content if self.soul_message else ""
        thinking_context = {
            "tools_desc": tools_desc,
            "cwd": os.getcwd(),
            "memory_context": memory_context,
            "soul_text": soul_text,
        }

        plan_steps = []

        if mode == "MODE_DEEP":
            # ── DEEP: Full inner monologue + structured plan ──
            yield AuroraEvent(type="log", content="Pensamento profundo ativado...")

            thinking_result = self.thinker.process(user_input, thinking_context)
            thought_stream = thinking_result.get("thought_stream", "")
            plan_steps = thinking_result.get("plan", [user_input])
            self_notes = thinking_result.get("self_notes", "")

            self.logger.log("thought", thought_stream[:500])
            yield AuroraEvent(type="thought", content=thought_stream)

            if self_notes:
                self.logger.log("self_note", self_notes[:200])
                yield AuroraEvent(
                    type="log",
                    content=f"Auto-nota: {self_notes[:100]}",
                )

            # Critic validates the plan
            plan_steps = self.critic.validate_plan(plan_steps)
            self.logger.log("plan", str(plan_steps))
            yield AuroraEvent(
                type="plan",
                content=plan_steps,
                metadata={"mode": "DEEP"},
            )

        else:
            # ── SHALLOW: Quick reflection before responding ──
            yield AuroraEvent(type="log", content="Reflexão rápida...")

            quick_thought = self.thinker.quick_reflect(
                user_input, thinking_context
            )
            self.logger.log("thought", quick_thought[:300])
            yield AuroraEvent(type="thought", content=quick_thought)

            plan_steps = [user_input]
            yield AuroraEvent(
                type="plan",
                content=plan_steps,
                metadata={"mode": "SHALLOW"},
            )

        # ── 4. Execution Loop (Brain) ──
        self.chat_history.append(HumanMessage(content=user_input))

        if memory_context:
            self.chat_history.append(
                SystemMessage(content=f"[MEMÓRIAS RELEVANTES]\n{memory_context}")
            )

        execution_llm = LLMFactory.get_default_model().bind_tools(self.all_tools)

        brain_instruction = ""
        for i, step in enumerate(plan_steps):
            yield AuroraEvent(
                type="step_start",
                content=step,
                metadata={"step_index": i + 1, "total_steps": len(plan_steps)},
            )

            step_result = yield from self._execute_step(
                step=step,
                goal=user_input,
                execution_llm=execution_llm,
                is_deep=(mode == "MODE_DEEP"),
            )
            
            if step_result and step_result.strip():
                brain_instruction = step_result
            else:
                self.logger.log("warning", f"Step {i+1} returned empty instruction. Keeping previous.")

        # ── 5. Voice Synthesis ──
        if not brain_instruction:
            # Fallback A: No instruction generated
            if memory_context:
                brain_instruction = (
                    f"RESPONSE_INSTRUCTION: O processamento falhou, mas encontrei estas memórias sobre o assunto: "
                    f"'{memory_context[:300]}...'. Use essas informações para responder ao usuário de forma útil, "
                    f"explicando que houve um erro técnico no processamento profundo mas você recuperou isso da memória."
                )
            else:
                brain_instruction = "RESPONSE_INSTRUCTION: Diga ao usuário que houve um erro interno no processamento do pensamento, e por isso você não conseguiu formular uma resposta completa. Peça desculpas e pergunte se ele pode reformular."
        
        elif "RESPONSE_INSTRUCTION:" not in brain_instruction:
            # Fallback B: Raw text returned (likely tool output) without instruction prefix
            # Wrap it in an instruction for the Voice to explain naturally
            brain_instruction = f"RESPONSE_INSTRUCTION: O resultado técnico foi: '{brain_instruction}'. Explique isso ao usuário de forma natural e amigável."

        self.logger.log("brain_instruction", brain_instruction[:500])
        yield AuroraEvent(type="log", content="Sintetizando resposta...")

        final_text = self.voice.synthesize(
            instruction=brain_instruction,
            context={"user_input": user_input},
        )

        self.logger.log("voice_output", final_text[:500])
        yield AuroraEvent(type="final_answer", content=final_text)

        # ── 6. Memory Save (for significant interactions) ──
        if mode == "MODE_DEEP" and self.memory and self.memory.is_available:
            summary = f"User: {user_input[:200]}"
            self.memory.save(summary)

    def _execute_step(
        self, step: str, goal: str, execution_llm, is_deep: bool
    ) -> Generator[AuroraEvent, None, str]:
        """Execute a single step with tool calls. Returns brain instruction."""
        step_completed = False
        retries = 0
        max_retries = 5
        last_result = ""

        while not step_completed and retries < max_retries:
            messages = self.chat_history + [
                SystemMessage(
                    content=(
                        f"PASSO ATUAL: {step}\n"
                        "Execute este passo. Use ferramentas se necessário.\n\n"
                        "IMPORTANTE: Quando terminar, NÃO responda diretamente ao "
                        "usuário. Em vez disso, gere uma INSTRUÇÃO descrevendo o que "
                        "a Aurora deve dizer ao usuário. Use o formato:\n"
                        "RESPONSE_INSTRUCTION: <instrução detalhada do que responder>\n\n"
                        "Exemplo: RESPONSE_INSTRUCTION: Cumprimente o usuário "
                        "casualmente, diga que está tudo bem, pergunte o que ele "
                        "precisa hoje. Mencione que tem X ferramentas disponíveis.\n\n"
                        "A instrução deve conter TODAS as informações necessárias "
                        "para gerar a resposta (dados, resultados de ferramentas, "
                        "números, etc). Outro modelo vai transformar essa instrução "
                        "em uma fala natural."
                    )
                ),
            ]

            try:
                response = execution_llm.invoke(messages)
                self.chat_history.append(response)

                if response.tool_calls:
                    for tool_call in response.tool_calls:
                        tool_name = tool_call["name"]
                        tool_args = tool_call["args"]

                        self.logger.log("tool_call", tool_name, {"args": tool_args})
                        yield AuroraEvent(
                            type="tool_call",
                            content=tool_name,
                            metadata={"args": tool_args},
                        )

                        tool = self.tools_map.get(tool_name)
                        result = "Ferramenta não encontrada."
                        if tool:
                            try:
                                result = tool.invoke(tool_args)
                            except Exception as e:
                                result = f"Erro na ferramenta: {e}"

                        last_result = str(result)
                        self.logger.log("tool_result", last_result[:300], {
                            "tool": tool_name,
                        })
                        yield AuroraEvent(
                            type="tool_result",
                            content=last_result[:200],
                            metadata={"full_content": last_result},
                        )

                        self.chat_history.append(
                            ToolMessage(
                                tool_call_id=tool_call["id"],
                                content=last_result,
                                name=tool_name,
                            )
                        )

                else:
                    content = response.content or ""

                    if "RESPONSE_INSTRUCTION:" in content:
                        instruction = content.split(
                            "RESPONSE_INSTRUCTION:", 1
                        )[1].strip()
                        last_result = instruction

                        # ── Runtime Critique (DEEP mode only) ──
                        if is_deep:
                            critique = self.critic.critique_step(
                                step=step,
                                result=instruction[:500],
                                goal=goal,
                            )
                            quality = critique.get("quality", "acceptable")
                            feedback = critique.get("feedback", "")

                            self.logger.log("critique", f"{quality}: {feedback}")
                            yield AuroraEvent(
                                type="thought",
                                content=f"[Crítica] {quality}: {feedback}",
                            )

                            if quality == "needs_retry" and retries < max_retries - 1:
                                yield AuroraEvent(
                                    type="log",
                                    content=f"Retry: {feedback}",
                                )
                                retries += 1
                                continue

                        step_completed = True

                    elif "STEP_DONE" in content:
                        # Backward compat: handle old format
                        final_text = content.replace("STEP_DONE:", "").strip()
                        last_result = final_text
                        step_completed = True

                    else:
                        retries += 1

            except Exception as e:
                self.logger.log("error", f"Execution error: {e}")
                yield AuroraEvent(type="error", content=f"Erro na execução: {e}")
                break

        if not step_completed and retries >= max_retries:
             self.logger.log("warning", f"Max retries ({max_retries}) reached for step: {step}")
             yield AuroraEvent(type="log", content="Limite de tentativas atingido para este passo.")

        return last_result
