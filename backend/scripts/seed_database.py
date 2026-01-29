#!/usr/bin/env python3
"""
Database seeding script for WellnessWay Diet Planner

This script creates sample data for development and testing purposes.
Run this after setting up the database and running migrations.

Usage:
    python scripts/seed_database.py [--clear]
    
Options:
    --clear    Clear existing data before seeding
"""

import asyncio
import sys
import os
from datetime import date, datetime, timedelta
from uuid import uuid4
import json

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User
from app.models.health_context import HealthContextDocument
from app.models.diet_plan import DietPlan
from app.services.health_calculations import (
    calculate_bmr, calculate_tdee, calculate_safety_constraints,
    generate_health_context_document
)
from app.services.health_context_service import HealthContextService
from app.services.diet_plan_service import DietPlanService

# Sample user profiles with diverse characteristics
SAMPLE_USERS = [
    {
        "name": "Alice Johnson",
        "age": 28,
        "gender": "female",
        "height_cm": 165.0,
        "weight_kg": 68.0,
        "body_fat_percentage": 22.0,
        "muscle_mass_kg": 28.0,
        "activity_level": "moderately_active",
        "goals": {
            "primary_goal": "fat_loss",
            "target_weight_kg": 62.0,
            "timeline_weeks": 12
        },
        "preferences": {
            "diet_type": "non_vegetarian",
            "allergies": ["nuts", "shellfish"],
            "foods_to_avoid": ["spicy_food"],
            "meals_per_day": 4,
            "budget_constraints": "moderate",
            "lifestyle_constraints": "busy_professional"
        }
    },
    {
        "name": "Marcus Chen",
        "age": 35,
        "gender": "male",
        "height_cm": 178.0,
        "weight_kg": 75.0,
        "body_fat_percentage": 15.0,
        "muscle_mass_kg": 38.0,
        "activity_level": "very_active",
        "goals": {
            "primary_goal": "muscle_gain",
            "target_weight_kg": 82.0,
            "timeline_weeks": 16
        },
        "preferences": {
            "diet_type": "non_vegetarian",
            "allergies": [],
            "foods_to_avoid": [],
            "meals_per_day": 5,
            "budget_constraints": "flexible",
            "lifestyle_constraints": "gym_enthusiast"
        }
    },
    {
        "name": "Priya Sharma",
        "age": 24,
        "gender": "female",
        "height_cm": 160.0,
        "weight_kg": 55.0,
        "body_fat_percentage": None,
        "muscle_mass_kg": None,
        "activity_level": "lightly_active",
        "goals": {
            "primary_goal": "maintenance",
            "target_weight_kg": None,
            "timeline_weeks": None
        },
        "preferences": {
            "diet_type": "vegetarian",
            "allergies": ["dairy"],
            "foods_to_avoid": ["onion", "garlic"],
            "meals_per_day": 3,
            "budget_constraints": "budget_conscious",
            "lifestyle_constraints": "student"
        }
    },
    {
        "name": "David Rodriguez",
        "age": 42,
        "gender": "male",
        "height_cm": 185.0,
        "weight_kg": 95.0,
        "body_fat_percentage": 28.0,
        "muscle_mass_kg": 35.0,
        "activity_level": "sedentary",
        "goals": {
            "primary_goal": "fat_loss",
            "target_weight_kg": 80.0,
            "timeline_weeks": 24
        },
        "preferences": {
            "diet_type": "non_vegetarian",
            "allergies": ["gluten"],
            "foods_to_avoid": ["processed_food", "sugar"],
            "meals_per_day": 3,
            "budget_constraints": "moderate",
            "lifestyle_constraints": "desk_job"
        }
    },
    {
        "name": "Emma Thompson",
        "age": 31,
        "gender": "female",
        "height_cm": 172.0,
        "weight_kg": 63.0,
        "body_fat_percentage": 18.0,
        "muscle_mass_kg": 32.0,
        "activity_level": "extremely_active",
        "goals": {
            "primary_goal": "muscle_gain",
            "target_weight_kg": 68.0,
            "timeline_weeks": 20
        },
        "preferences": {
            "diet_type": "vegan",
            "allergies": ["soy"],
            "foods_to_avoid": [],
            "meals_per_day": 6,
            "budget_constraints": "flexible",
            "lifestyle_constraints": "athlete"
        }
    }
]

