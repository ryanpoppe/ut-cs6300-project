import pytest
from agents.evals.evaluator import TrajectoryRecorder, TrajectoryEvaluator
from agents.core.agent_state import AgentState


def test_trajectory_recorder():
    recorder = TrajectoryRecorder()
    state = AgentState()
    state.add_step("Think", "action", {}, "obs")
    
    trajectory = recorder.record(
        input_data="Test input",
        state=state,
        final_output="Test output"
    )
    
    assert trajectory["input"] == "Test input"
    assert trajectory["final_output"] == "Test output"
    assert len(trajectory["steps"]) == 1


def test_trajectory_evaluator_final_output():
    evaluator = TrajectoryEvaluator()
    
    trajectory = {
        "input": "Test",
        "final_output": "The answer is 42",
        "steps": [],
        "tool_calls": []
    }
    
    result = evaluator.evaluate_trajectory(
        trajectory,
        expected_output="The answer is 42"
    )
    
    assert result["scores"]["final_correctness"] == 1.0


def test_trajectory_evaluator_partial_match():
    evaluator = TrajectoryEvaluator()
    
    trajectory = {
        "input": "Test",
        "final_output": "The result is approximately 42 degrees",
        "steps": [],
        "tool_calls": []
    }
    
    result = evaluator.evaluate_trajectory(
        trajectory,
        expected_output="The answer is exactly 42"
    )
    
    assert 0 < result["scores"]["final_correctness"] < 1.0


def test_trajectory_evaluator_coherence():
    evaluator = TrajectoryEvaluator()
    
    trajectory = {
        "input": "Test",
        "final_output": "Result",
        "steps": [
            {"thought": "Think 1", "action": "action1", "action_input": {}, "observation": "obs1"},
            {"thought": "Think 2", "action": "action2", "action_input": {}, "observation": "obs2"}
        ],
        "tool_calls": []
    }
    
    result = evaluator.evaluate_trajectory(trajectory)
    
    assert "coherence" in result["scores"]
    assert result["scores"]["coherence"] > 0.5


def test_trajectory_evaluator_tool_usage():
    evaluator = TrajectoryEvaluator()
    
    trajectory = {
        "input": "Test",
        "final_output": "Result",
        "steps": [],
        "tool_calls": [
            {"tool_name": "tool1", "success": True},
            {"tool_name": "tool2", "success": True},
            {"tool_name": "tool3", "success": False}
        ]
    }
    
    result = evaluator.evaluate_trajectory(trajectory)
    
    assert result["scores"]["tool_usage_accuracy"] == 2/3


def test_trajectory_evaluator_dataset():
    evaluator = TrajectoryEvaluator()
    
    trajectories = [
        {
            "input": "Q1",
            "final_output": "A1",
            "steps": [],
            "tool_calls": []
        },
        {
            "input": "Q2",
            "final_output": "A2",
            "steps": [],
            "tool_calls": []
        }
    ]
    
    dataset = [
        {"expected_output": "A1"},
        {"expected_output": "A2"}
    ]
    
    summary = evaluator.evaluate_dataset(trajectories, dataset)
    
    assert "results" in summary
    assert len(summary["results"]) == 2
    assert "aggregate_scores" in summary


def test_trajectory_evaluator_custom_evaluator():
    evaluator = TrajectoryEvaluator()
    
    def custom_eval(trajectory):
        return 0.75
    
    trajectory = {
        "input": "Test",
        "final_output": "Result",
        "steps": [],
        "tool_calls": []
    }
    
    result = evaluator.evaluate_trajectory(
        trajectory,
        custom_evaluators={"custom": custom_eval}
    )
    
    assert "custom" in result["scores"]
    assert result["scores"]["custom"] == 0.75


def test_trajectory_recorder_save_load(tmp_path):
    recorder = TrajectoryRecorder()
    state = AgentState()
    state.add_step("Think", "action", {}, "obs")
    
    recorder.record("Input", state, "Output")
    
    file_path = tmp_path / "trajectories.json"
    recorder.save_to_file(str(file_path))
    
    new_recorder = TrajectoryRecorder()
    new_recorder.load_from_file(str(file_path))
    
    assert len(new_recorder.get_all_trajectories()) == 1
