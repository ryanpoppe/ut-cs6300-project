# ReAct Agent Framework Specification (LangChain)

This document defines the architecture, required components, testing strategy, and evaluation system for implementing a **ReAct-style agent** using **LangChain**.  
Coding agents should follow this specification when generating code.

---

# 1. Overview

The goal of this framework is to provide:

- A clean, **class-based**, modular architecture  
- Full **unit testability** (LLM mocks, tool mocks, state tests)  
- A pluggable **ReAct loop** implementation  
- A robust **evaluation system** for ReAct trajectories  
- Easy extensibility for new tools, prompts, and scoring approaches

This is NOT tied to a specific domain — it is a reusable agent framework.

---

# 2. Architecture Requirements

## 2.1 Core Modules

Implement the following classes and modules:

### Class: `BaseAgent`
Abstract base class defining the agent interface.

Must include:
- `plan()`  
- `act()`  
- `observe()`  
- `run(input: str)`  
- Internal reference to an `AgentState` object  

BaseAgent MUST NOT depend directly on LangChain — only subclasses may.

---

### Class: `ReActAgent(BaseAgent)`
Implements ReAct logic:

Loop format:
```
[Thought] → [Action] → [Observation] → repeat → [Final Answer]
```

Requirements:
- Compatible with LangChain (LCEL or Chains)
- Accept LLM, tools, memory via dependency injection
- Maintain step-by-step log in `AgentState`
- Detect “final answer” signals
- Configurable:
  - max steps  
  - stop conditions  
  - tool error behavior  
- Return final output + full trajectory

---

### Class: `AgentState`
Tracks:
- Thoughts  
- Actions  
- Observations  
- LLM messages  
- Tool calls  
- Final output  

Must be:
- Fully serializable
- Usable for later evaluation

---

### Class: `PromptBuilder`
Responsible for constructing prompts consisting of:
- System instructions  
- ReAct scaffolding  
- Tool list  
- Previous steps from `AgentState`  
- User input  

Prompts must be:
- Fully customizable  
- Easy to override  
- Versioned or configurable if necessary  

---

### Tooling Layer

#### Class: `ToolRegistry`
- Registers available tools
- Makes them accessible to the agent
- Ensures each tool has a name, description, input schema, and call handler

#### Class: `Tool` Wrappers
- Wrap LangChain tools  
- Provide mockable interfaces for unit tests  
- Enforce input/output validation  

---

# 3. Testing Requirements

The framework must be fully testable.  

## 3.1 Unit Testing

Use **pytest** with the following expectations:

### Mock the LLM
- Return deterministic “thought/action” sequences  
- Test prompt formatting  
- Test loop continuation/stopping  
- Test error recovery logic  

### Mock tools
- Fake tool outputs  
- Test correct formatting of tool calls  
- Test multi-step tool reasoning  
- Test mis-specified actions  

### Test evaluation modules
- Ensure full trajectory is recorded  
- Ensure evaluator scores are correct  
- Ensure rule violations are detected  

### Integration test
A full-run ReAct sequence with fixed seeds and deterministic mocks.

---

# 4. ReAct Loop Requirements

The loop MUST:

1. Produce a Thought  
2. Select an Action (or Final Answer)  
3. Execute the Action through a Tool  
4. Capture the Observation  
5. Continue until:
   - Final answer  
   - Max steps reached  
   - Invalid or cyclic pattern detected  

The `AgentState` must log *every* step.

Include safe-guards:
- Infinite loop protection  
- Unsupported tool detection  
- Hallucinated-action detection  
- Graceful tool errors  

---

# 5. Evaluation Requirements

Provide a dedicated evaluation module.

### Class: `TrajectoryRecorder`
- Logs thoughts, actions, observations  
- Produces a serializable trajectory  
- Supports replay

### Class: `TrajectoryEvaluator`
Accepts:
- Dataset entries  
- Gold labels  
- Expected intermediate actions  
- Custom scoring functions  

Produces:
```json
{
  "results": [
    {
      "input": "...",
      "final_output": "...",
      "final_score": 0-1,
      "trajectory_score": 0-1,
      "errors": [...]
    }
  ]
}
```

### Required Evaluation Metrics
- Final correctness  
- Step-by-step correctness  
- Coherence of reasoning  
- Tool usage accuracy  
- Hallucination / rule violation tracking  

### Dataset Format
```json
{
  "dataset": [
    {
      "input": "question",
      "expected_output": "gold",
      "expected_trajectory": [...]
    }
  ]
}
```

---

# 6. Configuration & DI Requirements

Implement config objects:

- `AgentConfig`
- `LLMConfig`
- `ToolConfig`

Agent must NOT hardcode:
- LLM  
- Tools  
- Memory  
- Prompts  

Everything must be injectable for easy testing.

---

# 7. Deliverables (for code generation)

Coding agents should produce:

## 7.1 Full directory structure
Example:
```
agents/
  core/
  react/
  tools/
  memory/
  prompts/
  evals/
tests/
  unit/
  integration/
```

## 7.2 Implementations
- All classes defined above  
- ReActAgent example using two mock tools  
- Example prompt templates  
- Example eval runner  

## 7.3 Tests
- pytest unit tests for each component  
- Integration test for entire ReAct pipeline  

## 7.4 Documentation
- README explaining usage, architecture, and extension points  
- Docstrings for all public classes and methods  

---

# 8. Additional Constraints

- Must work with **LangChain ≥ 1.0**  
- Avoid hard-coded logic; keep things modular  
- Support both sync + async execution  
- Keep classes small and single-purpose  

---

**This document is authoritative. All generated code must follow this specification.**
