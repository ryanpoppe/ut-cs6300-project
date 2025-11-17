from typing import Any, Dict, List, Optional, Union
import json
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import AIMessage, HumanMessage
from agents.core.base_agent import BaseAgent
from agents.core.agent_state import AgentState
from agents.core.config import AgentConfig
from agents.prompts.prompt_builder import PromptBuilder
from agents.tools.tool_registry import ToolRegistry

try:
    from langgraph.prebuilt import create_react_agent
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False


class ReActAgent(BaseAgent):
    def __init__(self,
                 llm: Union[BaseLanguageModel, Any],
                 tool_registry: ToolRegistry,
                 prompt_builder: PromptBuilder,
                 config: Optional[AgentConfig] = None):
        super().__init__()
        self.llm = llm
        self.tool_registry = tool_registry
        self.prompt_builder = prompt_builder
        self.config = config or AgentConfig()
        self.current_step = 0
        self.agent_executor = None
        
        should_use_langgraph = (
            LANGGRAPH_AVAILABLE and 
            hasattr(llm, 'invoke') and 
            hasattr(llm, 'bind_tools')
        )
        
        if should_use_langgraph:
            self._setup_langgraph_agent()
        else:
            self.agent_executor = None
    
    def _setup_langgraph_agent(self):
        tools = self.tool_registry.get_langchain_tools()
        self.agent_executor = create_react_agent(self.llm, tools)
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        lines = response.strip().split('\n')
        
        thought = ""
        action = None
        action_input = None
        final_answer = None
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith("Thought:"):
                thought = line.replace("Thought:", "").strip()
                i += 1
                while i < len(lines) and not lines[i].strip().startswith(("Action:", "Final Answer:")):
                    thought += " " + lines[i].strip()
                    i += 1
                continue
            
            if line.startswith("Action:"):
                action = line.replace("Action:", "").strip()
                i += 1
                continue
            
            if line.startswith("Action Input:"):
                action_input_str = line.replace("Action Input:", "").strip()
                i += 1
                while i < len(lines) and not lines[i].strip().startswith(("Thought:", "Observation:", "Final Answer:")):
                    action_input_str += " " + lines[i].strip()
                    i += 1
                
                try:
                    action_input = json.loads(action_input_str)
                except json.JSONDecodeError:
                    action_input = {"raw_input": action_input_str}
                continue
            
            if line.startswith("Final Answer:"):
                final_answer = line.replace("Final Answer:", "").strip()
                i += 1
                while i < len(lines):
                    final_answer += " " + lines[i].strip()
                    i += 1
                break
            
            i += 1
        
        return {
            "thought": thought,
            "action": action,
            "action_input": action_input,
            "final_answer": final_answer
        }
    
    def plan(self, input_data: str) -> Dict[str, Any]:
        tools = self.tool_registry.get_tool_descriptions()
        prompt = self.prompt_builder.build_prompt(
            user_input=input_data,
            tools=tools,
            state=self.state
        )
        
        if hasattr(self.llm, 'invoke'):
            if isinstance(prompt, str):
                response = self.llm.invoke(prompt)
            else:
                messages = [{"role": "user", "content": prompt}]
                response = self.llm.invoke(messages)
            
            if hasattr(response, 'content'):
                response = response.content
        else:
            messages = [{"role": "user", "content": prompt}]
            response = self.llm.invoke(messages)
        
        parsed = self.parse_response(response)
        return parsed
        lines = response.strip().split('\n')
        
        thought = ""
        action = None
        action_input = None
        final_answer = None
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith("Thought:"):
                thought = line.replace("Thought:", "").strip()
                i += 1
                while i < len(lines) and not lines[i].strip().startswith(("Action:", "Final Answer:")):
                    thought += " " + lines[i].strip()
                    i += 1
                continue
            
            if line.startswith("Action:"):
                action = line.replace("Action:", "").strip()
                i += 1
                continue
            
            if line.startswith("Action Input:"):
                action_input_str = line.replace("Action Input:", "").strip()
                i += 1
                while i < len(lines) and not lines[i].strip().startswith(("Thought:", "Observation:", "Final Answer:")):
                    action_input_str += " " + lines[i].strip()
                    i += 1
                
                try:
                    action_input = json.loads(action_input_str)
                except json.JSONDecodeError:
                    action_input = {"raw_input": action_input_str}
                continue
            
            if line.startswith("Final Answer:"):
                final_answer = line.replace("Final Answer:", "").strip()
                i += 1
                while i < len(lines):
                    final_answer += " " + lines[i].strip()
                    i += 1
                break
            
            i += 1
        
        return {
            "thought": thought,
            "action": action,
            "action_input": action_input,
            "final_answer": final_answer
        }
    
    def plan(self, input_data: str) -> Dict[str, Any]:
        tools = self.tool_registry.get_tool_descriptions()
        prompt = self.prompt_builder.build_prompt(
            user_input=input_data,
            tools=tools,
            state=self.state
        )
        
        messages = [{"role": "user", "content": prompt}]
        response = self.llm.invoke(messages)
        
        parsed = self.parse_response(response)
        return parsed
    
    
    def act(self, action: str, action_input: Dict[str, Any]) -> Any:
        if not self.tool_registry.has_tool(action):
            error_msg = f"Tool '{action}' not found. Available tools: {[t.name for t in self.tool_registry.get_all_tools()]}"
            self.state.record_tool_call(action, action_input, None, success=False, error=error_msg)
            return {"error": error_msg}
        
        try:
            result = self.tool_registry.execute_tool(action, **action_input)
            self.state.record_tool_call(action, action_input, result, success=True)
            return result
        except Exception as e:
            error_msg = f"Error executing tool '{action}': {str(e)}"
            self.state.record_tool_call(action, action_input, None, success=False, error=error_msg)
            return {"error": error_msg}
    
    def observe(self, action_result: Any) -> str:
        if isinstance(action_result, dict):
            if "error" in action_result:
                return f"Error: {action_result['error']}"
            return json.dumps(action_result, indent=2)
        return str(action_result)
    
    def run(self, input_data: str) -> str:
        self.reset()
        self.state.add_message("user", input_data)
        self.current_step = 0
        
        if self.agent_executor and LANGGRAPH_AVAILABLE:
            try:
                messages = [HumanMessage(content=input_data)]
                result = self.agent_executor.invoke({"messages": messages})
                
                if "messages" in result:
                    for msg in result["messages"]:
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            for tool_call in msg.tool_calls:
                                tool_name = tool_call.get("name", "")
                                tool_input = tool_call.get("args", {})
                                
                                self.state.add_step(
                                    thought="",
                                    action=tool_name,
                                    action_input=tool_input,
                                    observation=""
                                )
                        
                        if isinstance(msg, AIMessage) and not hasattr(msg, 'tool_calls'):
                            output = msg.content
                            self.state.set_final_output(output)
                            return output
                
                last_message = result["messages"][-1]
                if isinstance(last_message, AIMessage):
                    output = last_message.content
                    self.state.set_final_output(output)
                    return output
                
            except Exception as e:
                error_msg = f"Agent execution error: {str(e)}"
                self.state.set_error(error_msg)
                return error_msg
        
        while self.current_step < self.config.max_steps:
            self.current_step += 1
            
            parsed = self.plan(input_data)
            
            thought = parsed.get("thought", "")
            action = parsed.get("action")
            action_input = parsed.get("action_input")
            final_answer = parsed.get("final_answer")
            
            if final_answer:
                self.state.add_step(thought=thought)
                self.state.set_final_output(final_answer)
                return final_answer
            
            if not action:
                self.state.add_step(thought=thought)
                continue
            
            action_result = self.act(action, action_input or {})
            observation = self.observe(action_result)
            
            self.state.add_step(
                thought=thought,
                action=action,
                action_input=action_input,
                observation=observation
            )
            
            if isinstance(action_result, dict) and "error" in action_result:
                if self.config.stop_on_error:
                    error_msg = f"Stopped due to error: {action_result['error']}"
                    self.state.set_error(error_msg)
                    return error_msg
        
        timeout_msg = f"Reached maximum steps ({self.config.max_steps}) without finding final answer"
        self.state.set_error(timeout_msg)
        return timeout_msg
