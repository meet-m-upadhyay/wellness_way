#!/usr/bin/env python3
"""
Simple HuggingFace API test to check if the key works
"""

import requests
import json
import os

# Test the API key with a simple request (loaded from environment)
api_key = os.getenv("HUGGINGFACE_API_KEY")
if not api_key:
    print("HUGGINGFACE_API_KEY not set in environment; set it before running this test.")
    exit(1)

# Try the new Inference Providers API format
endpoints_to_test = [
    "https://router.huggingface.co/v1/chat/completions"
]

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Try different models that should be supported by Inference Providers
payloads_to_test = [
    # Try popular chat models that should be available
    {
        "model": "meta-llama/Llama-3.2-1B-Instruct",
        "messages": [
            {"role": "user", "content": "Hello!"}
        ],
        "max_tokens": 50
    },
    {
        "model": "microsoft/Phi-3-mini-4k-instruct",
        "messages": [
            {"role": "user", "content": "Hello!"}
        ],
        "max_tokens": 50
    },
    {
        "model": "Qwen/Qwen2.5-0.5B-Instruct",
        "messages": [
            {"role": "user", "content": "Hello!"}
        ],
        "max_tokens": 50
    },
    {
        "model": "HuggingFaceH4/zephyr-7b-beta",
        "messages": [
            {"role": "user", "content": "Hello!"}
        ],
        "max_tokens": 50
    }
]

# First, let's check if the API key is valid by testing a simple endpoint
print("🔑 Testing API key validity...")
try:
    # Test with a simple model info request
    response = requests.get(
        "https://huggingface.co/api/models/gpt2",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=10
    )
    print(f"Model info status: {response.status_code}")
    if response.status_code == 401:
        print("❌ API key is invalid")
        exit(1)
    elif response.status_code == 200:
        print("✅ API key appears to be valid")
    else:
        print(f"❓ Unexpected status: {response.status_code}")
except Exception as e:
    print(f"❌ Error testing API key: {e}")

print("\n" + "="*60)
print("🧪 Testing inference endpoints...")

for endpoint in endpoints_to_test:
    print(f"\n🎯 Testing endpoint: {endpoint}")
    
    for i, payload in enumerate(payloads_to_test):
        print(f"  📦 Payload format {i+1}:")
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            print(f"    Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"    ✅ SUCCESS! Response: {str(result)[:200]}...")
                print(f"    🎉 Working endpoint: {endpoint}")
                print(f"    🎉 Working payload: {json.dumps(payload, indent=2)}")
                exit(0)
            elif response.status_code == 503:
                print("    ✅ API key valid - model loading (503)")
                print(f"    Response: {response.text[:200]}")
                # This is actually success - the API key works
                print(f"    🎉 API key is working! Endpoint: {endpoint}")
                exit(0)
            elif response.status_code == 401:
                print("    ❌ Invalid API key")
                exit(1)
            elif response.status_code == 410:
                print("    ⚠️ Endpoint deprecated")
                print(f"    Response: {response.text[:200]}")
            else:
                print(f"    ❓ Status {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")

print("\n❌ No working endpoints found")