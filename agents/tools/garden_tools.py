from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from agents.tools.tool_registry import Tool
from agents.tools.pfaf_database import PFAFDatabase


class GetClimateDataTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_climate_data",
            description="Retrieves USDA hardiness zone and frost dates for a zipcode",
            parameters={
                "zipcode": {
                    "type": "string",
                    "description": "5-digit US postal code",
                    "required": True
                }
            }
        )
        self.climate_database = self._load_climate_data()
    
    def _load_climate_data(self) -> Dict[str, Any]:
        return {
            "94102": {
                "hardiness_zone": "10a",
                "last_spring_frost": "N/A (frost-free)",
                "first_fall_frost": "N/A (frost-free)",
                "growing_season_days": 365
            },
            "10001": {
                "hardiness_zone": "7b",
                "last_spring_frost": "2024-04-15",
                "first_fall_frost": "2024-11-15",
                "growing_season_days": 214
            },
            "55401": {
                "hardiness_zone": "5a",
                "last_spring_frost": "2024-05-10",
                "first_fall_frost": "2024-10-01",
                "growing_season_days": 144
            },
            "78701": {
                "hardiness_zone": "9a",
                "last_spring_frost": "2024-03-01",
                "first_fall_frost": "2024-12-01",
                "growing_season_days": 275
            }
        }
    
    def run(self, **kwargs) -> Dict[str, Any]:
        zipcode = kwargs.get("zipcode")
        
        if not zipcode or len(zipcode) != 5:
            return {"error": "Invalid zipcode format. Please provide a 5-digit US postal code."}
        
        if zipcode not in self.climate_database:
            return {
                "error": f"Zipcode {zipcode} not found in database. Please provide a different zipcode or your USDA zone manually."
            }
        
        return self.climate_database[zipcode]


