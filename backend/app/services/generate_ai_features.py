"""Utility script to generate AI features for products that don't have them."""
from sqlalchemy.orm import Session
from app.models.product import Product
from app.services.products.hunnit.db_service import HunnitProductDBService
from app.utils.logger import get_logger

logger = get_logger("generate_ai_features")


def generate_ai_features_for_products(db: Session, batch_size: int = 10) -> tuple[int, int]:
    """
    Generate AI features for all products that don't have them yet.
    
    Args:
        db: Database session
        batch_size: Number of products to process in each batch
        
    Returns:
        Tuple of (successful_count, failed_count)
    """
    db_service = HunnitProductDBService(db)
    
    # Get all products without AI features
    products_without_features = db.query(Product).filter(
        (Product.ai_features.is_(None)) | (Product.ai_features == [])
    ).all()
    
    if not products_without_features:
        logger.info("All products already have AI features")
        return 0, 0
    
    logger.info(f"Found {len(products_without_features)} products without AI features")
    
    successful = 0
    failed = 0
    
    # Process in batches
    for i in range(0, len(products_without_features), batch_size):
        batch = products_without_features[i:i + batch_size]
        
        for product in batch:
            try:
                # Generate AI features
                if db_service.generate_ai_features_for_product(product):
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                failed += 1
                logger.error(f"Error generating AI features for product {product.id}: {e}")
        
        # Commit batch
        try:
            db.commit()
            logger.info(f"Committed batch: {i // batch_size + 1} ({successful} successful, {failed} failed so far)")
        except Exception as e:
            logger.error(f"Error committing batch: {e}")
            db.rollback()
    
    logger.info(f"AI feature generation complete: {successful} successful, {failed} failed")
    return successful, failed

