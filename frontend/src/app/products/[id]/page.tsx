import { notFound } from "next/navigation";
import Link from "next/link";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ProductImageGallery } from "@/components/features/products/product-image-gallery";
import { getProductById } from "@/lib/api/products";
import { ROUTES } from "@/lib/constants";

interface ProductDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function ProductDetailPage({
  params,
}: ProductDetailPageProps) {
  const { id } = await params;

  // Try to fetch product by ID (can be UUID or external_id)
  const product = await getProductById(id, true);

  if (!product) {
    notFound();
  }

  // Extract variants from attributes
  // Variants are stored in product.attributes under the "variants" key
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

  if (product.attributes) {
    // Check if variants exist in attributes
    const variantsKey = Object.keys(product.attributes).find(
      (key) => key.toLowerCase() === "variants"
    );
    
    if (variantsKey) {
      const variantsValue = product.attributes[variantsKey];
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
    <div className="min-h-screen bg-background">
      <Header />

      <main className="container mx-auto px-4 py-8">
        <Link
          href={ROUTES.HOME}
          className="text-sm text-muted-foreground hover:text-foreground mb-6 inline-block"
        >
          ← Back to Products
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <ProductImageGallery
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

            {product.tags && product.tags.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Tags</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {product.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-muted rounded-md text-sm text-muted-foreground"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
            {product.features && product.features.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Features</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="list-disc list-inside space-y-2">
                    {product.features.map((feature, index) => (
                      <li key={index} className="text-muted-foreground">
                        {typeof feature === "string" ? feature : String(feature)}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            {product.attributes && Object.keys(product.attributes).length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Attributes</CardTitle>
                </CardHeader>
                <CardContent>
                  <dl className="space-y-4">
                    {Object.entries(product.attributes).map(([key, value]) => {
                      // Handle arrays of objects (like variants)
                      if (Array.isArray(value) && value.length > 0 && typeof value[0] === "object") {
                        return (
                          <div key={key} className="space-y-2">
                            <dt className="font-medium mb-2">{key}:</dt>
                            <dd className="text-muted-foreground">
                              <div className="space-y-2 pl-4 border-l-2 border-muted">
                                {value.map((item: unknown, index: number) => {
                                  const obj = item as Record<string, unknown>;
                                  const variantInfo = [
                                    obj.title && `Title: ${obj.title}`,
                                    obj.sku && `SKU: ${obj.sku}`,
                                    obj.price && `Price: ₹${Number(obj.price).toLocaleString()}`,
                                    obj.compare_at_price && `Compare: ₹${Number(obj.compare_at_price).toLocaleString()}`,
                                    obj.option1 && `Option 1: ${obj.option1}`,
                                    obj.option2 && `Option 2: ${obj.option2}`,
                                    obj.option3 && `Option 3: ${obj.option3}`,
                                    obj.available !== undefined && `Available: ${obj.available ? "Yes" : "No"}`,
                                  ]
                                    .filter(Boolean)
                                    .join(" • ");
                                  
                                  return (
                                    <div key={index} className="text-sm">
                                      <span className="font-medium">Variant {index + 1}:</span> {variantInfo || "N/A"}
                                    </div>
                                  );
                                })}
                              </div>
                            </dd>
                          </div>
                        );
                      }
                      
                      // Handle single objects (like options)
                      if (typeof value === "object" && value !== null && !Array.isArray(value)) {
                        const obj = value as Record<string, unknown>;
                        return (
                          <div key={key} className="space-y-2">
                            <dt className="font-medium mb-2">{key}:</dt>
                            <dd className="text-muted-foreground">
                              <div className="space-y-1 pl-4 border-l-2 border-muted">
                                {Object.entries(obj).map(([nestedKey, nestedValue]) => {
                                  let displayValue: string;
                                  if (nestedValue === null || nestedValue === undefined) {
                                    displayValue = "N/A";
                                  } else if (Array.isArray(nestedValue)) {
                                    displayValue = nestedValue.map(String).join(", ");
                                  } else if (typeof nestedValue === "object") {
                                    displayValue = JSON.stringify(nestedValue);
                                  } else {
                                    displayValue = String(nestedValue);
                                  }
                                  return (
                                    <div key={nestedKey} className="text-sm">
                                      <span className="font-medium">{nestedKey}:</span> {displayValue}
                                    </div>
                                  );
                                })}
                              </div>
                            </dd>
                          </div>
                        );
                      }
                      
                      // Handle arrays of primitives
                      if (Array.isArray(value)) {
                        return (
                          <div key={key} className="flex justify-between">
                            <dt className="font-medium">{key}:</dt>
                            <dd className="text-muted-foreground">
                              {value.map(String).join(", ")}
                            </dd>
                          </div>
                        );
                      }
                      
                      // Handle primitives and dates
                      let displayValue: string;
                      if (value === null || value === undefined) {
                        displayValue = "N/A";
                      } else if (typeof value === "string" && value.match(/^\d{4}-\d{2}-\d{2}T/)) {
                        // Format ISO date strings
                        try {
                          const date = new Date(value);
                          displayValue = date.toLocaleString();
                        } catch {
                          displayValue = String(value);
                        }
                      } else {
                        displayValue = String(value);
                      }

                      return (
                        <div key={key} className="flex justify-between">
                          <dt className="font-medium">{key}:</dt>
                          <dd className="text-muted-foreground">{displayValue}</dd>
                        </div>
                      );
                    })}
                  </dl>
                </CardContent>
              </Card>
            )}

            <Button size="lg" className="w-full">
              Add to Cart
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}

