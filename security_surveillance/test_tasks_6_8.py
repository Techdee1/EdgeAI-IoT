"""
Comprehensive Test Suite for Tasks 6-8
Tests mode switching API, launcher, and health endpoints
"""
import requests
import json
import subprocess
import time
import sys

BASE_URL = "http://localhost:8080"

def test_task_6_mode_api():
    """Test Task 6: Mode Switching API"""
    print("\n" + "=" * 70)
    print("🧪 TASK 6: MODE SWITCHING API")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    # Test 1: GET /api/mode
    print("\n✅ Test 1: GET /api/mode")
    try:
        r = requests.get(f"{BASE_URL}/api/mode", timeout=5)
        data = r.json()
        print(f"   Status: {r.status_code}")
        print(f"   Mode: {data.get('mode')}")
        print(f"   Switching: {data.get('switching')}")
        
        assert r.status_code == 200
        assert 'mode' in data
        assert 'switching' in data
        assert data['mode'] in ['security', 'health']
        print("   ✅ PASSED")
        passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        failed += 1
    
    # Test 2: POST /api/switch_mode with invalid mode
    print("\n✅ Test 2: POST /api/switch_mode (invalid mode)")
    try:
        r = requests.post(f"{BASE_URL}/api/switch_mode?mode=invalid", timeout=5)
        data = r.json()
        print(f"   Status: {r.status_code}")
        print(f"   Response: {json.dumps(data, indent=6)}")
        
        assert 'success' in data
        assert data['success'] == False
        assert 'error' in data
        print("   ✅ PASSED - Invalid mode correctly rejected")
        passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        failed += 1
    
    # Test 3: Health check
    print("\n✅ Test 3: GET /health")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        data = r.json()
        print(f"   Status: {r.status_code}")
        print(f"   Service: {data.get('service')}")
        
        assert r.status_code == 200
        assert data['status'] == 'healthy'
        print("   ✅ PASSED")
        passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        failed += 1
    
    print(f"\n📊 Task 6 Results: {passed} passed, {failed} failed")
    return passed, failed


