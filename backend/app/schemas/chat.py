"""Chat schemas for RAG-based product recommendations."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from app.schemas.products.hunnit.schemas import DBProduct


class ChatMessage(BaseModel):
    """Single chat message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = None
    max_results: int = 5
    similarity_threshold: float = 0.6


class ProductRecommendation(BaseModel):
    """Product recommendation with score."""
    product: DBProduct
    similarity_score: float


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    response: str
    products: List[DBProduct]
    needs_clarification: bool
    recommendations: Optional[List[ProductRecommendation]] = None

