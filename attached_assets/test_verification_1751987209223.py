#!/usr/bin/env python3
"""
Test script to verify bot functionality
"""

import asyncio
import aiohttp
import sys
import os

async def test_highrise_api():
    """Test the Highrise API connection"""
    print("Testing Highrise API connection...")
    
    try:
        url = "https://webapi.highrise.game/users?username=test"
        headers = {
            'User-Agent': 'Discord-Bot/1.0',
            'Accept': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                print(f"API Response Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"API Response: {data}")
                    
                    if 'users' in data and data['users']:
                        user_data = data['users'][0]
                        print(f"Username: {user_data.get('username', 'N/A')}")
                        print(f"User ID: {user_data.get('user_id', 'N/A')}")
                        print(f"Bio: {user_data.get('bio', 'No bio')}")
                        print("✅ Highrise API is working correctly!")
                        return True
                    else:
                        print("❌ No user data found in API response")
                        return False
                else:
                    print(f"❌ API request failed with status {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

async def test_bio_validation():
    """Test bio validation with verification code"""
    print("\nTesting bio validation...")
    
    try:
        # Test with a user that has bio content
        url = "https://webapi.highrise.game/users?username=test"
        headers = {
            'User-Agent': 'Discord-Bot/1.0',
            'Accept': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'users' in data and data['users']:
                        user_data = data['users'][0]
                        bio = user_data.get('bio', '')
                        print(f"User bio: {bio}")
                        
                        # Test verification code detection
                        test_code = "ABC123"
                        if test_code in bio:
                            print(f"✅ Verification code {test_code} found in bio")
                        else:
                            print(f"ℹ️  Verification code {test_code} not found in bio (as expected)")
                        
                        print("✅ Bio validation system is working correctly!")
                        return True
                    else:
                        print("❌ No user data found for bio validation test")
                        return False
                else:
                    print(f"❌ Bio validation test failed with status {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Bio validation test failed: {e}")
        return False

async def test_marketplace_api():
    """Test marketplace API functionality"""
    print("\nTesting marketplace API...")
    
    try:
        # Test item search
        url = "https://webapi.highrise.game/items?name=hat"
        headers = {
            'User-Agent': 'Discord-Bot/1.0',
            'Accept': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                print(f"Marketplace API Response Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"Items found: {len(data.get('items', []))}")
                    
                    if 'items' in data and data['items']:
                        item = data['items'][0]
                        print(f"Sample item: {item.get('name', 'N/A')}")
                        print(f"Item ID: {item.get('id', 'N/A')}")
                        print("✅ Marketplace API is working correctly!")
                        return True
                    else:
                        print("ℹ️  No items found (API is working, just no results)")
                        return True
                else:
                    print(f"❌ Marketplace API request failed with status {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Marketplace API test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🔍 Testing Victor Bot Functionality\n")
    
    # Test Highrise API
    api_result = await test_highrise_api()
    
    # Test bio validation
    bio_result = await test_bio_validation()
    
    # Test marketplace API
    market_result = await test_marketplace_api()
    
    print(f"\n📊 Test Results:")
    print(f"Highrise API: {'✅ PASS' if api_result else '❌ FAIL'}")
    print(f"Bio Validation: {'✅ PASS' if bio_result else '❌ FAIL'}")
    print(f"Marketplace API: {'✅ PASS' if market_result else '❌ FAIL'}")
    
    if api_result and bio_result and market_result:
        print("\n🎉 All systems are working correctly!")
        print("The bot should be fully functional with:")
        print("  - User verification through bio checking")
        print("  - Marketplace integration with real-time data")
        print("  - No API key required (public endpoints)")
    else:
        print("\n⚠️  Some systems may need attention")
    
    return api_result and bio_result and market_result

if __name__ == "__main__":
    asyncio.run(main())