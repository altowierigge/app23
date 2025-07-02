#!/usr/bin/env python3
"""
Test script to demonstrate the API key management functionality.
"""

import asyncio
import httpx
import json


async def test_api_key_management():
    """Test the API key management endpoints."""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        print("🧪 Testing API Key Management Features")
        print("=" * 50)
        
        # 1. Check initial health status
        print("\n1. Checking initial health status...")
        try:
            response = await client.get(f"{base_url}/api/health")
            health = response.json()
            
            print(f"   Overall status: {health['overall_status']}")
            if 'api_keys' in health.get('checks', {}):
                api_status = health['checks']['api_keys']
                print(f"   OpenAI: {'✅' if api_status.get('openai') else '❌'}")
                print(f"   Anthropic: {'✅' if api_status.get('anthropic') else '❌'}")
                print(f"   Google: {'✅' if api_status.get('google') else '❌'}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # 2. Test API key validation (invalid keys)
        print("\n2. Testing API key validation with invalid keys...")
        try:
            invalid_payload = {
                "openai_key": "invalid-key",
                "anthropic_key": "sk-short",
                "google_key": "wrong-prefix"
            }
            
            response = await client.post(
                f"{base_url}/api/settings/apikeys",
                headers={"Content-Type": "application/json"},
                content=json.dumps(invalid_payload)
            )
            
            print(f"   Status: {response.status_code}")
            if response.status_code != 200:
                error = response.json()
                print(f"   Expected validation error: {error['detail']}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # 3. Test API key validation (valid format)
        print("\n3. Testing API key update with valid format...")
        try:
            valid_payload = {
                "openai_key": "sk-" + "a" * 45,  # Valid format but fake key
                "anthropic_key": "sk-ant-" + "b" * 40,  # Valid format but fake key
                "google_key": "AIza" + "c" * 35  # Valid format but fake key
            }
            
            response = await client.post(
                f"{base_url}/api/settings/apikeys",
                headers={"Content-Type": "application/json"},
                content=json.dumps(valid_payload)
            )
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Success: {result['message']}")
                print(f"   Updated keys: {', '.join(result['updated_keys'])}")
            else:
                error = response.json()
                print(f"   ❌ Error: {error['detail']}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # 4. Verify .env file was updated
        print("\n4. Checking if .env file was updated...")
        try:
            with open('.env', 'r') as f:
                env_content = f.read()
                
            if 'OPENAI_API_KEY=sk-' in env_content:
                print("   ✅ OpenAI key found in .env")
            if 'ANTHROPIC_API_KEY=sk-ant-' in env_content:
                print("   ✅ Anthropic key found in .env")
            if 'GOOGLE_API_KEY=AIza' in env_content:
                print("   ✅ Google key found in .env")
                
        except Exception as e:
            print(f"   ❌ Error reading .env: {e}")
        
        # 5. Test API key validation endpoint
        print("\n5. Testing API key validation endpoint...")
        try:
            response = await client.post(f"{base_url}/api/validate-keys")
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   Valid keys: {result['valid_keys']}/{result['total_keys']}")
                print(f"   All valid: {'✅' if result['all_valid'] else '❌'}")
            else:
                error = response.json()
                print(f"   ❌ Error: {error['detail']}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("\n🎉 API Key Management Test Complete!")
        print("\nTo test the web interface:")
        print("1. Open http://localhost:8000/settings in your browser")
        print("2. Configure your actual API keys")
        print("3. Watch the health status update in real-time")


if __name__ == "__main__":
    asyncio.run(test_api_key_management())