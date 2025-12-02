"""Vector search service for semantic product retrieval using pgvector."""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from pgvector.sqlalchemy import Vector
import numpy as np
from app.models.product import Product
from app.rag import get_embedding_service
from app.utils.logger import get_logger

logger = get_logger("vector_search")


class VectorSearchService:
    """Service for semantic product search using vector embeddings."""
    
    def __init__(self, db: Session):
        """Initialize vector search service with database session."""
        self.db = db
        self.embedding_service = None
        try:
            self.embedding_service = get_embedding_service()
        except Exception as e:
            logger.warning(f"Embedding service not available: {e}")
    
    def search_similar_products(
        self,
        query_embedding: List[float],
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[Product, float]]:
        """
        Search for products similar to the query embedding using cosine similarity.
        
        Args:
            query_embedding: Query vector embedding
            limit: Maximum number of results to return
            similarity_threshold: Minimum cosine similarity score (0-1)
        
        Returns:
            List of tuples (Product, similarity_score) sorted by similarity
        """
        if not query_embedding:
            logger.warning("Empty query embedding provided")
            return []
        
        try:
            # Convert embedding to numpy array and normalize
            query_vec = np.array(query_embedding)
            query_vec = query_vec / np.linalg.norm(query_vec)
            
            # Use pgvector cosine distance operator (1 - cosine similarity)
            # We want products where 1 - cosine_distance > threshold
            # Which means cosine_distance < 1 - threshold
            max_distance = 1 - similarity_threshold
            
            # Query using pgvector's cosine distance operator
            # Using raw SQL for better performance with pgvector
            # Convert numpy array to string format for pgvector
            query_vec_str = "[" + ",".join(map(str, query_vec.tolist())) + "]"
            
            query = text("""
                SELECT 
                    id,
                    1 - (embedding <=> CAST(:query_vec AS vector)) as similarity
                FROM products
                WHERE embedding IS NOT NULL
                AND (embedding <=> CAST(:query_vec AS vector)) < :max_distance
                ORDER BY embedding <=> CAST(:query_vec AS vector)
                LIMIT :limit
            """)
            
            results = self.db.execute(
                query,
                {
                    "query_vec": query_vec_str,
                    "max_distance": max_distance,
                    "limit": limit
                }
            ).fetchall()
            
            # Fetch full product objects
            products_with_scores = []
            for row in results:
                product_id = row[0]
                similarity = float(row[1])
                
                product = self.db.query(Product).filter(Product.id == product_id).first()
                if product:
                    products_with_scores.append((product, similarity))
            
            logger.info(f"Found {len(products_with_scores)} similar products")
            return products_with_scores
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    def search_by_query_text(
        self,
        query_text: str,
        limit: int = 5,
        similarity_threshold: float = 0.7,
        enhance_query: bool = True
    ) -> List[Tuple[Product, float]]:
        """
        Search for products by converting query text to embedding first.
        
        Args:
            query_text: Natural language query
            limit: Maximum number of results to return
            similarity_threshold: Minimum cosine similarity score (0-1)
            enhance_query: Whether to enhance query with synonyms and normalization
        
        Returns:
            List of tuples (Product, similarity_score) sorted by similarity
        """
        if not self.embedding_service:
            logger.error("Embedding service not available for query text search")
            return []
        
        # Enhance query if enabled
        final_query = query_text
        if enhance_query:
            try:
                from app.rag.query_enhancement import QueryEnhancer
                enhancer = QueryEnhancer()
                final_query = enhancer.enhance(query_text)
            except Exception as e:
                logger.warning(f"Query enhancement failed: {e}, using original query")
                final_query = query_text
        
        query_embedding = self.embedding_service.generate_embedding(
            final_query,
            task_type="RETRIEVAL_QUERY"
        )
        
        if not query_embedding:
            logger.warning("Failed to generate embedding for query text")
            return []
        
        return self.search_similar_products(
            query_embedding,
            limit=limit,
            similarity_threshold=similarity_threshold
        )
    
    def get_products_with_embeddings_count(self) -> int:
        """Get count of products that have embeddings."""
        return self.db.query(Product).filter(Product.embedding.isnot(None)).count()

