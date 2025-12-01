"""Utility script to generate embeddings for products that don't have them."""
from sqlalchemy.orm import Session
from app.models.product import Product
from app.rag import get_embedding_service
from app.utils.logger import get_logger

logger = get_logger("generate_embeddings")


def generate_embeddings_for_products(db: Session, batch_size: int = 10) -> tuple[int, int]:
    """
    Generate embeddings for all products that don't have embeddings yet.
    
    Args:
        db: Database session
        batch_size: Number of products to process in each batch
        
    Returns:
        Tuple of (successful_count, failed_count)
    """
    try:
        embedding_service = get_embedding_service()
    except Exception as e:
        logger.error(f"Failed to initialize embedding service: {e}")
        return 0, 0
    
    # Get all products without embeddings
    products_without_embeddings = db.query(Product).filter(
        Product.embedding.is_(None)
    ).all()
    
    if not products_without_embeddings:
        logger.info("All products already have embeddings")
        return 0, 0
    
    logger.info(f"Found {len(products_without_embeddings)} products without embeddings")
    
    successful = 0
    failed = 0
    
    # Process in batches
    for i in range(0, len(products_without_embeddings), batch_size):
        batch = products_without_embeddings[i:i + batch_size]
        
        for product in batch:
            try:
                # Prepare product data
                product_data = {
                    "title": product.title,
                    "description": product.description,
                    "body_html": product.body_html,
                    "vendor": product.vendor,
                    "product_type": product.product_type,
                    "tags": product.tags if product.tags else [],
                    "price": product.price,
                }
                
                # Generate embedding
                embedding = embedding_service.generate_product_embedding(product_data)
                
                if embedding:
                    product.embedding = embedding
                    successful += 1
                    logger.info(f"Generated embedding for product: {product.title} (ID: {product.id})")
                else:
                    failed += 1
                    logger.warning(f"Failed to generate embedding for product: {product.title} (ID: {product.id})")
                    
            except Exception as e:
                failed += 1
                logger.error(f"Error generating embedding for product {product.id}: {e}")
        
        # Commit batch
        try:
            db.commit()
            logger.info(f"Committed batch: {i // batch_size + 1} ({successful} successful, {failed} failed so far)")
        except Exception as e:
            logger.error(f"Error committing batch: {e}")
            db.rollback()
    
    logger.info(f"Embedding generation complete: {successful} successful, {failed} failed")
    return successful, failed


def regenerate_all_embeddings(db: Session, batch_size: int = 10) -> tuple[int, int]:
    """
    Regenerate embeddings for all products (even if they already have embeddings).
    
    Args:
        db: Database session
        batch_size: Number of products to process in each batch
        
    Returns:
        Tuple of (successful_count, failed_count)
    """
    try:
        embedding_service = get_embedding_service()
    except Exception as e:
        logger.error(f"Failed to initialize embedding service: {e}")
        return 0, 0
    
    # Get all products
    all_products = db.query(Product).all()
    
    if not all_products:
        logger.info("No products found")
        return 0, 0
    
    logger.info(f"Regenerating embeddings for {len(all_products)} products")
    
    successful = 0
    failed = 0
    
    # Process in batches
    for i in range(0, len(all_products), batch_size):
        batch = all_products[i:i + batch_size]
        
        for product in batch:
            try:
                # Prepare product data
                product_data = {
                    "title": product.title,
                    "description": product.description,
                    "body_html": product.body_html,
                    "vendor": product.vendor,
                    "product_type": product.product_type,
                    "tags": product.tags if product.tags else [],
                    "price": product.price,
                }
                
                # Generate embedding
                embedding = embedding_service.generate_product_embedding(product_data)
                
                if embedding:
                    product.embedding = embedding
                    successful += 1
                    logger.info(f"Regenerated embedding for product: {product.title} (ID: {product.id})")
                else:
                    failed += 1
                    logger.warning(f"Failed to regenerate embedding for product: {product.title} (ID: {product.id})")
                    
            except Exception as e:
                failed += 1
                logger.error(f"Error regenerating embedding for product {product.id}: {e}")
        
        # Commit batch
        try:
            db.commit()
            logger.info(f"Committed batch: {i // batch_size + 1} ({successful} successful, {failed} failed so far)")
        except Exception as e:
            logger.error(f"Error committing batch: {e}")
            db.rollback()
    
    logger.info(f"Embedding regeneration complete: {successful} successful, {failed} failed")
    return successful, failed

