from typing import Any, Callable, Dict, List, Optional
from abc import ABC, abstractmethod


class Tool(ABC):
    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        self.name = name
        self.description = description
        self.parameters = parameters
    
    @abstractmethod
    def run(self, **kwargs) -> Any:
        pass
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        required_params = [
            k for k, v in self.parameters.items() 
            if v.get("required", False)
        ]
        return all(param in input_data for param in required_params)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class FunctionTool(Tool):
    def __init__(self, 
                 name: str, 
                 description: str, 
                 parameters: Dict[str, Any],
                 func: Callable):
        super().__init__(name, description, parameters)
        self.func = func
    
    def run(self, **kwargs) -> Any:
        if not self.validate_input(kwargs):
            raise ValueError(f"Invalid input for tool {self.name}")
        return self.func(**kwargs)


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool):
        self._tools[tool.name] = tool
    
    def unregister(self, tool_name: str):
        if tool_name in self._tools:
            del self._tools[tool_name]
    
    def get_tool(self, tool_name: str) -> Optional[Tool]:
        return self._tools.get(tool_name)
    
    def get_all_tools(self) -> List[Tool]:
        return list(self._tools.values())
    
    def get_tool_descriptions(self) -> List[Dict[str, Any]]:
        return [tool.to_dict() for tool in self._tools.values()]
    
    def has_tool(self, tool_name: str) -> bool:
        return tool_name in self._tools
    
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found in registry")
        return tool.run(**kwargs)
    
    def clear(self):
        self._tools.clear()
