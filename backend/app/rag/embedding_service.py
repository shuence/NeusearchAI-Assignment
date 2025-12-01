"""Embedding service for generating vector embeddings using Gemini API."""
from typing import List, Optional
from google import genai
from google.genai import types
import numpy as np
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger("embedding_service")


class EmbeddingService:
    """Service for generating embeddings using Gemini Embeddings API."""
    
    def __init__(self):
        """Initialize the embedding service with Gemini API client."""
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in environment variables")
        
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_EMBEDDING_MODEL
        self.dimension = settings.GEMINI_EMBEDDING_DIMENSION
    
    def _prepare_product_text(self, product_data: dict) -> str:
        """
        Prepare a text representation of a product for embedding.
        
        Args:
            product_data: Dictionary containing product fields
            
        Returns:
            Combined text string for embedding
        """
        parts = []
        
        # Add title (most important)
        if product_data.get("title"):
            parts.append(f"Title: {product_data['title']}")
        
        # Add description
        if product_data.get("description"):
            parts.append(f"Description: {product_data['description']}")
        
        # Add body_html if description is not available or is short
        if product_data.get("body_html") and (
            not product_data.get("description") or 
            len(product_data.get("description", "")) < 100
        ):
            # Simple HTML tag removal
            import re
            body_text = re.sub(r'<[^>]+>', '', product_data['body_html']).strip()
            if body_text:
                parts.append(f"Details: {body_text[:500]}")  # Limit length
        
        # Add vendor
        if product_data.get("vendor"):
            parts.append(f"Brand: {product_data['vendor']}")
        
        # Add product type/category
        if product_data.get("product_type"):
            parts.append(f"Category: {product_data['product_type']}")
        
        # Add tags
        if product_data.get("tags") and isinstance(product_data["tags"], list):
            tags_str = ", ".join(product_data["tags"])
            if tags_str:
                parts.append(f"Tags: {tags_str}")
        
        # Add price information
        if product_data.get("price"):
            parts.append(f"Price: ${product_data['price']}")
        
        return " | ".join(parts)
    
    def generate_embedding(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> Optional[List[float]]:
        """
        Generate a single embedding for a text string.
        
        Args:
            text: Text to generate embedding for
            task_type: Task type for embedding optimization
                      Options: RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY, SEMANTIC_SIMILARITY, etc.
        
        Returns:
            List of float values representing the embedding, or None if error
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding generation")
            return None
        
        try:
            result = self.client.models.embed_content(
                model=self.model,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=self.dimension
                )
            )
            
            if result.embeddings and len(result.embeddings) > 0:
                embedding = result.embeddings[0]
                
                # Normalize embedding for dimensions other than 3072
                # (3072 is already normalized by Gemini)
                if self.dimension != 3072:
                    embedding_values = np.array(embedding.values)
                    norm = np.linalg.norm(embedding_values)
                    if norm > 0:
                        embedding_values = embedding_values / norm
                    return embedding_values.tolist()
                
                return list(embedding.values)
            else:
                logger.error("No embeddings returned from Gemini API")
                return None
                
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in a single batch.
        
        Args:
            texts: List of texts to generate embeddings for
            task_type: Task type for embedding optimization
        
        Returns:
            List of embeddings (or None for failed embeddings)
        """
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [text for text in texts if text and text.strip()]
        if not valid_texts:
            logger.warning("No valid texts provided for batch embedding")
            return [None] * len(texts)
        
        try:
            result = self.client.models.embed_content(
                model=self.model,
                contents=valid_texts,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=self.dimension
                )
            )
            
            embeddings = []
            valid_idx = 0
            
            for i, text in enumerate(texts):
                if text and text.strip():
                    if valid_idx < len(result.embeddings):
                        embedding = result.embeddings[valid_idx]
                        
                        # Normalize if needed
                        if self.dimension != 3072:
                            embedding_values = np.array(embedding.values)
                            norm = np.linalg.norm(embedding_values)
                            if norm > 0:
                                embedding_values = embedding_values / norm
                            embeddings.append(embedding_values.tolist())
                        else:
                            embeddings.append(list(embedding.values))
                        
                        valid_idx += 1
                    else:
                        embeddings.append(None)
                else:
                    embeddings.append(None)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return [None] * len(texts)
    
    def generate_product_embedding(self, product_data: dict) -> Optional[List[float]]:
        """
        Generate embedding for a product by preparing its text representation.
        
        Args:
            product_data: Dictionary containing product fields (title, description, etc.)
        
        Returns:
            List of float values representing the embedding, or None if error
        """
        product_text = self._prepare_product_text(product_data)
        if not product_text:
            logger.warning("No text could be prepared from product data")
            return None
        
        return self.generate_embedding(product_text, task_type="RETRIEVAL_DOCUMENT")


# Global instance (lazy initialization)
_embedding_service: Optional[EmbeddingService] = None
_embedding_service_error: Optional[Exception] = None


def get_embedding_service() -> EmbeddingService:
    """
    Get or create the global embedding service instance.
    
    Raises:
        ValueError: If GEMINI_API_KEY is not set or service initialization fails
    """
    global _embedding_service, _embedding_service_error
    
    if _embedding_service_error is not None:
        # Re-raise the previous error
        raise _embedding_service_error
    
    if _embedding_service is None:
        try:
            _embedding_service = EmbeddingService()
        except Exception as e:
            _embedding_service_error = e
            raise
    
    return _embedding_service

