from agents.tools.pfaf_database import PFAFDatabase


# print out plant data for testing
if __name__ == "__main__":
    db = PFAFDatabase()
    plant_name = "Basil"
    plant = db.get_plant_by_name(plant_name)
    if plant:
        print(f"Plant Data for '{plant_name}':")
        for key, value in plant.items():
            print(f"{key}: {value}")
    else:
        print(f"Plant '{plant_name}' not found in database.")
