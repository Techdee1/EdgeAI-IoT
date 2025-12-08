"""
Test Mode Switching API
Quick test for the mode switching functionality
"""
import requests
import time
import json


def test_mode_switch():
    """Test mode switching API endpoints"""
    base_url = "http://localhost:8080/api"
    
    print("=" * 70)
    print("🧪 TESTING MODE SWITCHING API")
    print("=" * 70)
    
    try:
        # Test 1: Get current mode
        print("\n1️⃣  Testing GET /api/mode...")
        response = requests.get(f"{base_url}/mode")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Current mode: {data['mode']}")
            print(f"   ✅ Switching: {data['switching']}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            return
        
        current_mode = data['mode']
        target_mode = "health" if current_mode == "security" else "security"
        
        # Test 2: Switch mode
        print(f"\n2️⃣  Testing POST /api/switch_mode (to {target_mode})...")
        response = requests.post(
            f"{base_url}/switch_mode",
            json={"mode": target_mode}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ Mode switch initiated: {data['message']}")
                print(f"   ✅ New mode: {data['mode']}")
            else:
                print(f"   ⚠️  Switch failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
        
        # Test 3: Verify mode changed
        print("\n3️⃣  Verifying mode change...")
        time.sleep(1)
        response = requests.get(f"{base_url}/mode")
        if response.status_code == 200:
            data = response.json()
            if data['mode'] == target_mode:
                print(f"   ✅ Mode successfully changed to: {data['mode']}")
            else:
                print(f"   ⚠️  Mode not changed yet: {data['mode']}")
                print(f"   (System may still be switching: {data['switching']})")
        
        # Test 4: Test invalid mode
        print("\n4️⃣  Testing invalid mode...")
        response = requests.post(
            f"{base_url}/switch_mode",
            json={"mode": "invalid_mode"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if not data.get('success'):
                print(f"   ✅ Invalid mode rejected: {data.get('error')}")
            else:
                print(f"   ❌ Should have rejected invalid mode")
        
        # Test 5: Get health stats (if in health mode)
        print("\n5️⃣  Testing health stats endpoint...")
        response = requests.get(f"{base_url}/agriculture/health/stats")
        if response.status_code == 200:
            data = response.json()
            if 'error' in data:
                print(f"   ⚠️  Health data not available: {data['error']}")
            else:
                print(f"   ✅ Health stats retrieved")
                if 'summary' in data:
                    summary = data['summary']
                    print(f"      Total scans: {summary.get('total_scans', 0)}")
                    print(f"      Crops monitored: {summary.get('crops_monitored', 0)}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
        
        print("\n" + "=" * 70)
        print("✅ MODE SWITCHING TEST COMPLETE")
        print("=" * 70)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error: Dashboard not running")
        print("   Start the dashboard first: python launch_integrated.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_mode_switch()
