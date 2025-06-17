"""
Test Script für Web API Endpoints
"""

import requests
import json
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_api_endpoints():
    """Teste alle API Endpoints"""
    base_url = "http://localhost:5000"
    
    print("🧪 WEB API ENDPOINT TESTS")
    print("=" * 50)
    
    endpoints = [
        "/api/dashboard-data",
        "/api/live-prices",
        "/api/arbitrage-alerts", 
        "/api/performance-data",
        "/api/portfolio-snapshots",
        "/api/telegram-stats",
        "/api/bot-health"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\n📡 Testing {endpoint}...")
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    if 'data' in data:
                        data_count = len(data['data']) if isinstance(data['data'], list) else 'object'
                        print(f"✅ SUCCESS - Data: {data_count}")
                    else:
                        print(f"✅ SUCCESS - {data}")
                else:
                    print(f"⚠️ API returned success=false: {data.get('error')}")
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ CONNECTION ERROR - Server nicht erreichbar")
            break
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 API Tests abgeschlossen!")
    print(f"🌐 Frontend URL: {base_url}")


if __name__ == "__main__":
    print("⏳ Warte 2 Sekunden für Server-Start...")
    time.sleep(2)
    test_api_endpoints()