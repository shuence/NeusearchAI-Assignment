"""RAG service for product recommendations using vector search and LLM."""
import re
import time
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from google import genai
from google.genai import types
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
        if not db:
            raise ValueError("Database session is required")
        
        self.db = db
        self.vector_search = VectorSearchService(db)
        
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set - LLM features will be limited")
            self.llm_client = None
        else:
            try:
                self.llm_client = genai.Client(api_key=settings.GEMINI_API_KEY)
                self.llm_model = "gemini-2.0-flash"  # Fast and cost-effective for chat
            except Exception as e:
                logger.error(f"Failed to initialize LLM client: {e}")
                self.llm_client = None
    
    def _format_product_context(self, products: List[Product]) -> str:
        """Format products as context for LLM."""
        if not products:
            return "No products found."
        
        context_parts = []
        for i, product in enumerate(products, 1):
            # Handle None product
            if product is None:
                logger.warning(f"Product at index {i-1} is None, skipping")
                continue
            
            # Safely extract product fields with defaults
            try:
                title = str(product.title) if product.title else "Untitled Product"
                price = product.price if product.price is not None else None
                vendor = str(product.vendor) if product.vendor else "N/A"
                category = str(product.product_type) if product.product_type else "N/A"
                description = str(product.description) if product.description else "N/A"
                
                # Truncate description to avoid overly long context
                if len(description) > 200:
                    description = description[:200] + "..."
                
                product_info = f"""
Product {i}:
- Title: {title}
- Price: ₹{price if price is not None else 'N/A'}
- Vendor: {vendor}
- Category: {category}
- Description: {description}
"""
            except Exception as e:
                logger.warning(f"Error formatting product {i}: {e}, skipping")
                continue
            # Safely handle tags
            try:
                if product.tags and isinstance(product.tags, list):
                    # Filter out None/empty tags
                    valid_tags = [str(tag) for tag in product.tags[:5] if tag and str(tag).strip()]
                    if valid_tags:
                        product_info += f"- Tags: {', '.join(valid_tags)}\n"
            except Exception as e:
                logger.debug(f"Error processing tags for product {i}: {e}")
            
            # Extract color and size information from variants
            if product.features:
                features = product.features
                
                # Extract from variants (option1, option2, option3)
                if isinstance(features, dict) and "variants" in features:
                    variants = features.get("variants", [])
                    if variants:
                        # Collect unique option values from variants
                        colors = set()
                        sizes = set()
                        # Common color keywords (including compound colors like "deep burgundy")
                        color_keywords = [
                            'red', 'blue', 'green', 'black', 'white', 'yellow', 'pink', 'purple', 
                            'orange', 'gray', 'grey', 'brown', 'beige', 'navy', 'maroon', 'teal', 
                            'coral', 'ivory', 'cream', 'tan', 'khaki', 'burgundy', 'deep burgundy',
                            'magenta', 'cyan', 'lime', 'olive', 'salmon', 'turquoise', 'violet', 'indigo',
                            'charcoal', 'peach', 'mint', 'lavender', 'rose', 'gold', 'silver',
                            'bronze', 'copper', 'plum', 'emerald', 'sapphire', 'ruby', 'amber',
                            'smoke', 'sage', 'stone', 'sand', 'camel', 'cognac', 'mocha', 'espresso',
                            'deep', 'light', 'dark', 'bright', 'pale', 'vibrant'
                        ]
                        # Common size patterns
                        size_patterns = ['xs', 's', 'm', 'l', 'xl', 'xxl', 'xxxl', 'xxxxl', 
                                        'small', 'medium', 'large', 'extra small', 'extra large',
                                        'one size', 'os', 'free size']
                        
                        for variant in variants:
                            if not isinstance(variant, dict):
                                continue
                            
                            try:
                                variant_title = variant.get("title")
                                if variant_title:
                                    title_str = str(variant_title).strip()
                                    if title_str:  # Only process non-empty strings
                                        title_lower = title_str.lower()
                                        # Check if title contains any color keyword
                                        for color_keyword in color_keywords:
                                            if color_keyword in title_lower:
                                                # Extract the color part from title (before "/" or first part)
                                                color_part = title_str.split('/')[0].strip()
                                                if color_part:
                                                    colors.add(color_part)
                                                break
                                
                                # option1 is typically Color, option2 is typically Size
                                opt1 = variant.get("option1")
                                opt2 = variant.get("option2")
                                opt3 = variant.get("option3")
                                
                                # Check option1 (usually color)
                                if opt1:
                                    try:
                                        opt1_str = str(opt1).strip()
                                        if opt1_str:  # Only process non-empty strings
                                            opt1_lower = opt1_str.lower()
                                            # Check if it's a color
                                            if any(c in opt1_lower for c in color_keywords):
                                                colors.add(opt1_str)
                                            # Check if it's a size
                                            elif any(s == opt1_lower or opt1_lower.endswith(s) or opt1_lower.startswith(s) for s in size_patterns):
                                                sizes.add(opt1_str)
                                            # Also check for numeric sizes
                                            elif opt1_str.isdigit() and len(opt1_str) <= 3:
                                                sizes.add(opt1_str)
                                            # If it contains color-like words, treat as color
                                            elif any(c in opt1_lower for c in ['color', 'colour', 'hue', 'shade']):
                                                colors.add(opt1_str)
                                            # Default: if it's a single word or short phrase, likely a color
                                            elif len(opt1_str.split()) <= 2 and not opt1_str.isdigit():
                                                colors.add(opt1_str)
                                    except Exception as e:
                                        logger.debug(f"Error processing option1: {e}")
                                
                                # Check option2 (usually size)
                                if opt2:
                                    try:
                                        opt2_str = str(opt2).strip()
                                        if opt2_str:
                                            opt2_lower = opt2_str.lower()
                                            if any(s == opt2_lower or opt2_lower.endswith(s) or opt2_lower.startswith(s) for s in size_patterns):
                                                sizes.add(opt2_str)
                                            elif opt2_str.isdigit() and len(opt2_str) <= 3:
                                                sizes.add(opt2_str)
                                            # If not clearly a size, might be a color
                                            elif any(c in opt2_lower for c in color_keywords):
                                                colors.add(opt2_str)
                                    except Exception as e:
                                        logger.debug(f"Error processing option2: {e}")
                                
                                # Check option3 (could be either)
                                if opt3:
                                    try:
                                        opt3_str = str(opt3).strip()
                                        if opt3_str:
                                            opt3_lower = opt3_str.lower()
                                            if any(c in opt3_lower for c in color_keywords):
                                                colors.add(opt3_str)
                                            elif any(s == opt3_lower or opt3_lower.endswith(s) or opt3_lower.startswith(s) for s in size_patterns):
                                                sizes.add(opt3_str)
                                            elif opt3_str.isdigit() and len(opt3_str) <= 3:
                                                sizes.add(opt3_str)
                                    except Exception as e:
                                        logger.debug(f"Error processing option3: {e}")
                            except Exception as e:
                                logger.debug(f"Error processing variant: {e}")
                                continue
                        
                        # Add colors and sizes to product info
                        if colors:
                            product_info += f"- Available Colors: {', '.join(sorted(colors))}\n"
                        if sizes:
                            product_info += f"- Available Sizes: {', '.join(sorted(sizes))}\n"
                        
                        # Add detailed variant information: sizes available for each color
                        # This helps answer queries like "What sizes does X come in for Deep Burgundy?"
                        # Standard pattern: option1 = Color, option2 = Size
                        color_size_map = {}
                        for variant in variants:
                            if isinstance(variant, dict):
                                opt1 = variant.get("option1")  # Typically Color
                                opt2 = variant.get("option2")  # Typically Size
                                
                                # Standard pattern: option1 is color, option2 is size
                                color = None
                                size = None
                                
                                if opt1:
                                    opt1_str = str(opt1).strip()
                                    # Assume option1 is color (most common pattern)
                                    # But verify it's not clearly a size
                                    opt1_lower = opt1_str.lower()
                                    if not (any(s == opt1_lower or opt1_lower.endswith(s) or opt1_lower.startswith(s) for s in size_patterns) or opt1_str.isdigit()):
                                        color = opt1_str
                                
                                if opt2:
                                    opt2_str = str(opt2).strip()
                                    # Assume option2 is size (most common pattern)
                                    # But verify it's not clearly a color
                                    opt2_lower = opt2_str.lower()
                                    if any(s == opt2_lower or opt2_lower.endswith(s) or opt2_lower.startswith(s) for s in size_patterns) or opt2_str.isdigit():
                                        size = opt2_str
                                    # If option2 looks like a color and option1 wasn't set, use it as color
                                    elif not color and any(c in opt2_lower for c in color_keywords):
                                        color = opt2_str
                                
                                # If we have both color and size, add to map
                                if color and size:
                                    if color not in color_size_map:
                                        color_size_map[color] = set()
                                    color_size_map[color].add(size)
                        
                        # Add color-specific size information
                        if color_size_map:
                            product_info += "- Sizes by Color:\n"
                            for color, size_set in sorted(color_size_map.items()):
                                sorted_sizes = sorted(size_set, key=lambda x: (
                                    ['xs', 's', 'm', 'l', 'xl', 'xxl', 'xxxl'].index(x.lower()) 
                                    if x.lower() in ['xs', 's', 'm', 'l', 'xl', 'xxl', 'xxxl'] 
                                    else 999, x
                                ))
                                product_info += f"  • {color}: {', '.join(sorted_sizes)}\n"
                
                # Also check options structure if available
                if isinstance(features, dict) and "options" in features:
                    options = features.get("options", [])
                    for option in options:
                        if isinstance(option, dict):
                            option_name = option.get("name", "").lower()
                            option_values = option.get("values", [])
                            if option_values:
                                # Filter out None/empty values
                                valid_values = [str(v) for v in option_values if v and str(v).strip()]
                                if valid_values:
                                    if "color" in option_name or "colour" in option_name:
                                        product_info += f"- Available Colors: {', '.join(valid_values)}\n"
                                    elif "size" in option_name:
                                        product_info += f"- Available Sizes: {', '.join(valid_values)}\n"
            
            context_parts.append(product_info)
        
        return "\n".join(context_parts)
    
    def _calculate_metadata_context(self, products: List[Product]) -> str:
        """Calculate metadata context for products (price range, categories, etc.)."""
        if not products:
            return ""
        
        context_parts = []
        
        try:
            # Calculate average price with safe handling
            prices = []
            for p in products:
                if p and p.price is not None:
                    try:
                        price = float(p.price)
                        if price > 0:  # Only include valid positive prices
                            prices.append(price)
                    except (ValueError, TypeError):
                        continue
            
            if prices:
                avg_price = sum(prices) / len(prices)
                if avg_price > 0:
                    if avg_price < 50:
                        price_range = "budget-friendly"
                    elif avg_price < 150:
                        price_range = "mid-range"
                    else:
                        price_range = "premium"
                    context_parts.append(f"Products are in the {price_range} price range (average ₹{avg_price:.0f}).")
        except Exception as e:
            logger.debug(f"Error calculating price metadata: {e}")
        
        try:
            # Find common category with safe handling
            categories = []
            for p in products:
                if p and p.product_type:
                    try:
                        category = str(p.product_type).strip()
                        if category:
                            categories.append(category)
                    except Exception:
                        continue
            
            if categories:
                try:
                    common_category = max(set(categories), key=categories.count)
                    if common_category:
                        context_parts.append(f"Most products are in the {common_category} category.")
                except Exception as e:
                    logger.debug(f"Error finding common category: {e}")
        except Exception as e:
            logger.debug(f"Error calculating category metadata: {e}")
        
        return " ".join(context_parts)
    
    def _build_prompt(
        self,
        user_query: str,
        products: List[Product],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        is_informational: bool = False
    ) -> str:
        """Build improved prompt for the LLM with better context."""
        product_context = self._format_product_context(products)
        metadata_context = self._calculate_metadata_context(products)
        
        # Check if query contains color-related terms
        color_keywords = [
            'red', 'blue', 'green', 'black', 'white', 'yellow', 'pink', 'purple', 
            'orange', 'gray', 'grey', 'brown', 'beige', 'navy', 'maroon', 'teal', 
            'coral', 'ivory', 'cream', 'tan', 'khaki', 'burgundy', 'deep burgundy',
            'magenta', 'cyan', 'lime', 'olive', 'salmon', 'turquoise', 'violet', 'indigo',
            'charcoal', 'peach', 'mint', 'lavender', 'rose', 'gold', 'silver',
            'bronze', 'copper', 'plum', 'emerald', 'sapphire', 'ruby', 'amber',
            'color', 'colour', 'hue', 'shade'
        ]
        query_lower = user_query.lower()
        is_color_query = any(keyword in query_lower for keyword in color_keywords)
        
        # Check if query contains price-related terms
        price_info = self._parse_price_query(user_query)
        is_price_query = price_info and price_info.get("is_price_query", False)
        
        color_emphasis = ""
        if is_color_query and not is_informational:
            color_emphasis = """
12. COLOR QUERIES: If the user is searching for a specific color (e.g., "Deep Burgundy", "red", "blue"), 
    emphasize products that have that exact color available. The product cards will automatically show 
    the color-specific variant image when available. Make sure to highlight that these products come 
    in the requested color.
"""
        
        price_emphasis = ""
        if is_price_query and not is_informational:
            price_constraints = []
            if price_info.get("min_price"):
                price_constraints.append(f"minimum ₹{price_info['min_price']:.0f}")
            if price_info.get("max_price"):
                price_constraints.append(f"maximum ₹{price_info['max_price']:.0f}")
            
            price_constraint_text = " and ".join(price_constraints) if price_constraints else "specific price range"
            
            price_emphasis = f"""
13. PRICE QUERIES: The user is searching for products within a {price_constraint_text}. 
    - Emphasize that the products shown match their price requirements
    - Mention the price range in your response (e.g., "These products are all under ₹{price_info.get('max_price', 'N/A'):.0f}" or "These are budget-friendly options")
    - Highlight value proposition when relevant
    - If no products match the price criteria, explain this clearly and suggest adjusting the price range
"""
        
        informational_guidance = ""
        if is_informational:
            informational_guidance = """
12. INFORMATIONAL QUERIES: The user is asking for information about a specific product (e.g., "What sizes does X come in?", 
    "What colors are available for Y?"). 
    - Answer the question directly using the product information provided
    - DO NOT show product cards - this is an informational query, not a product discovery query
    - Provide specific details like sizes, colors, materials, etc. from the product context
    - If the product is not found in the context, politely say you couldn't find that specific product
    - Keep the response focused on answering the question, not recommending products
"""
        
        product_display_note = "2. The products will be displayed as cards with images below your message automatically" if not is_informational else "2. DO NOT display product cards - this is an informational query, just provide the answer"
        
        system_prompt = f"""You are a helpful product recommendation assistant for an e-commerce website. 
Your role is to help users find products that match their needs based on their queries.

IMPORTANT GUIDELINES:
1. DO NOT list product names, titles, or create bullet points of products in your response (EXCEPT when answering specific questions about product details)
{product_display_note}
3. Your response should be a conversational explanation of why these products match the user's query
4. Interpret abstract and nuanced queries (e.g., "something for gym and meetings", "furniture for 2bhk apartment")
5. If the query is unclear or ambiguous, ask ONE clarifying question to better understand the user's needs
6. Be conversational, friendly, and helpful
7. If no products match well, politely explain why and suggest what might help
8. Keep responses concise but informative (2-3 sentences)
9. Focus on explaining the match between the query and the products, not listing them
10. Consider price range, style, use case, and category when explaining matches
11. ANSWER QUESTIONS ABOUT PRODUCT DETAILS: If users ask about specific product details like colors, sizes, materials, or other attributes, provide that information directly from the product context provided. For example, if asked "What colors does this come in?" or "What sizes are available?", list the available options clearly.
12. PRODUCT IMAGES: Product images are automatically displayed by the system below your response. You should NEVER say you cannot show images, cannot display products, or that showing images is beyond your capabilities. The system handles image display automatically - you just need to provide helpful responses about the products. If users ask to see products or images, simply provide a helpful response and the system will display the product cards with images automatically.
{color_emphasis}
{price_emphasis}
{informational_guidance}
EXAMPLES OF GOOD RESPONSES:
- "I found some great options that work well for both gym workouts and professional meetings. These pieces combine athletic functionality with a polished look that transitions seamlessly from exercise to office."
- "These products match your search for casual everyday wear. They're comfortable, versatile pieces that work well for various occasions."
- "I found some options, but could you tell me more about the specific style you're looking for? Are you interested in something more formal or casual?"
- "The Zen Nova Dress comes in Smoke Grey. Available sizes are S, M, L, and XL." (when asked about specific product details)

Product Context:
"""
        
        user_prompt = f"""
User Query: {user_query}
"""
        
        if metadata_context:
            user_prompt += f"\nContext: {metadata_context}\n"
        
        if is_informational:
            user_prompt += """
The user is asking for information about a specific product. Please:
1. Answer the question directly using the product information provided above
2. Provide specific details like sizes, colors, materials, etc. from the product context
3. If the product is not found in the context, politely say you couldn't find that specific product
4. DO NOT show product cards - this is an informational query, just provide the answer
5. Keep the response focused on answering the question, not recommending products

Remember: 
- This is an informational query, not a product discovery query
- Answer the question directly without showing product recommendations
- Provide specific details from the product context when available
"""
        else:
            user_prompt += """
Based on the above products, please:
1. Interpret what the user is looking for
2. If needed, ask ONE clarifying question to better understand their needs
3. Provide a conversational response explaining why these products match (DO NOT list product names)
4. If the query is clear and products match well, explain the match directly
5. Consider the price range, category, and use cases when explaining relevance
6. If the user asks about specific product details (colors, sizes, materials, etc.), provide that information directly from the product context above
7. If users ask to see products, images, or want to view items, provide a helpful response - the system will automatically display product cards with images below your message

Remember: 
- DO NOT include product names or create lists when explaining matches
- DO provide specific details (colors, sizes, etc.) when the user asks about them
- DO NOT say you cannot show images or that displaying products is beyond your capabilities - the system handles this automatically
- Just provide a natural conversational response - product images will be displayed automatically by the system
"""
        
        if conversation_history:
            history_text = "\n".join([
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in conversation_history[-5:]  # Last 5 messages for context
            ])
            user_prompt = f"Previous conversation:\n{history_text}\n\n{user_prompt}"
        
        return system_prompt + product_context + "\n\n" + user_prompt
    
    def _parse_price_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Parse price-related information from user query.
        
        Returns:
            Dict with price constraints:
            - min_price: Optional minimum price
            - max_price: Optional maximum price
            - price_keywords: List of price-related keywords found
            - is_price_query: Whether this is primarily a price query
        """
        if not query or not isinstance(query, str):
            return None
        
        try:
            query_lower = query.lower()
            price_info = {
                "min_price": None,
                "max_price": None,
                "price_keywords": [],
                "is_price_query": False
            }
            
            # Price-related keywords
            price_keywords = [
                "price", "cost", "budget", "cheap", "expensive", "affordable",
                "under", "below", "over", "above", "between", "upto", "up to",
                "less than", "more than", "maximum", "minimum", "max", "min",
                "rupee", "rupees", "rs", "₹", "inr"
            ]
            
            # Check if query contains price-related terms
            found_keywords = [kw for kw in price_keywords if kw in query_lower]
            if found_keywords:
                price_info["price_keywords"] = found_keywords
                price_info["is_price_query"] = True
            
            # Extract numeric price values (handle ₹, Rs, rupee formats)
            # Pattern: (₹|Rs|rupee|rupees)?\s*(\d+([.,]\d+)?)
            price_pattern = r'(?:₹|rs\.?|rupees?|inr)?\s*(\d+(?:[.,]\d+)?)'
            price_matches = re.findall(price_pattern, query_lower, re.IGNORECASE)
            
            # Convert to float values
            price_values = []
            for match in price_matches:
                try:
                    # Remove commas and convert to float
                    price_str = match.replace(',', '')
                    price_val = float(price_str)
                    if price_val > 0:
                        price_values.append(price_val)
                except (ValueError, TypeError):
                    continue
            
            # Determine min/max based on context keywords
            if price_values:
                # Check for "under", "below", "less than", "upto", "up to", "maximum", "max"
                if any(kw in query_lower for kw in ["under", "below", "less than", "upto", "up to", "maximum", "max"]):
                    price_info["max_price"] = max(price_values)
                
                # Check for "over", "above", "more than", "minimum", "min"
                elif any(kw in query_lower for kw in ["over", "above", "more than", "minimum", "min"]):
                    price_info["min_price"] = min(price_values)
                
                # Check for "between" or "and" (range)
                elif "between" in query_lower or (len(price_values) >= 2 and "and" in query_lower):
                    price_values_sorted = sorted(price_values)
                    price_info["min_price"] = price_values_sorted[0]
                    price_info["max_price"] = price_values_sorted[-1]
                
                # If only one price value and query suggests upper bound
                elif len(price_values) == 1:
                    # Default: if keywords suggest upper bound, use as max
                    if any(kw in query_lower for kw in ["under", "below", "less than", "upto", "up to"]):
                        price_info["max_price"] = price_values[0]
                    # Default: if keywords suggest lower bound, use as min
                    elif any(kw in query_lower for kw in ["over", "above", "more than"]):
                        price_info["min_price"] = price_values[0]
                    # Default: treat as max price if no clear indication
                    else:
                        price_info["max_price"] = price_values[0]
            
            # Handle qualitative price terms
            if not price_values:
                if any(kw in query_lower for kw in ["cheap", "affordable", "budget", "low price", "low cost"]):
                    price_info["max_price"] = 100  # Default: under ₹100 for "cheap"
                    price_info["is_price_query"] = True
                elif any(kw in query_lower for kw in ["expensive", "premium", "luxury", "high price", "high cost"]):
                    price_info["min_price"] = 200  # Default: over ₹200 for "expensive"
                    price_info["is_price_query"] = True
            
            return price_info if price_info["is_price_query"] or price_info["min_price"] or price_info["max_price"] else None
            
        except Exception as e:
            logger.debug(f"Error parsing price query: {e}")
            return None
    
    def _filter_by_price(
        self,
        products: List[Tuple[Product, float]],
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> List[Tuple[Product, float]]:
        """
        Filter products by price range.
        
        Args:
            products: List of (Product, score) tuples
            min_price: Minimum price (inclusive)
            max_price: Maximum price (inclusive)
        
        Returns:
            Filtered list of (Product, score) tuples
        """
        if not products:
            return []
        
        if min_price is None and max_price is None:
            return products
        
        filtered = []
        for product, score in products:
            if product is None:
                continue
            
            try:
                price = product.price
                if price is None:
                    # If price is missing and we have constraints, skip it
                    # unless we're being lenient (only max constraint)
                    if min_price is not None:
                        continue
                    # If only max_price constraint, include products without price
                    if max_price is not None:
                        filtered.append((product, score))
                    continue
                
                price_float = float(price)
                
                # Check price constraints
                if min_price is not None and price_float < min_price:
                    continue
                if max_price is not None and price_float > max_price:
                    continue
                
                # Product passes price filter
                filtered.append((product, score))
                
            except (ValueError, TypeError) as e:
                logger.debug(f"Error processing price for product {product.id}: {e}")
                continue
        
        return filtered
    
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
    
    def _is_informational_query(self, user_query: str) -> bool:
        """Detect if query is asking for information about a specific product rather than discovering products."""
        if not user_query or not isinstance(user_query, str):
            return False
        
        try:
            query_lower = user_query.lower().strip()
            if not query_lower:
                return False
            
            # Informational query patterns
            informational_patterns = [
                r'what (sizes?|colors?|colours?|materials?|features?|specs?|specifications?) (does|do|is|are)',
                r'does .+ (come|comes) in',
                r'is .+ available in',
                r'can .+ (come|comes) in',
                r'tell me (about|more about)',
                r'what (is|are) .+ (sizes?|colors?|colours?|materials?|features?)',
                r'does .+ have',
                r'what (does|do) .+ (have|come in)',
                r'is .+ (available|in stock)',
                r'how much (does|do|is) .+ (cost|price)',
            ]
            
            # Check if query matches informational patterns
            for pattern in informational_patterns:
                try:
                    if re.search(pattern, query_lower):
                        return True
                except re.error as e:
                    logger.debug(f"Invalid regex pattern {pattern}: {e}")
                    continue
            
            # Check if query starts with informational question words and mentions a specific product
            question_starters = ['what', 'does', 'is', 'can', 'tell me', 'show me']
            if any(query_lower.startswith(starter) for starter in question_starters):
                # If it mentions a specific product name (capitalized words or quoted text), likely informational
                # This is a heuristic - we'll refine based on whether we find a matching product
                return None  # Return None to indicate "maybe, check products first"
            
            return False
        except Exception as e:
            logger.warning(f"Error detecting informational query: {e}")
            return False
    
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
        # Validate inputs
        if not user_query or not isinstance(user_query, str):
            logger.warning("Invalid user_query provided")
            return {
                "response": "Please provide a valid query.",
                "products": [],
                "needs_clarification": False,
                "scores": []
            }
        
        user_query = user_query.strip()
        if not user_query:
            return {
                "response": "Please provide a non-empty query.",
                "products": [],
                "needs_clarification": False,
                "scores": []
            }
        
        # Validate max_results
        try:
            max_results = int(max_results)
            if max_results < 1:
                max_results = 5
            if max_results > 20:
                max_results = 20
        except (ValueError, TypeError):
            max_results = 5
        
        # Validate similarity_threshold
        try:
            similarity_threshold = float(similarity_threshold)
            if similarity_threshold < 0.0:
                similarity_threshold = 0.0
            if similarity_threshold > 1.0:
                similarity_threshold = 1.0
        except (ValueError, TypeError):
            similarity_threshold = 0.6
        
        # Validate conversation_history
        if conversation_history is not None:
            if not isinstance(conversation_history, list):
                logger.warning("Invalid conversation_history type, ignoring")
                conversation_history = None
            else:
                # Filter out invalid messages
                valid_history = []
                for msg in conversation_history:
                    if isinstance(msg, dict) and "role" in msg and "content" in msg:
                        if msg["role"] in ["user", "assistant"] and isinstance(msg["content"], str):
                            valid_history.append(msg)
                conversation_history = valid_history[:50]  # Limit to 50 messages
        
        try:
            if auto_adjust_threshold:
                try:
                    adjusted_threshold = self._calculate_optimal_threshold(user_query)
                    if adjusted_threshold != similarity_threshold:
                        logger.info(f"Adjusted similarity threshold: {similarity_threshold} -> {adjusted_threshold}")
                        similarity_threshold = adjusted_threshold
                except Exception as e:
                    logger.warning(f"Error adjusting threshold: {e}, using default")
            
            logger.info(f"Searching for products matching query: {user_query}")
            try:
                search_results = self.vector_search.search_by_query_text(
                    query_text=user_query,
                    limit=max_results * 2,
                    similarity_threshold=similarity_threshold,
                    enhance_query=True  # Enable query enhancement
                )
            except Exception as e:
                logger.error(f"Error in vector search: {e}", exc_info=True)
                return {
                    "response": "I encountered an error while searching for products. Please try again.",
                    "products": [],
                    "needs_clarification": False,
                    "scores": []
                }
            
            # Validate search_results
            if not isinstance(search_results, list):
                logger.warning("Invalid search_results format")
                search_results = []
            
            # Filter out None products and invalid scores
            valid_results = []
            for result in search_results:
                if isinstance(result, tuple) and len(result) == 2:
                    product, score = result
                    if product is not None:
                        try:
                            score = float(score)
                            if 0.0 <= score <= 1.0:  # Valid similarity score range
                                valid_results.append((product, score))
                        except (ValueError, TypeError):
                            logger.debug(f"Invalid similarity score: {score}")
                            continue
            
            search_results = valid_results
            
            # If we got too few results, try with lower threshold
            if len(search_results) < max_results and similarity_threshold > 0.3:
                logger.info(f"Got {len(search_results)} results, trying with lower threshold")
                try:
                    retry_results = self.vector_search.search_by_query_text(
                        query_text=user_query,
                        limit=max_results * 2,
                        similarity_threshold=max(0.3, similarity_threshold - 0.2),
                        enhance_query=True
                    )
                    # Validate retry results
                    if isinstance(retry_results, list):
                        valid_retry = []
                        for result in retry_results:
                            if isinstance(result, tuple) and len(result) == 2:
                                product, score = result
                                if product is not None:
                                    try:
                                        score = float(score)
                                        if 0.0 <= score <= 1.0:
                                            valid_retry.append((product, score))
                                    except (ValueError, TypeError):
                                        continue
                        if len(valid_retry) > len(search_results):
                            search_results = valid_retry
                except Exception as e:
                    logger.warning(f"Error in retry search: {e}, using original results")
            
            # Parse price query if present
            price_info = self._parse_price_query(user_query)
            
            # Apply price filtering if price constraints are present
            if price_info and (price_info.get("min_price") is not None or price_info.get("max_price") is not None):
                logger.info(f"Applying price filter: min={price_info.get('min_price')}, max={price_info.get('max_price')}")
                search_results = self._filter_by_price(
                    search_results,
                    min_price=price_info.get("min_price"),
                    max_price=price_info.get("max_price")
                )
                # If price filtering removed too many results, try to get more
                if len(search_results) < max_results:
                    logger.info(f"Price filter reduced results to {len(search_results)}, fetching more candidates")
                    try:
                        # Get more candidates with lower threshold
                        additional_results = self.vector_search.search_by_query_text(
                            query_text=user_query,
                            limit=max_results * 3,  # Get more candidates
                            similarity_threshold=max(0.3, similarity_threshold - 0.15),
                            enhance_query=True
                        )
                        # Apply price filter to additional results
                        additional_results = self._filter_by_price(
                            additional_results,
                            min_price=price_info.get("min_price"),
                            max_price=price_info.get("max_price")
                        )
                        # Combine and deduplicate by product ID
                        seen_ids = set()
                        combined_results = []
                        for product, score in search_results:
                            if product and product.id not in seen_ids:
                                seen_ids.add(product.id)
                                combined_results.append((product, score))
                        for product, score in additional_results:
                            if product and product.id not in seen_ids:
                                seen_ids.add(product.id)
                                combined_results.append((product, score))
                        # Sort by score and limit
                        combined_results.sort(key=lambda x: x[1], reverse=True)
                        search_results = combined_results[:max_results * 2]
                    except Exception as e:
                        logger.warning(f"Error fetching additional price-filtered results: {e}")
            
            # Limit to max_results and extract products
            search_results = search_results[:max_results]
            products = [product for product, score in search_results]
            
            # Additional validation: ensure products are valid
            products = [p for p in products if p is not None]
            
            # Check if this is an informational query (asking about specific product details)
            is_informational = self._is_informational_query(user_query)
            
            if not products:
                # No products found - return a helpful message
                # price_info is already parsed above, reuse it
                if price_info and (price_info.get("min_price") is not None or price_info.get("max_price") is not None):
                    # Price filter was applied but no products matched
                    price_msg_parts = []
                    if price_info.get("min_price"):
                        price_msg_parts.append(f"above ₹{price_info['min_price']:.0f}")
                    if price_info.get("max_price"):
                        price_msg_parts.append(f"under ₹{price_info['max_price']:.0f}")
                    price_constraint = " and ".join(price_msg_parts)
                    response_msg = f"I couldn't find any products matching your query with prices {price_constraint}. Could you try adjusting your price range or be more specific about what you're looking for?"
                else:
                    response_msg = "I couldn't find any products matching your query. Could you try rephrasing your request or be more specific about what you're looking for?"
                
                return {
                    "response": response_msg,
                    "products": [],
                    "needs_clarification": False,
                    "scores": []
                }
            
            # For informational queries, we still need products to answer the question
            # but we'll instruct the LLM not to show them as recommendations
            if not self.llm_client:
                # Fallback: return products without LLM interpretation
                logger.warning("LLM not available - returning products without interpretation")
                return {
                    "response": f"I found {len(products)} product(s) that might match your query:",
                    "products": products if not is_informational else [],  # Don't show products for informational queries
                    "needs_clarification": False,
                    "scores": [score for _, score in search_results]
                }
            
            # Build prompt (with special handling for informational queries)
            try:
                prompt = self._build_prompt(user_query, products, conversation_history, is_informational=is_informational)
                if not prompt or not prompt.strip():
                    logger.warning("Empty prompt generated")
                    prompt = f"User query: {user_query}\n\nPlease provide a helpful response."
            except Exception as e:
                logger.error(f"Error building prompt: {e}", exc_info=True)
                prompt = f"User query: {user_query}\n\nPlease provide a helpful response."
            
            logger.info("Generating LLM response...")
            try:
                # Add timeout and retry logic for LLM calls
                max_retries = 2
                retry_delay = 1
                
                for attempt in range(max_retries):
                    try:
                        response = self.llm_client.models.generate_content(
                            model=self.llm_model,
                            contents=prompt
                        )
                        break
                    except Exception as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"LLM call failed (attempt {attempt + 1}), retrying: {e}")
                            time.sleep(retry_delay)
                            retry_delay *= 2
                        else:
                            raise
                
                # Extract response text safely
                if hasattr(response, 'text'):
                    llm_response = str(response.text)
                elif hasattr(response, 'candidates') and response.candidates:
                    # Handle structured response
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        parts = candidate.content.parts
                        if parts:
                            llm_response = str(parts[0].text) if hasattr(parts[0], 'text') else str(parts[0])
                        else:
                            llm_response = str(response)
                    else:
                        llm_response = str(response)
                else:
                    llm_response = str(response)
                
                if not llm_response or not llm_response.strip():
                    logger.warning("Empty LLM response received")
                    llm_response = "I found some products that might match your query."
            except Exception as e:
                logger.error(f"Error calling LLM: {e}", exc_info=True)
                # Fallback response
                if products:
                    llm_response = f"I found {len(products)} product(s) that might match your query."
                else:
                    llm_response = "I couldn't find any products matching your query. Could you try rephrasing your request?"
            
            # Clean response safely
            try:
                cleaned_response = llm_response
                # Apply cleaning patterns one by one with error handling
                cleaning_patterns = [
                    (r'^\s*[-*•]\s*.*?:\s*.*$', '', re.MULTILINE),
                    (r'\*\*.*?\*\*:', '', 0),
                    (r'^.*?Sports Bra.*?:.*$', '', re.MULTILINE | re.IGNORECASE),
                    (r'^.*?Top.*?:.*$', '', re.MULTILINE | re.IGNORECASE),
                    (r'\n{3,}', '\n\n', 0),
                ]
                
                for pattern, replacement, flags in cleaning_patterns:
                    try:
                        cleaned_response = re.sub(pattern, replacement, cleaned_response, flags=flags)
                    except re.error as e:
                        logger.debug(f"Error applying cleaning pattern {pattern}: {e}")
                        continue
                
                cleaned_response = cleaned_response.strip()
            except Exception as e:
                logger.warning(f"Error cleaning response: {e}, using original")
                cleaned_response = llm_response.strip()
            
            # For informational queries, return answer without products
            if is_informational:
                return {
                    "response": cleaned_response.strip(),
                    "products": [],  # Don't show product cards for informational queries
                    "needs_clarification": False,
                    "scores": []
                }
            cleaned_response = cleaned_response.strip()
            
            # If cleaning removed everything, use original
            if not cleaned_response:
                cleaned_response = llm_response.strip()
            
            # Detect clarification requests safely
            try:
                clarification_keywords = [
                    "could you clarify",
                    "can you tell me more",
                    "what do you mean",
                    "could you be more specific",
                    "what are you looking for",
                ]
                response_lower = cleaned_response.lower()
                needs_clarification = (
                    any(keyword in response_lower for keyword in clarification_keywords) 
                    and "?" in cleaned_response
                )
            except Exception as e:
                logger.debug(f"Error detecting clarification: {e}")
                needs_clarification = False
            
            # Return products for discovery queries (informational queries already returned above)
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
        # Validate inputs
        if not products or not isinstance(products, list):
            return "Please provide a valid list of products to compare."
        
        # Filter out None products
        products = [p for p in products if p is not None]
        
        if len(products) < 2:
            return "Please provide at least 2 products to compare."
        
        if len(products) > 4:
            products = products[:4]  # Limit to 4 products
        
        # Remove duplicates based on product ID
        seen_ids = set()
        unique_products = []
        for product in products:
            try:
                product_id = getattr(product, 'id', None)
                if product_id and product_id not in seen_ids:
                    seen_ids.add(product_id)
                    unique_products.append(product)
            except Exception:
                continue
        
        if len(unique_products) < 2:
            return "Please provide at least 2 unique products to compare."
        
        products = unique_products
        
        try:
            if not self.llm_client:
                # Fallback: generate simple comparison
                try:
                    product_titles = []
                    for p in products:
                        if p and hasattr(p, 'title') and p.title:
                            product_titles.append(str(p.title))
                    if product_titles:
                        titles_str = ", ".join(product_titles[:4])
                        return f"Comparing {len(products)} products: {titles_str}. Please enable LLM for detailed insights."
                    else:
                        return f"Comparing {len(products)} products. Please enable LLM for detailed insights."
                except Exception as e:
                    logger.warning(f"Error generating fallback comparison: {e}")
                    return f"Comparing {len(products)} products. Please enable LLM for detailed insights."
            
            # Build comparison prompt
            try:
                product_context = self._format_product_context(products)
                if not product_context or product_context.strip() == "No products found.":
                    return "Unable to generate comparison: product information is missing."
            except Exception as e:
                logger.error(f"Error formatting product context: {e}", exc_info=True)
                return "I'm sorry, I encountered an error while processing the product information."
            
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
            try:
                # Add timeout and retry logic
                max_retries = 2
                retry_delay = 1
                
                for attempt in range(max_retries):
                    try:
                        response = self.llm_client.models.generate_content(
                            model=self.llm_model,
                            contents=prompt
                        )
                        break
                    except Exception as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"LLM call failed (attempt {attempt + 1}), retrying: {e}")
                            time.sleep(retry_delay)
                            retry_delay *= 2
                        else:
                            raise
                
                # Extract response safely
                if hasattr(response, 'text'):
                    insight = str(response.text)
                elif hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        parts = candidate.content.parts
                        if parts:
                            insight = str(parts[0].text) if hasattr(parts[0], 'text') else str(parts[0])
                        else:
                            insight = str(response)
                    else:
                        insight = str(response)
                else:
                    insight = str(response)
                
                if not insight or not insight.strip():
                    return "Unable to generate comparison insight."
                
                # Clean up the response safely
                try:
                    cleaned_insight = re.sub(r'\n{3,}', '\n\n', insight)
                    cleaned_insight = cleaned_insight.strip()
                except Exception as e:
                    logger.debug(f"Error cleaning insight: {e}")
                    cleaned_insight = insight.strip()
                
                return cleaned_insight if cleaned_insight else "Unable to generate comparison insight."
            except Exception as e:
                logger.error(f"Error calling LLM for comparison: {e}", exc_info=True)
                return "I'm sorry, I encountered an error while generating the comparison. Please try again."
            
        except Exception as e:
            logger.error(f"Error generating comparison insight: {e}", exc_info=True)
            return "I'm sorry, I encountered an error while generating the comparison. Please try again."

    def generate_follow_ups(
        self,
        user_query: str,
        assistant_response: str,
        products: List[Product],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> List[str]:
        """
        Generate AI-based follow-up suggestions based on user's previous message and context.
        
        Args:
            user_query: User's previous message/query
            assistant_response: Assistant's response to the user
            products: List of products returned (if any)
            conversation_history: Previous conversation messages for context
        
        Returns:
            List of suggested follow-up questions (3-5 suggestions)
        """
        # Validate inputs
        if not user_query or not isinstance(user_query, str):
            user_query = ""
        if not assistant_response or not isinstance(assistant_response, str):
            assistant_response = ""
        if not products or not isinstance(products, list):
            products = []
        if conversation_history is not None and not isinstance(conversation_history, list):
            conversation_history = None
        
        try:
            if not self.llm_client:
                # Fallback: return simple product-based suggestions
                logger.warning("LLM not available - returning simple follow-up suggestions")
                follow_ups = []
                # Filter out None products
                valid_products = [p for p in products if p is not None]
                if valid_products:
                    try:
                        first_product = valid_products[0]
                        if first_product and hasattr(first_product, 'title') and first_product.title:
                            title = str(first_product.title)
                            if len(title) < 50:  # Avoid overly long titles
                                follow_ups.append(f"Tell me more about {title}")
                    except Exception as e:
                        logger.debug(f"Error processing first product: {e}")
                    
                    if len(valid_products) > 1:
                        follow_ups.append(f"Compare these {len(valid_products)} products")
                    follow_ups.append("Show me similar products")
                follow_ups.append("What are the best alternatives?")
                return follow_ups[:5]
            
            # Build prompt for follow-up generation
            product_context = ""
            try:
                valid_products = [p for p in products if p is not None]
                if valid_products:
                    product_context = f"\n\nProducts found: {len(valid_products)} product(s)"
                    try:
                        first_product = valid_products[0]
                        if first_product and hasattr(first_product, 'title') and first_product.title:
                            title = str(first_product.title)
                            if len(title) > 100:
                                title = title[:100] + "..."
                            product_context += f"\nFirst product: {title}"
                    except Exception:
                        pass
            except Exception as e:
                logger.debug(f"Error building product context: {e}")
            
            conversation_context = ""
            if conversation_history:
                try:
                    # Filter valid messages
                    valid_history = []
                    for msg in conversation_history:
                        if isinstance(msg, dict) and "role" in msg and "content" in msg:
                            if msg["role"] in ["user", "assistant"] and isinstance(msg["content"], str):
                                valid_history.append(msg)
                    
                    # Include last 3 messages for context
                    recent_history = valid_history[-3:]
                    if recent_history:
                        conversation_context = "\n\nRecent conversation:\n" + "\n".join([
                            f"{'User' if msg['role'] == 'user' else 'Assistant'}: {str(msg['content'])[:100]}"
                            for msg in recent_history
                        ])
                except Exception as e:
                    logger.debug(f"Error building conversation context: {e}")
            
            system_prompt = """You are generating clickable follow-up question suggestions for a product recommendation chat.