class QueryPlantDatabaseTool(Tool):
    def __init__(self, pfaf_db: Optional[PFAFDatabase] = None):
        super().__init__(
            name="query_plant_database",
            description="Searches for plants matching growing requirements",
            parameters={
                "hardiness_zone": {
                    "type": "string",
                    "description": "USDA hardiness zone (e.g., '7b')",
                    "required": True
                },
                "sun_requirement": {
                    "type": "string",
                    "enum": ["full_sun", "partial_shade", "full_shade"],
                    "description": "Sunlight needs",
                    "required": True
                },
                "plant_type": {
                    "type": "string",
                    "enum": ["vegetable", "herb", "flower", "fruit", "perennial", "annual"],
                    "description": "Type of plant",
                    "required": False
                },
                "space_category": {
                    "type": "string",
                    "enum": ["small", "medium", "large"],
                    "description": "Space requirement",
                    "required": False
                },
                "growing_goal": {
                    "type": "string",
                    "description": "User's growing goal",
                    "required": False
                },
                "whitelist": {
                    "type": "array",
                    "description": "Specific plants user wants",
                    "required": False
                },
                "blacklist": {
                    "type": "array",
                    "description": "Plants to exclude",
                    "required": False
                }
            }
        )
        try:
            self.pfaf_db = pfaf_db or PFAFDatabase()
            self.use_pfaf = True
        except FileNotFoundError:
            self.use_pfaf = False
            self.plant_database = self._load_fallback_database()
    
    def _load_fallback_database(self) -> List[Dict[str, Any]]:
        return [
            {
                "common_name": "Tomato",
                "scientific_name": "Solanum lycopersicum",
                "plant_type": "vegetable",
                "hardiness_zones": ["3", "4", "5", "6", "7", "8", "9", "10", "11"],
                "sun_requirement": "full_sun",
                "water_needs": "medium",
                "space_category": "medium",
                "spacing_inches": 24,
                "days_to_maturity": 70,
                "planting_method": "transplant",
                "height_inches": 48,
                "spread_inches": 24,
                "continuous_harvest": True,
                "companion_plants": ["basil", "marigold", "carrot"],
                "antagonist_plants": ["cabbage", "fennel"]
            },
            {
                "common_name": "Basil",
                "scientific_name": "Ocimum basilicum",
                "plant_type": "herb",
                "hardiness_zones": ["4", "5", "6", "7", "8", "9", "10", "11"],
                "sun_requirement": "full_sun",
                "water_needs": "medium",
                "space_category": "small",
                "spacing_inches": 12,
                "days_to_maturity": 60,
                "planting_method": "both",
                "height_inches": 18,
                "spread_inches": 12,
                "continuous_harvest": True,
                "companion_plants": ["tomato", "pepper"],
                "antagonist_plants": []
            },
            {
                "common_name": "Lettuce",
                "scientific_name": "Lactuca sativa",
                "plant_type": "vegetable",
                "hardiness_zones": ["2", "3", "4", "5", "6", "7", "8", "9", "10", "11"],
                "sun_requirement": "partial_shade",
                "water_needs": "medium",
                "space_category": "small",
                "spacing_inches": 8,
                "days_to_maturity": 45,
                "planting_method": "both",
                "height_inches": 8,
                "spread_inches": 10,
                "continuous_harvest": True,
                "companion_plants": ["carrot", "radish"],
                "antagonist_plants": []
            },
            {
                "common_name": "Marigold",
                "scientific_name": "Tagetes",
                "plant_type": "flower",
                "hardiness_zones": ["2", "3", "4", "5", "6", "7", "8", "9", "10", "11"],
                "sun_requirement": "full_sun",
                "water_needs": "low",
                "space_category": "small",
                "spacing_inches": 10,
                "days_to_maturity": 50,
                "planting_method": "both",
                "height_inches": 12,
                "spread_inches": 10,
                "continuous_harvest": True,
                "companion_plants": ["tomato", "pepper", "most vegetables"],
                "antagonist_plants": []
            },
            {
                "common_name": "Parsley",
                "scientific_name": "Petroselinum crispum",
                "plant_type": "herb",
                "hardiness_zones": ["5", "6", "7", "8", "9", "10"],
                "sun_requirement": "partial_shade",
                "water_needs": "medium",
                "space_category": "small",
                "spacing_inches": 8,
                "days_to_maturity": 70,
                "planting_method": "both",
                "height_inches": 12,
                "spread_inches": 10,
                "continuous_harvest": True,
                "companion_plants": ["tomato", "asparagus"],
                "antagonist_plants": []
            },
            {
                "common_name": "Pepper",
                "scientific_name": "Capsicum annuum",
                "plant_type": "vegetable",
                "hardiness_zones": ["3", "4", "5", "6", "7", "8", "9", "10", "11"],
                "sun_requirement": "full_sun",
                "water_needs": "medium",
                "space_category": "medium",
                "spacing_inches": 18,
                "days_to_maturity": 70,
                "planting_method": "transplant",
                "height_inches": 24,
                "spread_inches": 18,
                "continuous_harvest": True,
                "companion_plants": ["basil", "onion"],
                "antagonist_plants": ["fennel"]
            },
            {
                "common_name": "Mint",
                "scientific_name": "Mentha",
                "plant_type": "herb",
                "hardiness_zones": ["3", "4", "5", "6", "7", "8", "9", "10", "11"],
                "sun_requirement": "partial_shade",
                "water_needs": "high",
                "space_category": "small",
                "spacing_inches": 12,
                "days_to_maturity": 60,
                "planting_method": "transplant",
                "height_inches": 12,
                "spread_inches": 24,
                "continuous_harvest": True,
                "companion_plants": ["cabbage", "tomato"],
                "antagonist_plants": [],
                "notes": "Invasive - best grown in containers"
            },
            {
                "common_name": "Cilantro",
                "scientific_name": "Coriandrum sativum",
                "plant_type": "herb",
                "hardiness_zones": ["2", "3", "4", "5", "6", "7", "8", "9", "10", "11"],
                "sun_requirement": "partial_shade",
                "water_needs": "medium",
                "space_category": "small",
                "spacing_inches": 6,
                "days_to_maturity": 50,
                "planting_method": "seed",
                "height_inches": 18,
                "spread_inches": 8,
                "continuous_harvest": False,
                "companion_plants": ["beans", "peas"],
                "antagonist_plants": []
            }
        ]
    
    def run(self, **kwargs) -> Dict[str, Any]:
        zone = kwargs.get("hardiness_zone")
        sun = kwargs.get("sun_requirement")
        plant_type = kwargs.get("plant_type")
        whitelist = kwargs.get("whitelist", [])
        blacklist = kwargs.get("blacklist", [])
        
        if self.use_pfaf:
            try:
                results = self.pfaf_db.query_plants(
                    hardiness_zone=zone,
                    sun_requirement=sun,
                    plant_type=plant_type,
                    edible_only=True,
                    whitelist=whitelist,
                    blacklist=blacklist,
                    limit=20
                )
                
                if not results:
                    return {
                        "plant_list": [],
                        "message": "No plants found matching criteria in PFAF database. Consider relaxing constraints.",
                        "source": "PFAF"
                    }
                
                return {
                    "plant_list": results[:10],
                    "source": "PFAF",
                    "total_found": len(results)
                }
            except Exception as e:
                return {
                    "error": f"Error querying PFAF database: {str(e)}",
                    "source": "PFAF"
                }
        
        zone_num = ''.join(filter(str.isdigit, zone)) if zone else ""
        
        results = []
        for plant in self.plant_database:
            if blacklist and plant["common_name"].lower() in [b.lower() for b in blacklist]:
                continue
            
            if whitelist:
                if plant["common_name"].lower() not in [w.lower() for w in whitelist]:
                    continue
            
            if zone_num not in plant["hardiness_zones"]:
                continue
            
            if plant["sun_requirement"] != sun and not (
                sun == "partial_shade" and plant["sun_requirement"] in ["full_sun", "full_shade"]
            ):
                continue
            
            if plant_type and plant["plant_type"] != plant_type:
                continue
            
            results.append(plant)
        
        if not results:
            return {
                "plant_list": [],
                "message": "No plants found matching criteria. Consider relaxing constraints.",
                "source": "fallback"
            }
        
        return {
            "plant_list": results,
            "source": "fallback"
        }


