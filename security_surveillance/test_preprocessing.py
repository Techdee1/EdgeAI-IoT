"""
Test Preprocessing Module
Tests for image preprocessing, input handling, and camera management
"""
import unittest
import cv2
import numpy as np
from pathlib import Path
import tempfile
import base64
from modules.preprocessing import (
    ImagePreprocessor,
    ImageInputHandler,
    CameraManager,
    preprocess_for_detection,
    preprocess_for_classification
)


class TestImagePreprocessor(unittest.TestCase):
    """Test ImagePreprocessor class"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.preprocessor = ImagePreprocessor(target_size=(640, 640))
        
        # Create test image (300x200, BGR)
        self.test_image = np.random.randint(0, 255, (200, 300, 3), dtype=np.uint8)
    
    def test_resize_frame_no_aspect(self):
        """Test resize without maintaining aspect ratio"""
        resized = self.preprocessor.resize_frame(
            self.test_image,
            size=(640, 640),
            maintain_aspect=False
        )
        
        self.assertEqual(resized.shape, (640, 640, 3))
    
    def test_resize_frame_with_aspect(self):
        """Test resize with aspect ratio preservation"""
        resized = self.preprocessor.resize_frame(
            self.test_image,
            size=(640, 640),
            maintain_aspect=True
        )
        
        self.assertEqual(resized.shape, (640, 640, 3))
    
    def test_normalize_standard(self):
        """Test standard normalization"""
        normalized = self.preprocessor.normalize_image(
            self.test_image,
            method='standard'
        )
        
        # Should be in range [0, 1]
        self.assertTrue(np.all(normalized >= 0))
        self.assertTrue(np.all(normalized <= 1))
        self.assertEqual(normalized.dtype, np.float32)
    
    def test_normalize_imagenet(self):
        """Test ImageNet normalization"""
        normalized = self.preprocessor.normalize_image(
            self.test_image,
            method='imagenet'
        )
        
        self.assertEqual(normalized.dtype, np.float32)
    
    def test_normalize_minmax(self):
        """Test min-max normalization"""
        normalized = self.preprocessor.normalize_image(
            self.test_image,
            method='minmax'
        )
        
        self.assertTrue(np.all(normalized >= 0))
        self.assertTrue(np.all(normalized <= 1))
    
    def test_apply_clahe(self):
        """Test CLAHE enhancement"""
        enhanced = self.preprocessor.apply_clahe(self.test_image)
        
        self.assertEqual(enhanced.shape, self.test_image.shape)
        self.assertEqual(enhanced.dtype, np.uint8)
    
    def test_gaussian_blur(self):
        """Test Gaussian blur"""
        blurred = self.preprocessor.apply_gaussian_blur(self.test_image)
        
        self.assertEqual(blurred.shape, self.test_image.shape)
    
    def test_sharpening(self):
        """Test sharpening filter"""
        sharpened = self.preprocessor.apply_sharpening(self.test_image)
        
        self.assertEqual(sharpened.shape, self.test_image.shape)
    
    def test_brightness_contrast(self):
        """Test brightness/contrast adjustment"""
        adjusted = self.preprocessor.adjust_brightness_contrast(
            self.test_image,
            brightness=20,
            contrast=10
        )
        
        self.assertEqual(adjusted.shape, self.test_image.shape)
        self.assertEqual(adjusted.dtype, np.uint8)
    
    def test_auto_white_balance(self):
        """Test automatic white balance"""
        balanced = self.preprocessor.auto_white_balance(self.test_image)
        
        self.assertEqual(balanced.shape, self.test_image.shape)
        self.assertEqual(balanced.dtype, np.uint8)


class TestImageInputHandler(unittest.TestCase):
    """Test ImageInputHandler class"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.handler = ImageInputHandler()
        
        # Create test image
        self.test_image = np.random.randint(0, 255, (200, 300, 3), dtype=np.uint8)
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
    
    def test_load_from_file(self):
        """Test loading image from file"""
        # Save test image
        test_path = Path(self.temp_dir) / "test_image.jpg"
        cv2.imwrite(str(test_path), self.test_image)
        
        # Load image
        loaded = self.handler.load_from_file(test_path)
        
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.shape, self.test_image.shape)
    
    def test_load_from_file_not_found(self):
        """Test loading non-existent file"""
        loaded = self.handler.load_from_file("nonexistent.jpg")
        self.assertIsNone(loaded)
    
    def test_encode_decode_base64(self):
        """Test base64 encoding and decoding"""
        # Encode to base64
        base64_str = self.handler.encode_to_base64(self.test_image, format='JPEG')
        
        self.assertTrue(base64_str.startswith('data:image/jpeg;base64,'))
        
        # Decode from base64
        decoded = self.handler.load_from_base64(base64_str)
        
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded.shape, self.test_image.shape)
    
    def test_load_from_bytes(self):
        """Test loading from raw bytes"""
        # Encode to bytes
        _, buffer = cv2.imencode('.jpg', self.test_image)
        img_bytes = buffer.tobytes()
        
        # Load from bytes
        loaded = self.handler.load_from_bytes(img_bytes)
        
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.shape[0], self.test_image.shape[0])
        self.assertEqual(loaded.shape[1], self.test_image.shape[1])
    
    def test_save_to_file(self):
        """Test saving image to file"""
        save_path = Path(self.temp_dir) / "saved_image.jpg"
        
        success = self.handler.save_to_file(self.test_image, save_path)
        
        self.assertTrue(success)
        self.assertTrue(save_path.exists())
        
        # Verify saved image can be loaded
        loaded = cv2.imread(str(save_path))
        self.assertIsNotNone(loaded)


