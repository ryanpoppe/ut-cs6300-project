from agents.react.react_agent import ReActAgent
from agents.core.config import AgentConfig
from agents.tools.tool_registry import ToolRegistry
from agents.tools.garden_tools import (
    GetClimateDataTool,
    QueryPlantDatabaseTool,
    CheckCompanionCompatibilityTool,
    CalculatePlanterLayoutTool,
    GeneratePlantingScheduleTool,
    GenerateGardenVisualizationTool
)
from agents.prompts.prompt_builder import PromptBuilder
from agents.prompts.garden_prompts import GARDEN_SYSTEM_PROMPT, GARDEN_REACT_FORMAT


class MockLLM:
    def invoke(self, messages):
        return """Thought: I need to help plan a garden
Final Answer: Based on your location and requirements, I recommend creating a garden with complementary plants."""


def create_garden_agent():
    registry = ToolRegistry()
    registry.register(GetClimateDataTool())
    registry.register(QueryPlantDatabaseTool())
    registry.register(CheckCompanionCompatibilityTool())
    registry.register(CalculatePlanterLayoutTool())
    registry.register(GeneratePlantingScheduleTool())
    registry.register(GenerateGardenVisualizationTool())
    
    prompt_builder = PromptBuilder(
        system_prompt=GARDEN_SYSTEM_PROMPT,
        react_format=GARDEN_REACT_FORMAT
    )
    
    config = AgentConfig(
        max_steps=15,
        enable_logging=True
    )
    
    llm = MockLLM()
    
    agent = ReActAgent(
        llm=llm,
        tool_registry=registry,
        prompt_builder=prompt_builder,
        config=config
    )
    
    return agent


def main():
    print("Garden Design Assistant - ReAct Agent Example")
    print("=" * 50)
    
    agent = create_garden_agent()
    
    user_input = """
    I want to plan a vegetable garden for my backyard.
    Zipcode: 94102
    Planter: 1 raised bed, 4 feet by 8 feet
    Sunlight: Full sun (6+ hours daily)
    Goal: Food production
    I love tomatoes and basil, but no eggplant please.
    """
    
    print("\nUser Input:")
    print(user_input)
    print("\n" + "=" * 50)
    print("\nProcessing...\n")
    
    result = agent.run(user_input)
    
    print("\nAgent Response:")
    print(result)
    print("\n" + "=" * 50)
    
    print("\nAgent State Summary:")
    print(f"Total Steps: {len(agent.state.steps)}")
    print(f"Tool Calls: {len(agent.state.tool_calls)}")
    print(f"Is Complete: {agent.state.is_complete}")
    
    if agent.state.tool_calls:
        print("\nTools Used:")
        for call in agent.state.tool_calls:
            print(f"  - {call['tool_name']}: {'Success' if call['success'] else 'Failed'}")
    
    print("\n" + "=" * 50)
    print("Example completed!")


if __name__ == "__main__":
    main()
