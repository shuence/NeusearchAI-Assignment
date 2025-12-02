# Neusearch Backend API

FastAPI backend application with RAG (Retrieval-Augmented Generation) capabilities for intelligent product search and recommendations.

## Overview

The backend provides a RESTful API for product search, chat-based recommendations, and product management. It uses PostgreSQL with pgvector for vector search, Redis for caching, and Google Gemini API for embeddings and LLM responses.

## Tech Stack

- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL with pgvector extension
- **Cache**: Redis 5.0.1
- **ORM**: SQLAlchemy 2.0.23
- **Migrations**: Alembic 1.12.1
- **AI/ML**: Google Gemini API (Embeddings & LLM)
- **Scheduler**: APScheduler 3.10.4
- **HTTP Client**: httpx 0.25.2
- **Validation**: Pydantic 2.5.0
- **Rate Limiting**: slowapi 0.1.9
- **Logging**: structlog 23.2.0

## Project Structure

``` bash
backend/
├── app/
│   ├── config/          # Configuration files
│   │   ├── database.py   # Database connection & session management
│   │   ├── redis.py      # Redis client configuration
│   │   └── settings.py   # Application settings (Pydantic)
│   ├── constants.py      # Application constants
│   ├── controller/       # Request controllers
│   │   ├── health_controller.py
│   │   └── products/
│   │       └── hunnit/
│   │           └── controller.py
│   ├── docs/            # API documentation
│   │   └── scalar.py    # Scalar API docs setup
│   ├── middleware/      # Custom middleware
│   │   ├── metrics.py   # Performance metrics
│   │   ├── rate_limit.py # Rate limiting
│   │   └── validation.py # Request validation & error handling
│   ├── models/          # SQLAlchemy models
│   │   └── product.py   # Product data model
│   ├── rag/             # RAG implementation
│   │   ├── embedding_service.py    # Embedding generation
│   │   ├── generate_embeddings.py   # Batch embedding generation
│   │   ├── query_enhancement.py     # Query processing
│   │   ├── rag_service.py           # Main RAG orchestration
│   │   └── vector_search.py         # Vector similarity search
│   ├── routers/         # API route handlers
│   │   ├── health.py
│   │   ├── chat.py      # Chat/RAG endpoints
│   │   └── products/
│   │       └── hunnit/
│   │           └── router.py
│   ├── schemas/         # Pydantic schemas
│   │   ├── common.py
│   │   ├── health.py
│   │   ├── chat.py
│   │   └── products/
│   │       └── hunnit/
│   │           └── schemas.py
│   ├── scrapers/        # Web scrapers
│   ├── services/        # Business logic services
│   │   ├── email_service.py         # Email notifications
│   │   ├── generate_ai_features.py  # AI feature generation
│   │   ├── health_service.py
│   │   ├── scheduler.py             # Background job scheduler
│   │   ├── startup_sync.py          # Initial product sync
│   │   └── products/
│   │       └── hunnit/
│   │           ├── db_service.py    # Database operations
│   │           ├── redis_service.py # Redis caching
│   │           └── service.py       # Product service
│   ├── types/           # Type definitions
│   └── utils/           # Utility functions
│       ├── api_response.py  # Standardized API responses
│       ├── env_validation.py # Environment variable validation
│       └── logger.py         # Logging setup
├── alembic/             # Database migrations
│   ├── env.py
│   └── versions/        # Migration files
├── scripts/             # Utility scripts
│   └── init-pgvector.sql # pgvector initialization
├── tests/               # Test files
│   ├── conftest.py      # Pytest configuration
│   ├── test_chat.py
│   ├── test_email_service.py
│   ├── test_health.py
│   ├── test_products.py
│   └── test_rate_limiting.py
├── logs/                # Application logs
├── main.py              # FastAPI application entry point
├── requirements.txt     # Python dependencies
├── pytest.ini          # Pytest configuration
└── Dockerfile          # Docker configuration
```

## Prerequisites

- Python 3.9+
- PostgreSQL 12+ with pgvector extension
- Redis 6+
- Google Gemini API key (for RAG features)

## Setup

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Application
ENVIRONMENT=development
APP_NAME=Neusearch API
APP_VERSION=1.0.0

# Database
DATABASE_URL=postgresql://neusearch:neusearch@localhost:5432/neusearch

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Gemini API (required for RAG)
GEMINI_API_KEY=your_gemini_api_key_here

# Scraping
SCRAPE_INTERVAL_HOURS=6
SYNC_ON_STARTUP=true

# CORS
CORS_ORIGINS=["http://localhost:3000"]
CORS_ALLOW_CREDENTIALS=true

# Email (optional, for error notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=your_email@gmail.com
SMTP_TO=admin@example.com
```

### 4. Database Setup

#### Install pgvector Extension

```bash
# Connect to PostgreSQL
psql -U neusearch -d neusearch

