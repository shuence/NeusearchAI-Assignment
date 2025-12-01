"""Hunnit.com scraper service."""
from typing import List, Optional
import httpx
from app.schemas.products.hunnit.schemas import Product, ProductsResponse
from app.utils.logger import get_logger

logger = get_logger("hunnit_service")


class HunnitScraperService:
    """Service for scraping products from Hunnit.com."""
    
    BASE_URL = "https://hunnit.com/products.json"
    
    async def fetch_products(self) -> List[Product]:
        """
        Fetch all products from Hunnit.com products.json endpoint.
        Specifically scrapes https://hunnit.com/products.json
        
        Returns:
            List of Hunnit Product objects
            
        Raises:
            httpx.HTTPError: If the HTTP request fails
            ValueError: If the response data is invalid
        """
        logger.info(f"Fetching products from {self.BASE_URL}")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.BASE_URL)
                response.raise_for_status()
                
                data = response.json()
                
                # Validate and parse the response
                if "products" not in data:
                    raise ValueError("Invalid response format: 'products' key not found")
                
                products_response = ProductsResponse(**data)
                logger.info(f"Successfully fetched {len(products_response.products)} products")
                return products_response.products
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while fetching products: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            raise
    
    async def fetch_product_by_id(self, product_id: int) -> Optional[Product]:
        """
        Fetch a specific product by ID from Hunnit.com.
        
        Args:
            product_id: The ID of the product to fetch
            
        Returns:
            Product object if found, None otherwise
        """
        products = await self.fetch_products()
        for product in products:
            if product.id == product_id:
                return product
        return None
    
    async def fetch_products_by_tag(self, tag: str) -> List[Product]:
        """
        Fetch products filtered by tag.
        
        Args:
            tag: The tag to filter by
            
        Returns:
            List of Product objects matching the tag
        """
        products = await self.fetch_products()
        return [p for p in products if tag.lower() in [t.lower() for t in p.tags]]
    
    async def fetch_products_by_vendor(self, vendor: str) -> List[Product]:
        """
        Fetch products filtered by vendor.
        
        Args:
            vendor: The vendor name to filter by
            
        Returns:
            List of Product objects from the specified vendor
        """
        products = await self.fetch_products()
        return [p for p in products if p.vendor.lower() == vendor.lower()]

