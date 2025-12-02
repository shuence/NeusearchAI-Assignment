"""Hunnit products router for product scraping endpoints."""
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.controller.products.hunnit.controller import HunnitController
from app.schemas.products.hunnit.schemas import Product, ScrapeResponse, DBProduct
from app.config.database import get_db

router = APIRouter()


@router.get("/scrape", response_model=ScrapeResponse)
async def scrape_hunnit_products(
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


@router.get("", response_model=List[DBProduct])
async def get_all_products(
    from_db: bool = True,
    db: Session = Depends(get_db)
) -> List[DBProduct]:
    """
    Get all products. By default, returns products from database.
    
    Args:
        from_db: If True, get from database. If False, scrape from Hunnit.com
    
    Returns:
        List of all products
    """
    controller = HunnitController(db=db)
    
    if from_db:
        # Get all products from database
        db_products = controller.get_all_products_from_db()
        return [DBProduct.model_validate(product) for product in db_products]
    else:
        # Scrape from Hunnit.com (legacy behavior)
        response = await controller.scrape_all_products(save_to_db=False)
        if not response.success or response.products is None:
            raise HTTPException(
                status_code=500,
                detail=response.message
            )
        # Convert scraped products to DBProduct format (simplified)
        return [
            DBProduct(
                id=str(p.id),
                external_id=str(p.id),
                title=p.title,
                handle=p.handle,
                description=p.body_html[:500] if p.body_html else None,
                body_html=p.body_html,
                vendor=p.vendor,
                product_type=p.product_type,
                category=p.product_type,
                tags=p.tags,
                image_urls=[str(img.src) for img in p.images] if p.images else None,
            )
            for p in response.products
        ]


@router.get("/{product_id}", response_model=DBProduct)
async def get_product(
    product_id: str,
    from_db: bool = True,
    db: Session = Depends(get_db)
) -> DBProduct:
    """
    Get a specific product by ID. By default, searches in database first.
    
    Args:
        product_id: The ID of the product (UUID for DB, or external_id)
        from_db: If True, search in database. If False, scrape from Hunnit.com
        
    Returns:
        Product object
        
    Raises:
        HTTPException: If product not found
    """
    controller = HunnitController(db=db)
    
    if from_db:
        # Try to get from database by UUID first
        product = controller.get_product_from_db_by_id(product_id)
        if product:
            return DBProduct.model_validate(product)
        
        # Try by external_id
        product = controller.get_product_from_db_by_external_id(product_id)
        if product:
            return DBProduct.model_validate(product)
        
        raise HTTPException(
            status_code=404,
            detail=f"Product with ID {product_id} not found in database"
        )
    else:
        # Legacy: scrape from Hunnit.com
        try:
            external_id_int = int(product_id)
            product = await controller.get_product_by_id(external_id_int)
            if product is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product with ID {product_id} not found"
                )
            # Convert to DBProduct format
            return DBProduct(
                id=str(product.id),
                external_id=str(product.id),
                title=product.title,
                handle=product.handle,
                description=product.body_html[:500] if product.body_html else None,
                body_html=product.body_html,
                vendor=product.vendor,
                product_type=product.product_type,
                category=product.product_type,
                tags=product.tags,
                image_urls=[str(img.src) for img in product.images] if product.images else None,
            )
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid product ID format: {product_id}"
            )


@router.get("/tag/{tag}", response_model=List[DBProduct])
async def get_products_by_tag(
    tag: str,
    from_db: bool = True,
    db: Session = Depends(get_db)
) -> List[DBProduct]:
    """
    Get products filtered by tag. By default, searches in database.
    
    Args:
        tag: The tag to filter by
        from_db: If True, search in database. If False, scrape from Hunnit.com
        
    Returns:
        List of products matching the tag
    """
    controller = HunnitController(db=db)
    
    if from_db:
        db_products = controller.get_products_from_db_by_tag(tag)
        return [DBProduct.model_validate(product) for product in db_products]
    else:
        products = await controller.get_products_by_tag(tag)
        return [
            DBProduct(
                id=str(p.id),
                external_id=str(p.id),
                title=p.title,
                handle=p.handle,
                description=p.body_html[:500] if p.body_html else None,
                body_html=p.body_html,
                vendor=p.vendor,
                product_type=p.product_type,
                category=p.product_type,
                tags=p.tags,
                image_urls=[str(img.src) for img in p.images] if p.images else None,
            )
            for p in products
        ]


@router.get("/vendor/{vendor}", response_model=List[DBProduct])
async def get_products_by_vendor(
    vendor: str,
    from_db: bool = True,
    db: Session = Depends(get_db)
) -> List[DBProduct]:
    """
    Get products filtered by vendor. By default, searches in database.
    
    Args:
        vendor: The vendor name to filter by
        from_db: If True, search in database. If False, scrape from Hunnit.com
        
    Returns:
        List of products from the specified vendor
    """
    controller = HunnitController(db=db)
    
    if from_db:
        db_products = controller.get_products_from_db_by_vendor(vendor)
        return [DBProduct.model_validate(product) for product in db_products]
    else:
        products = await controller.get_products_by_vendor(vendor)
        return [
            DBProduct(
                id=str(p.id),
                external_id=str(p.id),
                title=p.title,
                handle=p.handle,
                description=p.body_html[:500] if p.body_html else None,
                body_html=p.body_html,
                vendor=p.vendor,
                product_type=p.product_type,
                category=p.product_type,
                tags=p.tags,
                image_urls=[str(img.src) for img in p.images] if p.images else None,
            )
            for p in products
        ]


@router.get("/stats/count", response_model=dict)
async def get_product_count(db: Session = Depends(get_db)) -> dict:
    """
    Get total number of products in the database.
    
    Returns:
        Dictionary with product count
    """
    controller = HunnitController(db=db)
    count = controller.get_product_count_from_db()
    return {"count": count, "source": "database"}


@router.get("/cache/status", response_model=dict)
async def get_cache_status() -> dict:
    """
    Get Redis cache status and metadata.
    
    Returns:
        Dictionary with cache status information
    """
    from app.services.products.hunnit.redis_service import HunnitProductRedisService
    
    try:
        redis_service = HunnitProductRedisService()
        count = redis_service.get_products_count()
        timestamp_info = redis_service.get_scrape_timestamp()
        
        return {
            "cache_available": True,
            "products_cached": count,
            "last_scrape": timestamp_info,
            "status": "active" if count else "empty"
        }
    except Exception as e:
        return {
            "cache_available": False,
            "error": str(e),
            "status": "unavailable"
        }