class TestCameraManager(unittest.TestCase):
    """Test CameraManager class"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.manager = CameraManager()
    
    def test_list_available_cameras(self):
        """Test listing available cameras"""
        cameras = self.manager.list_available_cameras()
        
        self.assertIsInstance(cameras, list)
        # Note: May be empty if no cameras available
    
    def test_camera_info_no_connection(self):
        """Test getting camera info without connection"""
        info = self.manager.get_camera_info()
        
        self.assertEqual(info, {})
    
    def test_disconnect_camera(self):
        """Test disconnecting camera"""
        # Should not raise error even if no camera connected
        self.manager.disconnect_camera()
        
        self.assertIsNone(self.manager.camera)
        self.assertIsNone(self.manager.current_source)
    
    def tearDown(self):
        """Cleanup"""
        self.manager.disconnect_camera()


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    def test_preprocess_for_detection(self):
        """Test detection preprocessing"""
        processed = preprocess_for_detection(
            self.test_image,
            target_size=(640, 640),
            normalize=True,
            enhance=False
        )
        
        self.assertEqual(processed.shape, (640, 640, 3))
        # Should be normalized to [0, 1]
        self.assertTrue(np.all(processed >= 0))
        self.assertTrue(np.all(processed <= 1))
    
    def test_preprocess_for_detection_with_enhance(self):
        """Test detection preprocessing with enhancement"""
        processed = preprocess_for_detection(
            self.test_image,
            target_size=(640, 640),
            normalize=False,
            enhance=True
        )
        
        self.assertEqual(processed.shape, (640, 640, 3))
        self.assertEqual(processed.dtype, np.uint8)
    
    def test_preprocess_for_classification(self):
        """Test classification preprocessing"""
        processed = preprocess_for_classification(
            self.test_image,
            target_size=(224, 224),
            normalize_method='imagenet'
        )
        
        self.assertEqual(processed.shape, (224, 224, 3))
        self.assertEqual(processed.dtype, np.float32)
    
    def test_preprocess_for_classification_standard(self):
        """Test classification with standard normalization"""
        processed = preprocess_for_classification(
            self.test_image,
            target_size=(224, 224),
            normalize_method='standard'
        )
        
        self.assertEqual(processed.shape, (224, 224, 3))
        self.assertTrue(np.all(processed >= 0))
        self.assertTrue(np.all(processed <= 1))


def run_tests():
    """Run all preprocessing tests"""
    print("=" * 70)
    print("PREPROCESSING MODULE TESTS")
    print("=" * 70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestImagePreprocessor))
    suite.addTests(loader.loadTestsFromTestCase(TestImageInputHandler))
    suite.addTests(loader.loadTestsFromTestCase(TestCameraManager))
    suite.addTests(loader.loadTestsFromTestCase(TestConvenienceFunctions))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
