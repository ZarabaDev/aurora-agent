import os
import sys
from typing import List, Generator, Any, Dict, Union
from dataclasses import dataclass

# Add project root to sys.path if not present
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from tool_loader import load_dynamic_tools
from basic_tools import BASIC_TOOLS
from brain import AgentBrain
from planner import AgentPlanner
from critic import AgentCritic
from memory_tools import MemoryTools

# --- Event Types ---
@dataclass
class AuroraEvent:
    type: str # 'log', 'plan', 'step_start', 'tool_call', 'tool_result', 'thought', 'final_answer', 'error', 'setup_complete'
    content: Any
    metadata: Dict[str, Any] = None

class AuroraEngine:
    def __init__(self):
        self.brain = None
        self.planner = None
        self.critic = None
        self.all_tools = []
        self.chat_history = []
        self.tools_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools_library")

    def initialize(self):
        """Initializes components and loads tools."""
        try:
            self.brain = AgentBrain()
            self.planner = AgentPlanner()
            self.critic = AgentCritic()
            
            # Load Tools
            if not os.path.exists(self.tools_dir):
                os.makedirs(self.tools_dir)
            
            dynamic_tools = load_dynamic_tools(self.tools_dir)
            
            # Initialize Memory Tools
            memory_manager = MemoryTools(self.brain)
            memory_tools = memory_manager.get_tools()
            
            self.all_tools = BASIC_TOOLS + dynamic_tools + memory_tools
            
            return AuroraEvent(type="setup_complete", content=f"Aurora Online. Loaded {len(self.all_tools)} tools.", metadata={"tool_count": len(self.all_tools)})
        
        except Exception as e:
            return AuroraEvent(type="error", content=f"Initialization failed: {e}")

    def refresh_tools(self):
        """Hot reload tools."""
        try:
            dynamic_tools = load_dynamic_tools(self.tools_dir)
            memory_manager = MemoryTools(self.brain)
            memory_tools = memory_manager.get_tools()
            self.all_tools = BASIC_TOOLS + dynamic_tools + memory_tools
        except Exception as e:
            # Non-critical, just log
            pass

    def process_message(self, user_input: str) -> Generator[AuroraEvent, None, None]:
        """
        Main interaction loop. Yields events as they happen.
        """
        self.refresh_tools()
        tools_desc = "\n".join([f"- {t.name}: {t.description}" for t in self.all_tools])
        
        # --- PLANNING ---
        yield AuroraEvent(type="log", content="Planning...")
        try:
            plan_steps, thinking_mode = self.planner.create_plan(user_input, tools_desc)
            
            if len(plan_steps) > 1:
                plan_steps = self.critic.validate_plan(plan_steps, mode=thinking_mode)
            
            yield AuroraEvent(type="plan", content=plan_steps, metadata={"mode": thinking_mode})
        except Exception as e:
            yield AuroraEvent(type="error", content=f"Planning failed: {e}")
            return

        # --- EXECUTION ---
        self.chat_history.append(HumanMessage(content=user_input))
        interaction_responses = []

        for i, step in enumerate(plan_steps):
            yield AuroraEvent(type="step_start", content=step, metadata={"step_index": i+1, "total_steps": len(plan_steps)})
            
            # CRITIC: Skip check
            if interaction_responses and self.critic.should_skip_step(step, interaction_responses, mode=thinking_mode):
                yield AuroraEvent(type="log", content="Step skipped (already done).")
                continue

            step_completed = False
            retries = 0
            max_retries = 5

            step_context = f"""
            ATENÇÃO: MODO DE EXECUÇÃO
            Você está executando o passo {i+1} de {len(plan_steps)}: "{step}".
            
            Objetivo do Usuário Original: "{user_input}"
            Histórico recente já aconteceu. Foco no passo ATUAL.
            
            INSTRUCÕES:
            1. Se precisar fazer algo técnico, USE UMA FERRAMENTA.
            2. Pensamentos internos devem ser discretos.
            3. QUANDO TERMINAR o passo e quiser FALAR com o usuário, inicie a resposta com "STEP_DONE:".
            """
            
            # Temporary context message
            self.chat_history.append(SystemMessage(content=step_context))
            
            while not step_completed and retries < max_retries:
                try:
                    response = self.brain.think(user_input, self.chat_history, tools=self.all_tools)
                except Exception as e:
                    yield AuroraEvent(type="error", content=f"Brain error: {e}")
                    break

                if response.tool_calls:
                    self.chat_history.append(response)
                    
                    for tool_call in response.tool_calls:
                        tool_name = tool_call["name"]
                        tool_args = tool_call["args"]
                        tool_id = tool_call["id"]
                        
                        yield AuroraEvent(type="tool_call", content=tool_name, metadata={"args": tool_args})
                        
                        selected_tool = next((t for t in self.all_tools if t.name == tool_name), None)
                        tool_result = "Error: Tool not found"
                        
                        if selected_tool:
                            try:
                                tool_result = selected_tool.invoke(tool_args)
                            except Exception as e:
                                tool_result = f"Error executing: {e}"
                        
                        yield AuroraEvent(type="tool_result", content=str(tool_result)[:200] + "...", metadata={"full_content": str(tool_result)})
                        
                        self.chat_history.append(ToolMessage(
                            tool_call_id=tool_id,
                            content=str(tool_result),
                            name=tool_name
                        ))
                    
                    retries += 1
                
                else:
                    # Text Response
                    content = response.content
                    if "STEP_DONE" in content.upper():
                        import re
                        clean_content = re.sub(r'step_done:?', '', content, flags=re.IGNORECASE).strip()
                        
                        if clean_content:
                            if self.critic.is_duplicate_response(clean_content, interaction_responses, mode=thinking_mode):
                                yield AuroraEvent(type="log", content="Duplicate response suppressed.")
                            else:
                                interaction_responses.append(clean_content)
                                self.chat_history.append(AIMessage(content=clean_content))
                                yield AuroraEvent(type="final_answer", content=clean_content)
                        else:
                             yield AuroraEvent(type="log", content="Step finished silently.")
                        
                        step_completed = True
                    else:
                        # Internal thought
                        yield AuroraEvent(type="thought", content=content)
                        self.chat_history.append(response)
                        self.chat_history.append(SystemMessage(content="Você não usou 'STEP_DONE'. Se terminou, use 'STEP_DONE:'. Se não, use ferramenta."))
                        retries += 1
