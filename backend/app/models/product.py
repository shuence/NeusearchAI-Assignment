"""Product database models."""
from sqlalchemy import Column, Integer, String, Text, Float, ARRAY, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.config.database import Base
import uuid


class Product(Base):
    """Product model for storing scraped product data."""
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String, unique=True, nullable=False, index=True)  # ID from Hunnit.com
    title = Column(String, nullable=False, index=True)
    handle = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    price = Column(Float, nullable=True)
    compare_at_price = Column(Float, nullable=True)
    vendor = Column(String, nullable=True, index=True)
    product_type = Column(String, nullable=True, index=True)
    category = Column(String, nullable=True, index=True)
    tags = Column(ARRAY(String), nullable=True)
    image_urls = Column(ARRAY(String), nullable=True)
    features = Column(JSON, nullable=True)  # Store variant info, options, etc.
    ai_features = Column(ARRAY(String), nullable=True)  # AI-generated features
    
    # Vector embedding for semantic search
    embedding = Column(Vector(1536), nullable=True)  # 1536 for OpenAI, adjust for other models
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Product(id={self.id}, title='{self.title}', external_id='{self.external_id}')>"

