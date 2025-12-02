// API Response type (matches backend schema)
export interface ProductApiResponse {
  id: string;
  external_id: string;
  title: string;
  handle: string;
  description: string;
  body_html: string;
  price: number;
  compare_at_price: number | null;
  vendor: string;
  product_type: string;
  category: string;
  tags: string[];
  image_urls: string[];
  features: Record<string, unknown>;
  ai_features?: string[];
  created_at: string;
  updated_at: string;
  scraped_at: string;
}

// Frontend Product type (adapted for UI components)
export interface Product {
  id: string;
  title: string;
  price: number;
  description: string;
  image: string;
  category: string;
  ai_features?: string[];
  imageUrl?: string;
  // Additional fields from API
  external_id?: string;
  compare_at_price?: number | null;
  vendor?: string;
  product_type?: string;
  tags?: string[];
  image_urls?: string[];
  body_html?: string;
  features?: Record<string, unknown>; // Contains variants, options, etc.
}

