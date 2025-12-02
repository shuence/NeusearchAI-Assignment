"""Product database models."""
from sqlalchemy import Column, Integer, String, Text, Float, ARRAY, DateTime, JSON, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, ARRAY as PostgresARRAY
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.config.database import Base
import uuid
import json


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    
    Uses PostgreSQL's UUID type when available, otherwise uses String(36).
    """
    impl = String
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            return value
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, str):
                return uuid.UUID(value)
            return value


class ArrayType(TypeDecorator):
    """Platform-independent ARRAY type.
    
    Uses PostgreSQL's ARRAY type when available, otherwise uses JSON.
    """
    impl = JSON
    cache_ok = True
    
    def __init__(self, item_type, *args, **kwargs):
        self.item_type = item_type
        super().__init__(*args, **kwargs)
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresARRAY(self.item_type))
        else:
            return dialect.type_descriptor(JSON())
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            # Convert list to JSON string for SQLite
            if isinstance(value, list):
                return json.dumps(value)
            return value
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            # Convert JSON string back to list for SQLite
            if isinstance(value, str):
                return json.loads(value)
            return value


class Product(Base):
    """Product model for storing scraped product data."""
    __tablename__ = "products"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
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
    tags = Column(ArrayType(String), nullable=True)
    image_urls = Column(ArrayType(String), nullable=True)
    features = Column(JSON, nullable=True)  # Store variant info, options, etc.
    ai_features = Column(ArrayType(String), nullable=True)  # AI-generated features
    
    # Vector embedding for semantic search
    embedding = Column(Vector(1536), nullable=True)  # 1536 for OpenAI, adjust for other models
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Product(id={self.id}, title='{self.title}', external_id='{self.external_id}')>"

