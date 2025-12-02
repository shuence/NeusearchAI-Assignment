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
        # Price-related synonyms
        "cheap": ["affordable", "budget", "low price", "inexpensive", "economical", "value"],
        "expensive": ["premium", "luxury", "high price", "costly", "pricey", "upscale"],
        "affordable": ["cheap", "budget", "low price", "inexpensive", "economical", "value"],
        "budget": ["cheap", "affordable", "low price", "inexpensive", "economical"],
        "price": ["cost", "pricing", "amount", "rupee", "rupees"],
        "cost": ["price", "pricing", "amount", "rupee", "rupees"],
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
    
    def enhance_price_query(self, query: str) -> str:
        """Enhance price-related queries with price context."""
        if not query or not query.strip():
            return query
        
        query_lower = query.lower()
        
        # Price-related keywords that indicate price queries
        price_indicators = [
            "price", "cost", "budget", "cheap", "expensive", "affordable",
            "under", "below", "over", "above", "between", "upto", "up to",
            "less than", "more than", "maximum", "minimum", "max", "min",
            "rupee", "rupees", "rs", "₹"
        ]
        
        # Check if query contains price indicators
        has_price_indicator = any(indicator in query_lower for indicator in price_indicators)
        
        if has_price_indicator:
            # Add price-related context terms to help with retrieval
            price_context = []
            
            # Extract numeric values (prices)
            import re
            price_pattern = r'(?:₹|rs\.?|rupees?|inr)?\s*(\d+(?:[.,]\d+)?)'
            price_matches = re.findall(price_pattern, query_lower, re.IGNORECASE)
            
            if price_matches:
                # If we have price values, add price range context
                price_context.append("price range")
                price_context.append("pricing")
            
            # Add qualitative price terms based on keywords
            if any(kw in query_lower for kw in ["cheap", "affordable", "budget", "low"]):
                price_context.extend(["budget-friendly", "affordable", "value"])
            elif any(kw in query_lower for kw in ["expensive", "premium", "luxury", "high"]):
                price_context.extend(["premium", "luxury", "high-end"])
            
            # Combine original query with price context
            if price_context:
                enhanced = f"{query} {' '.join(price_context)}"
                logger.debug(f"Price query enhanced: '{query}' -> '{enhanced}'")
                return enhanced
        
        return query
    
    def enhance(self, query: str) -> str:
        """Apply all enhancement techniques."""
        if not query or not query.strip():
            return query
        
        normalized = self.normalize_query(query)
        
        # First enhance price queries if applicable
        price_enhanced = self.enhance_price_query(normalized)
        
        # Then expand with synonyms
        expanded = self.expand_query(price_enhanced)
        
        # Limit expansion to avoid too long queries
        words = expanded.split()
        if len(words) > 20:
            # Keep original query + first 10 additional terms
            original_words = normalized.split()
            additional = [w for w in words if w not in original_words][:10]
            expanded = f"{normalized} {' '.join(additional)}"
        
        logger.debug(f"Query enhanced: '{query}' -> '{expanded}'")
        return expanded

