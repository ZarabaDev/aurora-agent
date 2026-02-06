# agent_core/planner.py
import json
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

class AgentPlanner:
    def __init__(self, model_name="google/gemini-3-flash-preview"):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
             # Just a warning here, main.py or brain.py handles the hard error usually
            print("Warning: OPENROUTER_API_KEY not set for Planner")

        # Hack for langchain validation
        os.environ["OPENAI_API_KEY"] = api_key if api_key else "dummy"

        self.llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            openai_api_base="https://openrouter.ai/api/v1",
             model_kwargs={
                "response_format": { "type": "json_object" }
            }
        )

    def create_plan(self, user_objective: str, tools_overview: str) -> list:
        """
        Decomposes the user objective into a sequential list of steps.
        Returns a list of strings, where each string is a step.
        """
        
        system_prompt = f"""
        You are the Planner for an autonomous agent.
        Your goal is to break down a complex user request into small, executable steps AND decide the thinking mode.
        
        AVAILABLE TOOLS:
        {tools_overview}
        
        THINKING MODES:
        - "FAST": For simple queries, chitchat, or tasks that need speed (e.g. "Hi", "Check file").
        - "DEEP": For complex logic, coding, security checks, or dangerous actions.
        
        OUTPUT FORMAT:
        You must output a valid JSON object with "steps" (list) and "thinking_mode" (string).
        Example:
        {{{{
          "thinking_mode": "FAST",
          "steps": [
             "Reply to the user greeting."
          ]
        }}}}
        
        CRITICAL INSTRUCTIONS:
        1. If user says "Hi", "Hello", "How are you?", use FAST mode.
        2. If user asks for code, script, or analysis, use DEEP mode.
        3. Do NOT 'overthink' simple social interactions.
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{objective}")
        ])
        
        chain = prompt | self.llm
        
        try:
            response = chain.invoke({"objective": user_objective})
            content = response.content
            # Clean markdown code blocks if present
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            plan_data = json.loads(content)
            return plan_data.get("steps", []), plan_data.get("thinking_mode", "FAST")
        except Exception as e:
            print(f"Error creating plan: {e}")
            # Fallback plan
            return [f"Error planning: {e}. Just try to answer the user directly."], "FAST"
