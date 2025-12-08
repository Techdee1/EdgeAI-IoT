"""
Integrated System Launcher
Starts surveillance or health monitoring system with web dashboard
Supports dual-mode operation: security (default) or health
"""
import sys
import argparse
import threading
import time
import uvicorn
from pathlib import Path

# Import surveillance system
from main import SurveillanceSystem

# Import health monitoring system
from health_system import HealthSystem

# Import dashboard app
from dashboard.app import app

# Shared state between systems
surveillance_system = None
health_system = None
current_mode = "security"  # Default mode


def run_surveillance():
    """Run surveillance system in separate thread"""
    global surveillance_system
    
    print("\n🔒 Starting Surveillance System...")
    
    # Create system without starting yet
    surveillance_system = SurveillanceSystem(config_path='config/config.yaml')
    
    # Set up reference for dashboard
    app.state.app_state.surveillance_system = surveillance_system
    app.state.app_state.camera = surveillance_system.camera
    app.state.app_state.security_db = surveillance_system.database
    app.state.app_state.mode = "security"
    
    # Start surveillance (without signal handlers in thread)
    try:
        surveillance_system.start()
    except Exception as e:
        print(f"⚠️  Surveillance system error: {e}")


def run_health():
    """Run health monitoring system in separate thread"""
    global health_system
    
    print("\n🌱 Starting Health Monitoring System...")
    
    # Create system without starting yet
    health_system = HealthSystem(config_path='config/config.yaml')
    
    # Set up reference for dashboard
    app.state.app_state.health_system = health_system
    app.state.app_state.camera = health_system.camera
    app.state.app_state.health_db = health_system.database
    app.state.app_state.mode = "health"
    
    # Start health monitoring (without signal handlers in thread)
    try:
        health_system.start()
    except Exception as e:
        print(f"⚠️  Health system error: {e}")


def run_dashboard(mode="security"):
    """Run FastAPI dashboard"""
    print("\n📊 Starting Web Dashboard...")
    
    # Give system time to initialize
    time.sleep(2)
    
    mode_display = "🔒 Security Surveillance" if mode == "security" else "🌱 Health Monitoring"
    
    print("\n" + "=" * 70)
    print("🌐 WEB DASHBOARD")
    print("=" * 70)
    print(f"Mode: {mode_display}")
    print("Dashboard URL: http://localhost:8080")
    print("API Docs: http://localhost:8080/api/docs")
    print("Mode Switch: POST http://localhost:8080/api/switch_mode")
    print("=" * 70 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )


def main():
    """Main entry point"""
    global current_mode
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Edge AI Unified System - Security & Health Monitoring'
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['security', 'health'],
        default='security',
        help='Operating mode: security (surveillance) or health (crop monitoring)'
    )
    parser.add_argument(
        '--tflite',
        action='store_true',
        help='Use TFLite model for health mode (faster, recommended for Pi)'
    )
    args = parser.parse_args()
    
    current_mode = args.mode
    
    print("=" * 70)
    print("🚀 EDGE AI UNIFIED SYSTEM")
    print("=" * 70)
    
    if current_mode == "security":
        print("Mode: 🔒 Security Surveillance")
        print("Starting Security System + Web Dashboard...")
    else:
        print("Mode: 🌱 Crop Health Monitoring")
        model_type = "TFLite (optimized)" if args.tflite else "Keras"
        print(f"Model: {model_type}")
        print("Starting Health System + Web Dashboard...")
    
    print()
    
    try:
        # Start appropriate system in separate thread
        if current_mode == "security":
            system_thread = threading.Thread(
                target=run_surveillance,
                daemon=True,
                name="SurveillanceThread"
            )
        else:
            # Health mode - note: TFLite selection is configured in health_system.py
            system_thread = threading.Thread(
                target=run_health,
                daemon=True,
                name="HealthThread"
            )
        
        system_thread.start()
        
        # Run dashboard in main thread (for proper signal handling)
        run_dashboard(mode=current_mode)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Keyboard interrupt received")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🛑 Shutting down system...")
        if surveillance_system:
            surveillance_system.stop()
        if health_system:
            health_system.stop()
        print("✅ System stopped")


if __name__ == "__main__":
    main()
