"use client";

import { useState, useEffect, useMemo } from "react";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { FloatingChatWidget } from "@/components/features/chat/floating-chat-widget";
import { ProductGrid } from "@/components/features/products/product-grid";
import { ProductGridSkeleton } from "@/components/features/products/product-grid-skeleton";
import { ProductFilters, type FilterState } from "@/components/features/products/product-filters";
import { getProducts } from "@/lib/api/products";
import { filterAndSortProducts } from "@/lib/utils/filter-products";
import type { Product } from "@/types/product";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

const initialFilterState: FilterState = {
  searchQuery: "",
  selectedCategory: null,
  selectedVendor: null,
  priceRange: null,
  sortBy: "none",
};

export default function Home() {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterState, setFilterState] = useState<FilterState>(initialFilterState);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setIsLoading(true);
        const data = await getProducts();
        setProducts(data);
        if (data.length === 0) {
          toast.info("No products found", {
            description: "The product catalog is currently empty.",
          });
        }
      } catch (error) {
        console.error("Error loading products:", error);
        toast.error("Failed to load products", {
          description: error instanceof Error ? error.message : "Please try again later.",
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchProducts();
  }, []);

  // Filter and sort products based on filter state
  const filteredProducts = useMemo(() => {
    if (products.length === 0) return [];
    return filterAndSortProducts(products, filterState);
  }, [products, filterState]);

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header />

      <main className="container mx-auto px-4 py-4 lg:py-6 flex-1 max-w-7xl lg:max-w-6xl">
        <div className="mb-4 lg:mb-6">
          <h2 className="text-2xl lg:text-2xl font-bold mb-1 lg:mb-2">All Products</h2>
          <p className="text-sm lg:text-base text-muted-foreground">
            Browse our collection of products
          </p>
        </div>

        {isLoading ? (
          <>
            <ProductFilters
              products={[]}
              filteredProducts={[]}
              filterState={filterState}
              onFilterChange={setFilterState}
            />
            <ProductGridSkeleton count={6} />
          </>
        ) : products.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground mb-4">
              No products available at the moment.
            </p>
            <p className="text-sm text-muted-foreground">
              Please check if the backend API is running and the database is properly configured.
            </p>
          </div>
        ) : (
          <>
            <ProductFilters
              products={products}
              filteredProducts={filteredProducts}
              filterState={filterState}
              onFilterChange={setFilterState}
            />
            {filteredProducts.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-muted-foreground mb-4">
                  No products match your filters.
                </p>
                <p className="text-sm text-muted-foreground">
                  Try adjusting your search or filter criteria.
                </p>
              </div>
            ) : (
              <ProductGrid products={filteredProducts} />
            )}
          </>
        )}
      </main>
      <Footer />
      <FloatingChatWidget />
    </div>
  );
}
