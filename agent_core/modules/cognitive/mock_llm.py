from typing import Any, List, Optional
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableSerializable

# Shared state at module level to avoid Pydantic issues
FAST_RESPONSES = [
    "STATUS: DONE",              # Test 1 Gatekeeper (FAST) -> "MODE_FAST"
    "STATUS: DONE",              # Test 1 Critic (Success)
    "STATUS: DONE. MODE_DEEP",   # Test 2 Gatekeeper (DEEP) -> "MODE_DEEP"
    "STATUS: DONE"               # Test 2 Critic (Success)
]
FAST_INDEX = 0

REASONING_RESPONSES = [
    "STEP_DONE: Hello.", # Test 1 Execution (Orchestrator)
    # Test 2 Thinker (JSON Plan)
    """{
        "thought_stream": "Thinking...", 
        "plan": ["Step 1"]
    }""",
    "STEP_DONE: Task Done." # Test 2 Execution (Orchestrator)
]
REASONING_INDEX = 0

class MockFastRunnable(RunnableSerializable):
    class Config:
        arbitrary_types_allowed = True

    def invoke(self, input: Any, config: Optional[Any] = None) -> AIMessage:
        global FAST_INDEX
        if len(FAST_RESPONSES) == 0:
            return AIMessage(content="STATUS: DONE")
            
        idx = FAST_INDEX % len(FAST_RESPONSES)
        response = FAST_RESPONSES[idx]
        FAST_INDEX += 1
        return AIMessage(content=response)

    def bind_tools(self, tools: Any, **kwargs):
        return self

class MockReasoningRunnable(RunnableSerializable):
    class Config:
        arbitrary_types_allowed = True

    def invoke(self, input: Any, config: Optional[Any] = None) -> AIMessage:
        global REASONING_INDEX
        if len(REASONING_RESPONSES) == 0:
             return AIMessage(content="STEP_DONE: Done.")
             
        idx = REASONING_INDEX % len(REASONING_RESPONSES)
        response = REASONING_RESPONSES[idx]
        REASONING_INDEX += 1
        return AIMessage(content=response)

    def bind_tools(self, tools: Any, **kwargs):
        return self

class MockLLM:
    """Simulates LLM responses for testing cognitive flow."""
    
    @staticmethod
    def get_fast_model():
        return MockFastRunnable()

    @staticmethod
    def get_reasoning_model():
        return MockReasoningRunnable()
