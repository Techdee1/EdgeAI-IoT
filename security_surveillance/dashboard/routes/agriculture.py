"""
Smart Agriculture API Endpoints
Provides REST API for agriculture sensor data and irrigation control
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Optional
from datetime import datetime, timedelta
import random

router = APIRouter()


@router.get("/sensors")
async def get_all_sensors(request: Request):
    """
    Get current readings from all agriculture sensors
    (Will integrate with ESP32 via MQTT in future)
    """
    try:
        app_state = request.app.state.app_state
        
        # Placeholder data until ESP32 integration
        # TODO: Replace with actual MQTT sensor data
        sensors = {
            "soil_moisture": {
                "value": 45.2,
                "unit": "%",
                "status": "normal",
                "threshold_min": 30,
                "threshold_max": 70,
                "last_updated": datetime.now().isoformat()
            },
            "soil_temperature": {
                "value": 24.5,
                "unit": "°C",
                "status": "normal",
                "threshold_min": 15,
                "threshold_max": 30,
                "last_updated": datetime.now().isoformat()
            },
            "air_temperature": {
                "value": 28.3,
                "unit": "°C",
                "status": "normal",
                "threshold_min": 10,
                "threshold_max": 40,
                "last_updated": datetime.now().isoformat()
            },
            "air_humidity": {
                "value": 62.8,
                "unit": "%",
                "status": "normal",
                "threshold_min": 40,
                "threshold_max": 80,
                "last_updated": datetime.now().isoformat()
            },
            "light_intensity": {
                "value": 850,
                "unit": "lux",
                "status": "normal",
                "threshold_min": 200,
                "threshold_max": 2000,
                "last_updated": datetime.now().isoformat()
            }
        }
        
        return {
            "sensors": sensors,
            "count": len(sensors),
            "mode": "placeholder",
            "message": "Using placeholder data. ESP32 integration pending.",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sensor/{sensor_name}")
async def get_sensor_reading(sensor_name: str, request: Request):
    """
    Get current reading for a specific sensor
    """
    try:
        # Get all sensors and filter by name
        all_sensors = await get_all_sensors(request)
        sensors = all_sensors["sensors"]
        
        if sensor_name not in sensors:
            raise HTTPException(
                status_code=404,
                detail=f"Sensor '{sensor_name}' not found"
            )
        
        return {
            "sensor": sensor_name,
            "data": sensors[sensor_name],
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_sensor_history(
    request: Request,
    sensor: Optional[str] = None,
    hours: int = 24
):
    """
    Get historical sensor data for the last N hours
    (Will query agriculture database once implemented)
    """
    try:
        app_state = request.app.state.app_state
        
        # Placeholder historical data
        # TODO: Query actual database when ESP32 integration is complete
        
        # Generate sample time series data
        now = datetime.now()
        data_points = []
        
        for i in range(hours):
            timestamp = now - timedelta(hours=hours-i)
            data_points.append({
                "timestamp": timestamp.isoformat(),
                "soil_moisture": 40 + random.uniform(-5, 5),
                "soil_temperature": 24 + random.uniform(-2, 2),
                "air_temperature": 28 + random.uniform(-3, 3),
                "air_humidity": 60 + random.uniform(-10, 10),
                "light_intensity": 800 + random.uniform(-200, 200)
            })
        
        # Filter by specific sensor if requested
        if sensor:
            valid_sensors = ["soil_moisture", "soil_temperature", "air_temperature", 
                           "air_humidity", "light_intensity"]
            if sensor not in valid_sensors:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid sensor. Valid options: {valid_sensors}"
                )
            
            # Keep only requested sensor data
            data_points = [
                {"timestamp": dp["timestamp"], "value": dp[sensor]}
                for dp in data_points
            ]
        
        return {
            "history": data_points,
            "sensor_filter": sensor,
            "period_hours": hours,
            "count": len(data_points),
            "mode": "placeholder",
            "message": "Using placeholder data. ESP32 integration pending.",
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/irrigation/status")
async def get_irrigation_status(request: Request):
    """
    Get current irrigation system status
    """
    try:
        # Placeholder irrigation status
        # TODO: Connect to actual irrigation control system
        
        return {
            "pump_active": False,
            "valve_open": False,
            "mode": "auto",  # auto, manual, off
            "last_irrigation": (datetime.now() - timedelta(hours=6)).isoformat(),
            "next_scheduled": (datetime.now() + timedelta(hours=18)).isoformat(),
            "water_flow_rate": 0,  # liters per minute
            "total_today": 45.2,  # liters
            "status": "standby",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/irrigation/control")
async def control_irrigation(
    request: Request,
    action: str,  # start, stop, auto, manual
    duration: Optional[int] = None  # minutes (for manual start)
):
    """
    Control irrigation system
    Actions: start (manual), stop, auto (enable automation), manual (disable automation)
    """
    try:
        valid_actions = ["start", "stop", "auto", "manual"]
        if action not in valid_actions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action. Valid options: {valid_actions}"
            )
        
        # Placeholder control logic
        # TODO: Implement actual irrigation control via GPIO/relay
        
        response = {
            "action": action,
            "success": True,
            "message": f"Irrigation {action} command sent (placeholder)",
            "timestamp": datetime.now().isoformat()
        }
        
        if action == "start" and duration:
            response["duration_minutes"] = duration
            response["message"] = f"Irrigation started for {duration} minutes (placeholder)"
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_agriculture_stats(request: Request, days: int = 7):
    """
    Get agriculture system statistics for the last N days
    """
    try:
        app_state = request.app.state.app_state
        
        # Placeholder statistics
        # TODO: Calculate from actual database when ESP32 integration is complete
        
        return {
            "period_days": days,
            "total_irrigations": 14,
            "total_water_liters": 520.5,
            "avg_soil_moisture": 42.3,
            "avg_temperature": 26.8,
            "alerts_count": 3,
            "sensor_uptime": 99.2,  # percentage
            "recommendations": [
                "Soil moisture trending low - consider increasing irrigation",
                "Light levels optimal for current crop stage"
            ],
            "mode": "placeholder",
            "message": "Using placeholder data. ESP32 integration pending.",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_agriculture_alerts(request: Request, limit: int = 20):
    """
    Get recent agriculture system alerts
    (Low moisture, high temperature, sensor failures, etc.)
    """
    try:
        # Placeholder alerts
        # TODO: Query agriculture database for actual alerts
        
        alerts = [
            {
                "id": 1,
                "type": "warning",
                "sensor": "soil_moisture",
                "message": "Soil moisture below threshold (28%)",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "resolved": False
            },
            {
                "id": 2,
                "type": "info",
                "sensor": "irrigation",
                "message": "Automatic irrigation completed (15 min, 25L)",
                "timestamp": (datetime.now() - timedelta(hours=6)).isoformat(),
                "resolved": True
            }
        ]
        
        return {
            "alerts": alerts[:limit],
            "count": len(alerts),
            "mode": "placeholder",
            "message": "Using placeholder data. ESP32 integration pending.",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/status")
async def get_agriculture_system_status(request: Request):
    """
    Get overall agriculture system operational status
    """
    try:
        return {
            "esp32_connected": False,
            "mqtt_status": "disconnected",
            "sensors_active": 0,
            "sensors_total": 5,
            "irrigation_system": "ready",
            "database": "connected" if request.app.state.app_state.agriculture_db else "disconnected",
            "mode": "placeholder",
            "message": "ESP32 and MQTT integration pending",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CROP HEALTH MONITORING ENDPOINTS
# ============================================================================

@router.get("/health/stats")
async def get_health_stats(request: Request):
    """
    Get crop health monitoring statistics
    """
    try:
        app_state = request.app.state.app_state
        
        if not app_state.health_db:
            return {
                "error": "Health database not available",
                "mode": app_state.mode,
                "message": "Switch to health mode to access health monitoring data"
            }
        
        # Get summary from database
        summary = app_state.health_db.get_health_summary()
        crop_stats = app_state.health_db.get_crop_statistics()
        disease_stats = app_state.health_db.get_disease_statistics(limit=5)
        
        return {
            "summary": summary,
            "crops": crop_stats,
            "top_diseases": disease_stats,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/detections")
async def get_health_detections(
    request: Request,
    limit: int = 10,
    crop_type: Optional[str] = None
):
    """
    Get recent crop disease detections
    
    Args:
        limit: Maximum number of detections to return
        crop_type: Optional filter by crop type
    """
    try:
        app_state = request.app.state.app_state
        
        if not app_state.health_db:
            return {
                "error": "Health database not available",
                "detections": [],
                "count": 0
            }
        
        # Get recent detections
        detections = app_state.health_db.get_recent_detections(
            limit=limit,
            crop_type=crop_type
        )
        
        return {
            "detections": detections,
            "count": len(detections),
            "filter": {"crop_type": crop_type} if crop_type else None,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/latest")
async def get_latest_detection(request: Request):
    """
    Get the most recent crop health detection
    """
    try:
        app_state = request.app.state.app_state
        
        # Try to get from running health system first
        if app_state.health_system:
            latest = app_state.health_system.get_latest_detection()
            if latest:
                return {
                    "detection": latest['detection'],
                    "timestamp": latest['timestamp'].isoformat(),
                    "source": "live_system"
                }
        
        # Fallback to database
        if app_state.health_db:
            detections = app_state.health_db.get_recent_detections(limit=1)
            if detections:
                return {
                    "detection": detections[0],
                    "source": "database"
                }
        
        return {
            "detection": None,
            "message": "No detections available"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/crops")
async def get_monitored_crops(request: Request):
    """
    Get list of crops being monitored
    """
    try:
        app_state = request.app.state.app_state
        
        if not app_state.health_db:
            return {"crops": [], "count": 0}
        
        crop_stats = app_state.health_db.get_crop_statistics()
        
        # Format crop data
        crops = []
        for stat in crop_stats:
            health_rate = (stat['healthy_count'] / stat['total_scans'] * 100) if stat['total_scans'] > 0 else 0
            crops.append({
                "crop_type": stat['crop_type'],
                "total_scans": stat['total_scans'],
                "healthy_count": stat['healthy_count'],
                "disease_count": stat['disease_count'],
                "health_rate": round(health_rate, 1),
                "last_scan": stat['last_scan']
            })
        
        return {
            "crops": crops,
            "count": len(crops),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/diseases")
async def get_detected_diseases(request: Request, limit: int = 10):
    """
    Get list of diseases detected with statistics
    """
    try:
        app_state = request.app.state.app_state
        
        if not app_state.health_db:
            return {"diseases": [], "count": 0}
        
        disease_stats = app_state.health_db.get_disease_statistics(limit=limit)
        
        return {
            "diseases": disease_stats,
            "count": len(disease_stats),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/system_status")
async def get_health_system_status(request: Request):
    """
    Get health monitoring system status
    """
    try:
        app_state = request.app.state.app_state
        
        status = {
            "mode": app_state.mode,
            "system_active": app_state.health_system is not None and app_state.health_system.running if hasattr(app_state.health_system, 'running') else False,
            "database_connected": app_state.health_db is not None,
            "camera_connected": app_state.camera is not None,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add live stats if system is running
        if app_state.health_system and hasattr(app_state.health_system, 'get_stats'):
            try:
                live_stats = app_state.health_system.get_stats()
                status['live_stats'] = live_stats
            except:
                pass
        
        return status
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
