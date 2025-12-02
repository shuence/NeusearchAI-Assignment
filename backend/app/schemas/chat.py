"""Chat schemas for RAG-based product recommendations."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from app.schemas.products.hunnit.schemas import DBProduct


class ChatMessage(BaseModel):
    """Single chat message."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., min_length=1, max_length=5000, description="Message content")
    timestamp: Optional[str] = None
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is either 'user' or 'assistant'."""
        if v not in ['user', 'assistant']:
            raise ValueError("Role must be 'user' or 'assistant'")
        return v


class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=1000, description="User's query message")
    conversation_history: Optional[List[Dict[str, str]]] = None
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum number of products to return")
    similarity_threshold: float = Field(default=0.6, ge=0.0, le=1.0, description="Minimum similarity score (0-1)")
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate and sanitize message."""
        if not v or not v.strip():
            raise ValueError("Message cannot be empty or whitespace only")
        # Trim whitespace
        v = v.strip()
        # Check for extremely long messages (potential abuse)
        if len(v) > 1000:
            raise ValueError("Message is too long (max 1000 characters)")
        return v
    
    @field_validator('conversation_history')
    @classmethod
    def validate_conversation_history(cls, v: Optional[List[Dict[str, str]]]) -> Optional[List[Dict[str, str]]]:
        """Validate conversation history structure."""
        if v is None:
            return v
        
        # Limit conversation history length to prevent abuse
        if len(v) > 50:
            raise ValueError("Conversation history is too long (max 50 messages)")
        
        # Validate each message in history
        for msg in v:
            if not isinstance(msg, dict):
                raise ValueError("Each message in conversation_history must be a dictionary")
            if 'role' not in msg or 'content' not in msg:
                raise ValueError("Each message must have 'role' and 'content' fields")
            if msg['role'] not in ['user', 'assistant']:
                raise ValueError("Message role must be 'user' or 'assistant'")
            if not isinstance(msg['content'], str) or len(msg['content']) > 5000:
                raise ValueError("Message content must be a string with max 5000 characters")
        
        return v
    
    @model_validator(mode='after')
    def validate_request(self) -> 'ChatRequest':
        """Additional validation after model creation."""
        # Ensure message is not just whitespace
        if not self.message or not self.message.strip():
            raise ValueError("Message cannot be empty")
        return self


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
    suggested_follow_ups: Optional[List[str]] = None


class CompareRequest(BaseModel):
    """Request for product comparison endpoint."""
    product_ids: List[str] = Field(..., min_length=2, max_length=4, description="List of product IDs to compare (2-4 products)")


class CompareResponse(BaseModel):
    """Response from product comparison endpoint."""
    insight: str = Field(..., description="AI-generated comparison insight")
    products: List[DBProduct] = Field(..., description="List of compared products")

