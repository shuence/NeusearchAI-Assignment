# Neusearch AI

A full-stack search application with RAG (Retrieval-Augmented Generation) capabilities.

## Project Structure

``` bash
Neusearch/
├── backend/          # Python backend API
│   ├── app/          # Application code
│   │   ├── models/   # Data models
│   │   ├── rag/      # RAG implementation
│   │   ├── routers/  # API routes
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── scrapers/ # Web scrapers
│   │   └── utils/    # Utility functions
│   ├── scripts/      # Utility scripts
│   └── tests/        # Test files
└── frontend/         # Next.js frontend application
    ├── src/
    │   ├── app/      # Next.js App Router
    │   │   ├── layout.tsx
    │   │   ├── page.tsx          # Home page
    │   │   ├── globals.css
    │   │   ├── products/
    │   │   │   └── [id]/
    │   │   │       └── page.tsx   # Product detail page
    │   │   ├── chat/
    │   │   │   └── page.tsx       # Chat interface
    │   │   ├── compare/
    │   │   │   └── page.tsx       # Product comparison page
    │   │   ├── cart/
    │   │   │   └── page.tsx       # Shopping cart page
    │   │   ├── checkout/
    │   │   │   └── page.tsx       # Checkout page
    │   │   ├── orders/
    │   │   │   ├── page.tsx       # Order history page
    │   │   │   └── [id]/
    │   │   │       └── page.tsx   # Order detail page
    │   │   ├── order-success/
    │   │   │   └── page.tsx       # Order confirmation page
    │   │   └── not-found.tsx      # 404 page
    │   ├── components/
    │   │   ├── ui/                # shadcn/ui components
    │   │   ├── layout/            # Layout components (header, footer)
    │   │   └── features/          # Feature-specific components
    │   │       ├── products/      # Product-related components
    │   │       └── chat/          # Chat components
    │   ├── contexts/              # React contexts
    │   │   ├── cart-context.tsx   # Shopping cart state
    │   │   ├── comparison-context.tsx  # Product comparison state
    │   │   └── order-context.tsx   # Order management state
    │   ├── lib/
    │   │   ├── utils.ts           # Utility functions
    │   │   ├── constants.ts       # App constants
    │   │   └── api/               # API client functions
    │   ├── types/                 # TypeScript type definitions
    │   └── data/                  # Dummy/mock data
    │       └── products.ts        # Product dummy data
    ├── public/       # Static assets
    ├── components.json  # shadcn/ui configuration
    ├── next.config.ts
    ├── tailwind.config.ts
    ├── tsconfig.json
    ├── package.json
    └── pnpm-lock.yaml
```

## Prerequisites

- Python 3.9+
- Node.js 18+ (for frontend)
- pnpm (package manager)

## Setup

### Backend

1. Navigate to the backend directory:

```bash
cd backend
```

2. Create a virtual environment:

```bash
python3 -m venv venv
```

3. Activate the virtual environment:

```bash
# On macOS/Linux
source venv/bin/activate

# On Windows
venv\Scripts\activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Set up environment variables:

```bash
# Copy the example env file to backend/.env
cp .env.example backend/.env

# Or create backend/.env manually with database configuration
# Edit backend/.env with your configuration, especially DATABASE_URL
```

**Important**: Make sure to set the `DATABASE_URL` in your `backend/.env` file:

- For local development: `postgresql://neusearch:neusearch@localhost:5432/neusearch`
- For Docker Compose: `postgresql://neusearch:neusearch@postgres:5432/neusearch`

### Frontend (Next.js)

1. Navigate to the frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
pnpm install
```

3. Set up environment variables:

```bash
# Copy the example env file to frontend/.env.local
cp .env.example frontend/.env.local

# Or create frontend/.env.local manually
# Edit frontend/.env.local with your configuration
```

## Local Development with Docker

The easiest way to set up the development environment is using Docker Compose. This will start all services (frontend, backend, PostgreSQL with pgvector, and Redis) with hot-reloading enabled.

### Prerequisites

- Docker and Docker Compose installed
- `.env` file in the root directory (for Docker Compose)
- `backend/.env` file with required configuration (for local development)

### Quick Start

1. **Create a `.env` file in the root directory** (for Docker Compose):

```bash
# Copy the example env file from root
cp .env.example .env


**Note**: Docker Compose reads the `.env` file from the root directory. Make sure to create `.env` in the project root (same directory as `docker-compose.local.yml`).

2. **Start all services**:

```bash
docker-compose -f docker-compose.local.yml up
```

This will start:

