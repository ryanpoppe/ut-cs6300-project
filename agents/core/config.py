from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class LLMConfig:
    model_name: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    api_key: Optional[str] = None
    additional_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolConfig:
    name: str
    enabled: bool = True
    timeout: float = 30.0
    retry_count: int = 3
    additional_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentConfig:
    max_steps: int = 15
    max_retries: int = 3
    enable_logging: bool = True
    stop_on_error: bool = False
    stop_sequences: List[str] = field(default_factory=lambda: ["Final Answer:", "FINAL ANSWER:"])
    tool_configs: List[ToolConfig] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
