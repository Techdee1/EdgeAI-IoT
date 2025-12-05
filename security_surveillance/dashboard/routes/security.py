"""
Security & Surveillance API Endpoints
Provides REST API for security system data and control
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional
from datetime import datetime, timedelta
import os
import cv2
import asyncio

router = APIRouter()


@router.get("/stats")
async def get_security_stats(request: Request):
    """
    Get overall security system statistics
    Returns total detections, recordings, system status
    """
    try:
        app_state = request.app.state.app_state
        
        if not app_state.security_db:
            return {
                "status": "no_database",
                "message": "Security database not initialized"
            }
        
        # Get statistics from database
        totals = app_state.security_db.get_total_events()
        
        # Get storage info if available
        storage_info = {}
        if hasattr(app_state, 'surveillance_system') and app_state.surveillance_system:
            if app_state.surveillance_system.storage_manager:
                storage_info = app_state.surveillance_system.storage_manager.get_storage_usage()
        
        return {
            "total_detections": totals.get('detections', 0),
            "system_events": totals.get('system_events', 0),
            "storage_mb": storage_info.get('total_mb', 0),
            "storage_files": storage_info.get('file_count', 0),
            "status": "active",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detections")
async def get_recent_detections(
    request: Request,
    limit: int = 50,
    zone: Optional[str] = None
):
    """
    Get recent person detection events
    Optional filter by zone name
    """
    try:
        app_state = request.app.state.app_state
        
        if not app_state.security_db:
            return {"detections": [], "message": "Database not initialized"}
        
        # Get recent detections from database
        detections = app_state.security_db.get_recent_detections(limit=limit)
        
        # Filter by zone if specified
        if zone:
            detections = [d for d in detections if d.get('zone_name') == zone]
        
        return {
            "detections": detections,
            "count": len(detections),
            "zone_filter": zone,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/zones")
async def get_zone_statistics(request: Request, days: int = 7):
    """
    Get statistics per zone for the last N days
    """
    try:
        app_state = request.app.state.app_state
        
        if not app_state.security_db:
            return {"zones": [], "message": "Database not initialized"}
        
        # Get zone statistics
        zone_stats = app_state.security_db.get_zone_statistics(days=days)
        
        return {
            "zones": zone_stats,
            "period_days": days,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recordings")
async def get_recordings(
    request: Request,
    limit: int = 20,
    sort: str = "newest"
):
    """
    Get list of recorded video files
    """
    try:
        recordings_dir = "data/recordings"
        
        if not os.path.exists(recordings_dir):
            return {"recordings": [], "message": "Recordings directory not found"}
        
        # Get all MP4 files
        files = []
        for filename in os.listdir(recordings_dir):
            if filename.endswith('.mp4'):
                filepath = os.path.join(recordings_dir, filename)
                stat = os.stat(filepath)
                files.append({
                    "filename": filename,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "url": f"/api/security/recording/{filename}"
                })
        
        # Sort recordings
        if sort == "newest":
            files.sort(key=lambda x: x['created'], reverse=True)
        elif sort == "oldest":
            files.sort(key=lambda x: x['created'])
        elif sort == "largest":
            files.sort(key=lambda x: x['size_mb'], reverse=True)
        
        # Limit results
        files = files[:limit]
        
        return {
            "recordings": files,
            "count": len(files),
            "total_mb": sum(f['size_mb'] for f in files),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recording/{filename}")
async def get_recording_file(filename: str):
    """
    Download or stream a specific recording file
    """
    try:
        filepath = os.path.join("data/recordings", filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Recording not found")
        
        # Return file stream
        def iterfile():
            with open(filepath, mode="rb") as file:
                yield from file
        
        return StreamingResponse(
            iterfile(),
            media_type="video/mp4",
            headers={"Content-Disposition": f"inline; filename={filename}"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/status")
async def get_system_status(request: Request):
    """
    Get current system operational status
    """
    try:
        app_state = request.app.state.app_state
        
        status = {
            "database": "connected" if app_state.security_db else "disconnected",
            "camera": "disconnected",
            "recording": False,
            "frame_count": 0,
            "detections_today": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        # Check surveillance system status
        if hasattr(app_state, 'surveillance_system') and app_state.surveillance_system:
            sys = app_state.surveillance_system
            status["camera"] = "connected" if sys.camera and sys.running else "disconnected"
            status["frame_count"] = sys.frame_count
            status["recording"] = sys.recorder.is_recording if sys.recorder else False
        
        return status
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/people/count")
async def get_people_count(request: Request):
    """
    Get current number of people detected in frame
    (Real-time count - requires active surveillance system)
    """
    try:
        app_state = request.app.state.app_state
        
        # This would need to be updated by the surveillance system
        # For now, return last known count from recent detections
        if not app_state.security_db:
            return {"count": 0, "message": "Database not initialized"}
        
        # Get most recent detection
        recent = app_state.security_db.get_recent_detections(limit=1)
        
        return {
            "current_count": 1 if recent else 0,
            "last_seen": recent[0]['timestamp'] if recent else None,
            "status": "live" if recent else "no_recent_activity",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stream")
async def video_stream(request: Request, quality: str = "medium"):
    """
    Live MJPEG video stream from security camera
    Quality options: low (320x240), medium (640x480), high (1280x720)
    """
    try:
        app_state = request.app.state.app_state
        
        # Check if camera is available
        if not hasattr(app_state, 'camera') or not app_state.camera:
            raise HTTPException(
                status_code=503,
                detail="Camera not initialized or not available"
            )
        
        # Set quality parameters
        quality_settings = {
            "low": (320, 240, 50),     # width, height, jpeg quality
            "medium": (640, 480, 60),
            "high": (1280, 720, 80)
        }
        
        if quality not in quality_settings:
            quality = "medium"
        
        target_width, target_height, jpeg_quality = quality_settings[quality]
        
        async def generate_frames():
            """Generator function for MJPEG stream"""
            try:
                while True:
                    # Get frame from camera (returns tuple: success, frame)
                    ret, frame = app_state.camera.read_frame()
                    
                    if not ret or frame is None:
                        # Camera not providing frames, send error frame
                        error_frame = create_error_frame("Camera Unavailable")
                        _, buffer = cv2.imencode('.jpg', error_frame, 
                                                [cv2.IMWRITE_JPEG_QUALITY, 50])
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + 
                               buffer.tobytes() + b'\r\n')
                        await asyncio.sleep(1)
                        continue
                    
                    # Resize frame for streaming
                    frame_resized = cv2.resize(frame, (target_width, target_height))
                    
                    # Encode frame as JPEG
                    _, buffer = cv2.imencode('.jpg', frame_resized, 
                                            [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
                    
                    # Yield frame in MJPEG format
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + 
                           buffer.tobytes() + b'\r\n')
                    
                    # Control frame rate (approx 15 FPS for smooth streaming)
                    await asyncio.sleep(0.066)
            
            except Exception as e:
                print(f"Stream generation error: {e}")
                # Send error frame
                error_frame = create_error_frame(f"Stream Error: {str(e)}")
                _, buffer = cv2.imencode('.jpg', error_frame, 
                                        [cv2.IMWRITE_JPEG_QUALITY, 50])
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + 
                       buffer.tobytes() + b'\r\n')
        
        return StreamingResponse(
            generate_frames(),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/snapshot")
async def camera_snapshot(request: Request, annotated: bool = False):
    """
    Get a single snapshot image from the camera
    If annotated=true, includes detection boxes and labels
    """
    try:
        app_state = request.app.state.app_state
        
        if not hasattr(app_state, 'camera') or not app_state.camera:
            raise HTTPException(
                status_code=503,
                detail="Camera not initialized"
            )
        
        # Get current frame
        frame = app_state.camera.read_frame()
        
        if frame is None:
            error_frame = create_error_frame("Camera Unavailable")
            _, buffer = cv2.imencode('.jpg', error_frame, 
                                    [cv2.IMWRITE_JPEG_QUALITY, 80])
            return StreamingResponse(
                iter([buffer.tobytes()]),
                media_type="image/jpeg"
            )
        
        # If annotated, add detection boxes (if available)
        if annotated and hasattr(app_state, 'surveillance_system'):
            # TODO: Add detection overlay logic here when integrated
            pass
        
        # Encode as JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        
        return StreamingResponse(
            iter([buffer.tobytes()]),
            media_type="image/jpeg",
            headers={"Content-Disposition": f"inline; filename=snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def create_error_frame(message: str) -> any:
    """
    Create a black frame with error message
    """
    import numpy as np
    
    # Create black frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add text
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(message, font, 1, 2)[0]
    text_x = (640 - text_size[0]) // 2
    text_y = (480 + text_size[1]) // 2
    
    cv2.putText(frame, message, (text_x, text_y), font, 1, (255, 255, 255), 2)
    
    return frame
