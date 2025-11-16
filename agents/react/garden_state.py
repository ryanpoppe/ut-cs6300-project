from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from agents.core.agent_state import AgentState


@dataclass
class UserInput:
    zipcode: str
    planters: List[Dict[str, Any]]
    shade_level: str
    growing_goals: List[str]
    plant_preferences: Dict[str, List[str]]


@dataclass
class ClimateInfo:
    hardiness_zone: str
    last_spring_frost: str
    first_fall_frost: str
    growing_season_days: int


@dataclass
class Plant:
    common_name: str
    scientific_name: str
    plant_type: str
    hardiness_zones: List[str]
    sun_requirement: str
    water_needs: str
    space_category: str
    spacing_inches: float
    days_to_maturity: int
    planting_method: str
    height_inches: float
    spread_inches: float
    continuous_harvest: bool
    companion_plants: List[str]
    antagonist_plants: List[str]


@dataclass
class PlantLayout:
    layout: List[Dict[str, Any]]
    utilization_percentage: float
    warnings: List[str]


@dataclass
class PlantingSchedule:
    schedule: List[Dict[str, Any]]


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class GardenPlanState(AgentState):
    def __init__(self):
        super().__init__()
        self.user_requirements: Optional[UserInput] = None
        self.climate_data: Optional[ClimateInfo] = None
        self.candidate_plants: List[Plant] = []
        self.compatibility_matrix: Dict[tuple, Dict[str, Any]] = {}
        self.layout: Optional[PlantLayout] = None
        self.schedule: Optional[PlantingSchedule] = None
        self.validation_status: Optional[ValidationResult] = None
        self.current_phase: str = "discovery"
    
    def set_user_requirements(self, requirements: UserInput):
        self.user_requirements = requirements
        self.metadata["user_requirements"] = {
            "zipcode": requirements.zipcode,
            "planters": requirements.planters,
            "shade_level": requirements.shade_level,
            "growing_goals": requirements.growing_goals,
            "plant_preferences": requirements.plant_preferences
        }
    
    def set_climate_data(self, climate: ClimateInfo):
        self.climate_data = climate
        self.metadata["climate_data"] = {
            "hardiness_zone": climate.hardiness_zone,
            "last_spring_frost": climate.last_spring_frost,
            "first_fall_frost": climate.first_fall_frost,
            "growing_season_days": climate.growing_season_days
        }
    
    def add_candidate_plant(self, plant: Plant):
        self.candidate_plants.append(plant)
    
    def set_compatibility(self, plant_a: str, plant_b: str, relationship: Dict[str, Any]):
        self.compatibility_matrix[(plant_a, plant_b)] = relationship
    
    def set_layout(self, layout: PlantLayout):
        self.layout = layout
        self.metadata["layout"] = {
            "utilization": layout.utilization_percentage,
            "warnings": layout.warnings
        }
    
    def set_schedule(self, schedule: PlantingSchedule):
        self.schedule = schedule
    
    def set_validation(self, validation: ValidationResult):
        self.validation_status = validation
    
    def advance_phase(self, next_phase: str):
        self.current_phase = next_phase
        self.metadata["current_phase"] = next_phase
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict["garden_specific"] = {
            "current_phase": self.current_phase,
            "has_climate_data": self.climate_data is not None,
            "candidate_plants_count": len(self.candidate_plants),
            "has_layout": self.layout is not None,
            "has_schedule": self.schedule is not None
        }
        return base_dict
