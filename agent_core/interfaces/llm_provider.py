from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = None, tools: List[Any] = None) -> Any:
        pass
        
    @abstractmethod
    def generate_json(self, prompt: str, system_prompt: str = None) -> Dict[str, Any]:
        pass
