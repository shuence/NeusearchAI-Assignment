"""Database service for saving Hunnit products to PostgreSQL."""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.product import Product as ProductModel
from app.schemas.products.hunnit.schemas import Product as ScrapedProduct
from app.utils.logger import get_logger
from app.rag import get_embedding_service
from app.config.settings import settings
from datetime import datetime, timezone
from google import genai

logger = get_logger("hunnit_db_service")


class HunnitProductDBService:
    """Service for saving and retrieving Hunnit products from the database."""
    
    def __init__(self, db: Session):
        """Initialize database service with a database session."""
        self.db = db
    
    def _extract_price(self, product: ScrapedProduct) -> Optional[float]:
        """Extract price from product variants (use first available variant)."""
        if not product.variants or len(product.variants) == 0:
            return None
        
        # Get the first variant's price
        first_variant = product.variants[0]
        try:
            # Price is stored as string in the schema
            return float(first_variant.price)
        except (ValueError, AttributeError):
            return None
    
    def _extract_compare_at_price(self, product: ScrapedProduct) -> Optional[float]:
        """Extract compare_at_price from product variants."""
        if not product.variants or len(product.variants) == 0:
            return None
        
        # Get the first variant's compare_at_price
        first_variant = product.variants[0]
        if first_variant.compare_at_price:
            try:
                return float(first_variant.compare_at_price)
            except (ValueError, AttributeError):
                return None
        return None
    
    def _extract_image_urls(self, product: ScrapedProduct) -> List[str]:
        """Extract all image URLs from product."""
        image_urls = []
        
        # Add featured images from variants
        for variant in product.variants:
            if variant.featured_image and variant.featured_image.src:
                image_urls.append(str(variant.featured_image.src))
        
        # Add images from images list
        for image in product.images:
            if image.src:
                image_urls.append(str(image.src))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in image_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        return unique_urls
    
    def _extract_features(self, product: ScrapedProduct) -> dict:
        """Extract features/attributes from product (variants, options, etc.)."""
        features = {
            "variants": [],
            "options": [],
            "published_at": product.published_at,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
        }
        
        # Extract variant info
        for variant in product.variants:
            variant_data = {
                "id": variant.id,
                "title": variant.title,
                "price": variant.price,
                "compare_at_price": variant.compare_at_price,
                "sku": variant.sku,
                "available": variant.available,
                "requires_shipping": variant.requires_shipping,
                "taxable": variant.taxable,
                "grams": variant.grams,
                "option1": variant.option1,
                "option2": variant.option2,
                "option3": variant.option3,
            }
            # Include featured_image if available
            if variant.featured_image and variant.featured_image.src:
                variant_data["featured_image"] = {
                    "src": str(variant.featured_image.src),
                    "id": variant.featured_image.id,
                    "alt": variant.featured_image.alt,
                }
            features["variants"].append(variant_data)
        
        # Extract options
        for option in product.options:
            option_data = {
                "name": option.name,
                "position": option.position,
                "values": option.values,
            }
            features["options"].append(option_data)
        
        return features
    
    def _generate_ai_features(self, product: ScrapedProduct) -> Optional[List[str]]:
        """Generate AI features for a product using LLM."""
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set - skipping AI feature generation")
            return None
        
        try:
            llm_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            model = "gemini-2.0-flash"
            
            # Build product context
            product_info = f"""
Product Title: {product.title}
Description: {product.body_html[:500] if product.body_html else 'N/A'}
Price: {product.variants[0].price if product.variants else 'N/A'}
Vendor: {product.vendor}
Product Type: {product.product_type}
"""
            
            prompt = f"""You are a product feature extraction assistant. Based on the product information below, generate a list of 5-10 key features that would be useful for customers.

Focus on:
- Key product characteristics and benefits
- Important specifications or attributes
- Unique selling points
- Practical use cases or applications
- Material, design, or quality aspects

Return ONLY a bulleted list of features, one per line, starting with "•". Do not include any other text, explanations, or formatting.

Product Information:
{product_info}

Features:"""
            
            logger.info(f"Generating AI features for product: {product.title}")
            response = llm_client.models.generate_content(
                model=model,
                contents=prompt
            )
            
            ai_response = response.text if hasattr(response, 'text') else str(response)
            
            # Parse the response into a list of features
            features = []
            for line in ai_response.split('\n'):
                line = line.strip()
                if line and (line.startswith('•') or line.startswith('-') or line.startswith('*')):
                    # Remove bullet point markers
                    feature = line.lstrip('•-*').strip()
                    if feature:
                        features.append(feature)
                elif line and not line.startswith('Features:'):
                    # Some models might not use bullets
                    features.append(line)
            
            # Limit to 10 features
            features = features[:10]
            
            if features:
                logger.info(f"Generated {len(features)} AI features for product: {product.title}")
                return features
            else:
                logger.warning(f"No features extracted from AI response for product: {product.title}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating AI features for product {product.title}: {e}", exc_info=True)
            return None
    
    def _scraped_to_db_model(self, scraped_product: ScrapedProduct) -> ProductModel:
        """Convert scraped product schema to database model."""
        # Check if product already exists
        existing_product = self.db.query(ProductModel).filter(
            ProductModel.external_id == str(scraped_product.id)
        ).first()
        
        # Extract data
        price = self._extract_price(scraped_product)
        compare_at_price = self._extract_compare_at_price(scraped_product)
        image_urls = self._extract_image_urls(scraped_product)
        features = self._extract_features(scraped_product)
        
        # Get description from body_html (strip HTML tags for description)
        description = scraped_product.body_html
        if description:
            # Simple HTML tag removal (you might want to use a library like BeautifulSoup)
            import re
            description = re.sub(r'<[^>]+>', '', description).strip()
            if len(description) > 500:
                description = description[:500] + "..."
        
        # Prepare product data for embedding
        product_data = {
            "title": scraped_product.title,
            "description": description,
            "body_html": scraped_product.body_html,
            "vendor": scraped_product.vendor,
            "product_type": scraped_product.product_type,
            "tags": scraped_product.tags if scraped_product.tags else [],
            "price": price,
        }
        
        # Generate embedding for the product
        embedding = None
        try:
            embedding_service = get_embedding_service()
            embedding = embedding_service.generate_product_embedding(product_data)
            if embedding:
                logger.info(f"Generated embedding for product: {scraped_product.title}")
            else:
                logger.warning(f"Failed to generate embedding for product: {scraped_product.title}")
        except Exception as e:
            logger.error(f"Error generating embedding for product {scraped_product.title}: {e}")
            # Continue without embedding - don't fail the save operation
        
        # Generate AI features for the product
        ai_features = None
        if not existing_product or not existing_product.ai_features:
            # Only generate if new product or existing product doesn't have AI features
            ai_features = self._generate_ai_features(scraped_product)
        
        if existing_product:
            # Update existing product
            existing_product.title = scraped_product.title
            existing_product.handle = scraped_product.handle
            existing_product.description = description
            existing_product.body_html = scraped_product.body_html
            existing_product.price = price
            existing_product.compare_at_price = compare_at_price
            existing_product.vendor = scraped_product.vendor
            existing_product.product_type = scraped_product.product_type
            existing_product.category = scraped_product.product_type  # Use product_type as category
            existing_product.tags = scraped_product.tags if scraped_product.tags else []
            existing_product.image_urls = image_urls
            existing_product.features = features
            existing_product.embedding = embedding  # Update embedding
            if ai_features:
                existing_product.ai_features = ai_features  # Update AI features if generated
            existing_product.scraped_at = datetime.now(timezone.utc)
            
            logger.info(f"Updating product: {scraped_product.title} (external_id: {scraped_product.id})")
            return existing_product
        else:
            # Create new product
            db_product = ProductModel(
                external_id=str(scraped_product.id),
                title=scraped_product.title,
                handle=scraped_product.handle,
                description=description,
                body_html=scraped_product.body_html,
                price=price,
                compare_at_price=compare_at_price,
                vendor=scraped_product.vendor,
                product_type=scraped_product.product_type,
                category=scraped_product.product_type,  # Use product_type as category
                tags=scraped_product.tags if scraped_product.tags else [],
                image_urls=image_urls,
                features=features,
                embedding=embedding,  # Add embedding
                ai_features=ai_features,  # Add AI-generated features
            )
            
            logger.info(f"Creating new product: {scraped_product.title} (external_id: {scraped_product.id})")
            return db_product
    
    def save_product(self, scraped_product: ScrapedProduct) -> ProductModel:
        """
        Save or update a single product in the database.
        
        Args:
            scraped_product: Scraped product schema
            
        Returns:
            Saved Product model
        """
        db_product = self._scraped_to_db_model(scraped_product)
        
        if db_product.id is None or not hasattr(db_product, '_sa_instance_state') or db_product._sa_instance_state.pending:
            self.db.add(db_product)
        
        self.db.commit()
        self.db.refresh(db_product)
        
        return db_product
    
    def save_products(self, scraped_products: List[ScrapedProduct]) -> tuple[int, int]:
        """
        Save or update multiple products in the database.
        
        Args:
            scraped_products: List of scraped product schemas
            
        Returns:
            Tuple of (created_count, updated_count)
        """
        created_count = 0
        updated_count = 0
        
        for scraped_product in scraped_products:
            existing = self.db.query(ProductModel).filter(
                ProductModel.external_id == str(scraped_product.id)
            ).first()
            
            is_new = existing is None
            db_product = self._scraped_to_db_model(scraped_product)
            
            if is_new:
                self.db.add(db_product)
                created_count += 1
            else:
                updated_count += 1
            
            # Commit in batches to avoid memory issues
            if (created_count + updated_count) % 10 == 0:
                self.db.commit()
                logger.info(f"Saved {created_count + updated_count} products so far...")
        
        # Final commit
        self.db.commit()
        logger.info(f"Successfully saved {len(scraped_products)} products: {created_count} created, {updated_count} updated")
        
        return created_count, updated_count
    
    def get_all_products(self) -> List[ProductModel]:
        """Get all products from the database."""
        return self.db.query(ProductModel).all()
    
    def get_product_by_external_id(self, external_id: str) -> Optional[ProductModel]:
        """Get a product by its external ID (from Hunnit.com)."""
        return self.db.query(ProductModel).filter(
            ProductModel.external_id == external_id
        ).first()
    
    def get_product_by_id(self, product_id: str) -> Optional[ProductModel]:
        """Get a product by its database UUID."""
        try:
            import uuid
            product_uuid = uuid.UUID(product_id)
            return self.db.query(ProductModel).filter(ProductModel.id == product_uuid).first()
        except (ValueError, AttributeError):
            return None
    
    def get_products_by_tag(self, tag: str) -> List[ProductModel]:
        """Get products filtered by tag."""
        return self.db.query(ProductModel).filter(
            ProductModel.tags.contains([tag])
        ).all()
    
    def get_products_by_vendor(self, vendor: str) -> List[ProductModel]:
        """Get products filtered by vendor."""
        return self.db.query(ProductModel).filter(
            ProductModel.vendor == vendor
        ).all()
    
    def get_product_count(self) -> int:
        """Get total number of products in the database."""
        return self.db.query(ProductModel).count()
    
    def generate_ai_features_for_product(self, product: ProductModel) -> bool:
        """
        Generate AI features for an existing database product.
        
        Args:
            product: Product model from database
            
        Returns:
            True if features were generated successfully, False otherwise
        """
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set - skipping AI feature generation")
            return False
        
        try:
            llm_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            model = "gemini-2.0-flash"
            
            # Build product context from database product
            product_info = f"""
Product Title: {product.title}
Description: {product.body_html[:500] if product.body_html else (product.description[:500] if product.description else 'N/A')}
Price: {product.price if product.price else 'N/A'}
Vendor: {product.vendor or 'N/A'}
Product Type: {product.product_type or 'N/A'}
"""
            
            prompt = f"""You are a product feature extraction assistant. Based on the product information below, generate a list of 5-10 key features that would be useful for customers.

Focus on:
- Key product characteristics and benefits
- Important specifications or attributes
- Unique selling points
- Practical use cases or applications
- Material, design, or quality aspects

Return ONLY a bulleted list of features, one per line, starting with "•". Do not include any other text, explanations, or formatting.

Product Information:
{product_info}

Features:"""
            
            logger.info(f"Generating AI features for product: {product.title} (ID: {product.id})")
            response = llm_client.models.generate_content(
                model=model,
                contents=prompt
            )
            
            ai_response = response.text if hasattr(response, 'text') else str(response)
            
            # Parse the response into a list of features
            features = []
            for line in ai_response.split('\n'):
                line = line.strip()
                if line and (line.startswith('•') or line.startswith('-') or line.startswith('*')):
                    # Remove bullet point markers
                    feature = line.lstrip('•-*').strip()
                    if feature:
                        features.append(feature)
                elif line and not line.startswith('Features:'):
                    # Some models might not use bullets
                    features.append(line)
            
            # Limit to 10 features
            features = features[:10]
            
            if features:
                product.ai_features = features
                logger.info(f"Generated {len(features)} AI features for product: {product.title} (ID: {product.id})")
                return True
            else:
                logger.warning(f"No features extracted from AI response for product: {product.title} (ID: {product.id})")
                return False
                
        except Exception as e:
            logger.error(f"Error generating AI features for product {product.id}: {e}", exc_info=True)
            return False

