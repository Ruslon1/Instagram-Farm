from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import uuid

# Import configuration and core modules
from config.settings import settings
from core.logging import setup_logging, get_logger, log_api_request
from core.security import SecurityHeaders
from core import ConfigManager

# Import API routers
from api.accounts import router as accounts_router
from api.videos import router as videos_router
from api.tasks import router as tasks_router
from api.stats import router as stats_router
from api.tiktok_sources import router as tiktok_sources_router

# Import existing modules for initialization
from modules.database import init_database

# Setup logging first
setup_logging()
logger = get_logger("main")

# Initialize FastAPI
app = FastAPI(
    title=settings.app_name,
    description="Production-ready Instagram Bot with Proxy Support",
    version=settings.app_version,
    debug=settings.debug,
    docs_url="/docs" if settings.is_development() else None,
    redoc_url="/redoc" if settings.is_development() else None
)

# Security headers
security_headers = SecurityHeaders()


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    start_time = time.time()

    # Generate request ID for tracing
    request_id = str(uuid.uuid4())

    # Log API request
    log_api_request(
        method=request.method,
        path=request.url.path,
        request_id=request_id,
        user_agent=request.headers.get("user-agent"),
        client_ip=request.client.host
    )

    response = await call_next(request)

    # Add security headers
    for header, value in security_headers.get_security_headers().items():
        response.headers[header] = value

    # Add custom headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = str(time.time() - start_time)

    return response


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time"]
)


# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": time.time()
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with dependencies."""
    health_status = {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": time.time(),
        "checks": {
            "database": "unknown",
            "redis": "unknown",
            "filesystem": "unknown"
        }
    }

    # Check database connection
    try:
        from modules.database import get_database_connection
        with get_database_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check Redis connection
    try:
        import redis
        from urllib.parse import urlparse
        parsed_url = urlparse(settings.redis_url)
        r = redis.Redis(
            host=parsed_url.hostname,
            port=parsed_url.port,
            password=parsed_url.password,
            decode_responses=True
        )
        r.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check filesystem
    try:
        import os
        for directory in [settings.videos_dir, settings.sessions_dir, settings.logs_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
        health_status["checks"]["filesystem"] = "healthy"
    except Exception as e:
        health_status["checks"]["filesystem"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)


# Include API routers - БЕЗ response_model параметров
app.include_router(accounts_router, prefix="/api/accounts", tags=["accounts"])
app.include_router(videos_router, prefix="/api/videos", tags=["videos"])
app.include_router(tasks_router, prefix="/api/tasks", tags=["tasks"])
app.include_router(stats_router, prefix="/api/stats", tags=["statistics"])
app.include_router(tiktok_sources_router, prefix="/api/tiktok-sources", tags=["tiktok-sources"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error_type=type(exc).__name__,
        error_message=str(exc),
        exc_info=True
    )

    if settings.is_development():
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "type": type(exc).__name__,
                "message": str(exc),
                "path": request.url.path
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred"
            }
        )


# Initialize on startup - ИСПРАВЛЕНО: используем lifespan вместо on_event
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Instagram Bot API", version=settings.app_version, environment=settings.environment)

    try:
        # Initialize database
        init_database()
        logger.info("Database initialized successfully")

        # Create required directories
        import os
        for directory in [settings.videos_dir, settings.sessions_dir, settings.logs_dir]:
            os.makedirs(directory, exist_ok=True)
        logger.info("Required directories created")

        # Validate configuration
        config_issues = ConfigManager.validate_config()
        if config_issues:
            logger.warning("Configuration issues found", issues=config_issues)
            for issue in config_issues:
                logger.warning(f"Config issue: {issue}")

        # Log configuration summary
        logger.info(
            "Application configuration loaded",
            database_type=ConfigManager.get_database_config()['type'],
            redis_configured=bool(settings.redis_url),
            telegram_enabled=ConfigManager.get_telegram_config()['enabled'],
            security_enabled=bool(settings.api_key),
            debug=settings.debug
        )

        logger.info("Instagram Bot API started successfully")

    except Exception as e:
        logger.error("Failed to start application", error=str(e), exc_info=True)
        raise

    yield  # Приложение запущено

    # Shutdown
    logger.info("Shutting down Instagram Bot API")

# Применяем lifespan к приложению
app.router.lifespan_context = lifespan


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"{settings.app_name} - Production Ready",
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "running",
        "docs_url": "/docs" if settings.is_development() else "disabled_in_production",
        "features": [
            "Account management with proxy support",
            "Video processing and upload",
            "Task management with progress tracking",
            "Health monitoring",
            "Structured logging",
            "Security headers"
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development(),
        log_level="debug" if settings.debug else "info"
    )