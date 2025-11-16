import pytest
from agents.core.agent_state import AgentState, Step, Message
from datetime import datetime


def test_agent_state_initialization():
    state = AgentState()
    assert len(state.steps) == 0
    assert len(state.messages) == 0
    assert len(state.tool_calls) == 0
    assert state.final_output is None
    assert state.is_complete is False
    assert state.error is None


def test_add_step():
    state = AgentState()
    step = state.add_step(
        thought="I need to get climate data",
        action="get_climate_data",
        action_input={"zipcode": "94102"},
        observation="Zone 10a, frost-free"
    )
    
    assert len(state.steps) == 1
    assert state.steps[0].thought == "I need to get climate data"
    assert state.steps[0].action == "get_climate_data"
    assert state.steps[0].action_input == {"zipcode": "94102"}
    assert state.steps[0].observation == "Zone 10a, frost-free"


def test_add_message():
    state = AgentState()
    msg = state.add_message("user", "Plan my garden")
    
    assert len(state.messages) == 1
    assert state.messages[0].role == "user"
    assert state.messages[0].content == "Plan my garden"


def test_record_tool_call():
    state = AgentState()
    state.record_tool_call(
        tool_name="get_climate_data",
        tool_input={"zipcode": "94102"},
        tool_output={"zone": "10a"},
        success=True
    )
    
    assert len(state.tool_calls) == 1
    assert state.tool_calls[0]["tool_name"] == "get_climate_data"
    assert state.tool_calls[0]["success"] is True


def test_set_final_output():
    state = AgentState()
    state.set_final_output("Garden plan complete")
    
    assert state.final_output == "Garden plan complete"
    assert state.is_complete is True


def test_set_error():
    state = AgentState()
    state.set_error("Tool not found")
    
    assert state.error == "Tool not found"
    assert state.is_complete is True


def test_get_trajectory():
    state = AgentState()
    state.add_step("Think 1", "action1", {"param": 1}, "obs1")
    state.add_step("Think 2", "action2", {"param": 2}, "obs2")
    
    trajectory = state.get_trajectory()
    assert len(trajectory) == 2
    assert trajectory[0]["thought"] == "Think 1"
    assert trajectory[1]["thought"] == "Think 2"


def test_to_dict():
    state = AgentState()
    state.add_step("Think", "action", {}, "obs")
    state.add_message("user", "input")
    state.set_final_output("output")
    
    state_dict = state.to_dict()
    assert "steps" in state_dict
    assert "messages" in state_dict
    assert "final_output" in state_dict
    assert state_dict["final_output"] == "output"


def test_from_dict():
    original_state = AgentState()
    original_state.add_step("Think", "action", {}, "obs")
    original_state.set_final_output("output")
    
    state_dict = original_state.to_dict()
    restored_state = AgentState.from_dict(state_dict)
    
    assert len(restored_state.steps) == len(original_state.steps)
    assert restored_state.final_output == original_state.final_output


def test_serialization():
    state = AgentState()
    state.add_step("Think", "action", {"key": "value"}, "obs")
    
    json_str = state.to_json()
    assert isinstance(json_str, str)
    assert "Think" in json_str
