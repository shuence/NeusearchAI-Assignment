"""Query enhancement utilities for better RAG retrieval."""
from typing import List
import re
from app.utils.logger import get_logger

logger = get_logger("query_enhancement")


class QueryEnhancer:
    """Enhance queries for better retrieval."""
    
    # Common product-related synonyms and related terms
    SYNONYMS = {
        "shirt": ["top", "blouse", "tee", "t-shirt", "tshirt"],
        "pants": ["trousers", "bottoms", "jeans", "slacks"],
        "shoes": ["footwear", "sneakers", "boots", "trainers"],
        "bag": ["purse", "handbag", "tote", "backpack", "satchel"],
        "watch": ["timepiece", "wristwatch", "timepiece"],
        "gym": ["fitness", "workout", "exercise", "athletic", "training"],
        "meeting": ["business", "professional", "office", "formal", "corporate"],
        "casual": ["everyday", "relaxed", "informal", "comfortable"],
        "formal": ["business", "professional", "dressy", "elegant", "sophisticated"],
        "running": ["jogging", "athletic", "sport", "fitness"],
        "dress": ["gown", "frock", "outfit"],
        "jacket": ["coat", "blazer", "outerwear"],
        "sunglasses": ["shades", "eyewear", "sun glasses"],
    }
    
    def expand_query(self, query: str) -> str:
        """Expand query with synonyms and related terms."""
        query_lower = query.lower()
        expanded_terms = [query]  # Keep original query
        
        # Add synonyms for key terms
        for term, synonyms in self.SYNONYMS.items():
            if term in query_lower:
                # Add synonyms that aren't already in the query
                for synonym in synonyms:
                    if synonym not in query_lower:
                        expanded_terms.append(synonym)
        
        # Combine original query with expanded terms
        # Use original query first, then add synonyms
        if len(expanded_terms) > 1:
            return f"{query} {' '.join(expanded_terms[1:])}"
        return query
    
    def normalize_query(self, query: str) -> str:
        """Normalize query by removing noise and standardizing."""
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        # Remove special characters that don't add meaning (keep hyphens and apostrophes)
        query = re.sub(r'[^\w\s\'-]', '', query)
        return query
    
    def enhance(self, query: str) -> str:
        """Apply all enhancement techniques."""
        if not query or not query.strip():
            return query
        
        normalized = self.normalize_query(query)
        expanded = self.expand_query(normalized)
        
        # Limit expansion to avoid too long queries
        words = expanded.split()
        if len(words) > 20:
            # Keep original query + first 10 additional terms
            original_words = normalized.split()
            additional = [w for w in words if w not in original_words][:10]
            expanded = f"{normalized} {' '.join(additional)}"
        
        logger.debug(f"Query enhanced: '{query}' -> '{expanded}'")
        return expanded

