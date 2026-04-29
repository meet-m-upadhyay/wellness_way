import sys
import os
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.connection import SessionLocal
from app.services.ml_diet_pipeline.food_registry.importer import import_food_dataset
from app.services.ml_diet_pipeline.food_registry.providers.usda import USDAFoodRegistryProvider, USDAProviderConfig

mock_records = [
    {"fdcId": 1001, "description": "Oats (rolled, dry)", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 379}, {"nutrientName": "protein", "value": 13.2}, {"nutrientName": "fat", "value": 6.5}, {"nutrientName": "carbohydrate", "value": 67.7}, {"nutrientName": "fiber", "value": 10.1}]},
    {"fdcId": 1002, "description": "Chicken breast", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 120}, {"nutrientName": "protein", "value": 22.5}, {"nutrientName": "fat", "value": 2.6}, {"nutrientName": "carbohydrate", "value": 0}]},
    {"fdcId": 1003, "description": "Broccoli", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 34}, {"nutrientName": "protein", "value": 2.8}, {"nutrientName": "fat", "value": 0.4}, {"nutrientName": "carbohydrate", "value": 0.7}]},
    {"fdcId": 1004, "description": "Olive oil", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 884}, {"nutrientName": "protein", "value": 0}, {"nutrientName": "fat", "value": 100}, {"nutrientName": "carbohydrate", "value": 0}]},
    {"fdcId": 1005, "description": "Milk (whole)", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 61}, {"nutrientName": "protein", "value": 3.2}, {"nutrientName": "fat", "value": 3.3}, {"nutrientName": "carbohydrate", "value": 4.8}]},
    {"fdcId": 1006, "description": "Banana", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 89}, {"nutrientName": "protein", "value": 1.1}, {"nutrientName": "fat", "value": 0.3}, {"nutrientName": "carbohydrate", "value": 22.8}]},
    {"fdcId": 1007, "description": "Almonds", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 579}, {"nutrientName": "protein", "value": 21.2}, {"nutrientName": "fat", "value": 49.9}, {"nutrientName": "carbohydrate", "value": 21.6}]},
    {"fdcId": 1008, "description": "Paneer", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 296}, {"nutrientName": "protein", "value": 18.2}, {"nutrientName": "fat", "value": 22.5}, {"nutrientName": "carbohydrate", "value": 4.5}]},
    {"fdcId": 1009, "description": "Quinoa (dry)", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 368}, {"nutrientName": "protein", "value": 14.1}, {"nutrientName": "fat", "value": 6.1}, {"nutrientName": "carbohydrate", "value": 64.2}]},
    {"fdcId": 1010, "description": "Bell peppers", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 31}, {"nutrientName": "protein", "value": 1.0}, {"nutrientName": "fat", "value": 0.3}, {"nutrientName": "carbohydrate", "value": 6.0}]},
    {"fdcId": 1011, "description": "Greek yogurt (plain)", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 59}, {"nutrientName": "protein", "value": 10.2}, {"nutrientName": "fat", "value": 0.4}, {"nutrientName": "carbohydrate", "value": 3.6}]},
    {"fdcId": 1012, "description": "Tofu (extra-firm)", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 83}, {"nutrientName": "protein", "value": 10.0}, {"nutrientName": "fat", "value": 4.8}, {"nutrientName": "carbohydrate", "value": 1.9}]},
    {"fdcId": 1013, "description": "Spinach", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 23}, {"nutrientName": "protein", "value": 2.9}, {"nutrientName": "fat", "value": 0.4}, {"nutrientName": "carbohydrate", "value": 3.6}]},
    {"fdcId": 1014, "description": "Egg (whole)", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 155}, {"nutrientName": "protein", "value": 12.6}, {"nutrientName": "fat", "value": 10.6}, {"nutrientName": "carbohydrate", "value": 1.1}]},
    {"fdcId": 1015, "description": "Lentils (red, dry)", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 352}, {"nutrientName": "protein", "value": 24.6}, {"nutrientName": "fat", "value": 1.1}, {"nutrientName": "carbohydrate", "value": 63.4}]},
    {"fdcId": 1016, "description": "Black beans (dry)", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 341}, {"nutrientName": "protein", "value": 21.6}, {"nutrientName": "fat", "value": 1.4}, {"nutrientName": "carbohydrate", "value": 62.4}]},
    {"fdcId": 1017, "description": "Chickpeas (dry)", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 364}, {"nutrientName": "protein", "value": 19.3}, {"nutrientName": "fat", "value": 6.0}, {"nutrientName": "carbohydrate", "value": 60.6}]},
    {"fdcId": 1018, "description": "Avocado", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 160}, {"nutrientName": "protein", "value": 2.0}, {"nutrientName": "fat", "value": 14.7}, {"nutrientName": "carbohydrate", "value": 8.5}]},
    {"fdcId": 1019, "description": "Tomatoes", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 18}, {"nutrientName": "protein", "value": 0.9}, {"nutrientName": "fat", "value": 0.2}, {"nutrientName": "carbohydrate", "value": 3.9}]},
    {"fdcId": 1020, "description": "Onions", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 40}, {"nutrientName": "protein", "value": 1.1}, {"nutrientName": "fat", "value": 0.1}, {"nutrientName": "carbohydrate", "value": 9.3}]},
    {"fdcId": 1021, "description": "Sweet potato", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 86}, {"nutrientName": "protein", "value": 1.6}, {"nutrientName": "fat", "value": 0.1}, {"nutrientName": "carbohydrate", "value": 20.1}]},
    {"fdcId": 1022, "description": "Brown rice (dry)", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 364}, {"nutrientName": "protein", "value": 7.5}, {"nutrientName": "fat", "value": 2.7}, {"nutrientName": "carbohydrate", "value": 76.2}]},
    {"fdcId": 1023, "description": "Salmon", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 208}, {"nutrientName": "protein", "value": 20.4}, {"nutrientName": "fat", "value": 13.4}, {"nutrientName": "carbohydrate", "value": 0}]},
    {"fdcId": 1024, "description": "Berries (mixed)", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 50}, {"nutrientName": "protein", "value": 1.0}, {"nutrientName": "fat", "value": 0.5}, {"nutrientName": "carbohydrate", "value": 12.0}]},
    {"fdcId": 1025, "description": "Almond milk", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 15}, {"nutrientName": "protein", "value": 0.6}, {"nutrientName": "fat", "value": 1.1}, {"nutrientName": "carbohydrate", "value": 0.6}]},
    {"fdcId": 1026, "description": "Chia seeds", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 486}, {"nutrientName": "protein", "value": 16.5}, {"nutrientName": "fat", "value": 30.7}, {"nutrientName": "carbohydrate", "value": 42.1}]},
    {"fdcId": 1027, "description": "Apple", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 52}, {"nutrientName": "protein", "value": 0.3}, {"nutrientName": "fat", "value": 0.2}, {"nutrientName": "carbohydrate", "value": 13.8}]},
    {"fdcId": 1028, "description": "Cucumber", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 15}, {"nutrientName": "protein", "value": 0.7}, {"nutrientName": "fat", "value": 0.1}, {"nutrientName": "carbohydrate", "value": 3.6}]},
    {"fdcId": 1029, "description": "Hummus", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 166}, {"nutrientName": "protein", "value": 7.9}, {"nutrientName": "fat", "value": 9.6}, {"nutrientName": "carbohydrate", "value": 14.3}]},
    {"fdcId": 1030, "description": "Peanut butter", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 588}, {"nutrientName": "protein", "value": 25.1}, {"nutrientName": "fat", "value": 50.4}, {"nutrientName": "carbohydrate", "value": 20.0}]},
    {"fdcId": 1031, "description": "Walnuts", "dataType": "Foundation", "foodNutrients": [{"nutrientName": "energy", "value": 654}, {"nutrientName": "protein", "value": 15.2}, {"nutrientName": "fat", "value": 65.2}, {"nutrientName": "carbohydrate", "value": 13.7}]}
]

def main():
    print("Seeding ML Registry...")
    db = SessionLocal()
    try:
        # Use a new dataset version to avoid conflicts
        config = USDAProviderConfig(
            dataset_name="usda_foundation_mock_v4", 
            dataset_version="2026.4", 
            registry_version=1
        )
        provider = USDAFoodRegistryProvider(config=config, records=mock_records)
        import_food_dataset(
            db=db,
            provider=provider,
            dataset_name="usda_foundation_mock_v4",
            dataset_version="2026.4",
            registry_version=1
        )
        print("Done seeding the mock USDA food data!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
