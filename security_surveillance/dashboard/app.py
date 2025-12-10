"""
FastAPI Dashboard Application
Unified web dashboard for Security & Surveillance + Smart Agriculture
"""
from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import os
import time
from pathlib import Path
from typing import Optional
import json

# Get the dashboard directory path
DASHBOARD_DIR = Path(__file__).parent
STATIC_DIR = DASHBOARD_DIR / "static"
TEMPLATES_DIR = DASHBOARD_DIR / "templates"

# Create FastAPI app
app = FastAPI(
    title="EcoGuard",
    description="Unified dashboard for Security Surveillance and Smart Agriculture",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Global state to store system references (will be set by launcher)
class AppState:
    def __init__(self):
        self.mode = "security"  # Current mode: 'security' or 'health'
        self.security_system = None
        self.health_system = None
        self.security_db = None
        self.health_db = None
        self.camera_manager = None  # Shared camera manager
        self.uploaded_images_dir = Path("data/uploaded_images")  # Directory for uploaded images
        
        # Create uploaded images directory
        self.uploaded_images_dir.mkdir(parents=True, exist_ok=True)
        self.camera = None
        self.switching = False  # Mode switch in progress
        
app.state.app_state = AppState()


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main dashboard page"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "EcoGuard"}
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "EcoGuard",
        "version": "1.0.0"
    }


@app.get("/api/mode")
async def get_current_mode():
    """Get current system mode"""
    return {
        "mode": app.state.app_state.mode,
        "switching": app.state.app_state.switching
    }


