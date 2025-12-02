"""Environment variable validation utility."""
from typing import List, Tuple
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger("env_validation")


class EnvValidationError(Exception):
    """Exception raised when environment variable validation fails."""
    pass


def validate_environment_variables() -> Tuple[bool, List[str]]:
    """
    Validate required environment variables.
    
    Returns:
        Tuple of (is_valid, list_of_missing_vars)
    """
    missing_vars = []
    warnings = []
    
    # Required for production
    if settings.ENVIRONMENT == "production":
        if not settings.DATABASE_URL:
            missing_vars.append("DATABASE_URL")
    else:
        # Development: warn if using defaults
        if settings.DATABASE_URL == "postgresql://neusearch:neusearch@localhost:5432/neusearch":
            warnings.append("Using default DATABASE_URL. Set DATABASE_URL for production.")
    
    # Optional but recommended
    if not settings.GEMINI_API_KEY:
        warnings.append("GEMINI_API_KEY not set. RAG features will be limited.")
    
    # Redis is optional (caching)
    # No validation needed as it's optional
    
    return len(missing_vars) == 0, missing_vars, warnings


def validate_and_log() -> None:
    """Validate environment variables and log results."""
    is_valid, missing_vars, warnings = validate_environment_variables()
    
    if warnings:
        for warning in warnings:
            logger.warning(f"Environment variable warning: {warning}")
    
    if not is_valid:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        if settings.ENVIRONMENT == "production":
            raise EnvValidationError(error_msg)
        else:
            logger.warning(f"Continuing in {settings.ENVIRONMENT} mode despite missing variables")
    else:
        logger.info("Environment variable validation passed")

