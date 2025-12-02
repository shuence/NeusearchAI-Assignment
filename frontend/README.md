# Neusearch Frontend

Next.js 16 frontend application for Neusearch AI - a full-stack search application with RAG capabilities.

## Overview

Modern React application built with Next.js App Router, featuring AI-powered product search, chat interface, product comparison, shopping cart, and order management.

## Tech Stack

- **Framework**: Next.js 16.0.6 (App Router)
- **React**: 19.2.0
- **TypeScript**: 5.x
- **Styling**: Tailwind CSS 4.x
- **UI Components**: shadcn/ui (Radix UI + Tailwind)
- **Icons**: Lucide React
- **State Management**: React Context API
- **Form Handling**: Native React
- **Linting/Formatting**: Biome 2.2.0
- **Package Manager**: pnpm 9.0.0
- **Notifications**: Sonner

## Project Structure

``` bash
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Home page
│   │   ├── globals.css         # Global styles
│   │   ├── not-found.tsx       # 404 page
│   │   ├── products/
│   │   │   └── [id]/
│   │   │       └── page.tsx    # Product detail page
│   │   ├── chat/
│   │   │   └── page.tsx        # Full-page chat interface
│   │   ├── compare/
│   │   │   └── page.tsx        # Product comparison page
│   │   ├── cart/
│   │   │   └── page.tsx        # Shopping cart page
│   │   ├── checkout/
│   │   │   └── page.tsx        # Checkout page
│   │   ├── orders/
│   │   │   ├── page.tsx        # Order history
│   │   │   └── [id]/
│   │   │       └── page.tsx    # Order detail page
│   │   └── order-success/
│   │       └── page.tsx        # Order confirmation
│   ├── components/
│   │   ├── ui/                 # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── input.tsx
│   │   │   ├── label.tsx
│   │   │   ├── textarea.tsx
│   │   │   ├── skeleton.tsx
│   │   │   ├── carousel.tsx
│   │   │   ├── slider.tsx
│   │   │   ├── toaster.tsx
│   │   │   └── theme-toggle.tsx
│   │   ├── layout/             # Layout components
│   │   │   ├── header.tsx      # Navigation header
│   │   │   └── footer.tsx      # Footer
│   │   └── features/           # Feature components
│   │       ├── products/       # Product-related components
│   │       │   ├── product-card.tsx
│   │       │   ├── product-carousel.tsx
│   │       │   ├── product-comparison.tsx
│   │       │   └── comparison-table.tsx
│   │       └── chat/           # Chat components
│   │           └── floating-chat-widget.tsx
│   ├── contexts/              # React contexts
│   │   ├── cart-context.tsx   # Shopping cart state
│   │   ├── comparison-context.tsx # Product comparison state
│   │   └── order-context.tsx  # Order management state
│   ├── lib/
│   │   ├── api/               # API client functions
│   │   │   ├── chat.ts        # Chat API
│   │   │   ├── health.ts      # Health check API
│   │   │   └── products.ts    # Products API
│   │   ├── utils/
│   │   │   ├── api-client.ts  # Base API client
│   │   │   ├── filter-products.ts # Product filtering
│   │   │   └── seo.ts         # SEO utilities
│   │   ├── utils.ts           # General utilities
│   │   └── constants.ts       # App constants
│   ├── types/                 # TypeScript types
│   │   ├── product.ts         # Product types
│   │   └── health.ts          # Health check types
│   └── data/                  # Mock/dummy data
│       └── products.ts        # Product dummy data
├── public/                    # Static assets
├── components.json            # shadcn/ui configuration
├── next.config.ts             # Next.js configuration
├── tailwind.config.ts         # Tailwind CSS configuration
├── tsconfig.json              # TypeScript configuration
├── biome.json                 # Biome linter/formatter config
├── package.json               # Dependencies
└── pnpm-lock.yaml            # Lock file
```

## Prerequisites

- Node.js 18+
- pnpm 9.0.0+ (package manager)

## Setup

### 1. Install Dependencies

```bash
pnpm install
```

### 2. Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

For production, use your deployed backend URL:

```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### 3. Run Development Server

```bash
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Available Scripts

- `pnpm dev` - Start development server with hot reload
- `pnpm build` - Create optimized production build
- `pnpm start` - Start production server (requires build first)
- `pnpm lint` - Run Biome linter to check for code issues
- `pnpm format` - Format code using Biome formatter

## Features

### Core Features

