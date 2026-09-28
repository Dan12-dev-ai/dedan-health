import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .api.analyze import router as analyze_router, initialize_providers
from .core.config import get_settings, Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

# Rate limiting storage (in production, use Redis)
rate_limit_storage: dict = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute: int = 30, window_seconds: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/api/health", "/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        now = time.time()
        window_start = now - self.window_seconds

        # Clean old entries
        if client_ip in rate_limit_storage:
            rate_limit_storage[client_ip] = [
                ts for ts in rate_limit_storage[client_ip] if ts > window_start
            ]
        else:
            rate_limit_storage[client_ip] = []

        # Check limit
        if len(rate_limit_storage[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "details": {
                        "limit": self.requests_per_minute,
                        "window_seconds": self.window_seconds,
                        "retry_after": self.window_seconds,
                    },
                    "timestamp": time.time(),
                },
                headers={"Retry-After": str(self.window_seconds)},
            )

        # Record request
        rate_limit_storage[client_ip].append(now)

        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for audit trail."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            f"REQUEST: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        response = await call_next(request)
        
        # Log response
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"RESPONSE: {request.method} {request.url.path} "
            f"status={response.status_code} time={process_time:.1f}ms"
        )
        
        response.headers["X-Process-Time"] = f"{process_time:.1f}"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    settings = get_settings()
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} in {settings.ENVIRONMENT} mode")
    
    # Initialize AI providers
    try:
        await initialize_providers(settings)
        logger.info("AI providers initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AI providers: {e}")
        # Don't fail startup - providers might be optional in some configs
    
    # Start cleanup task for expired images
    import asyncio
    asyncio.create_task(periodic_cleanup())
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")


async def periodic_cleanup():
    """Periodically clean up expired images."""
    import asyncio
    from .services.image_service import image_service
    
    while True:
        await asyncio.sleep(3600)  # Run every hour
        try:
            deleted = image_service.cleanup_expired()
            if deleted:
                logger.info(f"Periodic cleanup: removed {deleted} expired images")
        except Exception as e:
            logger.error(f"Periodic cleanup error: {e}")


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = settings or get_settings()
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="DEDAN Health API - AI-powered medical triage for underserved regions",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Process-Time"],
    )

    # Trusted hosts (security)
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*.dedanhealth.org", "dedanhealth.org", "localhost", "127.0.0.1"],
        )

    # Rate limiting
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.RATE_LIMIT_REQUESTS,
        window_seconds=settings.RATE_LIMIT_WINDOW,
    )

    # Request logging
    app.add_middleware(RequestLoggingMiddleware)

    # Session middleware (for future auth)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.ADMIN_API_KEY or "dev-secret-change-in-production",
        https_only=settings.ENVIRONMENT == "production",
    )

    # Exception handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail if isinstance(exc.detail, str) else "HTTP error",
                "error_code": f"HTTP_{exc.status_code}",
                "details": exc.detail if isinstance(exc.detail, dict) else None,
                "timestamp": time.time(),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation error",
                "error_code": "VALIDATION_ERROR",
                "details": exc.errors(),
                "timestamp": time.time(),
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "error_code": "INTERNAL_ERROR",
                "details": {"type": type(exc).__name__} if settings.DEBUG else None,
                "timestamp": time.time(),
            },
        )

    # Include routers
    app.include_router(analyze_router)

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "operational",
            "documentation": "/docs" if settings.DEBUG else "disabled in production",
            "health_check": "/api/health",
        }

    # Legacy health check
    @app.get("/health")
    async def legacy_health():
        return {"status": "healthy", "service": settings.APP_NAME}

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.DEBUG,
    )