# Sample diet plan content for testing
SAMPLE_WEEKLY_PLAN = {
    "plan_type": "weekly",
    "days": [
        {
            "date": "2024-01-15",
            "day_name": "Monday",
            "meals": [
                {
                    "type": "breakfast",
                    "name": "Oatmeal with Berries and Almonds",
                    "ingredients": [
                        {"name": "rolled oats", "quantity": 50, "unit": "g"},
                        {"name": "mixed berries", "quantity": 100, "unit": "g"},
                        {"name": "almonds", "quantity": 15, "unit": "g"},
                        {"name": "milk", "quantity": 200, "unit": "ml"}
                    ],
                    "instructions": "Cook oats with milk, top with berries and chopped almonds",
                    "nutrition": {
                        "calories": 385,
                        "protein": 15.2,
                        "carbohydrates": 52.3,
                        "fat": 12.8,
                        "fiber": 8.5,
                        "sodium": 125
                    }
                },
                {
                    "type": "lunch",
                    "name": "Grilled Chicken Salad",
                    "ingredients": [
                        {"name": "chicken breast", "quantity": 120, "unit": "g"},
                        {"name": "mixed greens", "quantity": 100, "unit": "g"},
                        {"name": "cherry tomatoes", "quantity": 80, "unit": "g"},
                        {"name": "cucumber", "quantity": 50, "unit": "g"},
                        {"name": "olive oil", "quantity": 10, "unit": "ml"}
                    ],
                    "instructions": "Grill chicken, combine with vegetables, dress with olive oil",
                    "nutrition": {
                        "calories": 295,
                        "protein": 32.5,
                        "carbohydrates": 8.2,
                        "fat": 14.1,
                        "fiber": 3.8,
                        "sodium": 185
                    }
                },
                {
                    "type": "dinner",
                    "name": "Salmon with Quinoa and Vegetables",
                    "ingredients": [
                        {"name": "salmon fillet", "quantity": 150, "unit": "g"},
                        {"name": "quinoa", "quantity": 60, "unit": "g"},
                        {"name": "broccoli", "quantity": 100, "unit": "g"},
                        {"name": "bell peppers", "quantity": 80, "unit": "g"}
                    ],
                    "instructions": "Bake salmon, cook quinoa, steam vegetables",
                    "nutrition": {
                        "calories": 485,
                        "protein": 38.2,
                        "carbohydrates": 35.8,
                        "fat": 18.5,
                        "fiber": 6.2,
                        "sodium": 165
                    }
                }
            ],
            "daily_totals": {
                "calories": 1165,
                "protein": 85.9,
                "carbohydrates": 96.3,
                "fat": 45.4,
                "fiber": 18.5,
                "sodium": 475
            }
        }
        # Additional days would be added here in a real implementation
    ],
    "weekly_totals": {
        "calories": 8155,  # 7 days × ~1165 calories
        "protein": 601.3,
        "carbohydrates": 674.1,
        "fat": 317.8,
        "fiber": 129.5,
        "sodium": 3325
    }
}

SAMPLE_DAILY_PLAN = {
    "plan_type": "daily",
    "date": "2024-01-22",
    "meals": [
        {
            "type": "breakfast",
            "name": "Greek Yogurt Parfait",
            "ingredients": [
                {"name": "greek yogurt", "quantity": 150, "unit": "g"},
                {"name": "granola", "quantity": 30, "unit": "g"},
                {"name": "honey", "quantity": 15, "unit": "ml"},
                {"name": "strawberries", "quantity": 100, "unit": "g"}
            ],
            "instructions": "Layer yogurt with granola and fruit, drizzle with honey",
            "nutrition": {
                "calories": 285,
                "protein": 18.5,
                "carbohydrates": 35.2,
                "fat": 8.1,
                "fiber": 4.2,
                "sodium": 95
            }
        }
    ],
    "daily_totals": {
        "calories": 285,
        "protein": 18.5,
        "carbohydrates": 35.2,
        "fat": 8.1,
        "fiber": 4.2,
        "sodium": 95
    }
}


def clear_existing_data(session):
    """Clear existing data from all tables"""
    print("🗑️  Clearing existing data...")
    
    # Delete in reverse order of dependencies
    session.execute(text("DELETE FROM diet_plans"))
    session.execute(text("DELETE FROM health_context_documents"))
    session.execute(text("DELETE FROM diet_preferences"))
    session.execute(text("DELETE FROM health_goals"))
    session.execute(text("DELETE FROM users"))
    
    session.commit()
    print("✅ Existing data cleared")


def create_sample_users(session):
    """Create sample users with their goals and preferences"""
    print("👥 Creating sample users...")
    
    created_users = []
    
    for user_data in SAMPLE_USERS:
        # Create user
        user = User(
            id=uuid4(),
            name=user_data["name"],
            age=user_data["age"],
            gender=user_data["gender"],
            height_cm=user_data["height_cm"],
            weight_kg=user_data["weight_kg"],
            body_fat_percentage=user_data.get("body_fat_percentage"),
            muscle_mass_kg=user_data.get("muscle_mass_kg"),
            activity_level=user_data["activity_level"]
        )
        
        session.add(user)
        session.flush()  # Get the user ID
        
        # Create health goals
        goals_data = user_data["goals"]
        from app.models.user import HealthGoals
        goals = HealthGoals(
            id=uuid4(),
            user_id=user.id,
            primary_goal=goals_data["primary_goal"],
            target_weight_kg=goals_data.get("target_weight_kg"),
            timeline_weeks=goals_data.get("timeline_weeks")
        )
        session.add(goals)
        
        # Create diet preferences
        prefs_data = user_data["preferences"]
        from app.models.user import DietPreferences
        preferences = DietPreferences(
            id=uuid4(),
            user_id=user.id,
            diet_type=prefs_data["diet_type"],
            allergies=prefs_data["allergies"],
            foods_to_avoid=prefs_data["foods_to_avoid"],
            meals_per_day=prefs_data["meals_per_day"],
            budget_constraints=prefs_data.get("budget_constraints"),
            lifestyle_constraints=prefs_data.get("lifestyle_constraints")
        )
        session.add(preferences)
        
        created_users.append({
            "user": user,
            "goals": goals,
            "preferences": preferences
        })
        
        print(f"  ✅ Created user: {user.name}")
    
    session.commit()
    return created_users


