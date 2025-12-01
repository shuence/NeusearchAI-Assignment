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
- Price: ${product.price if product.price else 'N/A'}
- Vendor: {product.vendor or 'N/A'}
- Category: {product.product_type or 'N/A'}
- Description: {product.description[:200] if product.description else 'N/A'}
"""
            if product.tags:
                product_info += f"- Tags: {', '.join(product.tags[:5])}\n"
            
            context_parts.append(product_info)
        
        return "\n".join(context_parts)
    
    def _build_prompt(
        self,
        user_query: str,
        products: List[Product],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Build the prompt for the LLM."""
        product_context = self._format_product_context(products)
        
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

Product Context:
"""
        
        user_prompt = f"""
User Query: {user_query}

Based on the above products, please:
1. Interpret what the user is looking for
2. If needed, ask ONE clarifying question to better understand their needs
3. Provide a conversational response explaining why these products match (DO NOT list product names)
4. If the query is clear and products match well, explain the match directly

Remember: DO NOT include product names or create lists. Just provide a natural conversational response explaining the match.
"""
        
        # Add conversation history if provided
        if conversation_history:
            history_text = "\n".join([
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in conversation_history[-5:]  # Last 5 messages for context
            ])
            user_prompt = f"Previous conversation:\n{history_text}\n\n{user_prompt}"
        
        return system_prompt + product_context + "\n\n" + user_prompt
    
    def recommend_products(
        self,
        user_query: str,
        max_results: int = 5,
        similarity_threshold: float = 0.6,
        conversation_history: Optional[List[Dict[str, str]]] = None
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
            # Step 1: Vector search to find similar products
            logger.info(f"Searching for products matching query: {user_query}")
            search_results = self.vector_search.search_by_query_text(
                query_text=user_query,
                limit=max_results,
                similarity_threshold=similarity_threshold
            )
            
            products = [product for product, score in search_results]
            
            if not products:
                # No products found - return a helpful message
                return {
                    "response": "I couldn't find any products matching your query. Could you try rephrasing your request or be more specific about what you're looking for?",
                    "products": [],
                    "needs_clarification": False,
                    "scores": []
                }
            
            # Step 2: Use LLM to interpret query and generate response
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
            
            # Generate LLM response
            logger.info("Generating LLM response...")
            response = self.llm_client.models.generate_content(
                model=self.llm_model,
                contents=prompt
            )
            
            llm_response = response.text if hasattr(response, 'text') else str(response)
            
            # Clean up response - remove product names and bullet points if LLM included them
            # This is a safety measure in case the LLM doesn't follow instructions
            # Remove common patterns like "Product Name:" or bullet points with product names
            cleaned_response = re.sub(r'^\s*[-*•]\s*.*?:\s*.*$', '', llm_response, flags=re.MULTILINE)
            cleaned_response = re.sub(r'\*\*.*?\*\*:', '', cleaned_response)  # Remove bold product names
            cleaned_response = re.sub(r'^.*?Sports Bra.*?:.*$', '', cleaned_response, flags=re.MULTILINE | re.IGNORECASE)
            cleaned_response = re.sub(r'^.*?Top.*?:.*$', '', cleaned_response, flags=re.MULTILINE | re.IGNORECASE)
            # Clean up multiple newlines
            cleaned_response = re.sub(r'\n{3,}', '\n\n', cleaned_response)
            cleaned_response = cleaned_response.strip()
            
            # If cleaning removed everything, use original
            if not cleaned_response:
                cleaned_response = llm_response.strip()
            
            # Check if response is asking for clarification
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
            
            # Always return products - even if asking for clarification, show what we found
            # The frontend will display them as cards
            return {
                "response": cleaned_response,
                "products": products,  # Always return products to display as cards
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

