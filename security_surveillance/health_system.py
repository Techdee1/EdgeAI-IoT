"""
Health Monitoring System
Crop disease detection system using MobileNetV2
"""
import sys
import yaml
import time
import signal
import cv2
from datetime import datetime

# Import required modules
from modules.camera import CameraCapture
from modules.crop_detector import CropDiseaseDetector
from modules.database import HealthDatabase
from modules.performance import PerformanceMonitor


class HealthSystem:
    """Health monitoring system for crop disease detection"""
    
    def __init__(self, config_path='config/config.yaml'):
        """
        Initialize health system
        
        Args:
            config_path: Path to configuration file
        """
        print("=" * 70)
        print("🌱 EDGE AI CROP HEALTH MONITORING SYSTEM")
        print("=" * 70)
        print(f"Starting system at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # System state
        self.running = False
        self.frame_count = 0
        self.last_detection = None
        self.detection_interval = 30  # Frames between detections
        
        # Statistics
        self.stats = {
            'total_detections': 0,
            'healthy_count': 0,
            'disease_count': 0,
            'diseases_detected': {},
            'crops_monitored': {}
        }
        
        # Initialize all components
        self._init_components()
        
        # Set up signal handlers
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except ValueError:
            # Running in a thread, skip signal handlers
            pass
        
        print("\n✅ System initialization complete!")
        print("=" * 70)
    
    def _load_config(self, config_path):
        """Load configuration from YAML file"""
        print(f"📄 Loading configuration from {config_path}...")
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            print("   ✅ Configuration loaded")
            return config
        except Exception as e:
            print(f"   ❌ Failed to load config: {e}")
            print("   Using default configuration")
            return self._get_default_config()
    
    def _get_default_config(self):
        """Get default configuration if file not found"""
        return {
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
                'detection_interval': 30,
                'save_detections': True
            }
        }
    
    def _init_components(self):
        """Initialize all system components"""
        print("\n🔧 Initializing components...")
        
        # 1. Camera
        cam_config = self.config.get('camera', {})
        self.camera = CameraCapture(
            source=cam_config.get('source', 0),
            width=cam_config.get('width', 640),
            height=cam_config.get('height', 480)
        )
        
        # 2. Crop Disease Detector
        health_config = self.config.get('health_system', {})
        self.detector = CropDiseaseDetector(
            model_path=health_config.get('model_path', 'data/models/mobilenet_plantvillage.h5'),
            classes_path='data/models/plantvillage_classes.json',
            recommendations_path='data/disease_recommendations.json',
            conf_threshold=health_config.get('confidence_threshold', 0.6),
            use_tflite=health_config.get('use_tflite', False)
        )
        self.detector.load_model()
        
        # 3. Detection interval
        self.detection_interval = health_config.get('detection_interval', 30)
        
        # 4. Health Database
        self.database = HealthDatabase(db_path='data/logs/health_events.db')
        
        # 5. Performance Monitor
        self.performance = PerformanceMonitor()
        self.fps_start_time = time.time()
        self.fps_frame_count = 0
        
        print("   ✅ All components initialized")
    
    def start(self):
        """Start the health monitoring system"""
        print("\n🚀 Starting health monitoring system...")
        
        # Start camera
        if not self.camera.start():
            print("❌ Failed to start camera")
            return False
        
        self.running = True
        self.frame_count = 0
        
        print("✅ System is now monitoring...")
        print("\nPress Ctrl+C to stop\n")
        print("-" * 70)
        
        try:
            self._main_loop()
        except KeyboardInterrupt:
            print("\n\n⚠️  Keyboard interrupt received")
        except Exception as e:
            print(f"\n\n❌ Error in main loop: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.stop()
        
        return True
    
    def _main_loop(self):
        """Main processing loop"""
        while self.running:
            # Read frame
            ret, frame = self.camera.read_frame()
            if not ret or frame is None:
                print("⚠️  Failed to read frame")
                time.sleep(0.1)
                continue
            
            self.frame_count += 1
            
            # Run disease detection at intervals
            if self.frame_count % self.detection_interval == 0:
                self._process_detection(frame)
            
            # Display frame (for testing)
            display_frame = frame.copy()
            
            # Add detection info overlay if we have recent detection
            if self.last_detection:
                display_frame = self._add_overlay(display_frame)
            
            # Show frame (optional, can be disabled for headless operation)
            cv2.imshow('Health Monitoring', display_frame)
            
            # Check for key press
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\nStopping system...")
                break
            elif key == ord('d'):
                # Manual detection trigger
                print("\n🔍 Manual detection triggered...")
                self._process_detection(frame)
            
            # Update FPS tracking
            self.fps_frame_count += 1
            
            # Print stats periodically
            if self.frame_count % 100 == 0:
                self._print_stats()
    
    def _process_detection(self, frame):
        """Process disease detection on frame"""
        try:
            # Run detection
            detection, annotated_frame = self.detector.detect_disease(frame, draw_results=False)
            
            # Store detection
            self.last_detection = {
                'timestamp': datetime.now(),
                'detection': detection,
                'frame': annotated_frame
            }
            
            # Update statistics
            self.stats['total_detections'] += 1
            
            if detection['is_healthy']:
                self.stats['healthy_count'] += 1
            else:
                self.stats['disease_count'] += 1
                disease = detection['disease_name']
                self.stats['diseases_detected'][disease] = \
                    self.stats['diseases_detected'].get(disease, 0) + 1
            
            crop = detection['crop_type']
            self.stats['crops_monitored'][crop] = \
                self.stats['crops_monitored'].get(crop, 0) + 1
            
            # Log detection
            self._log_detection(detection)
            
            # Print detection result
            self._print_detection(detection)
            
        except Exception as e:
            print(f"❌ Error in detection: {e}")
    
    def _log_detection(self, detection):
        """Log detection to database"""
        try:
            # Use HealthDatabase to log detection
            self.database.log_detection(detection)
            
        except Exception as e:
            print(f"⚠️  Failed to log detection: {e}")
    
    def _print_detection(self, detection):
        """Print detection results"""
        print("\n" + "=" * 70)
        print("🔍 DETECTION RESULT")
        print("=" * 70)
        
        status_icon = "✅" if detection['is_healthy'] else "⚠️"
        status_text = "HEALTHY" if detection['is_healthy'] else "DISEASE DETECTED"
        
        print(f"{status_icon} Status: {status_text}")
        print(f"   Crop: {detection['crop_type']}")
        print(f"   Disease: {detection['disease_name']}")
        print(f"   Confidence: {detection['confidence']*100:.1f}%")
        
        if not detection['is_healthy']:
            rec = detection['recommendations']
            print(f"   Severity: {rec['severity'].upper()}")
            
            if rec['symptoms']:
                print(f"\n   Symptoms:")
                for symptom in rec['symptoms'][:3]:
                    print(f"   • {symptom}")
            
            if rec['organic_treatment']:
                print(f"\n   Organic Treatment:")
                for treatment in rec['organic_treatment'][:2]:
                    print(f"   • {treatment}")
        
        print("=" * 70 + "\n")
    
    def _add_overlay(self, frame):
        """Add detection info overlay to frame"""
        if not self.last_detection:
            return frame
        
        detection = self.last_detection['detection']
        h, w = frame.shape[:2]
        
        # Determine color based on health status
        if detection['is_healthy']:
            color = (0, 255, 0)  # Green
            status = "HEALTHY"
        else:
            color = (0, 0, 255)  # Red
            status = "DISEASE DETECTED"
        
        # Draw semi-transparent banner
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 100), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Draw status
        cv2.putText(frame, status, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        # Draw crop and disease
        crop_text = f"Crop: {detection['crop_type']}"
        cv2.putText(frame, crop_text, (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        disease_text = f"Disease: {detection['disease_name']}"
        cv2.putText(frame, disease_text, (10, 85),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Draw confidence
        conf_text = f"{detection['confidence']*100:.1f}%"
        cv2.putText(frame, conf_text, (w - 120, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        return frame
    
    def _print_stats(self):
        """Print system statistics"""
        elapsed = time.time() - self.fps_start_time
        fps = self.fps_frame_count / elapsed if elapsed > 0 else 0
        
        print("\n" + "-" * 70)
        print(f"📊 Frame: {self.frame_count} | FPS: {fps:.1f}")
        print(f"   Detections: {self.stats['total_detections']} "
              f"(Healthy: {self.stats['healthy_count']}, "
              f"Disease: {self.stats['disease_count']})")
        
        if self.stats['diseases_detected']:
            print(f"   Diseases found: {len(self.stats['diseases_detected'])}")
            for disease, count in list(self.stats['diseases_detected'].items())[:3]:
                print(f"      • {disease}: {count}")
        
        print("-" * 70 + "\n")
    
    def stop(self):
        """Stop the health monitoring system"""
        print("\n🛑 Stopping health monitoring system...")
        
        self.running = False
        
        # Stop camera
        if self.camera:
            self.camera.stop()
            print("   ✅ Camera stopped")
        
        # Database will auto-close on program exit
        if self.database:
            print("   ✅ Database flushed")
        
        # Close windows
        cv2.destroyAllWindows()
        
        # Print final statistics
        print("\n" + "=" * 70)
        print("📊 FINAL STATISTICS")
        print("=" * 70)
        print(f"Total frames processed: {self.frame_count}")
        print(f"Total detections: {self.stats['total_detections']}")
        print(f"Healthy detections: {self.stats['healthy_count']}")
        print(f"Disease detections: {self.stats['disease_count']}")
        
        if self.stats['diseases_detected']:
            print(f"\nDiseases detected:")
            for disease, count in sorted(self.stats['diseases_detected'].items(), 
                                        key=lambda x: x[1], reverse=True):
                print(f"   • {disease}: {count}")
        
        if self.stats['crops_monitored']:
            print(f"\nCrops monitored:")
            for crop, count in sorted(self.stats['crops_monitored'].items(), 
                                     key=lambda x: x[1], reverse=True):
                print(f"   • {crop}: {count}")
        
        print("=" * 70)
        print("✅ System stopped successfully")
    
    def _signal_handler(self, signum, frame):
        """Handle system signals"""
        print(f"\n⚠️  Received signal {signum}")
        self.stop()
        sys.exit(0)
    
    def get_latest_detection(self):
        """Get the most recent detection result"""
        return self.last_detection
    
    def get_stats(self):
        """Get current system statistics"""
        elapsed = time.time() - self.fps_start_time
        fps = self.fps_frame_count / elapsed if elapsed > 0 else 0
        
        return {
            'frame_count': self.frame_count,
            'fps': fps,
            'total_detections': self.stats['total_detections'],
            'healthy_count': self.stats['healthy_count'],
            'disease_count': self.stats['disease_count'],
            'diseases_detected': dict(self.stats['diseases_detected']),
            'crops_monitored': dict(self.stats['crops_monitored'])
        }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Edge AI Crop Health Monitoring System')
    parser.add_argument('--config', type=str, default='config/config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--tflite', action='store_true',
                       help='Use TFLite model (for Raspberry Pi)')
    
    args = parser.parse_args()
    
    # Create and start system
    system = HealthSystem(config_path=args.config)
    
    # Override TFLite setting if specified
    if args.tflite:
        system.detector.use_tflite = True
        print("🔄 Switched to TFLite model")
    
    system.start()


if __name__ == "__main__":
    main()
