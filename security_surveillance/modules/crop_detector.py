"""
Crop Disease Detection Module - MobileNetV2 inference pipeline
"""
import tensorflow as tf
import cv2
import numpy as np
from typing import Dict, Tuple, Optional
import time
import json
import os


class CropDiseaseDetector:
    """Handles crop disease detection using MobileNetV2"""
    
    def __init__(self, 
                 model_path: str = "data/models/mobilenet_plantvillage.h5",
                 classes_path: str = "data/models/plantvillage_classes.json",
                 recommendations_path: str = "data/disease_recommendations.json",
                 conf_threshold: float = 0.6,
                 use_tflite: bool = False):
        """
        Initialize crop disease detector
        
        Args:
            model_path: Path to model file (.h5 or .tflite)
            classes_path: Path to class names JSON file
            recommendations_path: Path to disease recommendations JSON file
            conf_threshold: Confidence threshold for predictions (0-1)
            use_tflite: Whether to use TFLite model (for Pi deployment)
        """
        self.model_path = model_path
        self.classes_path = classes_path
        self.recommendations_path = recommendations_path
        self.conf_threshold = conf_threshold
        self.use_tflite = use_tflite
        self.model = None
        self.interpreter = None
        self.class_names = []
        self.recommendations = {}
        self.input_size = (224, 224)
        
        # Load class names and recommendations
        self._load_classes()
        self._load_recommendations()
        
    def _load_classes(self) -> bool:
        """Load class names from JSON file"""
        try:
            if os.path.exists(self.classes_path):
                with open(self.classes_path, 'r') as f:
                    self.class_names = json.load(f)
                print(f"✅ Loaded {len(self.class_names)} disease classes")
                return True
            else:
                print(f"⚠️ Class names file not found: {self.classes_path}")
                return False
        except Exception as e:
            print(f"❌ Error loading class names: {e}")
            return False
    
    def _load_recommendations(self) -> bool:
        """Load disease recommendations from JSON file"""
        try:
            if os.path.exists(self.recommendations_path):
                with open(self.recommendations_path, 'r') as f:
                    self.recommendations = json.load(f)
                print(f"✅ Loaded recommendations for {len(self.recommendations)} diseases")
                return True
            else:
                print(f"⚠️ Recommendations file not found: {self.recommendations_path}")
                return False
        except Exception as e:
            print(f"❌ Error loading recommendations: {e}")
            return False
    
    def load_model(self) -> bool:
        """Load MobileNetV2 model (Keras or TFLite)"""
        try:
            if self.use_tflite:
                # Load TFLite model for Raspberry Pi
                tflite_path = self.model_path.replace('.h5', '.tflite')
                print(f"Loading TFLite model from {tflite_path}...")
                
                self.interpreter = tf.lite.Interpreter(model_path=tflite_path)
                self.interpreter.allocate_tensors()
                
                # Get input and output details
                self.input_details = self.interpreter.get_input_details()
                self.output_details = self.interpreter.get_output_details()
                
                print(f"✅ TFLite model loaded successfully!")
                print(f"   Input shape: {self.input_details[0]['shape']}")
                print(f"   Output shape: {self.output_details[0]['shape']}")
            else:
                # Load Keras model for development/testing
                print(f"Loading Keras model from {self.model_path}...")
                self.model = tf.keras.models.load_model(self.model_path)
                print(f"✅ Keras model loaded successfully!")
                print(f"   Input shape: {self.model.input_shape}")
                print(f"   Output shape: {self.model.output_shape}")
            
            print(f"   Confidence threshold: {self.conf_threshold}")
            print(f"   Classes: {len(self.class_names)}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess frame for MobileNetV2 input
        
        Args:
            frame: Input image (BGR format from OpenCV)
            
        Returns:
            Preprocessed image tensor (1, 224, 224, 3)
        """
        # NOTE: This PlantVillage model was trained on BGR images!
        # Do NOT convert to RGB - it will break predictions
        # Keep the BGR format as-is
        
        # Resize to model input size
        resized = cv2.resize(frame, self.input_size)
        
        # Normalize to [0, 1] range
        normalized = resized.astype(np.float32) / 255.0
        
        # Add batch dimension
        batch = np.expand_dims(normalized, axis=0)
        
        return batch
    
    def detect_disease(self, frame: np.ndarray, 
                       draw_results: bool = True,
                       preprocessed: bool = False) -> Tuple[Dict, np.ndarray]:
        """
        Detect crop disease in a frame
        
        Args:
            frame: Input image (BGR format) or preprocessed tensor if preprocessed=True
            draw_results: Whether to draw results on frame
            preprocessed: If True, frame is already preprocessed and ready for inference
            
        Returns:
            Tuple of (detection dict, annotated frame)
            Detection dict contains: disease_class, confidence, crop_type, disease_name
        """
        if (self.model is None and self.interpreter is None):
            print("⚠️ Model not loaded! Call load_model() first.")
            return {}, frame
        
        # Preprocess frame if needed
        if preprocessed:
            # Frame is already preprocessed, just ensure batch dimension
            if len(frame.shape) == 3:
                input_tensor = np.expand_dims(frame, axis=0)
            else:
                input_tensor = frame
        else:
            input_tensor = self.preprocess_frame(frame)
        
        # Run inference
        if self.use_tflite:
            # TFLite inference
            self.interpreter.set_tensor(self.input_details[0]['index'], input_tensor)
            self.interpreter.invoke()
            predictions = self.interpreter.get_tensor(self.output_details[0]['index'])
        else:
            # Keras inference
            predictions = self.model.predict(input_tensor, verbose=0)
        
        # Apply temperature scaling to sharpen predictions (helps with low-confidence models)
        temperature = 0.5  # Lower = sharper, higher = softer
        predictions_scaled = np.exp(np.log(predictions + 1e-10) / temperature)
        predictions_scaled = predictions_scaled / np.sum(predictions_scaled, axis=-1, keepdims=True)
        
        # Get top prediction
        class_idx = np.argmax(predictions_scaled[0])
        confidence = float(predictions_scaled[0][class_idx])
        
        # Parse disease class name
        disease_class = self.class_names[class_idx] if class_idx < len(self.class_names) else "Unknown"
        
        # Extract crop type and disease name from class string
        # Format: "Crop___Disease" (e.g., "Tomato___Late_blight")
        if "___" in disease_class:
            crop_type, disease_name = disease_class.split("___", 1)
            disease_name = disease_name.replace("_", " ")
        else:
            crop_type = "Unknown"
            disease_name = disease_class.replace("_", " ")
        
        # Get recommendations
        recommendations = self.get_recommendations(disease_class)
        
        detection = {
            'disease_class': disease_class,
            'confidence': confidence,
            'crop_type': crop_type,
            'disease_name': disease_name,
            'is_healthy': 'healthy' in disease_class.lower(),
            'recommendations': recommendations
        }
        
        # Draw results on frame
        annotated_frame = frame.copy()
        if draw_results:
            annotated_frame = self._draw_results(annotated_frame, detection)
        
        return detection, annotated_frame
    
    def _draw_results(self, frame: np.ndarray, detection: Dict) -> np.ndarray:
        """Draw detection results on frame"""
        h, w = frame.shape[:2]
        
        # Determine color based on health status
        if detection['is_healthy']:
            color = (0, 255, 0)  # Green for healthy
            status = "HEALTHY"
        else:
            color = (0, 0, 255)  # Red for diseased
            status = "DISEASE DETECTED"
        
        # Draw top banner
        banner_height = 120
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, banner_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Draw status
        cv2.putText(frame, status, (20, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3)
        
        # Draw crop type
        crop_text = f"Crop: {detection['crop_type']}"
        cv2.putText(frame, crop_text, (20, 65),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Draw disease name
        disease_text = f"Disease: {detection['disease_name']}"
        cv2.putText(frame, disease_text, (20, 95),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Draw confidence
        conf_text = f"Confidence: {detection['confidence']*100:.1f}%"
        cv2.putText(frame, conf_text, (w - 250, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Draw confidence bar
        bar_width = 200
        bar_height = 20
        bar_x = w - 250
        bar_y = 50
        
        # Background bar
        cv2.rectangle(frame, (bar_x, bar_y), 
                     (bar_x + bar_width, bar_y + bar_height),
                     (50, 50, 50), -1)
        
        # Confidence bar
        conf_bar_width = int(bar_width * detection['confidence'])
        cv2.rectangle(frame, (bar_x, bar_y),
                     (bar_x + conf_bar_width, bar_y + bar_height),
                     color, -1)
        
        return frame
    
    def get_top_predictions(self, frame: np.ndarray, top_k: int = 3) -> list:
        """
        Get top-k disease predictions
        
        Args:
            frame: Input image
            top_k: Number of top predictions to return
            
        Returns:
            List of (disease_class, confidence) tuples
        """
        if (self.model is None and self.interpreter is None):
            return []
        
        # Preprocess and predict
        input_tensor = self.preprocess_frame(frame)
        
        if self.use_tflite:
            self.interpreter.set_tensor(self.input_details[0]['index'], input_tensor)
            self.interpreter.invoke()
            predictions = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
        else:
            predictions = self.model.predict(input_tensor, verbose=0)[0]
        
        # Get top-k indices
        top_indices = np.argsort(predictions)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            disease_class = self.class_names[idx] if idx < len(self.class_names) else "Unknown"
            confidence = float(predictions[idx])
            results.append((disease_class, confidence))
        
        return results
    
    def benchmark_inference(self, frame: np.ndarray, num_runs: int = 10) -> dict:
        """
        Benchmark inference speed
        
        Args:
            frame: Test frame
            num_runs: Number of inference runs
            
        Returns:
            Dict with timing statistics
        """
        if (self.model is None and self.interpreter is None):
            return {'error': 'Model not loaded'}
        
        print(f"\n🔬 Benchmarking inference ({num_runs} runs)...")
        
        # Preprocess once
        input_tensor = self.preprocess_frame(frame)
        
        times = []
        for i in range(num_runs):
            start = time.time()
            
            if self.use_tflite:
                self.interpreter.set_tensor(self.input_details[0]['index'], input_tensor)
                self.interpreter.invoke()
                _ = self.interpreter.get_tensor(self.output_details[0]['index'])
            else:
                _ = self.model.predict(input_tensor, verbose=0)
            
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = np.mean(times)
        min_time = np.min(times)
        max_time = np.max(times)
        fps = 1.0 / avg_time if avg_time > 0 else 0
        
        stats = {
            'avg_time_ms': avg_time * 1000,
            'min_time_ms': min_time * 1000,
            'max_time_ms': max_time * 1000,
            'fps': fps,
            'model_type': 'TFLite' if self.use_tflite else 'Keras'
        }
        
        print(f"   Model type: {stats['model_type']}")
        print(f"   Average time: {stats['avg_time_ms']:.1f} ms")
        print(f"   Min time: {stats['min_time_ms']:.1f} ms")
        print(f"   Max time: {stats['max_time_ms']:.1f} ms")
        print(f"   Estimated FPS: {stats['fps']:.2f}")
        
        return stats
    
    def get_recommendations(self, disease_class: str) -> Dict:
        """
        Get treatment recommendations for a disease
        
        Args:
            disease_class: Disease class name (e.g., "Tomato___Late_blight")
            
        Returns:
            Dict with symptoms, causes, treatments, and prevention info
        """
        if disease_class in self.recommendations:
            return self.recommendations[disease_class]
        else:
            # Return empty recommendations if not found
            return {
                'disease_name': disease_class.replace('___', ' - ').replace('_', ' '),
                'crop': 'Unknown',
                'severity': 'unknown',
                'symptoms': [],
                'causes': [],
                'organic_treatment': [],
                'chemical_treatment': [],
                'prevention': []
            }
    
    def get_detection_summary(self, detection: Dict) -> str:
        """Get human-readable summary of detection"""
        if not detection:
            return "No detection"
        
        status = "Healthy" if detection['is_healthy'] else "Disease detected"
        summary = f"{status} - {detection['crop_type']}: {detection['disease_name']} ({detection['confidence']*100:.1f}%)"
        
        return summary
