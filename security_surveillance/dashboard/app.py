"""
FastAPI Dashboard Application
Unified web dashboard for Security & Surveillance + Smart Agriculture
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os
from pathlib import Path

# Get the dashboard directory path
DASHBOARD_DIR = Path(__file__).parent
STATIC_DIR = DASHBOARD_DIR / "static"
TEMPLATES_DIR = DASHBOARD_DIR / "templates"

# Create FastAPI app
app = FastAPI(
    title="Edge AI Dashboard",
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

# Global state to store system references (will be set by main.py)
class AppState:
    def __init__(self):
        self.security_db = None
        self.agriculture_db = None
        self.camera = None
        self.surveillance_system = None
        
app.state.app_state = AppState()


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main dashboard page"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Edge AI Dashboard"}
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Edge AI Dashboard",
        "version": "1.0.0"
    }


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("🚀 Edge AI Dashboard starting...")
    print(f"📁 Static files: {STATIC_DIR}")
    print(f"📄 Templates: {TEMPLATES_DIR}")
    print("📚 API docs available at: /api/docs")
    

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Edge AI Dashboard shutting down...")


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
