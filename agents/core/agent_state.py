from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class Step:
    thought: str
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "thought": self.thought,
            "action": self.action,
            "action_input": self.action_input,
            "observation": self.observation,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Message:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }


class AgentState:
    def __init__(self):
        self.steps: List[Step] = []
        self.messages: List[Message] = []
        self.tool_calls: List[Dict[str, Any]] = []
        self.final_output: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
        self.is_complete: bool = False
        self.error: Optional[str] = None

    def add_step(self, thought: str, action: Optional[str] = None, 
                 action_input: Optional[Dict[str, Any]] = None, 
                 observation: Optional[str] = None):
        step = Step(
            thought=thought,
            action=action,
            action_input=action_input,
            observation=observation
        )
        self.steps.append(step)
        return step

    def add_message(self, role: str, content: str):
        message = Message(role=role, content=content)
        self.messages.append(message)
        return message

    def record_tool_call(self, tool_name: str, tool_input: Dict[str, Any], 
                        tool_output: Any, success: bool = True, 
                        error: Optional[str] = None):
        self.tool_calls.append({
            "tool_name": tool_name,
            "input": tool_input,
            "output": tool_output,
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })

    def set_final_output(self, output: str):
        self.final_output = output
        self.is_complete = True

    def set_error(self, error: str):
        self.error = error
        self.is_complete = True

    def get_trajectory(self) -> List[Dict[str, Any]]:
        return [step.to_dict() for step in self.steps]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "steps": self.get_trajectory(),
            "messages": [msg.to_dict() for msg in self.messages],
            "tool_calls": self.tool_calls,
            "final_output": self.final_output,
            "metadata": self.metadata,
            "is_complete": self.is_complete,
            "error": self.error
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentState":
        state = cls()
        state.final_output = data.get("final_output")
        state.metadata = data.get("metadata", {})
        state.is_complete = data.get("is_complete", False)
        state.error = data.get("error")
        state.tool_calls = data.get("tool_calls", [])
        
        for step_data in data.get("steps", []):
            state.steps.append(Step(
                thought=step_data["thought"],
                action=step_data.get("action"),
                action_input=step_data.get("action_input"),
                observation=step_data.get("observation"),
                timestamp=datetime.fromisoformat(step_data["timestamp"])
            ))
        
        for msg_data in data.get("messages", []):
            state.messages.append(Message(
                role=msg_data["role"],
                content=msg_data["content"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"])
            ))
        
        return state
