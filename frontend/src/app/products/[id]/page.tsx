"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ProductImageCarousel } from "@/components/features/products/product-image-carousel";
import { ProductDetailSkeleton } from "@/components/features/products/product-detail-skeleton";
import { getProductById, getSimilarProducts } from "@/lib/api/products";
import { ProductGrid } from "@/components/features/products/product-grid";
import { CompareButton } from "@/components/features/products/compare-button";
import { AddToCartButton } from "@/components/features/products/add-to-cart-button";
import { ROUTES } from "@/lib/constants";
import type { Product } from "@/types/product";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";

export default function ProductDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [product, setProduct] = useState<Product | null>(null);
  const [similarProducts, setSimilarProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingSimilar, setIsLoadingSimilar] = useState(false);

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        setIsLoading(true);
        const data = await getProductById(id);
        if (!data) {
          router.push("/not-found");
          return;
        }
        setProduct(data);
        
        // Fetch similar products
        if (data) {
          setIsLoadingSimilar(true);
          try {
            const similar = await getSimilarProducts(data.id, 4);
            setSimilarProducts(similar);
          } catch (error) {
            console.error("Error loading similar products:", error);
          } finally {
            setIsLoadingSimilar(false);
          }
        }
      } catch (error) {
        console.error("Error loading product:", error);
        toast.error("Failed to load product", {
          description: error instanceof Error ? error.message : "Product not found.",
        });
        router.push("/not-found");
      } finally {
        setIsLoading(false);
      }
    };

    if (id) {
      fetchProduct();
    }
  }, [id, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        <Header />
        <main className="container mx-auto px-4 py-8 flex-1">
          <Skeleton className="h-6 w-32 mb-6" />
          <ProductDetailSkeleton />
        </main>
        <Footer />
      </div>
    );
  }

  if (!product) {
    return null;
  }

  // Extract variants from features for image carousel
  let variants: Array<{
    title?: string;
    sku?: string;
    price?: number | string;
    compare_at_price?: number | string;
    option1?: string;
    option2?: string;
    option3?: string;
    available?: boolean;
    featured_image?: {
      src?: string;
      id?: number;
      alt?: string;
    };
  }> | undefined;

  if (product.features) {
    const variantsKey = Object.keys(product.features).find(
      (key) => key.toLowerCase() === "variants"
    );
    
    if (variantsKey) {
      const variantsValue = product.features[variantsKey];
      if (Array.isArray(variantsValue) && variantsValue.length > 0) {
        variants = variantsValue.map((v: unknown) => {
          const variant = v as Record<string, unknown>;
          const featuredImage = variant.featured_image as Record<string, unknown> | undefined;
          return {
            title: variant.title as string | undefined,
            sku: variant.sku as string | undefined,
            price: variant.price as number | string | undefined,
            compare_at_price: variant.compare_at_price as number | string | undefined,
            option1: variant.option1 as string | undefined,
            option2: variant.option2 as string | undefined,
            option3: variant.option3 as string | undefined,
            available: variant.available as boolean | undefined,
            featured_image: featuredImage
              ? {
                  src: featuredImage.src as string | undefined,
                  id: featuredImage.id as number | undefined,
                  alt: featuredImage.alt as string | undefined,
                }
              : undefined,
          };
        });
      }
    }
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header />

      <main className="container mx-auto px-4 py-8 flex-1">
        <Link
          href={ROUTES.HOME}
          className="text-sm text-muted-foreground hover:text-foreground mb-6 inline-block"
        >
          ← Back to Products
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <ProductImageCarousel
            mainImage={product.image || product.imageUrl || "/placeholder.png"}
            imageUrls={product.image_urls}
            variants={variants}
          />

          <div className="space-y-6">
            <div>
              <p className="text-sm text-muted-foreground mb-2">
                {product.category}
              </p>
              <h1 className="text-4xl font-bold mb-4">{product.title}</h1>
              <div className="flex items-center gap-4 mb-6">
                <p className="text-3xl font-bold">
                  ₹{product.price.toLocaleString()}
                </p>
                {product.compare_at_price && product.compare_at_price > product.price && (
                  <p className="text-xl text-muted-foreground line-through">
                    ₹{product.compare_at_price.toLocaleString()}
                  </p>
                )}
              </div>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Description</CardTitle>
              </CardHeader>
              <CardContent>
                <div
                  className="text-muted-foreground prose prose-sm max-w-none"
                  dangerouslySetInnerHTML={{
                    __html: product.body_html || product.description || "",
                  }}
                />
              </CardContent>
            </Card>

            {product.ai_features && product.ai_features.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Features</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="list-disc list-inside space-y-2">
                    {product.ai_features.map((feature, index) => (
                      <li key={index} className="text-muted-foreground">
                        {feature}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}


            <div className="flex flex-col gap-3">
              <AddToCartButton product={product} size="lg" className="w-full" />
              <CompareButton product={product} size="lg" className="w-full" />
            </div>
          </div>
        </div>

        {/* Similar Products Section */}
        {similarProducts.length > 0 && (
          <div className="mt-16">
            <h2 className="text-2xl font-bold mb-6">You Might Also Like</h2>
            {isLoadingSimilar ? (
              <div className="text-center py-8">
                <Loader2 className="h-6 w-6 animate-spin mx-auto text-primary" />
              </div>
            ) : (
              <ProductGrid products={similarProducts} />
            )}
          </div>
        )}
      </main>
      <Footer />
    </div>
  );
}