# Run the initialization script
\i scripts/init-pgvector.sql
```

Or use the SQL script directly:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

#### Run Migrations

```bash
alembic upgrade head
```

### 5. Start the Server

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, access the API documentation:

- **Scalar API Docs**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>
- **OpenAPI JSON**: <http://localhost:8000/openapi.json>

## Key Endpoints

### Health Check

- `GET /api/health` - Health check endpoint

### Products

- `GET /api/products/hunnit` - List all products (with pagination, filtering, sorting)
- `GET /api/products/hunnit/{id}` - Get product by ID
- `POST /api/products/hunnit/scrape` - Trigger product scraping manually

### Chat (RAG)

- `POST /api/chat` - Chat endpoint for product recommendations
  - Request body: `{ "message": "user query", "conversation_history": [...] }`
  - Returns: `{ "response": "...", "products": [...], "suggested_questions": [...] }`
- `POST /api/chat/compare` - Compare multiple products with AI insights
  - Request body: `{ "product_ids": [1, 2, 3] }`
  - Returns: `{ "comparison": "...", "products": [...] }`

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_chat.py
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Code Structure

The application follows a layered architecture:

1. **Routers** (`app/routers/`) - Handle HTTP requests/responses
2. **Controllers** (`app/controller/`) - Business logic coordination
3. **Services** (`app/services/`) - Core business logic
4. **Models** (`app/models/`) - Database models
5. **Schemas** (`app/schemas/`) - Request/response validation

## Features

### RAG (Retrieval-Augmented Generation)

The RAG pipeline provides intelligent product search:

1. **Query Embedding**: User query is converted to a vector using Gemini Embedding API
2. **Vector Search**: Similar products are found using pgvector cosine similarity
3. **Context Building**: Top products are formatted with metadata
4. **LLM Response**: Gemini 2.0 Flash generates conversational response
5. **Post-processing**: Response is cleaned and formatted

**Key Components:**

- `embedding_service.py`: Generates embeddings for queries and products
- `vector_search.py`: Performs semantic search using pgvector
- `rag_service.py`: Orchestrates the full RAG pipeline
- `query_enhancement.py`: Enhances queries for better results

### Product Scraping

Automated product synchronization from Hunnit.com:

- **Source**: JSON API endpoint (`https://hunnit.com/products.json`)
- **Schedule**: Every 6 hours (configurable)
- **Startup Sync**: Checks if database has minimum products on startup
- **Embedding Generation**: Automatically generates embeddings for new products

### Caching

Redis caching for improved performance:

- Product listings cached with TTL
- Reduces database load
- Faster response times

### Rate Limiting

API endpoints are protected with rate limiting:

- Configurable limits per endpoint
- Returns 429 status when exceeded
- Uses slowapi library

### Error Handling

Comprehensive error handling:

- Structured error responses
- Email notifications for critical errors (production)
- Detailed logging with structlog

### Metrics

Performance metrics tracking:

- Request duration
- Response status codes
- Custom metrics via middleware

## Configuration

### Settings

All configuration is managed through `app/config/settings.py` using Pydantic Settings:

- Environment variable loading
- Type validation
- Default values
- Documentation

### Logging

Structured logging with structlog:

- JSON format in production
- Human-readable in development
- Log files in `logs/` directory
- Separate error log file

## Docker

### Build Image

```bash
docker build -t neusearch-backend .
```

### Run Container

```bash
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://neusearch:neusearch@postgres:5432/neusearch \
  -e GEMINI_API_KEY=your_key \
  neusearch-backend
```

### Docker Compose

See the root `docker-compose.local.yml` for full stack setup.

## Production Deployment

### Environment Variables

Ensure all required environment variables are set:

- `DATABASE_URL`: PostgreSQL connection string
- `GEMINI_API_KEY`: Google Gemini API key
- `REDIS_HOST`, `REDIS_PORT`: Redis configuration
- `ENVIRONMENT=production`: Set to production mode

### Database

1. Ensure pgvector extension is installed
2. Run migrations: `alembic upgrade head`
3. Verify database connection

### Monitoring

- Check logs in `logs/` directory
- Monitor API health endpoint
- Set up email notifications for errors
- Monitor Redis and PostgreSQL connections

## Troubleshooting

### Database Connection Issues

- Verify `DATABASE_URL` is correct
- Check PostgreSQL is running
- Ensure pgvector extension is installed
- Check network connectivity

### Redis Connection Issues

- Verify Redis is running
- Check `REDIS_HOST` and `REDIS_PORT`
- Application will continue without Redis (caching disabled)

### Embedding Generation Fails

- Verify `GEMINI_API_KEY` is set correctly
- Check API quota/limits
- Review error logs

### Migration Errors

- Ensure database is accessible
- Check migration files are in correct order
- Verify pgvector extension is installed before running migrations

## Testing

### Test Structure

- `conftest.py`: Pytest fixtures and configuration
- `test_*.py`: Test files for each module

### Running Tests

```bash
# All tests
pytest

# Specific test
pytest tests/test_chat.py::test_chat_endpoint

# With verbose output
pytest -v

# With coverage
pytest --cov=app --cov-report=term-missing
```

## Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation
4. Follow Python style guidelines (PEP 8)
5. Use type hints where possible

## License

See root README.md for license information.
