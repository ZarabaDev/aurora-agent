# agent_core/critic.py
import os
import json
from enum import Enum
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

class ThinkingMode(Enum):
    FAST = "FAST"
    DEEP = "DEEP"

class AgentCritic:
    def __init__(self):
        """
        Initializes the Critic with multi-model support.
        FAST: Groq (Llama 3 70B) - Ultra low latency
        DEEP: OpenRouter (DeepSeek R1) - High reasoning
        """
        self.fast_llm = self._init_fast_model()
        self.deep_llm = self._init_deep_model()
        
    def _init_fast_model(self):
        """Initializes Groq model for speed."""
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            try:
                return ChatGroq(
                    temperature=0.0,
                    model_name="llama-3.1-8b-instant",
                    groq_api_key=api_key,
                    max_tokens=300
                )
            except Exception as e:
                print(f"[Critic] Groq init failed: {e}. Falling back to OpenRouter.")
        
        # Fallback to OpenRouter Llama
        return ChatOpenAI(
            model="meta-llama/llama-3.2-3b-instruct:free",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            temperature=0.1,
            max_tokens=300
        )

    def _init_deep_model(self):
        """Initializes DeepSeek/OpenRouter model for reasoning."""
        return ChatOpenAI(
            model="tngtech/deepseek-r1t2-chimera:free",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            temperature=0.1,
            max_tokens=500,
            request_timeout=30
        )

    def _get_llm(self, mode: str):
        if mode == ThinkingMode.DEEP.value:
            return self.deep_llm
        return self.fast_llm

    def validate_plan(self, steps: list, mode: str = "FAST") -> list:
        """
        Analyzes a plan and fuses redundant/overlapping steps.
        """
        if len(steps) <= 1:
            return steps
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a plan optimizer. Remove redundant steps and merge duplicates.
            Return ONLY a valid JSON array of strings."""),
            ("human", "Optimize this plan:\n{steps_json}")
        ])
        
        try:
            llm = self._get_llm(mode)
            chain = prompt | llm
            response = chain.invoke({"steps_json": json.dumps(steps, ensure_ascii=False)})
            content = response.content.strip()
            
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            optimized = json.loads(content)
            if isinstance(optimized, list) and len(optimized) > 0:
                return optimized
        except Exception as e:
            print(f"[Critic] Plan validation ({mode}) failed: {e}")
        
        return steps

    def should_skip_step(self, step: str, recent_messages: list, mode: str = "FAST") -> bool:
        """Determines if a step has already been accomplished."""
        if not recent_messages:
            return False
            
        context = "\n".join(recent_messages[-3:])
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You determine if a task step has already been completed.
            Answer ONLY "YES" or "NO".
            YES = Step is CLEARLY done.
            NO = Step still needs action."""),
            ("human", """Step: "{step}"
            Recent Output:
            {context}
            
            Completed?""")
        ])
        
        try:
            llm = self._get_llm(mode)
            response = chain = prompt | llm
            response = chain.invoke({"step": step, "context": context})
            return "YES" in response.content.strip().upper()
        except Exception as e:
            print(f"[Critic] Skip check ({mode}) failed: {e}")
            return False

    def is_duplicate_response(self, new_response: str, previous_responses: list, mode: str = "FAST") -> bool:
        """Checks for duplicate content."""
        if not previous_responses:
            return False
            
        # Fast heuristic first
        for prev in previous_responses:
            if new_response == prev: return True
            if len(new_response) > 50 and len(prev) > 50 and new_response[:50] == prev[:50]:
                return True
        
        # LLM check
        context = "\n---\n".join(previous_responses[-2:])
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Detect duplicate messages. Answer ONLY "DUPLICATE" or "NEW"."""),
            ("human", """Previous:
            {context}
            
            New:
            {new_response}
            
            Is duplicate?""")
        ])
        
        try:
            llm = self._get_llm(mode)
            response = chain = prompt | llm
            response = chain.invoke({"context": context, "new_response": new_response})
            return "DUPLICATE" in response.content.strip().upper()
        except Exception as e:
            print(f"[Critic] Duplicate check ({mode}) failed: {e}")
            return False