CRITICAL UNDERSTANDING:
- These are SUGGESTIONS for what the USER can click/ask next
- These are NOT questions the AI assistant would ask the user
- These are questions the USER would type or click to continue exploring
- Think of these as "quick reply" buttons the user can click

Your task is to generate 3-5 natural follow-up questions that:
1. The USER can click/ask to explore products further
2. Are directly relevant to what the user just asked about
3. Help the user refine their search or learn more about products
4. Are concise (under 12 words each)
5. Sound natural and conversational

IMPORTANT GUIDELINES:
- These are USER questions that the user would ask, NOT assistant questions
- DO NOT generate questions asking the user for information (like "What kind of event?" or "What's your budget?")
- DO generate questions the user would ask to explore products (like "Show me more options" or "What are the best sellers?")
- Base questions on the USER'S query and what they might want to explore next
- If products were shown, questions can reference exploring those products further
- Questions should help users explore, compare, or refine their product search

WRONG EXAMPLES (these are assistant asking user - DO NOT GENERATE THESE):
- "What kind of formal event is it?" ❌ (assistant asking user)
- "What is the dress code?" ❌ (assistant asking user)
- "What's your budget?" ❌ (assistant asking user)
- "Do you need shoes or accessories?" ❌ (assistant asking user)
- "Are you looking for a dress?" ❌ (assistant asking user)

