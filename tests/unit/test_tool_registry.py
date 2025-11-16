import pytest
from agents.tools.tool_registry import Tool, FunctionTool, ToolRegistry


class MockTool(Tool):
    def __init__(self):
        super().__init__(
            name="mock_tool",
            description="A mock tool for testing",
            parameters={"param1": {"type": "string", "required": True}}
        )
    
    def run(self, **kwargs):
        return f"Executed with {kwargs}"


def test_tool_initialization():
    tool = MockTool()
    assert tool.name == "mock_tool"
    assert tool.description == "A mock tool for testing"
    assert "param1" in tool.parameters


def test_tool_validate_input():
    tool = MockTool()
    
    assert tool.validate_input({"param1": "value"}) is True
    assert tool.validate_input({}) is False


def test_tool_to_dict():
    tool = MockTool()
    tool_dict = tool.to_dict()
    
    assert tool_dict["name"] == "mock_tool"
    assert tool_dict["description"] == "A mock tool for testing"
    assert "parameters" in tool_dict


def test_function_tool():
    def test_func(x, y):
        return x + y
    
    tool = FunctionTool(
        name="add",
        description="Adds two numbers",
        parameters={"x": {"required": True}, "y": {"required": True}},
        func=test_func
    )
    
    result = tool.run(x=5, y=3)
    assert result == 8


def test_tool_registry_register():
    registry = ToolRegistry()
    tool = MockTool()
    
    registry.register(tool)
    assert registry.has_tool("mock_tool")


def test_tool_registry_get_tool():
    registry = ToolRegistry()
    tool = MockTool()
    registry.register(tool)
    
    retrieved = registry.get_tool("mock_tool")
    assert retrieved is not None
    assert retrieved.name == "mock_tool"


def test_tool_registry_unregister():
    registry = ToolRegistry()
    tool = MockTool()
    registry.register(tool)
    
    registry.unregister("mock_tool")
    assert not registry.has_tool("mock_tool")


def test_tool_registry_get_all_tools():
    registry = ToolRegistry()
    tool1 = MockTool()
    
    def func2(**kwargs):
        return "result2"
    
    tool2 = FunctionTool("tool2", "Second tool", {}, func2)
    
    registry.register(tool1)
    registry.register(tool2)
    
    tools = registry.get_all_tools()
    assert len(tools) == 2


def test_tool_registry_execute_tool():
    registry = ToolRegistry()
    tool = MockTool()
    registry.register(tool)
    
    result = registry.execute_tool("mock_tool", param1="test")
    assert "test" in result


def test_tool_registry_execute_nonexistent_tool():
    registry = ToolRegistry()
    
    with pytest.raises(ValueError, match="not found"):
        registry.execute_tool("nonexistent")


def test_tool_registry_get_tool_descriptions():
    registry = ToolRegistry()
    tool = MockTool()
    registry.register(tool)
    
    descriptions = registry.get_tool_descriptions()
    assert len(descriptions) == 1
    assert descriptions[0]["name"] == "mock_tool"


def test_tool_registry_clear():
    registry = ToolRegistry()
    registry.register(MockTool())
    
    registry.clear()
    assert len(registry.get_all_tools()) == 0
