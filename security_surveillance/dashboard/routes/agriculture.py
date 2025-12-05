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
