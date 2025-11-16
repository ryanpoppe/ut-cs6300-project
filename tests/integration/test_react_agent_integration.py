import pytest
from agents.react.react_agent import ReActAgent
from agents.core.config import AgentConfig
from agents.tools.tool_registry import ToolRegistry
from agents.tools.garden_tools import GetClimateDataTool, QueryPlantDatabaseTool
from agents.prompts.prompt_builder import PromptBuilder


class MockLLM:
    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0
    
    def invoke(self, messages):
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
            self.call_count += 1
            return response
        return "Final Answer: Completed"


def test_react_agent_single_tool_call():
    responses = [
        """Thought: I need to get climate data for the zipcode
Action: get_climate_data
Action Input: {"zipcode": "94102"}""",
        """Thought: I have the climate data
Final Answer: Zone 10a, frost-free climate"""
    ]
    
    llm = MockLLM(responses)
    registry = ToolRegistry()
    registry.register(GetClimateDataTool())
    builder = PromptBuilder()
    config = AgentConfig(max_steps=5)
    
    agent = ReActAgent(llm, registry, builder, config)
    result = agent.run("What is the climate for zipcode 94102?")
    
    assert "Zone 10a" in result or "frost-free" in result
    assert len(agent.state.steps) > 0
    assert len(agent.state.tool_calls) == 1


def test_react_agent_multiple_steps():
    responses = [
        """Thought: First, get climate data
Action: get_climate_data
Action Input: {"zipcode": "10001"}""",
        """Thought: Now query for plants
Action: query_plant_database
Action Input: {"hardiness_zone": "7b", "sun_requirement": "full_sun"}""",
        """Thought: I have all the information needed
Final Answer: For Zone 7b with full sun, suitable plants include Tomato, Basil, and Marigold."""
    ]
    
    llm = MockLLM(responses)
    registry = ToolRegistry()
    registry.register(GetClimateDataTool())
    registry.register(QueryPlantDatabaseTool())
    builder = PromptBuilder()
    config = AgentConfig(max_steps=10)
    
    agent = ReActAgent(llm, registry, builder, config)
    result = agent.run("What plants can I grow in zipcode 10001 with full sun?")
    
    assert agent.state.is_complete
    assert len(agent.state.tool_calls) == 2
    assert any("Tomato" in str(call) or "Basil" in str(call) for call in agent.state.tool_calls)


def test_react_agent_max_steps():
    responses = [
        """Thought: Keep thinking
Action: get_climate_data
Action Input: {"zipcode": "94102"}"""
    ] * 20
    
    llm = MockLLM(responses)
    registry = ToolRegistry()
    registry.register(GetClimateDataTool())
    builder = PromptBuilder()
    config = AgentConfig(max_steps=3)
    
    agent = ReActAgent(llm, registry, builder, config)
    result = agent.run("Test")
    
    assert "maximum steps" in result.lower()
    assert agent.state.error is not None


def test_react_agent_invalid_tool():
    responses = [
        """Thought: Use invalid tool
Action: nonexistent_tool
Action Input: {}""",
        """Thought: Tool not found
Final Answer: Could not complete task"""
    ]
    
    llm = MockLLM(responses)
    registry = ToolRegistry()
    builder = PromptBuilder()
    config = AgentConfig(max_steps=5, stop_on_error=False)
    
    agent = ReActAgent(llm, registry, builder, config)
    result = agent.run("Test")
    
    assert len(agent.state.tool_calls) == 1
    assert not agent.state.tool_calls[0]["success"]
