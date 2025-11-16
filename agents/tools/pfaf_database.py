import sqlite3
import os
from typing import List, Dict, Any, Optional
from pathlib import Path


class PFAFDatabase:
    
    SHADE_MAP = {
        'F': 'full_sun',        # Full sun only
        'S': 'partial_shade',   # Semi-shade / Partial shade
        'N': 'full_sun',        # No shade needed (full sun)
        'FS': 'full_sun',       # Full sun or semi-shade (prefers sun)
        'SN': 'partial_shade',  # Semi-shade or no sun (prefers shade)
        'FSN': 'full_sun'       # Tolerates all (mark as full sun capable)
    }
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "data" / "pfaf-data" / "data.sqlite"
        
        self.db_path = str(db_path)
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"PFAF database not found at {self.db_path}")
    
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def _parse_sun_requirement(self, shade_code: str) -> str:
        if not shade_code:
            return "unknown"
        
        shade_code = shade_code.strip().upper()
        return self.SHADE_MAP.get(shade_code, "unknown")
    
    def _parse_hardiness_zone(self, hardiness: str) -> List[str]:
        if not hardiness:
            return []
        
        zones = []
        parts = hardiness.split('-')
        if len(parts) == 2:
            try:
                start = int(parts[0])
                end = int(parts[1])
                zones = [str(i) for i in range(start, end + 1)]
            except ValueError:
                pass
        
        return zones
    
    def _parse_habit(self, habit: str) -> str:
        if not habit:
            return "unknown"
        
        habit = habit.lower()
        if 'annual' in habit:
            return 'annual'
        elif 'perennial' in habit or 'herb' in habit:
            return 'perennial'
        elif 'tree' in habit:
            return 'tree'
        elif 'shrub' in habit or 'bush' in habit:
            return 'shrub'
        elif 'vine' in habit or 'climber' in habit:
            return 'vine'
        else:
            return habit
    
    def _calculate_spacing(self, habit: str, height: Optional[float]) -> float:
        habit_lower = habit.lower() if habit else ""
        
        if 'tree' in habit_lower:
            return 10.0
        elif 'shrub' in habit_lower:
            return 3.0
        elif 'vine' in habit_lower or 'climber' in habit_lower:
            return 2.0
        elif height and height > 1.0:
            return 1.5
        else:
            return 1.0
    
    def _zone_matches(self, requested_zone: str, plant_hardiness: str) -> bool:
        if not plant_hardiness:
            return False
        
        requested_num = int(''.join(filter(str.isdigit, requested_zone)))
        
        parts = plant_hardiness.split('-')
        if len(parts) == 2:
            try:
                start = int(parts[0])
                end = int(parts[1])
                return start <= requested_num <= end
            except ValueError:
                return False
        
        return str(requested_num) in plant_hardiness
    
    def query_plants(self, 
                     hardiness_zone: Optional[str] = None,
                     sun_requirement: Optional[str] = None,
                     plant_type: Optional[str] = None,
                     edible_only: bool = True,
                     whitelist: Optional[List[str]] = None,
                     blacklist: Optional[List[str]] = None,
                     limit: int = 50) -> List[Dict[str, Any]]:
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                latin_name,
                common_name,
                habit,
                height,
                hardiness,
                shade,
                edibility_rating,
                medicinal_rating,
                summary,
                edible_uses
            FROM plants
            WHERE 1=1
        """
        params = []
        
        if edible_only:
            query += " AND edibility_rating > 0"
        
        if whitelist:
            whitelist_conditions = " OR ".join(["LOWER(common_name) LIKE ?" for _ in whitelist])
            query += f" AND ({whitelist_conditions})"
            params.extend([f"%{w.lower()}%" for w in whitelist])
        
        if plant_type:
            query += " AND LOWER(habit) LIKE ?"
            params.append(f"%{plant_type.lower()}%")
        
        query += f" LIMIT {min(limit * 100, 8000)}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            latin_name, common_name, habit, height, hardiness, shade, edibility, medicinal, summary, edible_uses = row
            
            if hardiness_zone and not self._zone_matches(hardiness_zone, hardiness):
                continue
            
            sun_req = self._parse_sun_requirement(shade)
            
            if sun_requirement and sun_req != "unknown":
                if sun_requirement == "full_sun" and sun_req != "full_sun":
                    continue
                elif sun_requirement == "partial_shade" and sun_req == "full_shade":
                    continue
                elif sun_requirement == "full_shade" and sun_req == "full_sun":
                    continue
            
            if blacklist and any(b.lower() in common_name.lower() for b in blacklist):
                continue
            
            parsed_habit = self._parse_habit(habit)
            spacing = self._calculate_spacing(habit, height)
            zones = self._parse_hardiness_zone(hardiness)
            
            plant = {
                "latin_name": latin_name or "Unknown",
                "common_name": common_name or latin_name or "Unknown",
                "plant_type": parsed_habit,
                "hardiness_zones": zones,
                "sun_requirement": sun_req,
                "spacing_feet": spacing,
                "edibility_rating": edibility or 0,
                "medicinal_rating": medicinal or 0,
                "height_meters": height,
                "summary": summary or "",
                "edible_uses": edible_uses or ""
            }
            
            results.append(plant)
            
            if len(results) >= limit:
                break
        
        conn.close()
        return results
    
    def get_plant_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                latin_name,
                common_name,
                habit,
                height,
                hardiness,
                shade,
                edibility_rating,
                medicinal_rating,
                summary,
                edible_uses,
                cultivation_details,
                propagation
            FROM plants
            WHERE LOWER(common_name) LIKE ? OR LOWER(latin_name) LIKE ?
            LIMIT 1
        """
        
        name_pattern = f"%{name.lower()}%"
        cursor.execute(query, (name_pattern, name_pattern))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        latin_name, common_name, habit, height, hardiness, shade, edibility, medicinal, summary, edible_uses, cultivation, propagation = row
        
        plant = {
            "latin_name": latin_name or "Unknown",
            "common_name": common_name or latin_name or "Unknown",
            "plant_type": self._parse_habit(habit),
            "hardiness_zones": self._parse_hardiness_zone(hardiness),
            "sun_requirement": self._parse_sun_requirement(shade),
            "spacing_feet": self._calculate_spacing(habit, height),
            "edibility_rating": edibility or 0,
            "medicinal_rating": medicinal or 0,
            "height_meters": height,
            "summary": summary or "",
            "edible_uses": edible_uses or "",
            "cultivation_details": cultivation or "",
            "propagation": propagation or ""
        }
        
        conn.close()
        return plant
    
    def get_companion_plants(self, plant_name: str) -> Dict[str, Any]:
        plant = self.get_plant_by_name(plant_name)
        
        if not plant:
            return {
                "beneficial": [],
                "antagonistic": [],
                "note": f"Plant '{plant_name}' not found in database"
            }
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT common_name, plant_type
            FROM plants
            WHERE plant_type = ? AND edibility_rating > 0
            LIMIT 5
        """
        
        cursor.execute(query, (plant['plant_type'],))
        similar_plants = cursor.fetchall()
        
        conn.close()
        
        beneficial = [name for name, _ in similar_plants[:3] if name != plant['common_name']]
        
        return {
            "beneficial": beneficial,
            "antagonistic": [],
            "note": "Companion planting data is limited in PFAF database"
        }
