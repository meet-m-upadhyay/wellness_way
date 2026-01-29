#!/usr/bin/env python3
"""
Test API endpoints via HTTP requests
"""

import asyncio
import aiohttp
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000/api/v1"

async def test_api_endpoints():
    print("🔍 Testing API endpoints via HTTP...")
    
    try:
        async with aiohttp.ClientSession() as session:
            
            # Test daily plan generation
            print("📋 Testing daily plan generation...")
            async with session.post(
                f"{BASE_URL}/diet-plans/daily",
                json={"target_date": "2026-01-19"},
                headers={"X-User-ID": "f53f6cb3-4b52-47ca-9cdb-bb61ece32610"}
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    print(f"✅ Daily plan created: {data['id']}")
                    daily_plan_id = data['id']
                    
                    # Test meal regeneration
                    print("🔄 Testing meal regeneration...")
                    async with session.post(
                        f"{BASE_URL}/diet-plans/{daily_plan_id}/regenerate-meal",
                        json={"day_index": 0, "meal_index": 0},
                        headers={"X-User-ID": "f53f6cb3-4b52-47ca-9cdb-bb61ece32610"}
                    ) as regen_response:
                        if regen_response.status == 200:
                            print("✅ Meal regeneration successful!")
                        else:
                            error_text = await regen_response.text()
                            print(f"❌ Meal regeneration failed: {regen_response.status} - {error_text}")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Daily plan creation failed: {response.status} - {error_text}")
            
            # Test weekly plan generation
            print("📋 Testing weekly plan generation...")
            async with session.post(
                f"{BASE_URL}/diet-plans/weekly",
                json={},
                headers={"X-User-ID": "f53f6cb3-4b52-47ca-9cdb-bb61ece32610"}
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    print(f"✅ Weekly plan created: {data['id']}")
                    weekly_plan_id = data['id']
                    
                    # Test day regeneration
                    print("🔄 Testing day regeneration...")
                    async with session.post(
                        f"{BASE_URL}/diet-plans/{weekly_plan_id}/regenerate-day",
                        json={"day_index": 0},
                        headers={"X-User-ID": "f53f6cb3-4b52-47ca-9cdb-bb61ece32610"}
                    ) as regen_response:
                        if regen_response.status == 200:
                            print("✅ Day regeneration successful!")
                        else:
                            error_text = await regen_response.text()
                            print(f"❌ Day regeneration failed: {regen_response.status} - {error_text}")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Weekly plan creation failed: {response.status} - {error_text}")
            
            # Test getting user plans
            print("📋 Testing get user plans...")
            async with session.get(
                f"{BASE_URL}/diet-plans",
                headers={"X-User-ID": "f53f6cb3-4b52-47ca-9cdb-bb61ece32610"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Retrieved {len(data['plans'])} plans")
                else:
                    error_text = await response.text()
                    print(f"❌ Get plans failed: {response.status} - {error_text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("⚠️  Make sure the backend server is running on localhost:8000")
    print("   Run: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    print()
    asyncio.run(test_api_endpoints())