- **Frontend** on <http://localhost:3000> (with hot-reloading)
- **Backend API** on <http://localhost:8000> (with auto-reload)
- **PostgreSQL** on localhost:5433 (with pgvector extension)
- **Redis** on localhost:6379

3. **Run database migrations** (first time only):

```bash
# Execute migrations inside the backend container
docker-compose -f docker-compose.local.yml exec backend alembic upgrade head
```

### Docker Compose Commands

```bash
# Start all services in detached mode
docker-compose -f docker-compose.local.yml up -d

# View logs from all services
docker-compose -f docker-compose.local.yml logs -f

# View logs from a specific service
docker-compose -f docker-compose.local.yml logs -f backend
docker-compose -f docker-compose.local.yml logs -f frontend

# Stop all services
docker-compose -f docker-compose.local.yml down

# Stop and remove volumes (clean slate)
docker-compose -f docker-compose.local.yml down -v

# Rebuild services after dependency changes
docker-compose -f docker-compose.local.yml up --build

# Execute commands in a running container
docker-compose -f docker-compose.local.yml exec backend bash
docker-compose -f docker-compose.local.yml exec frontend sh
```

### Services Overview

- **Frontend** (`neusearch-frontend-local`): Next.js development server with hot-reloading
- **Backend** (`neusearch-backend-local`): FastAPI server with auto-reload on code changes
- **PostgreSQL** (`neusearch-postgres-local`): Database with pgvector extension for vector search
- **Redis** (`neusearch-redis-local`): Cache for product data

### Hot Reloading

Both frontend and backend support hot-reloading:

- **Frontend**: Changes to files in `frontend/` will automatically trigger Next.js hot reload
- **Backend**: Changes to Python files in `backend/` will automatically restart the FastAPI server

### Database Access

To connect to PostgreSQL from your host machine:

```bash
# Using psql
psql -h localhost -p 5433 -U neusearch -d neusearch

# Or using Docker
docker-compose -f docker-compose.local.yml exec postgres psql -U neusearch -d neusearch
```

### Redis Access

To access Redis CLI:

```bash
docker-compose -f docker-compose.local.yml exec redis redis-cli
```

### Troubleshooting

**Port conflicts**: If ports 3000, 8000, 5433, or 6379 are already in use, you can modify the port mappings in `docker-compose.local.yml`.

**Services not starting**: Check logs with `docker-compose -f docker-compose.local.yml logs` to see error messages.

**Database connection issues**: Ensure the `DATABASE_URL` in your root `.env` file (for Docker) uses `postgres` as the hostname (Docker service name), not `localhost`.

**Frontend can't reach backend**: The frontend uses `http://localhost:8000` for client-side requests and `http://backend:8000` for server-side requests (SSR).

## Development

### Running the Backend

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start PostgreSQL (if using Docker Compose)
docker-compose up -d postgres

# Run database migrations (first time setup)
alembic upgrade head

# Run your backend server
uvicorn main:app --reload
```

### Running the Frontend

Navigate to the frontend directory and run:

```bash
cd frontend
pnpm dev
```

The Next.js development server will start on `http://localhost:3000` by default.

#### Available Frontend Commands

- **Development server**: `pnpm dev` - Starts the Next.js development server with hot reload
- **Production build**: `pnpm build` - Creates an optimized production build
- **Start production server**: `pnpm start` - Runs the production server (requires build first)
- **Lint code**: `pnpm lint` - Runs Biome linter to check for code issues
- **Format code**: `pnpm format` - Formats code using Biome formatter

## UI Components