@app.post("/api/switch_mode")
async def switch_mode(mode: str):
    """
    Switch between Security and Health modes
    
    Args:
        mode: Target mode ('security' or 'health')
    """
    app_state = app.state.app_state
    
    # Validate mode
    if mode not in ['security', 'health']:
        return {
            "success": False,
            "error": "Invalid mode. Must be 'security' or 'health'"
        }
    
    # Check if already in target mode
    if app_state.mode == mode:
        return {
            "success": True,
            "message": f"Already in {mode} mode",
            "mode": mode
        }
    
    # Mark as switching
    app_state.switching = True
    
    try:
        # Stop current system gracefully
        if app_state.mode == "security" and app_state.security_system:
            print("Stopping security system...")
            if hasattr(app_state.security_system, 'stop'):
                app_state.security_system.stop()
            time.sleep(1)
        elif app_state.mode == "health" and app_state.health_system:
            print("Stopping health system...")
            if hasattr(app_state.health_system, 'stop'):
                app_state.health_system.stop()
            time.sleep(1)
        
        # Switch mode
        app_state.mode = mode
        
        # Start new system (in production, would restart the process)
        print(f"Switched to {mode} mode")
        
        return {
            "success": True,
            "message": f"Switched to {mode} mode. Please restart the system to activate.",
            "mode": mode,
            "restart_required": True
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        app_state.switching = False


@app.post("/api/upload_image")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload an image for processing
    
    Args:
        file: Uploaded image file
        
    Returns:
        JSON with file information and processing results
    """
    try:
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Read file content
        content = await file.read()
        
        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: 10MB"
            )
        
        # Generate unique filename
        import uuid
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        ext = Path(file.filename).suffix
        filename = f"{timestamp}_{unique_id}{ext}"
        
        # Save file
        app_state = app.state.app_state
        file_path = app_state.uploaded_images_dir / filename
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Process image based on current mode
        from modules.preprocessing import ImageInputHandler
        
        handler = ImageInputHandler()
        image = handler.load_from_file(file_path)
        
        if image is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to load uploaded image"
            )
        
        # Get image dimensions
        height, width = image.shape[:2]
        
        result = {
            "success": True,
            "filename": filename,
            "file_path": str(file_path),
            "size_bytes": len(content),
            "dimensions": {
                "width": width,
                "height": height
            },
            "upload_time": timestamp
        }
        
        # Process with appropriate system
        if app_state.mode == "health" and app_state.health_system:
            # Don't use preprocess_for_classification - let detector handle it
            # The detector's preprocess_frame does the correct normalization
            detection_result = app_state.health_system.detector.detect_disease(
                image, 
                draw_results=False, 
                preprocessed=False
            )
            
            # detect_disease returns tuple (detection_dict, annotated_frame)
            if detection_result and isinstance(detection_result, tuple):
                detection = detection_result[0]
            else:
                detection = detection_result
            
            # Get confidence threshold from detector (default 0.6)
            conf_threshold = app_state.health_system.detector.conf_threshold
            
            print(f"[UPLOAD DEBUG] Detection: {detection}")
            print(f"[UPLOAD DEBUG] Confidence: {detection.get('confidence', 0) if detection else None}, Threshold: {conf_threshold}")
            
            if detection and detection.get("confidence", 0) >= conf_threshold:
                # Map detection keys correctly
                disease_name = detection.get("disease_name", detection.get("disease_class", "Unknown"))
                is_healthy = detection.get("is_healthy", False)
                severity = "low" if is_healthy else "high"
                crop_type = detection.get("crop_type", "Unknown")
                confidence = detection["confidence"]
                
                # Save detection to database
                try:
                    print(f"[DB SAVE] Attempting to save: crop={crop_type}, disease={disease_name}, conf={confidence:.2%}")
                    app_state.health_system.database.log_detection(
                        detection=detection,
                        image_path=str(file_path)
                    )
                    print(f"[DB SAVE] Successfully saved detection to database")
                except Exception as db_error:
                    print(f"[DB ERROR] Failed to save detection to database: {db_error}")
                    import traceback
                    traceback.print_exc()
                
                result["detection"] = {
                    "disease": disease_name,
                    "crop_type": crop_type,
                    "confidence": confidence,
                    "severity": severity,
                    "is_healthy": is_healthy,
                    "recommendations": detection.get("recommendations", [])
                }
            else:
                # Low confidence - add message about it
                if detection:
                    result["low_confidence"] = {
                        "message": "Detection confidence too low",
                        "confidence": detection.get("confidence", 0),
                        "threshold": conf_threshold
                    }
        
        elif app_state.mode == "security" and app_state.security_system:
            # Process with security system
            from modules.preprocessing import preprocess_for_detection
            
            processed = preprocess_for_detection(image, target_size=(640, 640))
            detections = app_state.security_system.detector.detect(processed)
            
            if detections:
                result["detections"] = [
                    {
                        "class": det["class"],
                        "confidence": det["confidence"],
                        "bbox": det["bbox"]
                    }
                    for det in detections
                ]
        
        return JSONResponse(result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing upload: {str(e)}"
        )


@app.get("/api/camera_sources")
async def get_camera_sources():
    """
    Get available camera sources
    
    Returns:
        List of available cameras and current selection
    """
    try:
        from modules.preprocessing import CameraManager
        
        app_state = app.state.app_state
        
        # Initialize camera manager if not exists
        if app_state.camera_manager is None:
            app_state.camera_manager = CameraManager()
        
        # List available cameras
        available_cameras = app_state.camera_manager.list_available_cameras()
        
        # Get current source info
        current_source = None
        if app_state.camera_manager.current_source is not None:
            current_source = {
                "source": app_state.camera_manager.current_source,
                "info": app_state.camera_manager.get_camera_info()
            }
        
        return {
            "success": True,
            "available_cameras": available_cameras,
            "current_source": current_source,
            "default_rtsp": "rtsp://172.16.122.6:554/1"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/api/select_camera")
async def select_camera(source: str):
    """
    Select and connect to a camera source
    
    Args:
        source: Camera source (USB index or RTSP URL)
        
    Returns:
        Connection status
    """
    try:
        from modules.preprocessing import CameraManager
        
        app_state = app.state.app_state
        
        # Initialize camera manager if not exists
        if app_state.camera_manager is None:
            app_state.camera_manager = CameraManager()
        
        # Try to parse as integer (USB camera)
        try:
            source_int = int(source)
            camera_source = source_int
        except ValueError:
            camera_source = source
        
        # Connect to camera
        success = app_state.camera_manager.connect_camera(camera_source)
        
        if success:
            info = app_state.camera_manager.get_camera_info()
            return {
                "success": True,
                "message": f"Connected to camera: {source}",
                "camera_info": info
            }
        else:
            return {
                "success": False,
                "error": f"Failed to connect to camera: {source}"
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/uploaded_images")
async def get_uploaded_images():
    """
    Get list of uploaded images
    
    Returns:
        List of uploaded image files
    """
    try:
        app_state = app.state.app_state
        
        # List uploaded images
        images = []
        for img_path in app_state.uploaded_images_dir.glob("*"):
            if img_path.is_file() and img_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                images.append({
                    "filename": img_path.name,
                    "path": str(img_path),
                    "size_bytes": img_path.stat().st_size,
                    "modified": img_path.stat().st_mtime
                })
        
        # Sort by modified time (newest first)
        images.sort(key=lambda x: x["modified"], reverse=True)
        
        return {
            "success": True,
            "count": len(images),
            "images": images
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    
    # Check if switch is in progress
    if app_state.switching:
        return {
            "success": False,
            "error": "Mode switch already in progress"
        }
    
    try:
        app_state.switching = True
        
        # Stop current system
        if app_state.mode == "security" and app_state.security_system:
            print(f"🛑 Stopping security system...")
            app_state.security_system.running = False
            time.sleep(1)  # Give it time to stop gracefully
        elif app_state.mode == "health" and app_state.health_system:
            print(f"🛑 Stopping health system...")
            app_state.health_system.running = False
            time.sleep(1)
        
        # Switch mode
        app_state.mode = mode
        print(f"🔄 Switched to {mode} mode")
        
        # Note: The launcher will handle starting the new system
        
        return {
            "success": True,
            "message": f"Switched to {mode} mode",
            "mode": mode
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        app_state.switching = False


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    import time
    print("🚀 EcoGuard starting...")
    print(f"📁 Static files: {STATIC_DIR}")
    print(f"📄 Templates: {TEMPLATES_DIR}")
    print(f"🔄 Current mode: {app.state.app_state.mode}")
    print("📚 API docs available at: /api/docs")
    

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 EcoGuard shutting down...")


# Import and include routers
from dashboard.routes import security, agriculture, websocket
app.include_router(security.router, prefix="/api/security", tags=["Security"])
app.include_router(agriculture.router, prefix="/api/agriculture", tags=["Agriculture"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("🔒 EDGE AI UNIFIED DASHBOARD")
    print("=" * 70)
    print("Starting FastAPI server...")
    print("Dashboard: http://localhost:8080")
    print("API Docs: http://localhost:8080/api/docs")
    print("=" * 70)
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