CORRECT EXAMPLES (these are user asking about products - GENERATE THESE):
- "Show me more formal options" ✅ (user exploring)
- "What are the best sellers?" ✅ (user asking about products)
- "Can you show me different colors?" ✅ (user exploring)
- "What sizes are available?" ✅ (user asking about products)
- "Show me similar products" ✅ (user exploring)
- "Compare these products" ✅ (user exploring)
- "What are the best alternatives?" ✅ (user exploring)

Format: Return ONLY a simple list, one question per line, no numbering, no bullets, no extra formatting.
Each line should be a complete, natural question that the USER would click/ask next.
"""
            
            # Safely truncate inputs
            safe_user_query = str(user_query)[:500] if user_query else ""
            safe_assistant_response = str(assistant_response)[:300] if assistant_response else ""
            
            user_prompt = f"""User's previous message: "{safe_user_query}"

Assistant's response: "{safe_assistant_response}"{product_context}{conversation_context}

Generate 3-5 clickable follow-up question suggestions that the USER can click/ask next.

These are suggestions for what the USER would type or click to continue exploring products. These are NOT questions the assistant would ask the user.

Think of these as "quick reply" buttons - what would the user want to ask next to explore products?

Examples of good user follow-up questions (what user would ask):
- "Show me more [category/style] options"
- "What are the best sellers?"
- "Can you show me different colors/sizes?"
- "Show me similar products"
- "Compare these products"
- "What are the best alternatives?"
- "Show me more casual options"
- "What's the price range?"

