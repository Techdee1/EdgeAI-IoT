"""
Camera Module - Handles video capture from device camera or IP camera
"""
import cv2
import time
from typing import Optional, Tuple
import numpy as np


class CameraCapture:
    """Handles camera initialization and frame capture"""
    
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
        
    def start(self) -> bool:
        """Initialize camera connection"""
        try:
            self.cap = cv2.VideoCapture(self.source)
            
            if not self.cap.isOpened():
                print(f"Error: Could not open camera source {self.source}")
                return False
            
            # Set resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            
            self.is_open = True
            print(f"Camera initialized: {self.width}x{self.height}")
            return True
            
        except Exception as e:
            print(f"Error starting camera: {e}")
            return False
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Capture a single frame
        
        Returns:
            Tuple of (success, frame)
        """
        if not self.is_open or self.cap is None:
            return False, None
        
        ret, frame = self.cap.read()
        return ret, frame
    
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
