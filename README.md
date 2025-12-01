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
    │   │   └── not-found.tsx      # 404 page
    │   ├── components/
    │   │   ├── ui/                # shadcn/ui components
    │   │   ├── layout/            # Layout components (header, footer)
    │   │   └── features/          # Feature-specific components
    │   │       └── products/      # Product-related components
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
# Copy the example env file
cp .env.example .env

# Or create .env manually with database configuration
# Edit .env with your configuration, especially DATABASE_URL
```

**Important**: Make sure to set the `DATABASE_URL` in your `.env` file:

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
cp .env.example .env.local
# Edit .env.local with your configuration
```

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

- **Button** - Already included as an example component

See the [shadcn/ui documentation](https://ui.shadcn.com/docs/components) for the full list of available components.

## Features

- RAG (Retrieval-Augmented Generation) implementation
- Web scraping capabilities
- RESTful API
- Next.js frontend with modern UI
- shadcn/ui component library
