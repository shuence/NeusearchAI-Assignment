"""Chat router for RAG-based product recommendations."""
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from app.rag import RAGService
from app.schemas.chat import ChatRequest, ChatResponse, ProductRecommendation, CompareRequest, CompareResponse
from app.schemas.products.hunnit.schemas import DBProduct
from app.config.database import get_db
from app.utils.logger import get_logger
from app.middleware.rate_limit import limiter

logger = get_logger("chat_router")

router = APIRouter()


@router.post("", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat(
    request: Request,
    chat_request: ChatRequest,
    db: Session = Depends(get_db)
) -> ChatResponse:
    """
    Chat endpoint for product recommendations using RAG.
    
    Handles natural language queries and returns product recommendations
    with explanations using vector search and LLM.
    
    Args:
        chat_request: Chat request with message and optional conversation history
        db: Database session
    
    Returns:
        ChatResponse with LLM-generated response and recommended products
    """
    try:
        # Validation is handled by Pydantic, but add extra safety checks
        if not chat_request.message or not chat_request.message.strip():
            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty"
            )
        
        # Validate conversation history if provided
        if chat_request.conversation_history:
            if len(chat_request.conversation_history) > 50:
                raise HTTPException(
                    status_code=400,
                    detail="Conversation history is too long (max 50 messages)"
                )
            # Validate each message structure
            for i, msg in enumerate(chat_request.conversation_history):
                if not isinstance(msg, dict):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid message format at index {i}: must be a dictionary"
                    )
                if "role" not in msg or "content" not in msg:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid message at index {i}: missing 'role' or 'content' field"
                    )
        
        # Initialize RAG service
        rag_service = RAGService(db)
        
        # Get recommendations
        result = rag_service.recommend_products(
            user_query=chat_request.message,
            max_results=chat_request.max_results,
            similarity_threshold=chat_request.similarity_threshold,
            conversation_history=chat_request.conversation_history
        )
        
        # Validate result structure
        if not isinstance(result, dict):
            logger.error("RAG service returned invalid result format")
            raise HTTPException(
                status_code=500,
                detail="Invalid response from recommendation service"
            )
        
        # Convert products to DBProduct schema with error handling
        db_products = []
        for product in result.get("products", []):
            try:
                db_products.append(DBProduct.model_validate(product))
            except Exception as e:
                logger.warning(f"Failed to validate product: {e}")
                continue
        
        # Create recommendations with scores
        recommendations = None
        products = result.get("products", [])
        scores = result.get("scores", [])
        
        if products and scores and len(products) == len(scores):
            try:
                recommendations = [
                    ProductRecommendation(
                        product=DBProduct.model_validate(product),
                        similarity_score=score
                    )
                    for product, score in zip(products, scores)
                ]
            except Exception as e:
                logger.warning(f"Failed to create recommendations: {e}")
                # Continue without recommendations
        
        # Generate AI-based follow-up suggestions
        suggested_follow_ups = None
        try:
            assistant_response = result.get("response", "")
            suggested_follow_ups = rag_service.generate_follow_ups(
                user_query=chat_request.message,
                assistant_response=assistant_response,
                products=products,
                conversation_history=chat_request.conversation_history
            )
            # Only include if we got valid follow-ups
            if not suggested_follow_ups or len(suggested_follow_ups) == 0:
                suggested_follow_ups = None
        except Exception as e:
            logger.warning(f"Failed to generate follow-ups: {e}")
            # Continue without follow-ups - not critical
        
        return ChatResponse(
            response=result.get("response", "I'm sorry, I couldn't process your request."),
            products=db_products,
            needs_clarification=result.get("needs_clarification", False),
            recommendations=recommendations,
            suggested_follow_ups=suggested_follow_ups
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        # Handle validation errors
        logger.warning(f"Validation error in chat endpoint: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request. Please try again."
        )


@router.post("/compare", response_model=CompareResponse)
@limiter.limit("10/minute")
async def compare_products(
    request: Request,
    compare_request: CompareRequest,
    db: Session = Depends(get_db)
) -> CompareResponse:
    """
    Compare products and generate AI insights.
    
    Takes a list of product IDs (2-4 products) and returns AI-generated
    comparison insights without asking questions.
    
    Args:
        compare_request: Compare request with product IDs
        db: Database session
    
    Returns:
        CompareResponse with AI-generated insight and product details
    """
    try:
        # Validate product IDs
        if not compare_request.product_ids or len(compare_request.product_ids) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 product IDs are required for comparison"
            )
        
        if len(compare_request.product_ids) > 4:
            raise HTTPException(
                status_code=400,
                detail="Maximum 4 products can be compared"
            )
        
        # Fetch products from database
        from app.models.product import Product
        
        products = []
        for product_id in compare_request.product_ids:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product with ID {product_id} not found"
                )
            products.append(product)
        
        # Initialize RAG service
        rag_service = RAGService(db)
        
        # Generate comparison insight
        insight = rag_service.compare_products(products)
        
        # Convert products to DBProduct schema
        db_products = []
        for product in products:
            try:
                db_products.append(DBProduct.model_validate(product))
            except Exception as e:
                logger.warning(f"Failed to validate product: {e}")
                continue
        
        return CompareResponse(
            insight=insight,
            products=db_products
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in compare endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while comparing products. Please try again."
        )


@router.get("/health")
async def chat_health(db: Session = Depends(get_db)) -> dict:
    """Check if chat/RAG service is available."""
    try:
        from app.rag.vector_search import VectorSearchService
        
        vector_search = VectorSearchService(db)
        products_with_embeddings = vector_search.get_products_with_embeddings_count()
        
        return {
            "status": "healthy",
            "products_with_embeddings": products_with_embeddings,
            "rag_available": True
        }
    except Exception as e:
        logger.error(f"Error checking chat health: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "rag_available": False
        }

