"""Redis service for caching Hunnit products."""
import json
from typing import List, Optional
from app.config.redis import get_redis_client
from app.schemas.products.hunnit.schemas import Product, ProductsResponse
from app.utils.logger import get_logger

logger = get_logger("hunnit_redis_service")

# Redis key prefixes
PRODUCTS_KEY = "hunnit:products"
PRODUCT_KEY_PREFIX = "hunnit:product:"
SCRAPE_TIMESTAMP_KEY = "hunnit:scrape:timestamp"
PRODUCTS_COUNT_KEY = "hunnit:products:count"


class HunnitProductRedisService:
    """Service for caching Hunnit products in Redis."""
    
    def __init__(self):
        """Initialize Redis service."""
        self.redis = get_redis_client()
    
    def save_products(self, products: List[Product], ttl: int = 86400) -> bool:
        """
        Save products to Redis cache.
        
        Args:
            products: List of products to cache
            ttl: Time to live in seconds (default: 24 hours)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Save all products as a JSON list
            products_data = [product.model_dump() for product in products]
            self.redis.setex(
                PRODUCTS_KEY,
                ttl,
                json.dumps(products_data, default=str)
            )
            
            # Save individual products for quick lookup
            for product in products:
                product_key = f"{PRODUCT_KEY_PREFIX}{product.id}"
                self.redis.setex(
                    product_key,
                    ttl,
                    json.dumps(product.model_dump(), default=str)
                )
            
            # Save metadata
            self.redis.setex(PRODUCTS_COUNT_KEY, ttl, len(products))
            self.redis.setex(SCRAPE_TIMESTAMP_KEY, ttl, json.dumps({
                "timestamp": self._get_current_timestamp(),
                "count": len(products)
            }, default=str))
            
            logger.info(f"Cached {len(products)} products in Redis with TTL {ttl}s")
            return True
        except Exception as e:
            logger.error(f"Failed to save products to Redis: {e}", exc_info=True)
            return False
    
    def get_products(self) -> Optional[List[Product]]:
        """
        Get all products from Redis cache.
        
        Returns:
            List of products if found, None otherwise
        """
        try:
            cached_data = self.redis.get(PRODUCTS_KEY)
            if cached_data is None:
                logger.debug("No products found in Redis cache")
                return None
            
            products_data = json.loads(cached_data)
            products = [Product(**product_data) for product_data in products_data]
            logger.info(f"Retrieved {len(products)} products from Redis cache")
            return products
        except Exception as e:
            logger.error(f"Failed to get products from Redis: {e}", exc_info=True)
            return None
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """
        Get a specific product from Redis cache by ID.
        
        Args:
            product_id: The ID of the product
            
        Returns:
            Product if found, None otherwise
        """
        try:
            product_key = f"{PRODUCT_KEY_PREFIX}{product_id}"
            cached_data = self.redis.get(product_key)
            if cached_data is None:
                return None
            
            product_data = json.loads(cached_data)
            return Product(**product_data)
        except Exception as e:
            logger.error(f"Failed to get product {product_id} from Redis: {e}", exc_info=True)
            return None
    
    def get_scrape_timestamp(self) -> Optional[dict]:
        """
        Get the timestamp of the last scrape.
        
        Returns:
            Dictionary with timestamp and count, or None
        """
        try:
            cached_data = self.redis.get(SCRAPE_TIMESTAMP_KEY)
            if cached_data is None:
                return None
            return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Failed to get scrape timestamp from Redis: {e}", exc_info=True)
            return None
    
    def get_products_count(self) -> Optional[int]:
        """
        Get the count of cached products.
        
        Returns:
            Count of products, or None
        """
        try:
            count = self.redis.get(PRODUCTS_COUNT_KEY)
            return int(count) if count else None
        except Exception as e:
            logger.error(f"Failed to get products count from Redis: {e}", exc_info=True)
            return None
    
    def clear_cache(self) -> bool:
        """
        Clear all cached products from Redis.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all product keys
            product_keys = self.redis.keys(f"{PRODUCT_KEY_PREFIX}*")
            
            # Delete all keys
            keys_to_delete = [PRODUCTS_KEY, PRODUCTS_COUNT_KEY, SCRAPE_TIMESTAMP_KEY] + product_keys
            if keys_to_delete:
                self.redis.delete(*keys_to_delete)
            
            logger.info("Cleared all Hunnit products from Redis cache")
            return True
        except Exception as e:
            logger.error(f"Failed to clear Redis cache: {e}", exc_info=True)
            return False
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as ISO format string."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()

