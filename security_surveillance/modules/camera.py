"""
Camera Module - Handles video capture from device camera or IP camera
"""
import cv2
import time
import threading
from typing import Optional, Tuple
import numpy as np


class CameraCapture:
    """Handles camera initialization and frame capture with thread safety"""
    
    def __init__(self, source: int = 0, width: int = 640, height: int = 480):
        """
        Initialize camera capture
        
        Args:
            source: Camera source (0 for device camera, or RTSP URL for IP camera)
            width: Frame width
            height: Frame height
        """
        self.source = source
        self.width = width
        self.height = height
        self.cap = None
        self.is_open = False
        self.lock = threading.Lock()  # Thread-safe frame reading
        self.last_frame = None
        self.last_ret = False
        
    def start(self) -> bool:
        """Initialize camera connection"""
        try:
            print(f"\n📹 Connecting to camera: {self.source}")
            
            # For RTSP streams, use CAP_FFMPEG backend with timeout
            if isinstance(self.source, str) and self.source.startswith('rtsp'):
                # Set environment variable to prevent FFmpeg threading issues
                import os
                os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp|fflags;nobuffer|flags;low_delay"
                
                self.cap = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)
                # Set connection timeout (in milliseconds)
                self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
                self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)
                # Reduce buffering to prevent threading issues
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            else:
                self.cap = cv2.VideoCapture(self.source)
            
            if not self.cap.isOpened():
                print(f"❌ Error: Could not open camera source {self.source}")
                print(f"   Please verify:")
                print(f"   1. Camera is online and accessible")
                print(f"   2. RTSP URL is correct")
                print(f"   3. You're on the same network as the camera")
                print(f"   4. No firewall blocking the connection")
                return False
            
            # Set resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            
            # Test read a frame to verify connection
            ret, test_frame = self.cap.read()
            if not ret:
                print(f"❌ Error: Camera opened but cannot read frames")
                self.cap.release()
                return False
            
            self.is_open = True
            print(f"✅ Camera connected successfully: {self.width}x{self.height}")
            print(f"   Actual frame size: {test_frame.shape[1]}x{test_frame.shape[0]}")
            return True
            
        except Exception as e:
            print(f"❌ Error starting camera: {e}")
            return False
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Capture a single frame (thread-safe)
        
        Returns:
            Tuple of (success, frame)
        """
        if not self.is_open or self.cap is None:
            return False, None
        
        with self.lock:
            try:
                ret, frame = self.cap.read()
                if ret:
                    # Cache the last successful frame
                    self.last_frame = frame.copy() if frame is not None else None
                    self.last_ret = ret
                return ret, frame
            except Exception as e:
                print(f"Error reading frame: {e}")
                # Return cached frame if available
                return self.last_ret, self.last_frame
    
    def release(self):
        """Release camera resources"""
        if self.cap is not None:
            self.cap.release()
            self.is_open = False
            print("Camera released")
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()
