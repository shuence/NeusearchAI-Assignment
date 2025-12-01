import Link from "next/link";
import Image from "next/image";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { Product } from "@/types/product";
import { ROUTES } from "@/lib/constants";

interface ProductCardProps {
  product: Product;
}

export function ProductCard({ product }: ProductCardProps) {
  // Format price with proper handling of edge cases
  const formatPrice = (price: number | null | undefined): string => {
    if (price === null || price === undefined || isNaN(price)) {
      return "Price not available";
    }
    if (price < 0) {
      return "Invalid price";
    }
    if (price === 0) {
      return "Free";
    }
    // Handle very large numbers
    if (price >= 10000000) {
      return `₹${(price / 10000000).toFixed(1)}Cr`;
    }
    if (price >= 100000) {
      return `₹${(price / 100000).toFixed(1)}L`;
    }
    if (price >= 1000) {
      return `₹${(price / 1000).toFixed(1)}K`;
    }
    return `₹${Math.round(price).toLocaleString("en-IN")}`;
  };

  // Get image source with fallback
  const imageSrc =
    product.image ||
    product.imageUrl ||
    product.image_urls?.[0] ||
    "/placeholder.png";

  // Get title with fallback
  const title = product.title || "Untitled Product";

  // Get description with fallback
  const description =
    product.description ||
    product.body_html?.replace(/<[^>]*>/g, "").substring(0, 100) ||
    "No description available";

  // Get category with fallback
  const category =
    product.category || product.product_type || product.vendor || "Uncategorized";

  return (
    <Card className="flex flex-col h-full hover:shadow-lg transition-shadow">
      <CardHeader className="shrink-0">
        <div className="w-full overflow-hidden rounded-lg bg-muted mb-4 relative h-[200px] flex items-center justify-center">
          <Image
            src={imageSrc}
            alt={title}
            width={800}
            height={800}
            className="object-contain w-full h-full"
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
            unoptimized
            onError={(e) => {
              // Fallback to placeholder on error
              const target = e.target as HTMLImageElement;
              if (target.src !== "/placeholder.png") {
                target.src = "/placeholder.png";
              }
            }}
          />
        </div>
        <CardTitle className="line-clamp-2 min-h-12">{title}</CardTitle>
        <CardDescription className="line-clamp-1">{category}</CardDescription>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col">
        <p className="text-sm text-muted-foreground line-clamp-2 flex-1">
          {description}
        </p>
        <p className="text-2xl font-bold mt-4 shrink-0">
          {formatPrice(product.price)}
        </p>
      </CardContent>
      <CardFooter className="shrink-0">
        <Link href={ROUTES.PRODUCT_DETAIL(product.id)} className="w-full">
          <Button className="w-full">View Details</Button>
        </Link>
      </CardFooter>
    </Card>
  );
}