This project uses [shadcn/ui](https://ui.shadcn.com/) for UI components built on top of Radix UI and Tailwind CSS.

### Adding Components

To add a new shadcn/ui component, you can use the CLI:

```bash
cd frontend
npx shadcn@latest add [component-name]
```

For example:

```bash
npx shadcn@latest add button
npx shadcn@latest add card
npx shadcn@latest add dialog
```

Components will be added to `src/components/ui/` and can be imported like:

```tsx
import { Button } from "@/components/ui/button";
```

### Available Components

The following shadcn/ui components are already included:

- **Button** - Interactive button component
- **Card** - Container component for content sections
- **Badge** - Status and label badges
- **Input** - Form input fields
- **Label** - Form labels
- **Textarea** - Multi-line text input
- **Skeleton** - Loading placeholders
- **Carousel** - Image/product carousel
- **Slider** - Range slider component
- **Toaster** - Toast notification system

See the [shadcn/ui documentation](https://ui.shadcn.com/docs/components) for the full list of available components.

## Features

### Core Features

- **RAG (Retrieval-Augmented Generation)** - Intelligent product search and recommendations using semantic search and LLM
- **AI-Powered Chat** - Conversational interface for product discovery with context-aware recommendations
- **Product Comparison** - Compare multiple products side-by-side with AI-generated insights
- **Shopping Cart** - Add products to cart and manage items before checkout
- **Checkout & Orders** - Complete checkout flow with order management and history
- **Floating Chat Widget** - Accessible chat interface available across all pages

### Technical Features

- **Web Scraping** - Automated product data synchronization from external sources
- **RESTful API** - FastAPI backend with comprehensive endpoints
- **Vector Search** - Semantic product search using pgvector and embeddings
- **Redis Caching** - High-performance caching for product data
- **Next.js Frontend** - Modern React application with server-side rendering
- **shadcn/ui Components** - Beautiful, accessible UI component library
- **Docker Containerization** - Easy deployment and development setup
- **Automated Synchronization** - Scheduled product updates and embedding generation

## Documentation

- **[Architecture Documentation](docs_local/ARCHITECTURE.md)**: Detailed system architecture, design patterns, and scalability considerations
- **[Migrations Guide](docs_local/MIGRATIONS.md)**: Database migration instructions

## Architecture and Design Decisions

### System Architecture

The application follows a clean, layered architecture:

1. **Frontend Layer** (Next.js 14+ with App Router)
   - Server-side rendering for better SEO
   - Client-side interactivity for chat interface
   - Type-safe API client with TypeScript
   - Component-based UI with shadcn/ui

2. **Backend Layer** (FastAPI)
   - RESTful API design
   - Dependency injection for database sessions
   - Service layer pattern for business logic
   - Controller layer for request handling

3. **Data Layer**
   - PostgreSQL with pgvector extension for vector storage
   - Redis for caching product data
   - Alembic for database migrations

4. **RAG Pipeline**
   - Embedding generation using Google Gemini Embedding API
   - Vector search using pgvector cosine similarity
   - LLM integration with Gemini 2.0 Flash for response generation

### Key Design Decisions

1. **Vector Database Choice: pgvector**
   - **Decision**: Use PostgreSQL with pgvector extension instead of dedicated vector DBs
   - **Rationale**:
     - Simpler infrastructure (one database instead of two)
     - ACID compliance for product data and embeddings
     - Lower operational overhead
     - Good performance for our scale (< 10K products)
   - **Trade-off**: Slightly slower than specialized vector DBs at very large scale, but sufficient for this use case

2. **Embedding Model: Gemini Embedding-001**
   - **Decision**: Use Google's Gemini embedding model
   - **Rationale**:
     - High-quality embeddings (1536 dimensions)
     - Good semantic understanding
     - Cost-effective API pricing
   - **Trade-off**: Vendor lock-in, but can be swapped with minimal code changes

3. **LLM: Gemini 2.0 Flash**
   - **Decision**: Use Gemini Flash for response generation
   - **Rationale**:
     - Fast response times
     - Good quality for conversational responses
     - Cost-effective for production use
   - **Trade-off**: May not be as creative as larger models, but sufficient for product recommendations

4. **Scraping Approach: JSON API**
   - **Decision**: Use Hunnit.com's public products.json endpoint
   - **Rationale**:
     - More reliable than HTML scraping
     - Structured data format
     - Faster and less resource-intensive
     - Respects rate limits better
   - **Trade-off**: Limited to sites with JSON APIs, but more maintainable

5. **Caching Strategy: Redis**
   - **Decision**: Cache product data in Redis
   - **Rationale**:
     - Reduces database load
     - Faster response times for product listings
     - Automatic expiration for freshness
   - **Trade-off**: Additional infrastructure, but significant performance gains

6. **Frontend Framework: Next.js**
   - **Decision**: Use Next.js App Router
   - **Rationale**:
     - Server-side rendering for better performance
     - Built-in API routes (though we use separate backend)
     - Excellent TypeScript support
     - Great developer experience
   - **Trade-off**: Learning curve, but industry standard

## Scraping Approach

### Hunnit.com Scraper

The scraper uses Hunnit.com's public JSON API endpoint (`https://hunnit.com/products.json`), which provides structured product data.

**Advantages:**

- No HTML parsing required
- Structured, consistent data format
- Faster and more reliable
- Less prone to breaking with site updates
- Respects rate limits naturally

**Implementation Details:**

- Uses `httpx` for async HTTP requests
- Validates response structure with Pydantic schemas
- Handles errors gracefully with retries
- Stores products in PostgreSQL with deduplication by `external_id`
- Generates embeddings automatically for new products

**Data Extracted:**

- Product title
- Price (in cents, converted to dollars)
- Description
- Product images (multiple URLs)
- Vendor information
- Product tags
- Product type/category
- Variants (size, color, etc.)

**Synchronization:**

- Automated scraping every 6 hours via background scheduler
- Startup sync checks if database has minimum products (default: 10)
- Only scrapes if below threshold
- Generates embeddings for products missing them

## RAG Pipeline Design

### Overview

The RAG (Retrieval-Augmented Generation) pipeline combines semantic search with LLM reasoning to provide intelligent product recommendations.

### Pipeline Flow

``` bash
User Query
    ↓
1. Generate Query Embedding (Gemini Embedding-001)
    ↓
2. Vector Search (pgvector cosine similarity)
    ↓
3. Retrieve Top-K Products (default: 5, threshold: 0.6)
    ↓
4. Format Product Context
    ↓
5. Build LLM Prompt (with conversation history)
    ↓
6. Generate Response (Gemini 2.0 Flash)
    ↓
7. Post-process & Return (products + explanation)
```

### Components

#### 1. Embedding Service (`embedding_service.py`)

- Generates embeddings using Gemini Embedding API
- Supports different task types (retrieval queries, documents)
- Handles API errors gracefully
- Caches embedding service instance

#### 2. Vector Search Service (`vector_search.py`)

- Performs semantic search using pgvector
- Uses cosine similarity for matching
- Filters by similarity threshold
- Returns ranked results with scores

#### 3. RAG Service (`rag_service.py`)

- Orchestrates the full pipeline
- Formats product context for LLM
- Builds prompts with conversation history
- Handles LLM responses and post-processing
- Detects clarification requests

### Key Features

1. **Semantic Understanding**
   - Handles abstract queries like "something for gym and meetings"
   - Understands context and intent
   - Maps user needs to product features

2. **Conversation Context**
   - Maintains conversation history (last 5 messages)
   - Provides context-aware recommendations
   - Enables follow-up questions

3. **Clarification Detection**
   - Identifies when user query is ambiguous
   - Asks targeted clarifying questions
   - Improves recommendation quality

4. **Fallback Handling**
   - Works without LLM (returns products with basic message)
   - Handles API failures gracefully
   - Provides helpful error messages

### Embedding Strategy

**Product Embeddings:**

- Generated from: `title + description + tags + product_type + vendor`
- Task type: `RETRIEVAL_DOCUMENT`
- Dimension: 1536
- Stored in PostgreSQL `products.embedding` column (vector type)

**Query Embeddings:**

- Generated from: user's natural language query
- Task type: `RETRIEVAL_QUERY`
- Same dimension (1536) for compatibility

### Similarity Threshold

- Default threshold: 0.6 (cosine similarity)
- Configurable per request
- Filters out irrelevant products
- Balances recall vs. precision

## Challenges and Trade-offs

### Challenges Faced

1. **Embedding Generation Timing**
   - **Challenge**: Products need embeddings before they can be searched
   - **Solution**: Automatic embedding generation on product creation and startup sync
   - **Trade-off**: Slight delay in search availability, but ensures data quality

2. **LLM Response Formatting**
   - **Challenge**: LLM sometimes lists products or uses bullet points despite instructions
   - **Solution**: Post-processing with regex to clean responses
   - **Trade-off**: May occasionally remove valid content, but improves UX consistency

3. **Vector Search Performance**
   - **Challenge**: pgvector queries can be slow with many products
   - **Solution**: Index on embedding column, limit results, use similarity threshold
   - **Trade-off**: May miss some relevant products, but acceptable for our scale

4. **Scraping Reliability**
   - **Challenge**: External APIs can be slow or unavailable
   - **Solution**: Async requests with timeouts, error handling, retries
   - **Trade-off**: Some products may be temporarily unavailable, but system remains stable

5. **Conversation Context Management**
   - **Challenge**: Maintaining context across multiple messages
   - **Solution**: Include last 5 messages in LLM prompt
   - **Trade-off**: Limited context window, but sufficient for most conversations

### Trade-offs Made

1. **Simplicity vs. Performance**
   - Chose pgvector over specialized vector DB for simplicity
   - Acceptable performance for current scale (< 10K products)
   - Can migrate to dedicated vector DB if needed

2. **Cost vs. Quality**
   - Used Gemini Flash instead of larger models for cost efficiency
   - Quality is sufficient for product recommendations
   - Can upgrade to larger models if needed

3. **Real-time vs. Cached**
   - Cache product listings in Redis for performance
   - Trade freshness for speed
   - Acceptable for product catalog (changes infrequently)

4. **Flexibility vs. Structure**
   - Structured API responses vs. free-form LLM responses
   - Chose structured for reliability and frontend integration
   - LLM provides conversational layer on top

## Deployment

### Docker Setup

The project includes Docker configuration for easy deployment:

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Services:**

- `backend`: FastAPI application (port 8000)
- `postgres`: PostgreSQL with pgvector (port 5432)
- `redis`: Redis cache (port 6379)

### Environment Variables

See `.env.example` files in `backend/` and `frontend/` directories for required environment variables.

**Backend Key Variables:**

- `DATABASE_URL`: PostgreSQL connection string
- `GEMINI_API_KEY`: Google Gemini API key (required for RAG)
- `REDIS_HOST`, `REDIS_PORT`: Redis configuration
- `ENVIRONMENT`: `development` or `production`

**Frontend Key Variables:**

- `NEXT_PUBLIC_API_URL`: Backend API URL

### Production Deployment

The project is configured for deployment on platforms like:

- **Vercel** (frontend) + **Railway/Render** (backend)
- **Docker Compose** on any VPS
- **AWS Lightsail** / **DigitalOcean**

See `deploy.sh` for an example deployment script.

## API Documentation

API documentation is available at `/api/docs` when running the backend (Scalar API docs).

**Key Endpoints:**

- `GET /api/health` - Health check
- `GET /api/products/hunnit` - List all products
- `GET /api/products/hunnit/{id}` - Get product by ID
- `POST /api/products/hunnit/scrape` - Trigger product scraping
- `POST /api/chat` - Chat endpoint for product recommendations
- `POST /api/chat/compare` - Compare multiple products with AI insights

## User Features

### Shopping Cart

- Add products to cart from product pages or search results
- View cart contents with item quantities and totals
- Update quantities or remove items
- Persistent cart storage using browser localStorage
- Cart badge indicator in header showing item count

### Checkout Flow

- Complete checkout form with customer and shipping information
- Support for multiple payment methods (Card, Cash on Delivery)
- Form validation with error messages
- Order summary with itemized breakdown
- Tax and shipping cost calculation
- Order confirmation page with order details

### Order Management

- View order history with all past orders
- Order detail pages showing full order information
- Order status tracking (pending, processing, shipped, delivered)
- Order number generation and tracking
- Customer and shipping information display

### Product Comparison

- Compare up to 4 products side-by-side
- AI-powered comparison insights highlighting key differences
- Structured comparison table with categorized features
- Similar products recommendations
- Send comparison to chat for further discussion
- Add/remove products from comparison easily

### Chat Interface

- Conversational AI for product discovery
- Context-aware recommendations based on conversation history
- Product cards displayed within chat messages
- Suggested follow-up questions
- Floating chat widget available on all pages
- Full-page chat interface for detailed conversations

## Future Improvements

If given more time, here are the improvements I would prioritize:

### Short-term (1-2 weeks)

1. **Enhanced Error Handling**
   - More specific error messages
   - Better user-facing error responses
   - Retry logic for transient failures

2. **Rate Limiting**
   - Implement rate limiting on API endpoints
   - Protect against abuse
   - Fair usage policies

3. **Testing**
   - Unit tests for services
   - Integration tests for API endpoints
   - E2E tests for critical flows

4. **Monitoring & Observability**
   - Add Prometheus metrics
   - Structured logging with correlation IDs
   - Error tracking (Sentry)

### Medium-term (1 month)

1. **Multi-source Scraping**
   - Support for multiple product sources
   - Unified product schema
   - Source-specific scrapers

2. **Advanced RAG Features**
   - Hybrid search (vector + keyword)
   - Re-ranking with cross-encoder
   - Query expansion
   - Multi-query retrieval

3. **User Personalization**
   - User profiles and preferences
   - Personalized recommendations
   - Search history
   - Favorite products
   - User authentication

4. **Performance Optimization**
   - Embedding caching
   - Query result caching
   - Database query optimization
   - CDN for static assets

5. **Payment Integration**
   - Real payment gateway integration (Stripe, Razorpay)
   - Payment status tracking
   - Refund processing

### Long-term (2-3 months)

1. **Analytics Dashboard**
   - Product search analytics
   - Popular queries
   - Conversion tracking
   - A/B testing framework

2. **Advanced Features**
   - Price tracking and alerts
   - Stock alerts
   - Wishlist functionality
   - Product reviews and ratings

3. **Scalability Improvements**
   - Migrate to dedicated vector DB (Pinecone/Weaviate) if needed
   - Horizontal scaling with load balancer
   - Database read replicas
   - Microservices architecture if scale requires

4. **ML Enhancements**
   - Fine-tuned embedding model
   - Custom ranking model
   - Query intent classification
   - Product categorization ML model
