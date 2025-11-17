from typing import Any, Callable, Dict, List, Optional
from abc import ABC, abstractmethod
from langchain_core.tools import BaseTool as LangChainBaseTool
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, create_model


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
    
    def to_langchain_tool(self) -> LangChainBaseTool:
        fields = {}
        for param_name, param_spec in self.parameters.items():
            param_type = param_spec.get("type", "string")
            param_desc = param_spec.get("description", "")
            is_required = param_spec.get("required", False)
            
            if param_type == "string":
                field_type = str
            elif param_type == "integer":
                field_type = int
            elif param_type == "boolean":
                field_type = bool
            elif param_type == "array":
                items_spec = param_spec.get("items", {})
                items_type = items_spec.get("type", "string")
                if items_type == "string":
                    field_type = List[str]
                elif items_type == "object":
                    field_type = List[Dict[str, Any]]
                else:
                    field_type = List[Any]
            elif param_type == "object":
                field_type = Dict[str, Any]
            else:
                field_type = Any
            
            if not is_required:
                field_type = Optional[field_type]
                fields[param_name] = (field_type, Field(default=None, description=param_desc))
            else:
                fields[param_name] = (field_type, Field(..., description=param_desc))
        
        args_schema = create_model(f"{self.name}_args", **fields) if fields else None
        
        return StructuredTool(
            name=self.name,
            description=self.description,
            func=self.run,
            args_schema=args_schema
        )


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
    
    def get_langchain_tools(self) -> List[LangChainBaseTool]:
        return [tool.to_langchain_tool() for tool in self._tools.values()]
    
    def clear(self):
        self._tools.clear()
