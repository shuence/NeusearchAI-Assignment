"""Hunnit product controller for handling product scraping requests."""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.services.products.hunnit.service import HunnitScraperService
from app.services.products.hunnit.db_service import HunnitProductDBService
from app.services.products.hunnit.redis_service import HunnitProductRedisService
from app.schemas.products.hunnit.schemas import Product, ScrapeResponse
from app.utils.logger import get_logger

logger = get_logger("hunnit_controller")


class HunnitController:
    """Controller for Hunnit product scraping endpoints."""
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize Hunnit controller with service."""
        self.scraper_service = HunnitScraperService()
        self.db = db
        self.redis_service = HunnitProductRedisService()
    
    async def scrape_all_products(self, save_to_db: bool = True, save_to_redis: bool = True) -> ScrapeResponse:
        """
        Scrape all products from Hunnit.com.
        Specifically scrapes from https://hunnit.com/products.json
        
        Flow: Scrape -> Save to Redis -> Save to DB
        
        Args:
            save_to_db: Whether to save scraped products to the database
            save_to_redis: Whether to save scraped products to Redis cache
            
        Returns:
            ScrapeResponse with all scraped Hunnit products
        """
        logger.info("Starting product scraping from Hunnit.com")
        try:
            products = await self.scraper_service.fetch_products()
            logger.info(f"Successfully scraped {len(products)} products")
            
            # Step 1: Save to Redis first (cache)
            if save_to_redis:
                try:
                    redis_saved = self.redis_service.save_products(products)
                    if redis_saved:
                        logger.info(f"Cached {len(products)} products in Redis")
                    else:
                        logger.warning("Failed to save products to Redis, continuing...")
                except Exception as e:
                    logger.error(f"Failed to save products to Redis: {e}", exc_info=True)
                    # Continue even if Redis save fails
            
            # Step 2: Save to database (persistent storage)
            if save_to_db and self.db:
                try:
                    db_service = HunnitProductDBService(self.db)
                    created, updated = db_service.save_products(products)
                    logger.info(f"Saved {len(products)} products to database: {created} created, {updated} updated")
                except Exception as e:
                    logger.error(f"Failed to save products to database: {e}", exc_info=True)
                    # Continue even if DB save fails
            
            return ScrapeResponse(
                success=True,
                message=f"Successfully scraped {len(products)} Hunnit products from hunnit.com",
                count=len(products),
                products=products
            )
        except Exception as e:
            logger.error(f"Failed to scrape Hunnit products: {e}", exc_info=True)
            return ScrapeResponse(
                success=False,
                message=f"Failed to scrape Hunnit products: {str(e)}",
                count=0,
                products=None
            )
    
    async def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """
        Get a specific product by ID.
        
        Args:
            product_id: The ID of the product to fetch
            
        Returns:
            Product if found, None otherwise
        """
        try:
            return await self.scraper_service.fetch_product_by_id(product_id)
        except Exception:
            return None
    
    async def get_products_by_tag(self, tag: str) -> List[Product]:
        """
        Get products filtered by tag.
        
        Args:
            tag: The tag to filter by
            
        Returns:
            List of products matching the tag
        """
        try:
            return await self.scraper_service.fetch_products_by_tag(tag)
        except Exception:
            return []
    
    async def get_products_by_vendor(self, vendor: str) -> List[Product]:
        """
        Get products filtered by vendor.
        
        Args:
            vendor: The vendor name to filter by
            
        Returns:
            List of products from the specified vendor
        """
        try:
            return await self.scraper_service.fetch_products_by_vendor(vendor)
        except Exception:
            return []
    
    def get_all_products_from_db(self) -> List:
        """
        Get all products from the database.
        
        Returns:
            List of Product models from database
        """
        if not self.db:
            raise ValueError("Database session not available")
        
        db_service = HunnitProductDBService(self.db)
        return db_service.get_all_products()
    
    def get_product_from_db_by_external_id(self, external_id: str):
        """
        Get a product from database by external ID.
        
        Args:
            external_id: The external ID from Hunnit.com
            
        Returns:
            Product model if found, None otherwise
        """
        if not self.db:
            raise ValueError("Database session not available")
        
        db_service = HunnitProductDBService(self.db)
        return db_service.get_product_by_external_id(external_id)
    
    def get_product_from_db_by_id(self, product_id: str):
        """
        Get a product from database by UUID.
        
        Args:
            product_id: The database UUID
            
        Returns:
            Product model if found, None otherwise
        """
        if not self.db:
            raise ValueError("Database session not available")
        
        db_service = HunnitProductDBService(self.db)
        return db_service.get_product_by_id(product_id)
    
    def get_products_from_db_by_tag(self, tag: str) -> List:
        """
        Get products from database filtered by tag.
        
        Args:
            tag: The tag to filter by
            
        Returns:
            List of Product models matching the tag
        """
        if not self.db:
            raise ValueError("Database session not available")
        
        db_service = HunnitProductDBService(self.db)
        return db_service.get_products_by_tag(tag)
    
    def get_products_from_db_by_vendor(self, vendor: str) -> List:
        """
        Get products from database filtered by vendor.
        
        Args:
            vendor: The vendor name to filter by
            
        Returns:
            List of Product models from the specified vendor
        """
        if not self.db:
            raise ValueError("Database session not available")
        
        db_service = HunnitProductDBService(self.db)
        return db_service.get_products_by_vendor(vendor)
    
    def get_product_count_from_db(self) -> int:
        """
        Get total number of products in the database.
        
        Returns:
            Total count of products
        """
        if not self.db:
            raise ValueError("Database session not available")
        
        db_service = HunnitProductDBService(self.db)
        return db_service.get_product_count()

