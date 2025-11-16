from typing import Dict, Any, List, Optional
from agents.core.agent_state import AgentState
import json


class TrajectoryRecorder:
    def __init__(self):
        self.trajectories: List[Dict[str, Any]] = []
    
    def record(self, 
               input_data: str, 
               state: AgentState, 
               final_output: str,
               metadata: Optional[Dict[str, Any]] = None):
        trajectory = {
            "input": input_data,
            "final_output": final_output,
            "steps": state.get_trajectory(),
            "tool_calls": state.tool_calls,
            "messages": [msg.to_dict() for msg in state.messages],
            "metadata": metadata or {}
        }
        self.trajectories.append(trajectory)
        return trajectory
    
    def get_all_trajectories(self) -> List[Dict[str, Any]]:
        return self.trajectories
    
    def save_to_file(self, filepath: str):
        with open(filepath, 'w') as f:
            json.dump(self.trajectories, f, indent=2)
    
    def load_from_file(self, filepath: str):
        with open(filepath, 'r') as f:
            self.trajectories = json.load(f)
    
    def clear(self):
        self.trajectories.clear()


class TrajectoryEvaluator:
    def __init__(self):
        self.evaluation_functions = {}
    
    def register_evaluator(self, name: str, func):
        self.evaluation_functions[name] = func
    
    def evaluate_trajectory(self, 
                           trajectory: Dict[str, Any],
                           expected_output: Optional[str] = None,
                           expected_trajectory: Optional[List[Dict[str, Any]]] = None,
                           custom_evaluators: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        
        results = {
            "input": trajectory["input"],
            "final_output": trajectory["final_output"],
            "scores": {},
            "errors": [],
            "warnings": []
        }
        
        if expected_output:
            final_score = self._evaluate_final_output(
                trajectory["final_output"],
                expected_output
            )
            results["scores"]["final_correctness"] = final_score
        
        if expected_trajectory:
            trajectory_score = self._evaluate_trajectory_steps(
                trajectory["steps"],
                expected_trajectory
            )
            results["scores"]["trajectory_correctness"] = trajectory_score
        
        coherence_score = self._evaluate_coherence(trajectory["steps"])
        results["scores"]["coherence"] = coherence_score
        
        tool_usage_score = self._evaluate_tool_usage(trajectory["tool_calls"])
        results["scores"]["tool_usage_accuracy"] = tool_usage_score
        
        hallucination_check = self._check_hallucinations(trajectory)
        results["scores"]["hallucination_free"] = hallucination_check["score"]
        if hallucination_check["issues"]:
            results["errors"].extend(hallucination_check["issues"])
        
        if custom_evaluators:
            for eval_name, eval_func in custom_evaluators.items():
                try:
                    custom_score = eval_func(trajectory)
                    results["scores"][eval_name] = custom_score
                except Exception as e:
                    results["warnings"].append(f"Custom evaluator '{eval_name}' failed: {str(e)}")
        
        for eval_name, eval_func in self.evaluation_functions.items():
            try:
                score = eval_func(trajectory)
                results["scores"][eval_name] = score
            except Exception as e:
                results["warnings"].append(f"Evaluator '{eval_name}' failed: {str(e)}")
        
        results["overall_score"] = sum(results["scores"].values()) / len(results["scores"]) if results["scores"] else 0.0
        
        return results
    
    def evaluate_dataset(self, 
                        trajectories: List[Dict[str, Any]],
                        dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        
        if len(trajectories) != len(dataset):
            raise ValueError("Number of trajectories must match dataset size")
        
        all_results = []
        for traj, expected in zip(trajectories, dataset):
            result = self.evaluate_trajectory(
                traj,
                expected_output=expected.get("expected_output"),
                expected_trajectory=expected.get("expected_trajectory")
            )
            all_results.append(result)
        
        aggregate_scores = {}
        for result in all_results:
            for score_name, score_value in result["scores"].items():
                if score_name not in aggregate_scores:
                    aggregate_scores[score_name] = []
                aggregate_scores[score_name].append(score_value)
        
        summary = {
            "results": all_results,
            "aggregate_scores": {
                name: {
                    "mean": sum(scores) / len(scores),
                    "min": min(scores),
                    "max": max(scores)
                }
                for name, scores in aggregate_scores.items()
            },
            "total_evaluations": len(all_results)
        }
        
        return summary
    
    def _evaluate_final_output(self, actual: str, expected: str) -> float:
        if actual.strip().lower() == expected.strip().lower():
            return 1.0
        
        actual_words = set(actual.lower().split())
        expected_words = set(expected.lower().split())
        
        if not expected_words:
            return 0.0
        
        overlap = len(actual_words.intersection(expected_words))
        return overlap / len(expected_words)
    
    def _evaluate_trajectory_steps(self, 
                                   actual_steps: List[Dict[str, Any]],
                                   expected_steps: List[Dict[str, Any]]) -> float:
        
        if not expected_steps:
            return 1.0
        
        matches = 0
        for expected_step in expected_steps:
            for actual_step in actual_steps:
                if expected_step.get("action") == actual_step.get("action"):
                    matches += 1
                    break
        
        return matches / len(expected_steps)
    
    def _evaluate_coherence(self, steps: List[Dict[str, Any]]) -> float:
        if not steps:
            return 0.0
        
        score = 1.0
        
        for step in steps:
            if not step.get("thought"):
                score -= 0.1
            
            if step.get("action") and not step.get("action_input"):
                score -= 0.1
            
            if step.get("action") and not step.get("observation"):
                score -= 0.05
        
        return max(0.0, min(1.0, score))
    
    def _evaluate_tool_usage(self, tool_calls: List[Dict[str, Any]]) -> float:
        if not tool_calls:
            return 1.0
        
        successful_calls = sum(1 for call in tool_calls if call.get("success", False))
        return successful_calls / len(tool_calls)
    
    def _check_hallucinations(self, trajectory: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        
        tool_calls = trajectory.get("tool_calls", [])
        for call in tool_calls:
            if not call.get("success"):
                error = call.get("error", "")
                if "not found" in error.lower():
                    issues.append(f"Hallucinated tool: {call.get('tool_name')}")
        
        steps = trajectory.get("steps", [])
        for step in steps:
            if step.get("action"):
                action = step["action"]
                tool_names = [call.get("tool_name") for call in tool_calls]
                if action not in tool_names:
                    issues.append(f"Action '{action}' not executed properly")
        
        score = 1.0 - (len(issues) * 0.2)
        score = max(0.0, min(1.0, score))
        
        return {
            "score": score,
            "issues": issues
        }
    
    def save_evaluation_results(self, results: Dict[str, Any], filepath: str):
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
