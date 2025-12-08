"""
Test Health System
Quick test with simulated camera feed
"""
import cv2
import numpy as np
from health_system import HealthSystem
import time


def test_health_system_basic():
    """Test health system with synthetic frames"""
    
    print("=" * 70)
    print("Testing Health System (Basic)")
    print("=" * 70)
    
    # Create system with test config
    config = {
        'camera': {
            'source': 0,
            'width': 640,
            'height': 480,
            'fps': 10
        },
        'health_system': {
            'model_path': 'data/models/mobilenet_plantvillage.h5',
            'use_tflite': False,
            'confidence_threshold': 0.6,
            'detection_interval': 10  # Detect every 10 frames for testing
        }
    }
    
    print("\n1️⃣ Initializing HealthSystem...")
    system = HealthSystem.__new__(HealthSystem)
    system.config = config
    system.running = False
    system.frame_count = 0
    system.last_detection = None
    system.detection_interval = 10
    system.stats = {
        'total_detections': 0,
        'healthy_count': 0,
        'disease_count': 0,
        'diseases_detected': {},
        'crops_monitored': {}
    }
    system._init_components()
    
    print("\n2️⃣ Testing detection on synthetic frames...")
    
    # Test with 3 synthetic frames
    for i in range(3):
        print(f"\n   Test {i+1}/3:")
        test_frame = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
        system._process_detection(test_frame)
    
    print("\n3️⃣ Getting system statistics...")
    stats = system.get_stats()
    
    print(f"\n📊 Statistics:")
    print(f"   Total detections: {stats['total_detections']}")
    print(f"   Healthy count: {stats['healthy_count']}")
    print(f"   Disease count: {stats['disease_count']}")
    print(f"   Diseases detected: {len(stats['diseases_detected'])}")
    print(f"   Crops monitored: {len(stats['crops_monitored'])}")
    
    print("\n4️⃣ Testing latest detection retrieval...")
    latest = system.get_latest_detection()
    if latest:
        detection = latest['detection']
        print(f"   Latest: {detection['crop_type']} - {detection['disease_name']}")
        print(f"   Confidence: {detection['confidence']*100:.1f}%")
        print(f"   Has recommendations: {len(detection['recommendations']) > 0}")
    
    # Cleanup (database auto-closes)
    
    print("\n" + "=" * 70)
    print("✅ Basic test completed successfully!")
    print("=" * 70)
    
    return True


def test_health_system_overlay():
    """Test the overlay display functionality"""
    
    print("\n" + "=" * 70)
    print("Testing Health System (Overlay)")
    print("=" * 70)
    
    # Create a minimal system
    config = {
        'camera': {'source': 0, 'width': 640, 'height': 480, 'fps': 10},
        'health_system': {
            'model_path': 'data/models/mobilenet_plantvillage.h5',
            'use_tflite': False,
            'confidence_threshold': 0.6,
            'detection_interval': 10
        }
    }
    
    system = HealthSystem.__new__(HealthSystem)
    system.config = config
    system.running = False
    system.frame_count = 0
    system.last_detection = None
    system.detection_interval = 10
    system.stats = {
        'total_detections': 0,
        'healthy_count': 0,
        'disease_count': 0,
        'diseases_detected': {},
        'crops_monitored': {}
    }
    system._init_components()
    
    # Create test frame
    test_frame = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
    
    print("\n1️⃣ Running detection...")
    system._process_detection(test_frame)
    
    print("\n2️⃣ Testing overlay rendering...")
    overlay_frame = system._add_overlay(test_frame.copy())
    
    print(f"   Original frame shape: {test_frame.shape}")
    print(f"   Overlay frame shape: {overlay_frame.shape}")
    print(f"   Overlay applied: {not np.array_equal(test_frame, overlay_frame)}")
    
    # Save test image
    output_path = "data/test_output/health_system_overlay_test.jpg"
    cv2.imwrite(output_path, overlay_frame)
    print(f"   Saved overlay test to: {output_path}")
    
    # Cleanup (database auto-closes)
    
    print("\n" + "=" * 70)
    print("✅ Overlay test completed successfully!")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    try:
        # Run basic test
        test_health_system_basic()
        
        # Run overlay test
        test_health_system_overlay()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