Remember: These are questions the USER asks about products, NOT questions asking the user for information."""
            
            prompt = system_prompt + "\n\n" + user_prompt
            
            logger.info("Generating AI follow-up suggestions...")
            try:
                # Add timeout and retry logic
                max_retries = 2
                retry_delay = 1
                
                for attempt in range(max_retries):
                    try:
                        response = self.llm_client.models.generate_content(
                            model=self.llm_model,
                            contents=prompt
                        )
                        break
                    except Exception as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"LLM call failed (attempt {attempt + 1}), retrying: {e}")
                            time.sleep(retry_delay)
                            retry_delay *= 2
                        else:
                            raise
                
                # Extract response safely
                if hasattr(response, 'text'):
                    follow_ups_text = str(response.text)
                elif hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        parts = candidate.content.parts
                        if parts:
                            follow_ups_text = str(parts[0].text) if hasattr(parts[0], 'text') else str(parts[0])
                        else:
                            follow_ups_text = str(response)
                    else:
                        follow_ups_text = str(response)
                else:
                    follow_ups_text = str(response)
            except Exception as e:
                logger.error(f"Error calling LLM for follow-ups: {e}", exc_info=True)
                # Return fallback suggestions
                follow_ups = []
                valid_products = [p for p in products if p is not None]
                if valid_products:
                    follow_ups.append("Tell me more about these products")
                    if len(valid_products) > 1:
                        follow_ups.append(f"Compare these {len(valid_products)} products")
                follow_ups.extend([
                    "Show me more options",
                    "What are the best alternatives?"
                ])
                return follow_ups[:5]
            
            # Parse the response into a list of follow-ups
            # Split by newlines and clean up
            follow_ups = []
            # Keywords that indicate the question is asking the user for information (bad)
            user_info_keywords = [
                'what kind of', 'what is your', 'what\'s your', 'what are your',
                'do you need', 'do you want', 'are you looking for', 'are you',
                'what do you', 'what would you', 'how much is your', 'what\'s the',
                'tell me about', 'can you tell me', 'could you tell me'
            ]
            
            for line in follow_ups_text.split('\n'):
                line = line.strip()
                # Remove numbering, bullets, dashes, etc.
                line = re.sub(r'^[\d\-\*•\.\)\s]+', '', line)
                line = line.strip()
                # Remove quotes if present
                line = line.strip('"\'')
                
                if line and len(line) > 5 and len(line) < 100:  # Reasonable length
                    line_lower = line.lower()
                    # Filter out questions that are asking the user for information
                    is_user_info_question = any(keyword in line_lower for keyword in user_info_keywords)
                    # Also check if it starts with these patterns
                    if line_lower.startswith(('what kind', 'what is', 'what\'s', 'do you', 'are you', 'tell me')):
                        # But allow questions like "What are the best sellers?" (user asking about products)
                        if not any(good_pattern in line_lower for good_pattern in ['best', 'available', 'show me', 'compare', 'similar', 'alternatives', 'options', 'colors', 'sizes', 'price']):
                            is_user_info_question = True
                    
                    if not is_user_info_question:
                        follow_ups.append(line)
            
            # Limit to 5 and ensure we have at least 3
            follow_ups = follow_ups[:5]
            
            # If we got fewer than 3, add some fallback suggestions
            if len(follow_ups) < 3:
                fallbacks = [
                    "Show me more options",
                    "What are the best alternatives?",
                    "Tell me more about these products"
                ]
                for fallback in fallbacks:
                    if fallback not in follow_ups and len(follow_ups) < 5:
                        follow_ups.append(fallback)
            
            return follow_ups[:5]
            
        except Exception as e:
            logger.error(f"Error generating follow-ups: {e}", exc_info=True)
            # Return fallback suggestions
            follow_ups = []
            if products and len(products) > 0:
                follow_ups.append("Tell me more about these products")
                if len(products) > 1:
                    follow_ups.append(f"Compare these {len(products)} products")
            follow_ups.extend([
                "Show me more options",
                "What are the best alternatives?"
            ])
            return follow_ups[:5]

