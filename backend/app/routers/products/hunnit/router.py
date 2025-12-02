"""Hunnit products router for product scraping endpoints."""
import time
from typing import List
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from app.controller.products.hunnit.controller import HunnitController
from app.schemas.products.hunnit.schemas import (
    Product, ScrapeResponse, DBProduct, ProductListResponse, ProductResponse
)
from app.config.database import get_db
from app.middleware.rate_limit import limiter

router = APIRouter()


@router.get("/scrape", response_model=ScrapeResponse)
@limiter.limit("5/hour")
async def scrape_hunnit_products(
    request: Request,
    save_to_db: bool = True,
    save_to_redis: bool = True,
    db: Session = Depends(get_db)
) -> ScrapeResponse:
    """
    Scrape all products from Hunnit.com and save to Redis and database.
    Specifically fetches product data from https://hunnit.com/products.json
    
    Flow: Scrape -> Save to Redis -> Save to DB
    
    Args:
        save_to_db: Whether to save scraped products to the database (default: True)
        save_to_redis: Whether to save scraped products to Redis cache (default: True)
    
    Returns:
        ScrapeResponse with all scraped Hunnit products
        
    Raises:
        HTTPException: If scraping fails or returns no products
    """
    start_time = time.time()
    try:
        controller = HunnitController(db=db)
        result = await controller.scrape_all_products(
            save_to_db=save_to_db,
            save_to_redis=save_to_redis
        )
        
        if not result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Scraping failed: {result.message}"
            )
        
        if not result.products or len(result.products) == 0:
            raise HTTPException(
                status_code=404,
                detail="No products found. The source may be unavailable or empty."
            )
        
        # Add response time
        response_time_ms = (time.time() - start_time) * 1000
        result.response_time_ms = round(response_time_ms, 2)
        return result
    except HTTPException:
        raise
    except Exception as e:
        from app.utils.logger import get_logger
        logger = get_logger("hunnit_router")
        logger.error(f"Error in scrape endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while scraping products. Please try again later."
        )


@router.get("", response_model=ProductListResponse)
@limiter.limit("60/minute")
async def get_all_products(
    request: Request,
    from_db: bool = True,
    db: Session = Depends(get_db)
) -> ProductListResponse:
    """
    Get all products. By default, returns products from database.
    
    Args:
        from_db: If True, get from database. If False, scrape from Hunnit.com
    
    Returns:
        ProductListResponse with all products and response time
    """
    start_time = time.time()
    try:
        controller = HunnitController(db=db)
        products = await controller.get_all_products_as_db_products(from_db=from_db)
        response_time_ms = (time.time() - start_time) * 1000
        return ProductListResponse(
            products=products,
            count=len(products),
            response_time_ms=round(response_time_ms, 2)
        )
    except Exception as e:
        from app.utils.logger import get_logger
        logger = get_logger("hunnit_router")
        logger.error(f"Error in get_all_products endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching products. Please try again later."
        )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    from_db: bool = True,
    db: Session = Depends(get_db)
) -> ProductResponse:
    """
    Get a specific product by ID. By default, searches in database first.
    
    Args:
        product_id: The ID of the product (UUID for DB, or external_id)
        from_db: If True, search in database. If False, scrape from Hunnit.com
        
    Returns:
        ProductResponse with product and response time
        
    Raises:
        HTTPException: If product not found
    """
    start_time = time.time()
    try:
        controller = HunnitController(db=db)
        product = await controller.get_product_as_db_product(product_id, from_db=from_db)
        
        if product is None:
            raise HTTPException(
                status_code=404,
                detail=f"Product with ID {product_id} not found"
            )
        
        response_time_ms = (time.time() - start_time) * 1000
        return ProductResponse(
            product=product,
            response_time_ms=round(response_time_ms, 2)
        )
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid product ID format: {product_id}"
        )
    except Exception as e:
        from app.utils.logger import get_logger
        logger = get_logger("hunnit_router")
        logger.error(f"Error in get_product endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching the product. Please try again later."
        )