async def create_health_context_documents(session, users_data):
    """Create health context documents for sample users"""
    print("📋 Creating health context documents...")
    
    hcd_service = HealthContextService(session)
    created_hcds = []
    
    for user_data in users_data:
        user = user_data["user"]
        goals = user_data["goals"]
        preferences = user_data["preferences"]
        
        # Generate HCD using the service method
        hcd = await hcd_service.update_health_context_from_profile(user.id)
        created_hcds.append(hcd)
        
        print(f"  ✅ Created HCD for {user.name} (BMR: {hcd.bmr_calories:.0f}, TDEE: {hcd.tdee_calories:.0f})")
    
    return created_hcds


async def create_sample_diet_plans(session, users_data, hcds):
    """Create sample diet plans for users"""
    print("🍽️  Creating sample diet plans...")
    
    diet_plan_service = DietPlanService(session)
    
    for i, (user_data, hcd) in enumerate(zip(users_data, hcds)):
        user = user_data["user"]
        
        try:
            # Create a weekly plan for some users
            if i % 2 == 0:  # Every other user gets a weekly plan
                weekly_plan = DietPlan(
                    id=uuid4(),
                    user_id=user.id,
                    hcd_id=hcd.id,
                    plan_type="weekly",
                    start_date=date.today(),
                    content=SAMPLE_WEEKLY_PLAN
                )
                session.add(weekly_plan)
                print(f"  ✅ Created weekly plan for {user.name}")
            
            # Create a daily plan for all users
            daily_plan = DietPlan(
                id=uuid4(),
                user_id=user.id,
                hcd_id=hcd.id,
                plan_type="daily",
                start_date=date.today(),
                content=SAMPLE_DAILY_PLAN
            )
            session.add(daily_plan)
            print(f"  ✅ Created daily plan for {user.name}")
            
        except Exception as e:
            print(f"  ⚠️  Could not create AI-generated plan for {user.name}: {e}")
            print(f"     Using sample plan instead")
    
    session.commit()


def print_summary(session):
    """Print a summary of created data"""
    print("\n📊 Database Seeding Summary:")
    
    # Count records
    user_count = session.execute(text("SELECT COUNT(*) FROM users")).scalar()
    hcd_count = session.execute(text("SELECT COUNT(*) FROM health_context_documents")).scalar()
    plan_count = session.execute(text("SELECT COUNT(*) FROM diet_plans")).scalar()
    
    print(f"  👥 Users: {user_count}")
    print(f"  📋 Health Context Documents: {hcd_count}")
    print(f"  🍽️  Diet Plans: {plan_count}")
    
    # Show sample user info
    print("\n👥 Sample Users Created:")
    users = session.execute(text("""
        SELECT u.name, u.age, u.gender, u.activity_level, hg.primary_goal, dp.diet_type
        FROM users u
        LEFT JOIN health_goals hg ON u.id = hg.user_id
        LEFT JOIN diet_preferences dp ON u.id = dp.user_id
        ORDER BY u.name
    """)).fetchall()
    
    for user in users:
        print(f"  • {user[0]} ({user[1]}y, {user[2]}, {user[3]}, goal: {user[4]}, diet: {user[5]})")


async def main():
    """Main seeding function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed the WellnessWay database with sample data")
    parser.add_argument("--clear", action="store_true", help="Clear existing data before seeding")
    args = parser.parse_args()
    
    print("🌱 WellnessWay Database Seeding")
    print("=" * 40)
    
    # Get database connection
    engine = create_engine(settings.get_database_url())
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Clear existing data if requested
        if args.clear:
            clear_existing_data(session)
        
        # Create sample data
        users_data = create_sample_users(session)
        hcds = await create_health_context_documents(session, users_data)
        await create_sample_diet_plans(session, users_data, hcds)
        
        # Print summary
        print_summary(session)
        
        print("\n🎉 Database seeding completed successfully!")
        print("\nYou can now:")
        print("  • Connect to the database to view the sample data")
        print("  • Test the API endpoints with existing users")
        print("  • Use the frontend with realistic data")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    asyncio.run(main())