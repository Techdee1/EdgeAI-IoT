"""
Integrated System Launcher
Starts both surveillance system and web dashboard
"""
import sys
import threading
import time
import uvicorn
from pathlib import Path

# Import surveillance system
from main import SurveillanceSystem

# Import dashboard app
from dashboard.app import app

# Shared state between systems
surveillance_system = None


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
    
    # Start surveillance (without signal handlers in thread)
    try:
        surveillance_system.start()
    except Exception as e:
        print(f"⚠️  Surveillance system error: {e}")


def run_dashboard():
    """Run FastAPI dashboard"""
    print("\n📊 Starting Web Dashboard...")
    
    # Give surveillance system time to initialize
    time.sleep(2)
    
    print("\n" + "=" * 70)
    print("🌐 WEB DASHBOARD")
    print("=" * 70)
    print("Dashboard URL: http://localhost:8080")
    print("API Docs: http://localhost:8080/api/docs")
    print("=" * 70 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )


def main():
    """Main entry point"""
    print("=" * 70)
    print("🚀 EDGE AI UNIFIED SYSTEM")
    print("=" * 70)
    print("Starting Security Surveillance + Web Dashboard...")
    print()
    
    try:
        # Start surveillance in separate thread
        surveillance_thread = threading.Thread(
            target=run_surveillance,
            daemon=True,
            name="SurveillanceThread"
        )
        surveillance_thread.start()
        
        # Run dashboard in main thread (for proper signal handling)
        run_dashboard()
        
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
        print("✅ System stopped")


if __name__ == "__main__":
    main()
