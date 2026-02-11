from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class AuroraEvent:
    type: str  # 'log', 'plan', 'step_start', 'tool_call', 'tool_result', 'thought', 'final_answer', 'error', 'setup_complete'
    content: Any
    metadata: Dict[str, Any] = None
