"""Chat router for RAG-based product recommendations."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.rag import RAGService
from app.schemas.chat import ChatRequest, ChatResponse, ProductRecommendation
from app.schemas.products.hunnit.schemas import DBProduct
from app.config.database import get_db
from app.utils.logger import get_logger

logger = get_logger("chat_router")

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
) -> ChatResponse:
    """
    Chat endpoint for product recommendations using RAG.
    
    Handles natural language queries and returns product recommendations
    with explanations using vector search and LLM.
    
    Args:
        request: Chat request with message and optional conversation history
        db: Database session
    
    Returns:
        ChatResponse with LLM-generated response and recommended products
    """
    try:
        # Validation is handled by Pydantic, but add extra safety checks
        if not request.message or not request.message.strip():
            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty"
            )
        
        # Validate conversation history if provided
        if request.conversation_history:
            if len(request.conversation_history) > 50:
                raise HTTPException(
                    status_code=400,
                    detail="Conversation history is too long (max 50 messages)"
                )
            # Validate each message structure
            for i, msg in enumerate(request.conversation_history):
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
            user_query=request.message,
            max_results=request.max_results,
            similarity_threshold=request.similarity_threshold,
            conversation_history=request.conversation_history
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
        
        return ChatResponse(
            response=result.get("response", "I'm sorry, I couldn't process your request."),
            products=db_products,
            needs_clarification=result.get("needs_clarification", False),
            recommendations=recommendations
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

