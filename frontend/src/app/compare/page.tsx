"use client";

import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { ProductComparison } from "@/components/features/products/product-comparison";

export default function ComparePage() {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header />
      <ProductComparison />
      <Footer />
    </div>
  );
}

