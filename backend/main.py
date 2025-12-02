from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from app.routers import health
from app.routers.products.hunnit import router as hunnit_router
from app.routers import chat
from app.schemas.common import MessageResponse
from app.config.settings import settings
from app.config.database import init_db, engine
from app.config.redis import get_redis_client, close_redis
from app.services.scheduler import start_scheduler, shutdown_scheduler
from app.services.startup_sync import sync_products_on_startup
from app.utils.logger import setup_logging, get_logger
from app.utils.env_validation import validate_and_log
from app.constants import STATUS_MESSAGE_HELLO
from app.docs import get_scalar_html
from app.middleware.validation import RequestValidationMiddleware, ErrorHandlingMiddleware
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from app.middleware.metrics import MetricsMiddleware
from app.services.email_service import send_startup_error_notification
from slowapi.errors import RateLimitExceeded

# Setup logging first
setup_logging()
logger = get_logger(__name__)

# Validate environment variables
try:
    validate_and_log()
except Exception as e:
    logger.error(f"Environment validation failed: {e}")
    # Note: Can't use async email here as we're not in async context yet
    # Email will be sent if app fails to start
    if settings.ENVIRONMENT == "production":
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting up application...")
    
    # Skip database initialization in test environment
    if settings.ENVIRONMENT != "test":
        try:
            # Initialize database - create tables if they don't exist
            logger.info("Initializing database...")
            init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            # Send email notification
            await send_startup_error_notification(e, component="Database")
            raise
    else:
        logger.info("Skipping database initialization in test environment")
    
    # Initialize Redis connection (skip in test environment)
    if settings.ENVIRONMENT != "test":
        try:
            logger.info("Initializing Redis connection...")
            get_redis_client()
            logger.info("Redis connection initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis (will continue without cache): {e}")
            # Send email notification (non-critical, but still notify)
            await send_startup_error_notification(e, component="Redis")
            # Continue without Redis - it's optional for caching
    else:
        logger.info("Skipping Redis initialization in test environment")
    
    # Sync products on startup (check DB and scrape if needed) - skip in test
    if settings.SYNC_ON_STARTUP and settings.ENVIRONMENT != "test":
        # Run sync in background task to not block startup
        async def run_startup_sync():
            """Run startup sync in background."""
        try:
            await sync_products_on_startup()
        except Exception as e:
            logger.error(f"Error in startup sync: {e}", exc_info=True)
            # Send email notification
            await send_startup_error_notification(e, component="Product Sync")
        
        try:
            logger.info("Starting initial product sync in background...")
            # Create background task for sync
            sync_task = asyncio.create_task(run_startup_sync())
            logger.info("Initial sync task created (running in background)")
        except Exception as e:
            logger.error(f"Failed to start initial sync: {e}", exc_info=True)
            # Send email notification
            await send_startup_error_notification(e, component="Product Sync Task")
    else:
        logger.info("Startup sync is disabled. Skipping initial product sync.")
    
    # Start scheduler for periodic scraping (skip in test environment)
    if settings.ENVIRONMENT != "test":
        try:
            logger.info("Starting scheduler...")
            start_scheduler()
            logger.info("Scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}", exc_info=True)
            # Send email notification
            await send_startup_error_notification(e, component="Scheduler")
            # Continue even if scheduler fails
    else:
        logger.info("Skipping scheduler start in test environment")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Shutdown scheduler
    try:
        shutdown_scheduler()
    except Exception as e:
        logger.error(f"Error shutting down scheduler: {e}", exc_info=True)
    
    # Close Redis connections
    try:
        await close_redis()
    except Exception as e:
        logger.error(f"Error closing Redis connections: {e}", exc_info=True)
    
    # Close database connections
    engine.dispose()
    logger.info("Database connections closed")


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    lifespan=lifespan,
)

# Initialize rate limiter with app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Add Scalar API documentation
@app.get("/docs", include_in_schema=False)
async def scalar_html():
    return get_scalar_html(
        openapi_schema=app.openapi(),
        title=app.title + " - API Documentation",
    )

# Error handling middleware (should be first to catch all errors)
app.add_middleware(ErrorHandlingMiddleware)

# Metrics middleware (track performance)
app.add_middleware(MetricsMiddleware)

# Request validation middleware
app.add_middleware(RequestValidationMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Include routers
app.include_router(health.router, prefix=settings.API_PREFIX, tags=["health"])
app.include_router(hunnit_router, prefix=f"{settings.API_PREFIX}/products/hunnit", tags=["products", "hunnit"])
app.include_router(chat.router, prefix=f"{settings.API_PREFIX}/chat", tags=["chat", "rag"])


@app.get("/", response_model=MessageResponse)
async def root() -> MessageResponse:
    """Root endpoint returning a hello world message."""
    return MessageResponse(message=STATUS_MESSAGE_HELLO)

