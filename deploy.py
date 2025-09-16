#!/usr/bin/env python3
"""
Deployment test script for Nutrition Mini App
Tests the mini app server locally before deploying to Render
"""

import os
import sys
import time
import subprocess
import requests
from dotenv import load_dotenv

load_dotenv()

def test_mini_app():
    """Test the mini app server"""
    print("🧪 Testing Nutrition Mini App...")

    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("Please copy .env.example to .env and fill in your values:")
        print("cp .env.example .env")
        return False

    # Check required environment variables
    required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file")
        return False

    print("✅ Environment variables configured")

    # Start the server
    print("🚀 Starting mini app server...")
    server_process = subprocess.Popen([sys.executable, 'mini_app_server.py'],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)

    # Wait for server to start
    time.sleep(3)

    try:
        # Test health check
        print("📡 Testing health endpoint...")
        response = requests.get('http://localhost:8080/health', timeout=5)

        if response.status_code == 200:
            print("✅ Health check passed!")
            health_data = response.json()
            print(f"   Status: {health_data.get('status')}")
            print(f"   Service: {health_data.get('service')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False

        # Test main dashboard (without user_id for now)
        print("📱 Testing dashboard endpoint...")
        response = requests.get('http://localhost:8080/nutrition-dashboard?user_id=123', timeout=10)

        if response.status_code == 200:
            print("✅ Dashboard endpoint working!")
            if "Nutrition Activity Rings" in response.text:
                print("✅ HTML template loaded correctly")
            if "Telegram WebApp" in response.text:
                print("✅ Telegram integration included")
        else:
            print(f"❌ Dashboard test failed: {response.status_code}")
            return False

        print("🎉 All tests passed! Mini app is ready for deployment.")
        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False
    finally:
        # Clean up
        server_process.terminate()
        server_process.wait()
        print("🧹 Server stopped")

if __name__ == "__main__":
    success = test_mini_app()
    sys.exit(0 if success else 1)
