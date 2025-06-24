from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Import API routers
from api.accounts import router as accounts_router
from api.videos import router as videos_router
from api.tasks import router as tasks_router
from api.stats import router as stats_router
from api.tiktok_sources import router as tiktok_sources_router

# Import existing modules for initialization
from modules.database import init_database

# Initialize FastAPI
app = FastAPI(
    title="Instagram Bot API",
    description="Web interface for Instagram Bot with Proxy Support",
    version="1.1.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(accounts_router, prefix="/api/accounts", tags=["accounts"])
app.include_router(videos_router, prefix="/api/videos", tags=["videos"])
app.include_router(tasks_router, prefix="/api/tasks", tags=["tasks"])
app.include_router(stats_router, prefix="/api/stats", tags=["statistics"])
app.include_router(tiktok_sources_router, prefix="/api/tiktok-sources", tags=["tiktok-sources"])

# Initialize on startup
@app.on_event("startup")
async def startup():
    init_database()
    os.makedirs("videos", exist_ok=True)
    os.makedirs("sessions", exist_ok=True)
    print("✅ FastAPI server started with proxy support")
    print("📡 Proxy features:")
    print("  - Individual account proxy configuration")
    print("  - Automatic proxy testing and health monitoring")
    print("  - Fallback to direct connection on proxy failure")
    print("  - Real-time proxy status tracking")

@app.get("/")
async def root():
    return {
        "message": "Instagram Bot API with Proxy Support",
        "status": "running",
        "version": "1.1.0",
        "features": [
            "Account management",
            "Video processing",
            "Task management",
            "Proxy support",
            "Health monitoring"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)