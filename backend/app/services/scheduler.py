"""Scheduler service for periodic tasks."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from app.config.database import SessionLocal
from app.controller.products.hunnit.controller import HunnitController
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger("scheduler")

# Global scheduler instance
_scheduler: AsyncIOScheduler = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


async def scrape_and_save_products():
    """Periodic task to scrape products and save to Redis and DB."""
    logger.info("Starting scheduled product scrape job...")
    db: Session = None
    try:
        # Create a new database session for this job
        db = SessionLocal()
        controller = HunnitController(db=db)
        
        # Scrape and save to both Redis and DB
        response = await controller.scrape_all_products(
            save_to_redis=True,
            save_to_db=True
        )
        
        if response.success:
            logger.info(f"Scheduled scrape completed successfully: {response.message}")
        else:
            logger.error(f"Scheduled scrape failed: {response.message}")
            
    except Exception as e:
        logger.error(f"Error in scheduled scrape job: {e}", exc_info=True)
    finally:
        if db:
            db.close()


def setup_scheduler():
    """Setup and start the scheduler with periodic tasks."""
    scheduler = get_scheduler()
    
    # Add the scraping job to run every 6 hours
    interval_hours = settings.SCRAPE_INTERVAL_HOURS
    scheduler.add_job(
        scrape_and_save_products,
        trigger=IntervalTrigger(hours=interval_hours),
        id="scrape_hunnit_products",
        name="Scrape Hunnit products and save to Redis/DB",
        replace_existing=True,
        max_instances=1,  # Prevent overlapping jobs
    )
    
    logger.info(f"Scheduler configured: scraping job will run every {interval_hours} hours")
    return scheduler


def start_scheduler():
    """Start the scheduler."""
    scheduler = setup_scheduler()
    scheduler.start()
    logger.info("Scheduler started successfully")
    return scheduler


def shutdown_scheduler():
    """Shutdown the scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown()
        _scheduler = None
        logger.info("Scheduler shut down")