@router.get("/tag/{tag}", response_model=ProductListResponse)
async def get_products_by_tag(
    tag: str,
    from_db: bool = True,
    db: Session = Depends(get_db)
) -> ProductListResponse:
    """
    Get products filtered by tag. By default, searches in database.
    
    Args:
        tag: The tag to filter by
        from_db: If True, search in database. If False, scrape from Hunnit.com
        
    Returns:
        ProductListResponse with products matching the tag and response time
    """
    start_time = time.time()
    try:
        controller = HunnitController(db=db)
        products = await controller.get_products_by_tag_as_db_products(tag, from_db=from_db)
        response_time_ms = (time.time() - start_time) * 1000
        return ProductListResponse(
            products=products,
            count=len(products),
            response_time_ms=round(response_time_ms, 2)
        )
    except Exception as e:
        from app.utils.logger import get_logger
        logger = get_logger("hunnit_router")
        logger.error(f"Error in get_products_by_tag endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching products. Please try again later."
        )


@router.get("/vendor/{vendor}", response_model=ProductListResponse)
async def get_products_by_vendor(
    vendor: str,
    from_db: bool = True,
    db: Session = Depends(get_db)
) -> ProductListResponse:
    """
    Get products filtered by vendor. By default, searches in database.
    
    Args:
        vendor: The vendor name to filter by
        from_db: If True, search in database. If False, scrape from Hunnit.com
        
    Returns:
        ProductListResponse with products from the specified vendor and response time
    """
    start_time = time.time()
    try:
        controller = HunnitController(db=db)
        products = await controller.get_products_by_vendor_as_db_products(vendor, from_db=from_db)
        response_time_ms = (time.time() - start_time) * 1000
        return ProductListResponse(
            products=products,
            count=len(products),
            response_time_ms=round(response_time_ms, 2)
        )
    except Exception as e:
        from app.utils.logger import get_logger
        logger = get_logger("hunnit_router")
        logger.error(f"Error in get_products_by_vendor endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching products. Please try again later."
        )


@router.get("/stats/count", response_model=dict)
async def get_product_count(db: Session = Depends(get_db)) -> dict:
    """
    Get total number of products in the database.
    
    Returns:
        Dictionary with product count and response time
    """
    start_time = time.time()
    try:
        controller = HunnitController(db=db)
        count = controller.get_product_count_from_db()
        response_time_ms = (time.time() - start_time) * 1000
        return {
            "count": count,
            "source": "database",
            "response_time_ms": round(response_time_ms, 2)
        }
    except Exception as e:
        from app.utils.logger import get_logger
        logger = get_logger("hunnit_router")
        logger.error(f"Error in get_product_count endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching product count. Please try again later."
        )


@router.get("/{product_id}/similar", response_model=ProductListResponse)
async def get_similar_products(
    product_id: str,
    limit: int = 4,
    db: Session = Depends(get_db)
) -> ProductListResponse:
    """
    Get similar products using vector search.
    
    Args:
        product_id: The ID of the product to find similar products for
        limit: Maximum number of similar products to return (default: 4)
        db: Database session
    
    Returns:
        ProductListResponse with similar products and response time
    """
    start_time = time.time()
    try:
        controller = HunnitController(db=db)
        similar_products = controller.get_similar_products_as_db_products(product_id, limit=limit)
        response_time_ms = (time.time() - start_time) * 1000
        return ProductListResponse(
            products=similar_products,
            count=len(similar_products),
            response_time_ms=round(response_time_ms, 2)
        )
    except Exception as e:
        from app.utils.logger import get_logger
        logger = get_logger("hunnit_router")
        logger.error(f"Error getting similar products: {e}", exc_info=True)
        response_time_ms = (time.time() - start_time) * 1000
        return ProductListResponse(
            products=[],
            count=0,
            response_time_ms=round(response_time_ms, 2)
        )


@router.get("/cache/status", response_model=dict)
async def get_cache_status() -> dict:
    """
    Get Redis cache status and metadata.
    
    Returns:
        Dictionary with cache status information and response time
    """
    start_time = time.time()
    try:
        controller = HunnitController()
        status = controller.get_cache_status()
        response_time_ms = (time.time() - start_time) * 1000
        status["response_time_ms"] = round(response_time_ms, 2)
        return status
    except Exception as e:
        from app.utils.logger import get_logger
        logger = get_logger("hunnit_router")
        logger.error(f"Error getting cache status: {e}", exc_info=True)
        response_time_ms = (time.time() - start_time) * 1000
        return {
            "cache_available": False,
            "error": str(e),
            "status": "unavailable",
            "response_time_ms": round(response_time_ms, 2)
        }

