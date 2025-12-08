"""
Test Crop Disease Detection Module
"""
import cv2
import numpy as np
from modules.crop_detector import CropDiseaseDetector
import sys


def test_crop_detector():
    """Test the crop disease detector with a synthetic image"""
    
    print("=" * 70)
    print("Testing Crop Disease Detector")
    print("=" * 70)
    
    # Initialize detector
    print("\n1️⃣ Initializing CropDiseaseDetector...")
    detector = CropDiseaseDetector(
        model_path="data/models/mobilenet_plantvillage.h5",
        classes_path="data/models/plantvillage_classes.json",
        conf_threshold=0.6,
        use_tflite=False  # Use Keras model for testing
    )
    
    # Load model
    print("\n2️⃣ Loading model...")
    if not detector.load_model():
        print("❌ Failed to load model")
        return False
    
    # Create a test image (random noise for now)
    print("\n3️⃣ Creating test image...")
    test_frame = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
    print(f"   Test frame shape: {test_frame.shape}")
    
    # Test preprocessing
    print("\n4️⃣ Testing preprocessing...")
    preprocessed = detector.preprocess_frame(test_frame)
    print(f"   Preprocessed shape: {preprocessed.shape}")
    print(f"   Value range: [{preprocessed.min():.3f}, {preprocessed.max():.3f}]")
    
    # Test detection
    print("\n5️⃣ Testing disease detection...")
    detection, annotated_frame = detector.detect_disease(test_frame, draw_results=True)
    
    print(f"\n   Detection Results:")
    print(f"   ├─ Disease class: {detection['disease_class']}")
    print(f"   ├─ Crop type: {detection['crop_type']}")
    print(f"   ├─ Disease name: {detection['disease_name']}")
    print(f"   ├─ Confidence: {detection['confidence']*100:.2f}%")
    print(f"   └─ Is healthy: {detection['is_healthy']}")
    
    # Test top-k predictions
    print("\n6️⃣ Testing top-3 predictions...")
    top_predictions = detector.get_top_predictions(test_frame, top_k=3)
    for i, (disease, conf) in enumerate(top_predictions, 1):
        print(f"   {i}. {disease}: {conf*100:.2f}%")
    
    # Test detection summary
    print("\n7️⃣ Testing detection summary...")
    summary = detector.get_detection_summary(detection)
    print(f"   Summary: {summary}")
    
    # Benchmark inference
    print("\n8️⃣ Benchmarking inference speed...")
    stats = detector.benchmark_inference(test_frame, num_runs=10)
    
    # Save test image
    print("\n9️⃣ Saving annotated test image...")
    output_path = "data/test_output/crop_detection_test.jpg"
    cv2.imwrite(output_path, annotated_frame)
    print(f"   Saved to: {output_path}")
    
    print("\n" + "=" * 70)
    print("✅ All tests passed!")
    print("=" * 70)
    
    return True


def test_tflite_detector():
    """Test TFLite version of the detector (for Pi deployment)"""
    
    print("\n" + "=" * 70)
    print("Testing TFLite Crop Disease Detector")
    print("=" * 70)
    
    # Initialize TFLite detector
    print("\n1️⃣ Initializing TFLite CropDiseaseDetector...")
    detector = CropDiseaseDetector(
        model_path="data/models/mobilenet_plantvillage.tflite",
        classes_path="data/models/plantvillage_classes.json",
        conf_threshold=0.6,
        use_tflite=True  # Use TFLite model
    )
    
    # Load model
    print("\n2️⃣ Loading TFLite model...")
    if not detector.load_model():
        print("❌ Failed to load TFLite model")
        return False
    
    # Create test image
    print("\n3️⃣ Creating test image...")
    test_frame = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
    
    # Test detection
    print("\n4️⃣ Testing TFLite disease detection...")
    detection, annotated_frame = detector.detect_disease(test_frame, draw_results=True)
    
    print(f"\n   Detection Results:")
    print(f"   ├─ Disease class: {detection['disease_class']}")
    print(f"   ├─ Crop type: {detection['crop_type']}")
    print(f"   ├─ Disease name: {detection['disease_name']}")
    print(f"   └─ Confidence: {detection['confidence']*100:.2f}%")
    
    # Benchmark TFLite inference
    print("\n5️⃣ Benchmarking TFLite inference speed...")
    stats = detector.benchmark_inference(test_frame, num_runs=10)
    
    print("\n" + "=" * 70)
    print("✅ TFLite tests passed!")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    try:
        # Test Keras model
        success = test_crop_detector()
        
        if success:
            # Test TFLite model
            test_tflite_detector()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Testing interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
