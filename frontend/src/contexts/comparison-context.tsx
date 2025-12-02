"use client";

import { createContext, useContext, useState, ReactNode } from "react";
import type { Product } from "@/types/product";

interface ComparisonContextType {
  products: Product[];
  addProduct: (product: Product) => void;
  removeProduct: (productId: string) => void;
  clearComparison: () => void;
  isInComparison: (productId: string) => boolean;
  canAddMore: boolean;
}

const ComparisonContext = createContext<ComparisonContextType | undefined>(undefined);

const MAX_COMPARISON = 4; // Allow up to 4 products to compare

export function ComparisonProvider({ children }: { children: ReactNode }) {
  const [products, setProducts] = useState<Product[]>([]);

  const addProduct = (product: Product) => {
    setProducts((prev) => {
      // Don't add if already in comparison
      if (prev.some((p) => p.id === product.id)) {
        return prev;
      }
      // Don't add if at max capacity
      if (prev.length >= MAX_COMPARISON) {
        return prev;
      }
      return [...prev, product];
    });
  };

  const removeProduct = (productId: string) => {
    setProducts((prev) => prev.filter((p) => p.id !== productId));
  };

  const clearComparison = () => {
    setProducts([]);
  };

  const isInComparison = (productId: string) => {
    return products.some((p) => p.id === productId);
  };

  const canAddMore = products.length < MAX_COMPARISON;

  return (
    <ComparisonContext.Provider
      value={{
        products,
        addProduct,
        removeProduct,
        clearComparison,
        isInComparison,
        canAddMore,
      }}
    >
      {children}
    </ComparisonContext.Provider>
  );
}

export function useComparison() {
  const context = useContext(ComparisonContext);
  if (context === undefined) {
    throw new Error("useComparison must be used within a ComparisonProvider");
  }
  return context;
}

