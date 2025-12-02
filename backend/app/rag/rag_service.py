"""RAG service for product recommendations using vector search and LLM."""
import re
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from google import genai
from app.rag.vector_search import VectorSearchService
from app.rag import get_embedding_service
from app.models.product import Product
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger("rag_service")


class RAGService:
    """RAG service that combines vector search with LLM for intelligent product recommendations."""
    
    def __init__(self, db: Session):
        """Initialize RAG service."""
        self.db = db
        self.vector_search = VectorSearchService(db)
        
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set - LLM features will be limited")
            self.llm_client = None
        else:
            self.llm_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self.llm_model = "gemini-2.0-flash"  # Fast and cost-effective for chat
    
    def _format_product_context(self, products: List[Product]) -> str:
        """Format products as context for LLM."""
        if not products:
            return "No products found."
        
        context_parts = []
        for i, product in enumerate(products, 1):
            product_info = f"""
Product {i}:
- Title: {product.title}
- Price: ₹{product.price if product.price else 'N/A'}
- Vendor: {product.vendor or 'N/A'}
- Category: {product.product_type or 'N/A'}
- Description: {product.description[:200] if product.description else 'N/A'}
"""
            if product.tags:
                product_info += f"- Tags: {', '.join(product.tags[:5])}\n"
            
            context_parts.append(product_info)
        
        return "\n".join(context_parts)
    
    def _calculate_metadata_context(self, products: List[Product]) -> str:
        """Calculate metadata context for products (price range, categories, etc.)."""
        if not products:
            return ""
        
        # Calculate average price
        prices = [p.price for p in products if p.price]
        avg_price = sum(prices) / len(prices) if prices else 0
        
        # Find common category
        categories = [p.product_type for p in products if p.product_type]
        common_category = max(set(categories), key=categories.count) if categories else None
        
        context_parts = []
        if common_category:
            context_parts.append(f"Most products are in the {common_category} category.")
        if avg_price > 0:
            if avg_price < 50:
                price_range = "budget-friendly"
            elif avg_price < 150:
                price_range = "mid-range"
            else:
                price_range = "premium"
            context_parts.append(f"Products are in the {price_range} price range (average ₹{avg_price:.0f}).")
        
        return " ".join(context_parts)
    
    def _build_prompt(
        self,
        user_query: str,
        products: List[Product],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Build improved prompt for the LLM with better context."""
        product_context = self._format_product_context(products)
        metadata_context = self._calculate_metadata_context(products)
        
        system_prompt = """You are a helpful product recommendation assistant for an e-commerce website. 
Your role is to help users find products that match their needs based on their queries.

IMPORTANT GUIDELINES:
1. DO NOT list product names, titles, or create bullet points of products in your response
2. The products will be displayed as cards with images below your message automatically
3. Your response should be a conversational explanation of why these products match the user's query
4. Interpret abstract and nuanced queries (e.g., "something for gym and meetings", "furniture for 2bhk apartment")
5. If the query is unclear or ambiguous, ask ONE clarifying question to better understand the user's needs
6. Be conversational, friendly, and helpful
7. If no products match well, politely explain why and suggest what might help
8. Keep responses concise but informative (2-3 sentences)
9. Focus on explaining the match between the query and the products, not listing them
10. Consider price range, style, use case, and category when explaining matches

EXAMPLES OF GOOD RESPONSES:
- "I found some great options that work well for both gym workouts and professional meetings. These pieces combine athletic functionality with a polished look that transitions seamlessly from exercise to office."
- "These products match your search for casual everyday wear. They're comfortable, versatile pieces that work well for various occasions."
- "I found some options, but could you tell me more about the specific style you're looking for? Are you interested in something more formal or casual?"

Product Context:
"""
        
        user_prompt = f"""
User Query: {user_query}
"""
        
        if metadata_context:
            user_prompt += f"\nContext: {metadata_context}\n"
        
        user_prompt += """
Based on the above products, please:
1. Interpret what the user is looking for
2. If needed, ask ONE clarifying question to better understand their needs
3. Provide a conversational response explaining why these products match (DO NOT list product names)
4. If the query is clear and products match well, explain the match directly
5. Consider the price range, category, and use cases when explaining relevance

Remember: DO NOT include product names or create lists. Just provide a natural conversational response explaining the match.
"""
        
        if conversation_history:
            history_text = "\n".join([
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in conversation_history[-5:]  # Last 5 messages for context
            ])
            user_prompt = f"Previous conversation:\n{history_text}\n\n{user_prompt}"
        
        return system_prompt + product_context + "\n\n" + user_prompt
    
    def _calculate_optimal_threshold(self, query: str, initial_result_count: int = 0) -> float:
        """Calculate optimal similarity threshold based on query characteristics."""
        base_threshold = 0.6
        
        # Lower threshold for short queries (less specific)
        query_words = len(query.split())
        if query_words <= 2:
            base_threshold -= 0.1
        
        # Lower threshold if we got few results (need more recall)
        if initial_result_count < 3:
            base_threshold -= 0.15
        
        # Higher threshold for very specific queries
        if query_words > 5:
            base_threshold += 0.05
        
        # Ensure threshold is within reasonable bounds
        return max(0.3, min(0.9, base_threshold))
    
    def recommend_products(
        self,
        user_query: str,
        max_results: int = 5,
        similarity_threshold: float = 0.6,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        auto_adjust_threshold: bool = True
    ) -> Dict[str, Any]:
        """
        Recommend products based on user query using RAG.
        
        Args:
            user_query: User's natural language query
            max_results: Maximum number of products to retrieve
            similarity_threshold: Minimum similarity score for products
            conversation_history: Previous conversation messages for context
        
        Returns:
            Dictionary with:
            - response: LLM-generated response text
            - products: List of recommended products
            - needs_clarification: Whether the LLM is asking for clarification
        """
        try:
            if auto_adjust_threshold:
                adjusted_threshold = self._calculate_optimal_threshold(user_query)
                if adjusted_threshold != similarity_threshold:
                    logger.info(f"Adjusted similarity threshold: {similarity_threshold} -> {adjusted_threshold}")
                    similarity_threshold = adjusted_threshold
            
            logger.info(f"Searching for products matching query: {user_query}")
            search_results = self.vector_search.search_by_query_text(
                query_text=user_query,
                limit=max_results * 2,
                similarity_threshold=similarity_threshold,
                enhance_query=True  # Enable query enhancement
            )
            
            # If we got too few results, try with lower threshold
            if len(search_results) < max_results and similarity_threshold > 0.3:
                logger.info(f"Got {len(search_results)} results, trying with lower threshold")
                search_results = self.vector_search.search_by_query_text(
                    query_text=user_query,
                    limit=max_results * 2,
                    similarity_threshold=max(0.3, similarity_threshold - 0.2),
                    enhance_query=True
                )
            
            # Limit to max_results
            search_results = search_results[:max_results]
            products = [product for product, score in search_results]
            
            if not products:
                # No products found - return a helpful message
                return {
                    "response": "I couldn't find any products matching your query. Could you try rephrasing your request or be more specific about what you're looking for?",
                    "products": [],
                    "needs_clarification": False,
                    "scores": []
                }
            
            if not self.llm_client:
                # Fallback: return products without LLM interpretation
                logger.warning("LLM not available - returning products without interpretation")
                return {
                    "response": f"I found {len(products)} product(s) that might match your query:",
                    "products": products,
                    "needs_clarification": False,
                    "scores": [score for _, score in search_results]
                }
            
            # Build prompt
            prompt = self._build_prompt(user_query, products, conversation_history)
            
            logger.info("Generating LLM response...")
            response = self.llm_client.models.generate_content(
                model=self.llm_model,
                contents=prompt
            )
            
            llm_response = response.text if hasattr(response, 'text') else str(response)
            
            cleaned_response = re.sub(r'^\s*[-*•]\s*.*?:\s*.*$', '', llm_response, flags=re.MULTILINE)
            cleaned_response = re.sub(r'\*\*.*?\*\*:', '', cleaned_response)
            cleaned_response = re.sub(r'^.*?Sports Bra.*?:.*$', '', cleaned_response, flags=re.MULTILINE | re.IGNORECASE)
            cleaned_response = re.sub(r'^.*?Top.*?:.*$', '', cleaned_response, flags=re.MULTILINE | re.IGNORECASE)
            cleaned_response = re.sub(r'\n{3,}', '\n\n', cleaned_response)
            cleaned_response = cleaned_response.strip()
            
            # If cleaning removed everything, use original
            if not cleaned_response:
                cleaned_response = llm_response.strip()
            
            clarification_keywords = [
                "could you clarify",
                "can you tell me more",
                "what do you mean",
                "could you be more specific",
                "what are you looking for",
                "?"
            ]
            needs_clarification = any(
                keyword.lower() in cleaned_response.lower() 
                for keyword in clarification_keywords
            ) and "?" in cleaned_response
            
            return {
                "response": cleaned_response,
                "products": products,
                "needs_clarification": needs_clarification,
                "scores": [score for _, score in search_results]
            }
            
        except Exception as e:
            logger.error(f"Error in RAG recommendation: {e}", exc_info=True)
            return {
                "response": "I'm sorry, I encountered an error while processing your request. Please try again.",
                "products": [],
                "needs_clarification": False,
                "scores": []
            }
    
    def compare_products(self, products: List[Product]) -> str:
        """
        Compare products and generate AI insights.
        
        Args:
            products: List of products to compare (2-4 products)
        
        Returns:
            AI-generated comparison insight string
        """
        if not products or len(products) < 2:
            return "Please provide at least 2 products to compare."
        
        if len(products) > 4:
            products = products[:4]  # Limit to 4 products
        
        try:
            if not self.llm_client:
                # Fallback: generate simple comparison
                product_titles = ", ".join([p.title for p in products])
                return f"Comparing {len(products)} products: {product_titles}. Please enable LLM for detailed insights."
            
            # Build comparison prompt
            product_context = self._format_product_context(products)
            
            system_prompt = """You are a helpful product comparison assistant. Your role is to provide structured, easy-to-read comparisons between products.

IMPORTANT GUIDELINES:
1. Format your response as structured bullet points organized by category
2. Use clear categories like: Price & Value, Key Features, Best For, Pros & Cons
3. Be objective and balanced in your comparison
4. Make it easy to scan and understand quickly
5. Use bullet points (•) for each comparison point
6. Focus on actionable insights that help users make decisions
7. Keep each bullet point concise (one line or short phrase)

Format your response like this (IMPORTANT: Always prefix each bullet point with the product name or identifier):
**Price & Value**
• [Product Name/Identifier]: [price info and value]
• [Product Name/Identifier]: [price info and value]

**Key Features**
• [Product Name/Identifier]: [key features]
• [Product Name/Identifier]: [key features]

**Best For**
• [Product Name/Identifier]: [use cases]
• [Product Name/Identifier]: [use cases]

**Pros & Cons**
• [Product Name/Identifier]: Pros: [list pros], Cons: [list cons]
OR format as:
• [Product Name/Identifier]: [pros and cons description]
• [Product Name/Identifier]: [pros and cons description]

**Summary**
• [Overall recommendation or key takeaway]

CRITICAL: For each bullet point, ALWAYS start with the product name or a clear identifier (like "Product 1", "Product 2", or use part of the product title) followed by a colon (:). This ensures each point can be matched to the correct product.

Product Context:
"""
            
            # Build product identifiers for the prompt
            product_identifiers = []
            for i, product in enumerate(products, 1):
                # Use first few words of title as identifier
                title_words = product.title.split()[:3]
                identifier = " ".join(title_words)
                product_identifiers.append(f"Product {i} ({identifier})")
            
            user_prompt = f"""
Please compare these {len(products)} products using structured bullet points organized by:
1. Price & Value - Compare prices and value proposition
2. Key Features - Highlight main feature differences
3. Best For - Best use cases for each product
4. Pros & Cons - List pros and cons for EACH product separately. Format: "Product X: Pros: [list], Cons: [list]" or "Product X: [pros and cons]"
5. Summary - Overall recommendation

IMPORTANT: For each bullet point, ALWAYS start with the product identifier followed by a colon (:).
Use these identifiers: {', '.join(product_identifiers)}

Example format:
• Product 1 (Zen Nova): ₹2698.0
• Product 2 (Zen Halo): ₹2698.0

For Pros & Cons, ensure you provide pros and cons for EACH product separately. Example:
• Product 1 (Zen Nova): Pros: Unique design, Cons: May not suit everyone
• Product 2 (Zen Halo): Pros: Classic style, Cons: Less distinctive

For Summary, provide a concise overall recommendation based on the comparison.

Use bullet points (•) for each point. Make it easy to scan and compare quickly.
"""
            
            prompt = system_prompt + product_context + "\n\n" + user_prompt
            
            logger.info(f"Generating comparison insight for {len(products)} products...")
            response = self.llm_client.models.generate_content(
                model=self.llm_model,
                contents=prompt
            )
            
            insight = response.text if hasattr(response, 'text') else str(response)
            
            # Clean up the response
            cleaned_insight = re.sub(r'\n{3,}', '\n\n', insight)
            cleaned_insight = cleaned_insight.strip()
            
            return cleaned_insight if cleaned_insight else "Unable to generate comparison insight."
            
        except Exception as e:
            logger.error(f"Error generating comparison insight: {e}", exc_info=True)
            return "I'm sorry, I encountered an error while generating the comparison. Please try again."

