from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from .agent_state import AgentState


class BaseAgent(ABC):
    def __init__(self):
        self.state: AgentState = AgentState()

    @abstractmethod
    def plan(self, input_data: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def act(self, action: str, action_input: Dict[str, Any]) -> Any:
        pass

    @abstractmethod
    def observe(self, action_result: Any) -> str:
        pass

    @abstractmethod
    def run(self, input_data: str) -> str:
        pass

    def reset(self):
        self.state = AgentState()

    def get_state(self) -> AgentState:
        return self.state
