"""
WebSocket Endpoints for Real-Time Updates
Provides live streaming of system events, detections, and sensor data
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set
import asyncio
import json
from datetime import datetime

router = APIRouter()

# Store active WebSocket connections
active_connections: Set[WebSocket] = set()


class ConnectionManager:
    """Manages WebSocket connections and broadcasts"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"✅ WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        self.active_connections.discard(websocket)
        print(f"❌ WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to a specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_detection(self, detection_data: dict):
        """Broadcast person detection event"""
        message = {
            "type": "detection",
            "data": detection_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def broadcast_sensor_update(self, sensor_data: dict):
        """Broadcast agriculture sensor update"""
        message = {
            "type": "sensor_update",
            "data": sensor_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def broadcast_alert(self, alert_data: dict):
        """Broadcast system alert"""
        message = {
            "type": "alert",
            "data": alert_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def broadcast_system_status(self, status_data: dict):
        """Broadcast system status update"""
        message = {
            "type": "system_status",
            "data": status_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/live")
async def websocket_live_updates(websocket: WebSocket):
    """
    WebSocket endpoint for real-time system updates
    Streams detections, sensor data, alerts, and system status
    """
    await manager.connect(websocket)
    
    try:
        # Send initial connection confirmation
        await manager.send_personal_message({
            "type": "connected",
            "message": "WebSocket connection established",
            "timestamp": datetime.now().isoformat()
        }, websocket)
        
        # Keep connection alive and handle incoming messages
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                # Handle different message types from client
                if message_type == "ping":
                    # Respond to ping with pong
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                
                elif message_type == "subscribe":
                    # Client subscribing to specific channels
                    channels = message.get("channels", [])
                    await manager.send_personal_message({
                        "type": "subscribed",
                        "channels": channels,
                        "message": f"Subscribed to {len(channels)} channels",
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                
                elif message_type == "request_status":
                    # Client requesting current system status
                    await manager.send_personal_message({
                        "type": "system_status",
                        "data": {
                            "security": "active",
                            "agriculture": "standby",
                            "connections": len(manager.active_connections)
                        },
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                
                else:
                    # Unknown message type
                    await manager.send_personal_message({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}",
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
            
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("WebSocket client disconnected normally")
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.websocket("/security")
async def websocket_security_updates(websocket: WebSocket):
    """
    WebSocket endpoint specifically for security system updates
    Streams person detections, zone violations, and tamper alerts
    """
    await manager.connect(websocket)
    
    try:
        await manager.send_personal_message({
            "type": "connected",
            "channel": "security",
            "message": "Connected to security updates channel",
            "timestamp": datetime.now().isoformat()
        }, websocket)
        
        while True:
            # Wait for client messages or keep alive
            data = await websocket.receive_text()
            
            # Echo back or handle commands
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await manager.send_personal_message({
                        "type": "pong",
                        "channel": "security",
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
            except:
                pass
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"Security WebSocket error: {e}")
        manager.disconnect(websocket)


@router.websocket("/agriculture")
async def websocket_agriculture_updates(websocket: WebSocket):
    """
    WebSocket endpoint specifically for agriculture system updates
    Streams sensor readings, irrigation events, and crop alerts
    """
    await manager.connect(websocket)
    
    try:
        await manager.send_personal_message({
            "type": "connected",
            "channel": "agriculture",
            "message": "Connected to agriculture updates channel",
            "timestamp": datetime.now().isoformat()
        }, websocket)
        
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await manager.send_personal_message({
                        "type": "pong",
                        "channel": "agriculture",
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
            except:
                pass
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"Agriculture WebSocket error: {e}")
        manager.disconnect(websocket)


# Export manager for use by other modules
def get_connection_manager():
    """Get the global WebSocket connection manager"""
    return manager