- **AI-Powered Chat** - Conversational interface for product discovery
- **Product Search** - Browse and search products with filters
- **Product Comparison** - Compare up to 4 products side-by-side with AI insights
- **Shopping Cart** - Add products, manage quantities, view totals
- **Checkout Flow** - Complete checkout with customer and shipping information
- **Order Management** - View order history and order details
- **Floating Chat Widget** - Accessible chat interface on all pages
- **Dark Mode** - Theme toggle for light/dark mode

### UI Components

The project uses [shadcn/ui](https://ui.shadcn.com/) for UI components, built on Radix UI and Tailwind CSS.

#### Adding New Components

```bash
cd frontend
npx shadcn@latest add [component-name]
```

Example:

```bash
npx shadcn@latest add dialog
npx shadcn@latest add dropdown-menu
```

#### Available Components

- **Button** - Interactive button with variants
- **Card** - Container for content sections
- **Badge** - Status and label badges
- **Input** - Form input fields
- **Label** - Form labels
- **Textarea** - Multi-line text input
- **Skeleton** - Loading placeholders
- **Carousel** - Image/product carousel
- **Slider** - Range slider component
- **Toaster** - Toast notification system
- **Theme Toggle** - Dark/light mode switcher

## State Management

The application uses React Context API for state management:

### Cart Context (`contexts/cart-context.tsx`)

- Manages shopping cart items
- Persists to localStorage
- Provides add, remove, update quantity functions

### Comparison Context (`contexts/comparison-context.tsx`)

- Manages products selected for comparison
- Limits to 4 products
- Provides add, remove, clear functions

### Order Context (`contexts/order-context.tsx`)

- Manages order history
- Persists to localStorage
- Provides create order, get order functions

## API Integration

### API Client (`lib/utils/api-client.ts`)

Base API client with:

- Type-safe request/response handling
- Error handling
- Server-side and client-side request support

### API Modules

- **`lib/api/chat.ts`** - Chat/RAG endpoints
- **`lib/api/products.ts`** - Product endpoints
- **`lib/api/health.ts`** - Health check endpoint

## Styling

### Tailwind CSS

The project uses Tailwind CSS 4.x for styling:

- Utility-first CSS framework
- Custom theme configuration in `tailwind.config.ts`
- Dark mode support via `next-themes`

### Global Styles

- `app/globals.css` - Global styles and Tailwind directives
- Custom CSS variables for theming

## TypeScript

Full TypeScript support:

- Strict type checking
- Type definitions in `src/types/`
- API response types
- Component prop types

## SEO

SEO utilities in `lib/utils/seo.ts`:

- Dynamic metadata generation
- Open Graph tags
- Twitter Card tags
- Structured data

## Development

### Hot Reload

Next.js provides automatic hot reloading:

- Changes to components update instantly
- Fast Refresh preserves component state
- No page reload needed

### Code Quality

- **Biome** for linting and formatting
- TypeScript for type safety
- ESLint rules via Biome

### Best Practices

1. **Component Structure**: Keep components small and focused
2. **Type Safety**: Use TypeScript types for all props and data
3. **API Calls**: Use the API client utilities
4. **State Management**: Use Context API for global state
5. **Styling**: Prefer Tailwind utilities over custom CSS

## Building for Production

### 1. Build

```bash
pnpm build
```

This creates an optimized production build in `.next/` directory.

### 2. Start Production Server

```bash
pnpm start
```

### 3. Deploy

The project is configured for deployment on:

- **Vercel** (recommended for Next.js)
- **Netlify**
- **Any Node.js hosting**

#### Vercel Deployment

1. Connect your repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push to main branch

#### Environment Variables for Production

- `NEXT_PUBLIC_API_URL` - Backend API URL

## Performance

### Optimizations

- **Server-Side Rendering (SSR)** - Better SEO and initial load
- **Static Generation** - Pre-rendered pages where possible
- **Image Optimization** - Next.js Image component
- **Code Splitting** - Automatic code splitting
- **Lazy Loading** - Components loaded on demand

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Troubleshooting

### Build Errors

- Clear `.next` directory: `rm -rf .next`
- Reinstall dependencies: `rm -rf node_modules && pnpm install`
- Check TypeScript errors: `pnpm build`

### API Connection Issues

- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check backend is running
- Check CORS settings on backend

### Styling Issues

- Clear browser cache
- Check Tailwind classes are correct
- Verify `globals.css` is imported

## Contributing

1. Follow the existing code structure
2. Use TypeScript for all new code
3. Follow component naming conventions
4. Add proper types for props and data
5. Use Tailwind utilities for styling
6. Run linter before committing: `pnpm lint`

## License

See root README.md for license information.
