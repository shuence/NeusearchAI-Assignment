"""Hunnit product controller for handling product scraping requests."""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.services.products.hunnit.service import HunnitScraperService
from app.services.products.hunnit.db_service import HunnitProductDBService
from app.services.products.hunnit.redis_service import HunnitProductRedisService
from app.schemas.products.hunnit.schemas import Product, ScrapeResponse, DBProduct
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
    
    def get_similar_products(
        self,
        product_id: str,
        limit: int = 4,
        similarity_threshold: float = 0.6
    ) -> List:
        """
        Get similar products using vector search.
        
        Args:
            product_id: The ID of the product to find similar products for
            limit: Maximum number of similar products to return
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of similar Product models
        """
        if not self.db:
            raise ValueError("Database session not available")
        
        try:
            from app.rag.vector_search import VectorSearchService
            
            # Get the product
            product = self.get_product_from_db_by_id(product_id)
            if not product:
                product = self.get_product_from_db_by_external_id(product_id)
            
            if not product or product.embedding is None:
                return []
            
            # Convert pgvector Vector to list
            import numpy as np
            if hasattr(product.embedding, 'tolist'):
                embedding_list = product.embedding.tolist()
            elif isinstance(product.embedding, (list, tuple)):
                embedding_list = list(product.embedding)
            else:
                # Try to convert numpy array
                embedding_array = np.array(product.embedding)
                embedding_list = embedding_array.tolist()
            
            if not embedding_list or len(embedding_list) == 0:
                return []
            
            # Use vector search to find similar products
            vector_search = VectorSearchService(self.db)
            similar_results = vector_search.search_similar_products(
                query_embedding=embedding_list,
                limit=limit + 1,  # +1 to exclude the product itself
                similarity_threshold=similarity_threshold
            )
            
            # Filter out the product itself
            similar_products = []
            for similar_product, score in similar_results:
                if str(similar_product.id) != product_id and str(similar_product.external_id) != product_id:
                    similar_products.append(similar_product)
                    if len(similar_products) >= limit:
                        break
            
            return similar_products
        except Exception as e:
            logger.error(f"Error getting similar products: {e}", exc_info=True)
            return []
    
    def get_cache_status(self) -> dict:
        """
        Get Redis cache status and metadata.
        
        Returns:
            Dictionary with cache status information
        """
        try:
            count = self.redis_service.get_products_count()
            timestamp_info = self.redis_service.get_scrape_timestamp()
            
            return {
                "cache_available": True,
                "products_cached": count or 0,
                "last_scrape": timestamp_info,
                "status": "active" if count else "empty"
            }
        except Exception as e:
            logger.error(f"Error getting cache status: {e}", exc_info=True)
            return {
                "cache_available": False,
                "error": str(e),
                "status": "unavailable"
            }
    
    def _convert_scraped_product_to_db_product(self, scraped_product: Product) -> DBProduct:
        """
        Convert a scraped Product schema to DBProduct schema.
        
        Args:
            scraped_product: Scraped product from Hunnit.com
            
        Returns:
            DBProduct schema
        """
        return DBProduct(
            id=str(scraped_product.id),
            external_id=str(scraped_product.id),
            title=scraped_product.title,
            handle=scraped_product.handle,
            description=scraped_product.body_html[:500] if scraped_product.body_html else None,
            body_html=scraped_product.body_html,
            vendor=scraped_product.vendor,
            product_type=scraped_product.product_type,
            category=scraped_product.product_type,
            tags=scraped_product.tags,
            image_urls=[str(img.src) for img in scraped_product.images] if scraped_product.images else None,
        )
    
    async def get_all_products_as_db_products(self, from_db: bool = True) -> List[DBProduct]:
        """
        Get all products as DBProduct schemas.
        
        Args:
            from_db: If True, get from database. If False, scrape from Hunnit.com
            
        Returns:
            List of DBProduct schemas
        """
        if from_db:
            db_products = self.get_all_products_from_db()
            return [DBProduct.model_validate(product) for product in db_products]
        else:
            # Scrape from Hunnit.com (legacy behavior)
            response = await self.scrape_all_products(save_to_db=False)
            if not response.success or response.products is None:
                return []
            return [self._convert_scraped_product_to_db_product(p) for p in response.products]
    
    async def get_product_as_db_product(
        self,
        product_id: str,
        from_db: bool = True
    ) -> Optional[DBProduct]:
        """
        Get a specific product as DBProduct schema.
        
        Args:
            product_id: The ID of the product (UUID for DB, or external_id)
            from_db: If True, search in database. If False, scrape from Hunnit.com
            
        Returns:
            DBProduct schema if found, None otherwise
        """
        if from_db:
            # Try to get from database by UUID first
            product = self.get_product_from_db_by_id(product_id)
            if product:
                return DBProduct.model_validate(product)
            
            # Try by external_id
            product = self.get_product_from_db_by_external_id(product_id)
            if product:
                return DBProduct.model_validate(product)
            
            return None
        else:
            # Legacy: scrape from Hunnit.com
            try:
                external_id_int = int(product_id)
                product = await self.get_product_by_id(external_id_int)
                if product is None:
                    return None
                return self._convert_scraped_product_to_db_product(product)
            except ValueError:
                return None
    
    async def get_products_by_tag_as_db_products(
        self,
        tag: str,
        from_db: bool = True
    ) -> List[DBProduct]:
        """
        Get products filtered by tag as DBProduct schemas.
        
        Args:
            tag: The tag to filter by
            from_db: If True, search in database. If False, scrape from Hunnit.com
            
        Returns:
            List of DBProduct schemas matching the tag
        """
        if from_db:
            db_products = self.get_products_from_db_by_tag(tag)
            return [DBProduct.model_validate(product) for product in db_products]
        else:
            products = await self.get_products_by_tag(tag)
            return [self._convert_scraped_product_to_db_product(p) for p in products]
    
    async def get_products_by_vendor_as_db_products(
        self,
        vendor: str,
        from_db: bool = True
    ) -> List[DBProduct]:
        """
        Get products filtered by vendor as DBProduct schemas.
        
        Args:
            vendor: The vendor name to filter by
            from_db: If True, search in database. If False, scrape from Hunnit.com
            
        Returns:
            List of DBProduct schemas from the specified vendor
        """
        if from_db:
            db_products = self.get_products_from_db_by_vendor(vendor)
            return [DBProduct.model_validate(product) for product in db_products]
        else:
            products = await self.get_products_by_vendor(vendor)
            return [self._convert_scraped_product_to_db_product(p) for p in products]
    
    def get_similar_products_as_db_products(
        self,
        product_id: str,
        limit: int = 4
    ) -> List[DBProduct]:
        """
        Get similar products as DBProduct schemas.
        
        Args:
            product_id: The ID of the product to find similar products for
            limit: Maximum number of similar products to return
            
        Returns:
            List of similar DBProduct schemas
        """
        similar_products = self.get_similar_products(product_id, limit=limit)
        return [DBProduct.model_validate(product) for product in similar_products]

