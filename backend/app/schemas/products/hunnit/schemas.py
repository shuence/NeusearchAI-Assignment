"""Product schemas for Hunnit.com scraping."""
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, HttpUrl, field_validator, model_validator


class FeaturedImage(BaseModel):
    """Featured image schema."""
    id: int
    product_id: int
    position: int
    created_at: str
    updated_at: str
    alt: Optional[str] = None
    width: int
    height: int
    src: HttpUrl
    variant_ids: List[int]


class Variant(BaseModel):
    """Product variant schema."""
    id: int
    title: str
    option1: Optional[str] = None
    option2: Optional[str] = None
    option3: Optional[str] = None
    sku: Optional[str] = None
    requires_shipping: bool
    taxable: bool
    featured_image: Optional[FeaturedImage] = None
    available: bool
    price: str
    grams: int
    compare_at_price: Optional[str] = None
    position: int
    product_id: int
    created_at: str
    updated_at: str


class ProductImage(BaseModel):
    """Product image schema."""
    id: int
    created_at: str
    position: int
    updated_at: str
    product_id: int
    variant_ids: List[int]
    src: HttpUrl
    width: int
    height: int


class ProductOption(BaseModel):
    """Product option schema."""
    name: str
    position: int
    values: List[str]


class Product(BaseModel):
    """Product schema from Hunnit.com."""
    id: int
    title: str
    handle: str
    body_html: str
    published_at: str
    created_at: str
    updated_at: str
    vendor: str
    product_type: str
    tags: List[str]
    variants: List[Variant]
    images: List[ProductImage]
    options: List[ProductOption]


class ProductsResponse(BaseModel):
    """Response schema for products list."""
    products: List[Product]


class ScrapeResponse(BaseModel):
    """Response schema for scraping operation."""
    success: bool
    message: str
    count: int
    products: Optional[List[Product]] = None


class DBProduct(BaseModel):
    """Product schema for database products."""
    id: str
    external_id: str
    title: str
    handle: str
    description: Optional[str] = None
    body_html: Optional[str] = None
    price: Optional[float] = None
    compare_at_price: Optional[float] = None
    vendor: Optional[str] = None
    product_type: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    image_urls: Optional[List[str]] = None
    features: Optional[dict] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    scraped_at: Optional[str] = None
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_id(cls, v):
        """Convert UUID to string."""
        if isinstance(v, UUID):
            return str(v)
        return v
    
    @field_validator('created_at', 'updated_at', 'scraped_at', mode='before')
    @classmethod
    def convert_datetime(cls, v):
        """Convert datetime to ISO format string."""
        if isinstance(v, datetime):
            return v.isoformat()
        return v
    
    class Config:
        from_attributes = True

