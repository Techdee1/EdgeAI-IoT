"""
Test Health Database
"""
from modules.database import HealthDatabase
from datetime import datetime
import os


def test_health_database():
    """Test HealthDatabase functionality"""
    
    print("=" * 70)
    print("Testing HealthDatabase")
    print("=" * 70)
    
    # Create test database
    test_db_path = 'data/test_output/test_health.db'
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    print("\n1️⃣ Initializing HealthDatabase...")
    db = HealthDatabase(db_path=test_db_path)
    
    # Test detection data
    test_detections = [
        {
            'crop_type': 'Tomato',
            'disease_class': 'Tomato___Late_blight',
            'disease_name': 'Late blight',
            'confidence': 0.89,
            'is_healthy': False,
            'recommendations': {
                'severity': 'critical',
                'symptoms': ['Water-soaked spots', 'White fuzzy growth'],
                'organic_treatment': ['Remove infected plants', 'Apply copper'],
                'chemical_treatment': ['Chlorothalonil', 'Mancozeb'],
                'prevention': ['Plant resistant varieties', 'Avoid overhead watering']
            }
        },
        {
            'crop_type': 'Tomato',
            'disease_class': 'Tomato___healthy',
            'disease_name': 'healthy',
            'confidence': 0.95,
            'is_healthy': True,
            'recommendations': {
                'severity': 'none',
                'symptoms': [],
                'organic_treatment': [],
                'chemical_treatment': [],
                'prevention': ['Maintain good practices']
            }
        },
        {
            'crop_type': 'Potato',
            'disease_class': 'Potato___Early_blight',
            'disease_name': 'Early blight',
            'confidence': 0.78,
            'is_healthy': False,
            'recommendations': {
                'severity': 'moderate',
                'symptoms': ['Dark brown spots with rings', 'Lower leaves affected'],
                'organic_treatment': ['Apply copper fungicides', 'Remove infected leaves'],
                'chemical_treatment': ['Chlorothalonil', 'Azoxystrobin'],
                'prevention': ['Rotate crops', 'Avoid overhead irrigation']
            }
        }
    ]
    
    print("\n2️⃣ Logging test detections...")
    for i, detection in enumerate(test_detections, 1):
        db.log_detection(detection)
        print(f"   Logged detection {i}/{len(test_detections)}: {detection['disease_name']}")
    
    print("\n3️⃣ Testing get_recent_detections...")
    recent = db.get_recent_detections(limit=5)
    print(f"   Retrieved {len(recent)} recent detections")
    for det in recent:
        print(f"   • {det['crop_type']}: {det['disease_name']} ({det['confidence']*100:.1f}%)")
    
    print("\n4️⃣ Testing get_disease_statistics...")
    disease_stats = db.get_disease_statistics()
    print(f"   Found {len(disease_stats)} diseases in statistics")
    for stat in disease_stats:
        print(f"   • {stat['disease_class']}: {stat['total_detections']} detections, "
              f"avg confidence {stat['avg_confidence']*100:.1f}%")
    
    print("\n5️⃣ Testing get_crop_statistics...")
    crop_stats = db.get_crop_statistics()
    print(f"   Monitoring {len(crop_stats)} crops")
    for stat in crop_stats:
        health_rate = (stat['healthy_count'] / stat['total_scans'] * 100) if stat['total_scans'] > 0 else 0
        print(f"   • {stat['crop_type']}: {stat['total_scans']} scans, "
              f"{stat['healthy_count']} healthy, {stat['disease_count']} diseased "
              f"(health rate: {health_rate:.1f}%)")
    
    print("\n6️⃣ Testing get_health_summary...")
    summary = db.get_health_summary()
    print(f"   Total detections: {summary['total_detections']}")
    print(f"   Healthy: {summary['healthy_count']} ({summary['health_rate']:.1f}%)")
    print(f"   Disease: {summary['disease_count']}")
    print(f"   Unique diseases: {summary['unique_diseases']}")
    print(f"   Crops monitored: {summary['crops_monitored']}")
    print(f"   Most common disease: {summary['most_common_disease']} "
          f"({summary['most_common_disease_count']} detections)")
    print(f"   Most scanned crop: {summary['most_scanned_crop']} "
          f"({summary['most_scanned_crop_count']} scans)")
    
    print("\n7️⃣ Testing crop filtering...")
    tomato_detections = db.get_recent_detections(limit=10, crop_type='Tomato')
    print(f"   Found {len(tomato_detections)} Tomato detections")
    
    print("\n8️⃣ Testing CSV export...")
    csv_path = 'data/test_output/health_export_test.csv'
    db.export_to_csv(csv_path)
    print(f"   Exported to: {csv_path}")
    
    print("\n9️⃣ Testing cleanup...")
    deleted = db.cleanup_old_records(days=365)  # Won't delete our test data
    print(f"   Cleanup completed: {deleted} records deleted")
    
    print("\n" + "=" * 70)
    print("✅ All HealthDatabase tests passed!")
    print("=" * 70)
    
    return True


def test_health_database_integration():
    """Test HealthDatabase with HealthSystem integration"""
    
    print("\n" + "=" * 70)
    print("Testing HealthDatabase Integration")
    print("=" * 70)
    
    from modules.crop_detector import CropDiseaseDetector
    import numpy as np
    
    # Create detector
    print("\n1️⃣ Initializing CropDiseaseDetector...")
    detector = CropDiseaseDetector()
    detector.load_model()
    
    # Create database
    test_db_path = 'data/test_output/test_health_integration.db'
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    print("\n2️⃣ Initializing HealthDatabase...")
    db = HealthDatabase(db_path=test_db_path)
    
    # Run detections and log
    print("\n3️⃣ Running detections and logging...")
    for i in range(3):
        test_frame = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
        detection, _ = detector.detect_disease(test_frame, draw_results=False)
        db.log_detection(detection)
        print(f"   Logged detection {i+1}: {detection['disease_name']}")
    
    # Check summary
    print("\n4️⃣ Checking summary...")
    summary = db.get_health_summary()
    print(f"   Total detections: {summary['total_detections']}")
    print(f"   Health rate: {summary['health_rate']:.1f}%")
    
    print("\n" + "=" * 70)
    print("✅ Integration test passed!")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    try:
        # Run database tests
        test_health_database()
        
        # Run integration test
        test_health_database_integration()
        
        print("\n" + "=" * 70)
        print("✅ ALL HEALTH DATABASE TESTS PASSED")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
