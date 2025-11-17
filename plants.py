from agents.tools.garden_tools import QueryPlantDatabaseTool

def main():
    print("Testing plant database...")
    tool = QueryPlantDatabaseTool()
    
    result = tool.run(
        hardiness_zone="8b",
        sun_requirement="full_sun",
        #plant_type="vegetable"
    )
    print("Plants suitable for zone 8b with full sun:")
    print(result)


if __name__ == "__main__":
    main()