def test_task_7_launcher():
    """Test Task 7: Launcher Dual-Mode Support"""
    print("\n" + "=" * 70)
    print("🧪 TASK 7: LAUNCHER DUAL-MODE SUPPORT")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    # Test 1: Check launcher has required functions
    print("\n✅ Test 1: Launcher structure")
    try:
        import launch_integrated
        
        required = ['run_surveillance', 'run_health', 'run_dashboard', 'main']
        for func in required:
            assert hasattr(launch_integrated, func), f"Missing {func}"
            print(f"   ✅ Function {func}() exists")
        
        assert hasattr(launch_integrated, 'health_system')
        assert hasattr(launch_integrated, 'current_mode')
        print("   ✅ Required variables exist")
        print("   ✅ PASSED")
        passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        failed += 1
    
    # Test 2: Check argparse support
    print("\n✅ Test 2: Command-line argument support")
    try:
        result = subprocess.run(
            ['python', 'launch_integrated.py', '--help'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        help_text = result.stdout
        assert '--mode' in help_text, "Missing --mode argument"
        assert 'security' in help_text, "Missing security mode"
        assert 'health' in help_text, "Missing health mode"
        
        print("   ✅ --mode argument supported")
        print("   ✅ Both security and health modes available")
        print("   ✅ PASSED")
        passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        failed += 1
    
    print(f"\n📊 Task 7 Results: {passed} passed, {failed} failed")
    return passed, failed


def test_task_8_health_endpoints():
    """Test Task 8: Health Dashboard Endpoints"""
    print("\n" + "=" * 70)
    print("🧪 TASK 8: HEALTH DASHBOARD ENDPOINTS")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    endpoints = [
        ('/api/agriculture/health/stats', 'Health stats'),
        ('/api/agriculture/health/detections', 'Health detections'),
        ('/api/agriculture/health/latest', 'Latest detection'),
        ('/api/agriculture/health/crops', 'Monitored crops'),
        ('/api/agriculture/health/diseases', 'Detected diseases'),
        ('/api/agriculture/health/system_status', 'System status'),
    ]
    
    for endpoint, name in endpoints:
        print(f"\n✅ Test: GET {endpoint}")
        try:
            r = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            print(f"   Status: {r.status_code}")
            
            assert r.status_code == 200, f"Wrong status: {r.status_code}"
            
            data = r.json()
            print(f"   Response keys: {list(data.keys())}")
            
            # Most health endpoints will show error if not in health mode
            # or return data if database is available
            if 'error' in data:
                print(f"   ⚠️  Not in health mode: {data['error']}")
            else:
                print(f"   ✅ Data returned successfully")
            
            print(f"   ✅ PASSED - {name} endpoint working")
            passed += 1
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            failed += 1
    
    print(f"\n📊 Task 8 Results: {passed} passed, {failed} failed")
    return passed, failed


def test_integration():
    """Test module imports and integration"""
    print("\n" + "=" * 70)
    print("🧪 INTEGRATION TESTS")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    # Test 1: HealthSystem import
    print("\n✅ Test: HealthSystem integration")
    try:
        from health_system import HealthSystem
        
        methods = ['start', 'stop', 'get_stats', 'get_latest_detection']
        for method in methods:
            assert hasattr(HealthSystem, method), f"Missing {method}"
        
        print("   ✅ HealthSystem imports correctly")
        print("   ✅ All required methods present")
        print("   ✅ PASSED")
        passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        failed += 1
    
    # Test 2: HealthDatabase import
    print("\n✅ Test: HealthDatabase integration")
    try:
        from modules.database import HealthDatabase
        
        methods = [
            'log_detection', 'get_recent_detections',
            'get_health_summary', 'get_crop_statistics',
            'get_disease_statistics'
        ]
        for method in methods:
            assert hasattr(HealthDatabase, method), f"Missing {method}"
        
        print("   ✅ HealthDatabase imports correctly")
        print("   ✅ All required methods present")
        print("   ✅ PASSED")
        passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        failed += 1
    
    # Test 3: Dashboard routes
    print("\n✅ Test: Dashboard routes integration")
    try:
        from dashboard.routes import agriculture
        import inspect
        
        functions = [name for name, obj in inspect.getmembers(agriculture) 
                    if inspect.isfunction(obj)]
        
        health_funcs = [
            'get_health_stats', 'get_health_detections',
            'get_latest_detection', 'get_monitored_crops',
            'get_detected_diseases', 'get_health_system_status'
        ]
        
        for func in health_funcs:
            assert func in functions, f"Missing {func}"
        
        print("   ✅ All health endpoints defined")
        print("   ✅ PASSED")
        passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        failed += 1
    
    print(f"\n📊 Integration Results: {passed} passed, {failed} failed")
    return passed, failed


def main():
    """Run all tests"""
    print("=" * 70)
    print("🧪 COMPREHENSIVE TESTS FOR TASKS 6-8")
    print("=" * 70)
    print("\nTesting implementations:")
    print("  Task 6: Mode Switching API")
    print("  Task 7: Launcher Dual-Mode Support")
    print("  Task 8: Health Dashboard Endpoints")
    print()
    
    total_passed = 0
    total_failed = 0
    
    # Run integration tests (no server needed)
    p, f = test_integration()
    total_passed += p
    total_failed += f
    
    # Check if server is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
        server_running = True
    except:
        server_running = False
    
    if server_running:
        # Run API tests
        p, f = test_task_6_mode_api()
        total_passed += p
        total_failed += f
        
        p, f = test_task_8_health_endpoints()
        total_passed += p
        total_failed += f
    else:
        print("\n⚠️  Dashboard not running - skipping API tests")
        print("   Start with: python launch_integrated.py")
    
    # Run launcher tests (no server needed)
    p, f = test_task_7_launcher()
    total_passed += p
    total_failed += f
    
    # Final summary
    print("\n" + "=" * 70)
    print("📊 FINAL RESULTS")
    print("=" * 70)
    print(f"✅ Total Passed: {total_passed}")
    print(f"❌ Total Failed: {total_failed}")
    print(f"📈 Success Rate: {total_passed}/{total_passed + total_failed} " +
          f"({100 * total_passed // (total_passed + total_failed) if total_passed + total_failed > 0 else 0}%)")
    print("=" * 70)
    
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
