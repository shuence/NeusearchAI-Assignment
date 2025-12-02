"""Startup sync service to ensure database is populated on app start."""
from sqlalchemy.orm import Session
from app.config.database import SessionLocal
from app.controller.products.hunnit.controller import HunnitController
from app.services.products.hunnit.db_service import HunnitProductDBService
from app.config.settings import settings
from app.utils.logger import get_logger
from app.rag.generate_embeddings import generate_embeddings_for_products
from app.services.generate_ai_features import generate_ai_features_for_products

logger = get_logger("startup_sync")


async def sync_products_on_startup():
    """
    Sync products on application startup.
    Checks if database has products, and if not (or if stale), scrapes and saves.
    """
    # Check if startup sync is enabled
    if not settings.SYNC_ON_STARTUP:
        logger.info("Startup sync is disabled. Skipping initial product sync.")
        return
    
    logger.info("Starting initial product sync on startup...")
    db: Session = None
    try:
        db = SessionLocal()
        db_service = HunnitProductDBService(db)
        
        # Check if we have products in the database
        product_count = db_service.get_product_count()
        logger.info(f"Current product count in database: {product_count}")
        
        # If database is empty or has very few products, scrape and save
        min_products_threshold = settings.MIN_PRODUCTS_THRESHOLD
        should_sync = product_count < min_products_threshold
        
        if should_sync:
            logger.info(f"Database has {product_count} products (below threshold of {min_products_threshold}). Starting initial scrape...")
            controller = HunnitController(db=db)
            
            # Scrape and save to both Redis and DB
            response = await controller.scrape_all_products(
                save_to_redis=True,
                save_to_db=True
            )
            
            if response.success:
                logger.info(f"Initial sync completed successfully: {response.message}")
                # Verify the sync
                new_count = db_service.get_product_count()
                logger.info(f"Database now has {new_count} products after sync")
            else:
                logger.error(f"Initial sync failed: {response.message}")
        else:
            logger.info(f"Database already has {product_count} products. Skipping initial scrape.")
        
        # Generate AI features for products that don't have them (after sync or if sync was skipped)
        try:
            logger.info("Checking for products without AI features...")
            successful, failed = generate_ai_features_for_products(db, batch_size=10)
            if successful > 0:
                logger.info(f"Generated AI features for {successful} products during startup")
            if failed > 0:
                logger.warning(f"Failed to generate AI features for {failed} products during startup")
            if successful == 0 and failed == 0:
                logger.info("All products already have AI features")
        except ValueError as ai_features_error:
            # This usually means GEMINI_API_KEY is not set
            logger.warning(f"AI feature generation skipped: {ai_features_error}")
        except Exception as ai_features_error:
            logger.warning(f"Could not generate AI features during startup: {ai_features_error}")
            # Continue - AI features are optional and can be generated later
        
        # Generate embeddings for products that don't have them (after sync or if sync was skipped)
        if settings.GENERATE_EMBEDDINGS_ON_STARTUP:
            try:
                logger.info("Checking for products without embeddings...")
                successful, failed = generate_embeddings_for_products(db, batch_size=10)
                if successful > 0:
                    logger.info(f"Generated embeddings for {successful} products during startup")
                if failed > 0:
                    logger.warning(f"Failed to generate embeddings for {failed} products during startup")
                if successful == 0 and failed == 0:
                    logger.info("All products already have embeddings")
            except ValueError as embedding_error:
                # This usually means GEMINI_API_KEY is not set
                logger.warning(f"Embedding generation skipped: {embedding_error}")
            except Exception as embedding_error:
                logger.warning(f"Could not generate embeddings during startup: {embedding_error}")
                # Continue - embeddings are optional and can be generated later
        else:
            logger.info("Embedding generation on startup is disabled")
            
            # Still try to sync Redis cache if it's empty (optional)
            try:
                from app.services.products.hunnit.redis_service import HunnitProductRedisService
                redis_service = HunnitProductRedisService()
                redis_count = redis_service.get_products_count()
                
                if redis_count is None or redis_count == 0:
                    logger.info("Redis cache is empty. Populating from database...")
                    # Get products from DB and cache them
                    db_products = db_service.get_all_products()
                    if db_products:
                        # Convert DB products to scraped product format for caching
                        # For now, we'll just log - full conversion would require more work
                        logger.info(f"Found {len(db_products)} products in DB. Redis cache will be populated on next scrape.")
                else:
                    logger.info(f"Redis cache already has {redis_count} products.")
            except Exception as redis_error:
                logger.warning(f"Could not check/sync Redis cache: {redis_error}")
                # Continue - Redis is optional
            
    except Exception as e:
        logger.error(f"Error during startup sync: {e}", exc_info=True)
        # Don't fail startup if sync fails - app can still run
    finally:
        if db:
            db.close()
            logger.info("Startup sync completed")