class CheckCompanionCompatibilityTool(Tool):
    def __init__(self):
        super().__init__(
            name="check_companion_compatibility",
            description="Validates companion planting relationships between plants",
            parameters={
                "plant_a": {
                    "type": "string",
                    "description": "First plant name",
                    "required": True
                },
                "plant_b": {
                    "type": "string",
                    "description": "Second plant name",
                    "required": True
                }
            }
        )
        self.compatibility_data = self._load_compatibility_data()
    
    def _load_compatibility_data(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        return {
            "tomato": {
                "basil": {
                    "relationship": "beneficial",
                    "reason": "Basil repels aphids and improves tomato flavor",
                    "confidence": 0.9
                },
                "marigold": {
                    "relationship": "beneficial",
                    "reason": "Marigolds deter nematodes and whiteflies",
                    "confidence": 0.85
                },
                "cabbage": {
                    "relationship": "antagonistic",
                    "reason": "Both are heavy feeders and compete for nutrients",
                    "confidence": 0.7
                },
                "fennel": {
                    "relationship": "antagonistic",
                    "reason": "Fennel inhibits growth of most plants",
                    "confidence": 0.95
                }
            },
            "basil": {
                "pepper": {
                    "relationship": "beneficial",
                    "reason": "Basil repels aphids and thrips that harm peppers",
                    "confidence": 0.85
                }
            },
            "pepper": {
                "fennel": {
                    "relationship": "antagonistic",
                    "reason": "Fennel inhibits pepper growth",
                    "confidence": 0.8
                }
            }
        }
    
    def run(self, **kwargs) -> Dict[str, Any]:
        plant_a = kwargs.get("plant_a", "").lower()
        plant_b = kwargs.get("plant_b", "").lower()
        
        if plant_a in self.compatibility_data:
            if plant_b in self.compatibility_data[plant_a]:
                return self.compatibility_data[plant_a][plant_b]
        
        if plant_b in self.compatibility_data:
            if plant_a in self.compatibility_data[plant_b]:
                return self.compatibility_data[plant_b][plant_a]
        
        return {
            "relationship": "neutral",
            "reason": "No known interaction between these plants",
            "confidence": 0.5
        }


class CalculatePlanterLayoutTool(Tool):
    def __init__(self):
        super().__init__(
            name="calculate_planter_layout",
            description="Computes spatial arrangement of plants in planter",
            parameters={
                "planter_dimensions": {
                    "type": "object",
                    "description": "Planter size and shape",
                    "required": True
                },
                "selected_plants": {
                    "type": "array",
                    "description": "List of plants with spacing requirements",
                    "required": True
                },
                "optimization_goal": {
                    "type": "string",
                    "enum": ["maximize_yield", "maximize_diversity", "aesthetic_arrangement"],
                    "description": "Layout optimization strategy",
                    "required": False
                }
            }
        )
    
    def run(self, **kwargs) -> Dict[str, Any]:
        planter = kwargs.get("planter_dimensions", {})
        plants = kwargs.get("selected_plants", [])
        goal = kwargs.get("optimization_goal", "maximize_diversity")
        
        length = planter.get("length_inches", 0)
        width = planter.get("width_inches", 0)
        shape = planter.get("shape", "rectangular")
        
        if shape == "circular":
            diameter = planter.get("diameter_inches", length)
            area = 3.14159 * (diameter / 2) ** 2
        else:
            area = length * width
        
        layout = []
        used_area = 0
        warnings = []
        
        for i, plant in enumerate(plants):
            spacing = plant.get("spacing_inches", 12)
            plant_area = spacing * spacing
            quantity = plant.get("quantity", 1)
            
            total_plant_area = plant_area * quantity
            
            if used_area + total_plant_area > area * 0.9:
                warnings.append(f"Insufficient space for all {plant['common_name']} plants")
                quantity = int((area * 0.9 - used_area) / plant_area)
                if quantity < 1:
                    continue
            
            x_positions = []
            y_positions = []
            
            for j in range(quantity):
                x = (j % int(length / spacing)) * spacing + spacing / 2
                y = (j // int(length / spacing)) * spacing + spacing / 2
                x_positions.append(x)
                y_positions.append(y)
            
            layout.append({
                "plant_name": plant["common_name"],
                "quantity": quantity,
                "positions": [{"x": x, "y": y} for x, y in zip(x_positions, y_positions)],
                "notes": plant.get("notes", "")
            })
            
            used_area += plant_area * quantity
        
        utilization = (used_area / area) * 100 if area > 0 else 0
        
        if utilization > 90:
            warnings.append("Planter may be overcrowded")
        
        return {
            "layout": layout,
            "utilization_percentage": round(utilization, 2),
            "warnings": warnings
        }


class GeneratePlantingScheduleTool(Tool):
    def __init__(self):
        super().__init__(
            name="generate_planting_schedule",
            description="Creates temporal planting plan based on frost dates",
            parameters={
                "plants": {
                    "type": "array",
                    "description": "Selected plants with maturity data",
                    "required": True
                },
                "frost_dates": {
                    "type": "object",
                    "description": "Last spring and first fall frost dates",
                    "required": True
                },
                "current_date": {
                    "type": "string",
                    "description": "Current date for schedule relevance",
                    "required": False
                },
                "succession_planting": {
                    "type": "boolean",
                    "description": "Whether to plan multiple harvests",
                    "required": False
                }
            }
        )
    
    def run(self, **kwargs) -> Dict[str, Any]:
        plants = kwargs.get("plants", [])
        frost_dates = kwargs.get("frost_dates", {})
        current_date_str = kwargs.get("current_date")
        succession = kwargs.get("succession_planting", False)
        
        current_date = datetime.now()
        if current_date_str and current_date_str != "N/A (frost-free)":
            try:
                current_date = datetime.fromisoformat(current_date_str)
            except:
                pass
        
        last_frost_str = frost_dates.get("last_spring_frost", "")
        first_frost_str = frost_dates.get("first_fall_frost", "")
        
        schedule = []
        
        for plant in plants:
            plant_name = plant.get("common_name", "Unknown")
            days_to_maturity = plant.get("days_to_maturity", 60)
            planting_method = plant.get("planting_method", "seed")
            
            if last_frost_str == "N/A (frost-free)" or not last_frost_str:
                plant_date_start = current_date
                plant_date_end = current_date + timedelta(days=14)
                action = "direct_sow" if planting_method in ["seed", "both"] else "transplant"
            else:
                try:
                    last_frost = datetime.fromisoformat(last_frost_str)
                    
                    if planting_method == "transplant":
                        plant_date_start = last_frost - timedelta(days=42)
                        plant_date_end = last_frost - timedelta(days=28)
                        action = "start_indoors"
                    else:
                        plant_date_start = last_frost + timedelta(days=7)
                        plant_date_end = last_frost + timedelta(days=21)
                        action = "direct_sow"
                except:
                    plant_date_start = current_date
                    plant_date_end = current_date + timedelta(days=14)
                    action = "direct_sow"
            
            expected_harvest = plant_date_end + timedelta(days=days_to_maturity)
            
            schedule.append({
                "plant_name": plant_name,
                "action": action,
                "date_range_start": plant_date_start.strftime("%Y-%m-%d"),
                "date_range_end": plant_date_end.strftime("%Y-%m-%d"),
                "expected_harvest": expected_harvest.strftime("%Y-%m-%d"),
                "notes": f"Plant {plant_name} approximately {days_to_maturity} days before harvest"
            })
            
            if succession and plant.get("continuous_harvest"):
                second_planting = plant_date_end + timedelta(days=21)
                second_harvest = second_planting + timedelta(days=days_to_maturity)
                schedule.append({
                    "plant_name": f"{plant_name} (succession)",
                    "action": action,
                    "date_range_start": second_planting.strftime("%Y-%m-%d"),
                    "date_range_end": (second_planting + timedelta(days=7)).strftime("%Y-%m-%d"),
                    "expected_harvest": second_harvest.strftime("%Y-%m-%d"),
                    "notes": "Succession planting for extended harvest"
                })
        
        return {"schedule": sorted(schedule, key=lambda x: x["date_range_start"])}


class GenerateGardenVisualizationTool(Tool):
    def __init__(self):
        super().__init__(
            name="generate_garden_visualization",
            description="Creates visual representation of garden layout",
            parameters={
                "layout_data": {
                    "type": "object",
                    "description": "Output from calculate_planter_layout",
                    "required": True
                },
                "planter_config": {
                    "type": "object",
                    "description": "Planter dimensions and shape",
                    "required": True
                },
                "format": {
                    "type": "string",
                    "enum": ["svg", "ascii"],
                    "description": "Output format",
                    "required": False
                },
                "style": {
                    "type": "string",
                    "enum": ["top_down", "labeled_diagram"],
                    "description": "Visualization style",
                    "required": False
                }
            }
        )
    
    def run(self, **kwargs) -> Dict[str, Any]:
        layout_data = kwargs.get("layout_data", {})
        planter_config = kwargs.get("planter_config", {})
        format_type = kwargs.get("format", "ascii")
        style = kwargs.get("style", "labeled_diagram")
        
        layout = layout_data.get("layout", [])
        length = planter_config.get("length_inches", 48)
        width = planter_config.get("width_inches", 48)
        
        if format_type == "ascii":
            visualization = self._generate_ascii_layout(layout, length, width)
        else:
            visualization = self._generate_svg_layout(layout, length, width)
        
        legend = {}
        for i, plant_entry in enumerate(layout):
            symbol = chr(65 + i)
            legend[symbol] = plant_entry["plant_name"]
        
        return {
            "visualization": visualization,
            "legend": legend,
            "format": format_type
        }
    
    def _generate_ascii_layout(self, layout: List[Dict], length: float, width: float) -> str:
        grid_width = min(40, int(length / 2))
        grid_height = min(20, int(width / 2))
        
        grid = [[" " for _ in range(grid_width)] for _ in range(grid_height)]
        
        for i, plant_entry in enumerate(layout):
            symbol = chr(65 + i)
            for pos in plant_entry.get("positions", []):
                x = int((pos["x"] / length) * grid_width)
                y = int((pos["y"] / width) * grid_height)
                if 0 <= y < grid_height and 0 <= x < grid_width:
                    grid[y][x] = symbol
        
        border = "+" + "-" * grid_width + "+\n"
        result = border
        for row in grid:
            result += "|" + "".join(row) + "|\n"
        result += border
        
        return result
    
    def _generate_svg_layout(self, layout: List[Dict], length: float, width: float) -> str:
        scale = 4
        svg_width = length * scale
        svg_height = width * scale
        
        svg = f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">\n'
        svg += f'  <rect width="{svg_width}" height="{svg_height}" fill="#8B7355" stroke="black" stroke-width="2"/>\n'
        
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8", "#F7DC6F"]
        
        for i, plant_entry in enumerate(layout):
            color = colors[i % len(colors)]
            for pos in plant_entry.get("positions", []):
                x = pos["x"] * scale
                y = pos["y"] * scale
                svg += f'  <circle cx="{x}" cy="{y}" r="8" fill="{color}" stroke="black" stroke-width="1"/>\n'
        
        svg += '</svg>'
        return svg
