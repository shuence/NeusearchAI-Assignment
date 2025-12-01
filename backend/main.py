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
from app.constants import STATUS_MESSAGE_HELLO
from app.docs import get_scalar_html

# Setup logging first
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting up application...")
    try:
        # Initialize database - create tables if they don't exist
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Initialize Redis connection
    try:
        logger.info("Initializing Redis connection...")
        get_redis_client()
        logger.info("Redis connection initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize Redis (will continue without cache): {e}")
        # Continue without Redis - it's optional for caching
    
    # Sync products on startup (check DB and scrape if needed)
    if settings.SYNC_ON_STARTUP:
        # Run sync in background task to not block startup
        async def run_startup_sync():
            """Run startup sync in background."""
            try:
                await sync_products_on_startup()
            except Exception as e:
                logger.error(f"Error in startup sync: {e}", exc_info=True)
        
        try:
            logger.info("Starting initial product sync in background...")
            # Create background task for sync
            sync_task = asyncio.create_task(run_startup_sync())
            logger.info("Initial sync task created (running in background)")
        except Exception as e:
            logger.error(f"Failed to start initial sync: {e}", exc_info=True)
            # Continue even if sync fails
    else:
        logger.info("Startup sync is disabled. Skipping initial product sync.")
    
    # Start scheduler for periodic scraping
    try:
        logger.info("Starting scheduler...")
        start_scheduler()
        logger.info("Scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}", exc_info=True)
        # Continue even if scheduler fails
    
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

# Add Scalar API documentation
@app.get("/docs", include_in_schema=False)
async def scalar_html():
    return get_scalar_html(
        openapi_schema=app.openapi(),
        title=app.title + " - API Documentation",
    )

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

