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
        if not request.message or not request.message.strip():
            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty"
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
        
        # Convert products to DBProduct schema
        db_products = [
            DBProduct.model_validate(product) 
            for product in result["products"]
        ]
        
        # Create recommendations with scores
        recommendations = None
        if result["products"] and result["scores"]:
            recommendations = [
                ProductRecommendation(
                    product=DBProduct.model_validate(product),
                    similarity_score=score
                )
                for product, score in zip(result["products"], result["scores"])
            ]
        
        return ChatResponse(
            response=result["response"],
            products=db_products,
            needs_clarification=result["needs_clarification"],
            recommendations=recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
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

