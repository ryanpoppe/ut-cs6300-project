from typing import Dict, List, Optional, Any
from agents.core.agent_state import AgentState


class PromptBuilder:
    def __init__(self, 
                 system_prompt: Optional[str] = None,
                 react_format: Optional[str] = None):
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.react_format = react_format or self._default_react_format()
    
    def _default_system_prompt(self) -> str:
        return """You are a helpful AI assistant that uses tools to solve problems.
You follow the ReAct (Reasoning + Acting) framework to think through problems step by step.

Always structure your responses as follows:
Thought: [Your reasoning about what to do next]
Action: [The tool to use]
Action Input: [The input to the tool in JSON format]
Observation: [The result will be provided here]
... (repeat Thought/Action/Observation as needed)
Thought: I now know the final answer
Final Answer: [Your final response to the user]"""
    
    def _default_react_format(self) -> str:
        return """
Follow this format:

Thought: Your reasoning about the current situation and what action to take
Action: The name of the tool to use (must be one of the available tools)
Action Input: The input for the tool as a JSON object
Observation: [This will be filled in with the tool result]

Repeat the Thought/Action/Observation cycle as many times as needed.

When you have enough information to answer the user's question, provide:
Thought: I now have all the information needed to provide a final answer
Final Answer: [Your complete answer to the user]
"""
    
    def build_prompt(self, 
                    user_input: str, 
                    tools: List[Dict[str, Any]], 
                    state: AgentState,
                    additional_context: Optional[str] = None) -> str:
        prompt_parts = [self.system_prompt]
        
        if tools:
            prompt_parts.append("\nAvailable Tools:")
            for tool in tools:
                tool_desc = f"\n- {tool['name']}: {tool['description']}"
                if 'parameters' in tool:
                    tool_desc += f"\n  Parameters: {tool['parameters']}"
                prompt_parts.append(tool_desc)
        
        prompt_parts.append(self.react_format)
        
        if state.steps:
            prompt_parts.append("\nPrevious Steps:")
            for i, step in enumerate(state.steps, 1):
                prompt_parts.append(f"\nStep {i}:")
                prompt_parts.append(f"Thought: {step.thought}")
                if step.action:
                    prompt_parts.append(f"Action: {step.action}")
                if step.action_input:
                    prompt_parts.append(f"Action Input: {step.action_input}")
                if step.observation:
                    prompt_parts.append(f"Observation: {step.observation}")
        
        if additional_context:
            prompt_parts.append(f"\nAdditional Context:\n{additional_context}")
        
        prompt_parts.append(f"\nUser Input: {user_input}")
        prompt_parts.append("\nNow provide your next Thought, Action, and Action Input (or Final Answer if ready):")
        
        return "\n".join(prompt_parts)
    
    def build_system_message(self, tools: List[Dict[str, Any]]) -> str:
        parts = [self.system_prompt]
        
        if tools:
            parts.append("\nAvailable Tools:")
            for tool in tools:
                parts.append(f"\n- {tool['name']}: {tool['description']}")
        
        parts.append(self.react_format)
        return "\n".join(parts)
    
    def build_user_message(self, 
                          user_input: str, 
                          state: AgentState,
                          additional_context: Optional[str] = None) -> str:
        parts = []
        
        if state.steps:
            parts.append("Previous Steps:")
            for i, step in enumerate(state.steps, 1):
                parts.append(f"\nStep {i}:")
                parts.append(f"Thought: {step.thought}")
                if step.action:
                    parts.append(f"Action: {step.action}")
                if step.action_input:
                    parts.append(f"Action Input: {step.action_input}")
                if step.observation:
                    parts.append(f"Observation: {step.observation}")
        
        if additional_context:
            parts.append(f"\nAdditional Context:\n{additional_context}")
        
        parts.append(f"\nUser Input: {user_input}")
        parts.append("\nProvide your next Thought, Action, and Action Input (or Final Answer if ready):")
        
        return "\n".join(parts)
