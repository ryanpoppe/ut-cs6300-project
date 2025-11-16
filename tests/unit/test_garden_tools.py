import pytest
from agents.tools.garden_tools import (
    GetClimateDataTool,
    QueryPlantDatabaseTool,
    CheckCompanionCompatibilityTool,
    CalculatePlanterLayoutTool,
    GeneratePlantingScheduleTool,
    GenerateGardenVisualizationTool
)


def test_get_climate_data_tool():
    tool = GetClimateDataTool()
    
    result = tool.run(zipcode="94102")
    assert "hardiness_zone" in result
    assert result["hardiness_zone"] == "10a"
    assert "growing_season_days" in result


def test_get_climate_data_invalid_zipcode():
    tool = GetClimateDataTool()
    
    result = tool.run(zipcode="123")
    assert "error" in result


def test_get_climate_data_unknown_zipcode():
    tool = GetClimateDataTool()
    
    result = tool.run(zipcode="99999")
    assert "error" in result


def test_query_plant_database_basic():
    tool = QueryPlantDatabaseTool()
    
    result = tool.run(
        hardiness_zone="10a",
        sun_requirement="full_sun"
    )
    
    assert "plant_list" in result
    assert len(result["plant_list"]) > 0


def test_query_plant_database_with_blacklist():
    tool = QueryPlantDatabaseTool()
    
    result = tool.run(
        hardiness_zone="10a",
        sun_requirement="full_sun",
        blacklist=["Tomato"]
    )
    
    plant_names = [p["common_name"] for p in result["plant_list"]]
    assert "Tomato" not in plant_names


def test_query_plant_database_with_whitelist():
    tool = QueryPlantDatabaseTool()
    
    result = tool.run(
        hardiness_zone="10a",
        sun_requirement="full_sun",
        whitelist=["Basil"]
    )
    
    plant_names = [p["common_name"] for p in result["plant_list"]]
    assert any("Basil" in name for name in plant_names)
    assert all("Basil" in name for name in plant_names)


def test_query_plant_database_no_matches():
    tool = QueryPlantDatabaseTool()
    
    result = tool.run(
        hardiness_zone="1a",
        sun_requirement="full_sun"
    )
    
    assert result["plant_list"] == []
    assert "message" in result


def test_check_companion_compatibility_beneficial():
    tool = CheckCompanionCompatibilityTool()
    
    result = tool.run(plant_a="tomato", plant_b="basil")
    
    assert result["relationship"] == "beneficial"
    assert "confidence" in result


def test_check_companion_compatibility_antagonistic():
    tool = CheckCompanionCompatibilityTool()
    
    result = tool.run(plant_a="tomato", plant_b="fennel")
    
    assert result["relationship"] == "antagonistic"


def test_check_companion_compatibility_neutral():
    tool = CheckCompanionCompatibilityTool()
    
    result = tool.run(plant_a="unknown1", plant_b="unknown2")
    
    assert result["relationship"] == "neutral"


def test_calculate_planter_layout():
    tool = CalculatePlanterLayoutTool()
    
    planter = {
        "length_inches": 48,
        "width_inches": 96,
        "shape": "rectangular"
    }
    
    plants = [
        {"common_name": "Tomato", "spacing_inches": 24, "quantity": 2},
        {"common_name": "Basil", "spacing_inches": 12, "quantity": 4}
    ]
    
    result = tool.run(
        planter_dimensions=planter,
        selected_plants=plants
    )
    
    assert "layout" in result
    assert "utilization_percentage" in result
    assert "warnings" in result
    assert len(result["layout"]) > 0


def test_calculate_planter_layout_overcrowded():
    tool = CalculatePlanterLayoutTool()
    
    planter = {
        "length_inches": 12,
        "width_inches": 12,
        "shape": "rectangular"
    }
    
    plants = [
        {"common_name": "Tomato", "spacing_inches": 24, "quantity": 10}
    ]
    
    result = tool.run(
        planter_dimensions=planter,
        selected_plants=plants
    )
    
    assert len(result["warnings"]) > 0


def test_generate_planting_schedule():
    tool = GeneratePlantingScheduleTool()
    
    plants = [
        {"common_name": "Tomato", "days_to_maturity": 70, "planting_method": "transplant", "continuous_harvest": True}
    ]
    
    frost_dates = {
        "last_spring_frost": "2024-04-15",
        "first_fall_frost": "2024-11-15"
    }
    
    result = tool.run(
        plants=plants,
        frost_dates=frost_dates,
        succession_planting=True
    )
    
    assert "schedule" in result
    assert len(result["schedule"]) > 0


def test_generate_planting_schedule_frost_free():
    tool = GeneratePlantingScheduleTool()
    
    plants = [
        {"common_name": "Tomato", "days_to_maturity": 70, "planting_method": "seed", "continuous_harvest": False}
    ]
    
    frost_dates = {
        "last_spring_frost": "N/A (frost-free)",
        "first_fall_frost": "N/A (frost-free)"
    }
    
    result = tool.run(
        plants=plants,
        frost_dates=frost_dates
    )
    
    assert "schedule" in result
    assert len(result["schedule"]) >= 1


def test_generate_garden_visualization_ascii():
    tool = GenerateGardenVisualizationTool()
    
    layout_data = {
        "layout": [
            {
                "plant_name": "Tomato",
                "quantity": 2,
                "positions": [{"x": 12, "y": 12}, {"x": 36, "y": 12}]
            }
        ]
    }
    
    planter_config = {
        "length_inches": 48,
        "width_inches": 48,
        "shape": "rectangular"
    }
    
    result = tool.run(
        layout_data=layout_data,
        planter_config=planter_config,
        format="ascii"
    )
    
    assert "visualization" in result
    assert "legend" in result
    assert isinstance(result["visualization"], str)


def test_generate_garden_visualization_svg():
    tool = GenerateGardenVisualizationTool()
    
    layout_data = {
        "layout": [
            {
                "plant_name": "Basil",
                "quantity": 1,
                "positions": [{"x": 24, "y": 24}]
            }
        ]
    }
    
    planter_config = {
        "length_inches": 48,
        "width_inches": 48,
        "shape": "rectangular"
    }
    
    result = tool.run(
        layout_data=layout_data,
        planter_config=planter_config,
        format="svg"
    )
    
    assert "visualization" in result
    assert "<svg" in result["visualization"]
