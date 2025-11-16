import pytest
from agents.prompts.prompt_builder import PromptBuilder
from agents.core.agent_state import AgentState


def test_prompt_builder_initialization():
    builder = PromptBuilder()
    assert builder.system_prompt is not None
    assert builder.react_format is not None


def test_prompt_builder_custom_prompts():
    custom_system = "Custom system prompt"
    custom_format = "Custom format"
    
    builder = PromptBuilder(
        system_prompt=custom_system,
        react_format=custom_format
    )
    
    assert builder.system_prompt == custom_system
    assert builder.react_format == custom_format


def test_build_prompt_basic():
    builder = PromptBuilder()
    state = AgentState()
    tools = [
        {
            "name": "test_tool",
            "description": "A test tool",
            "parameters": {"param1": {"type": "string"}}
        }
    ]
    
    prompt = builder.build_prompt(
        user_input="Test input",
        tools=tools,
        state=state
    )
    
    assert "Test input" in prompt
    assert "test_tool" in prompt
    assert "Available Tools" in prompt


def test_build_prompt_with_steps():
    builder = PromptBuilder()
    state = AgentState()
    state.add_step("First thought", "action1", {"key": "value"}, "observation1")
    
    prompt = builder.build_prompt(
        user_input="Test input",
        tools=[],
        state=state
    )
    
    assert "First thought" in prompt
    assert "action1" in prompt
    assert "observation1" in prompt
    assert "Previous Steps" in prompt


def test_build_prompt_with_context():
    builder = PromptBuilder()
    state = AgentState()
    
    prompt = builder.build_prompt(
        user_input="Test input",
        tools=[],
        state=state,
        additional_context="Extra context information"
    )
    
    assert "Extra context information" in prompt


def test_build_system_message():
    builder = PromptBuilder()
    tools = [
        {"name": "tool1", "description": "First tool"},
        {"name": "tool2", "description": "Second tool"}
    ]
    
    message = builder.build_system_message(tools)
    
    assert "tool1" in message
    assert "tool2" in message


def test_build_user_message():
    builder = PromptBuilder()
    state = AgentState()
    state.add_step("Thinking", "action", {}, "result")
    
    message = builder.build_user_message(
        user_input="User question",
        state=state
    )
    
    assert "User question" in message
    assert "Thinking" in message


def test_build_user_message_no_steps():
    builder = PromptBuilder()
    state = AgentState()
    
    message = builder.build_user_message(
        user_input="Simple question",
        state=state
    )
    
    assert "Simple question" in message
    assert "Previous Steps" not in message
