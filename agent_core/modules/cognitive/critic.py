"""
Critic v4.0 — Runtime critique module.

Validates plans, checks step completion, and provides
runtime quality assessment after each execution step.
"""

import json
from langchain_core.prompts import ChatPromptTemplate
from agent_core.interfaces.module import AgentModule
from agent_core.utils.llm_factory import LLMFactory


class Critic(AgentModule):
    def __init__(self):
        self.fast_llm = LLMFactory.get_fast_thinking_model()

    @property
    def name(self) -> str:
        return "Critic"

    def process(self, input_data: dict, context: dict = None) -> dict:
        """
        Generic process method.
        Expects input_data to have 'action' key:
        - 'validate_plan': Optimize and merge steps.
        - 'critique_step': Review quality of a completed step.
        """
        action = input_data.get("action")

        if action == "validate_plan":
            return self.validate_plan(input_data.get("steps", []))
        elif action == "critique_step":
            return self.critique_step(
                step=input_data.get("step", ""),
                result=input_data.get("result", ""),
                goal=input_data.get("goal", ""),
            )

        return {"error": "Unknown action"}

    def validate_plan(self, steps: list) -> list:
        """Optimizes a plan by removing redundant steps."""
        if len(steps) <= 1:
            return steps

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a plan optimizer for an AI agent.
Remove redundant steps, merge duplicates, and ensure logical order.
Return ONLY a valid JSON array of strings. No explanation."""),
            ("human", "Optimize this plan:\n{steps}"),
        ])

        try:
            chain = prompt | self.fast_llm
            response = chain.invoke({"steps": json.dumps(steps)})
            content = response.content.strip()

            if "```" in content:
                content = content.split("```")[1]
                if content.strip().startswith("json"):
                    content = content.strip()[4:]

            optimized = json.loads(content.strip())
            return optimized if isinstance(optimized, list) else steps
        except Exception:
            return steps

    def critique_step(self, step: str, result: str, goal: str) -> dict:
        """
        Runtime critique: evaluates the quality of a completed step.
        Returns: {quality: 'good'|'needs_retry'|'acceptable', feedback: str}
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the Critic module of Aurora, an AI agent.
Evaluate if an execution step achieved its goal.

Respond in VALID JSON only:
{{"quality": "good" | "needs_retry" | "acceptable", "feedback": "Brief critique in Portuguese"}}

Rules:
- "good": Step fully achieved the goal
- "acceptable": Partially done, move on
- "needs_retry": Critical failure, must retry"""),
            ("human", """Goal: {goal}
Step: {step}
Result: {result}

Evaluate:"""),
        ])

        try:
            chain = prompt | self.fast_llm
            response = chain.invoke({
                "goal": goal,
                "step": step,
                "result": result[:500],
            })
            content = response.content.strip()

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
        except Exception as e:
            return {"quality": "acceptable", "feedback": f"Crítica indisponível: {e}"}
