from abc import ABC, abstractmethod
from typing import Any, Dict

class AgentModule(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass
        
    @abstractmethod
    def process(self, input_data: Any, context: Dict[str, Any] = None) -> Any:
        pass
