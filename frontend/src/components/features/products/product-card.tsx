"use client";

import { useRouter } from "next/navigation";
import Image from "next/image";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CompareButton } from "./compare-button";
import { AddToCartButton } from "./add-to-cart-button";
import type { Product } from "@/types/product";
import { ROUTES } from "@/lib/constants";

interface ProductCardProps {
  product: Product;
}

export function ProductCard({ product }: ProductCardProps) {
  const router = useRouter();

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
    return `₹${Math.round(price).toLocaleString("en-IN")}`;
  };

  const imageSrc =
    product.image ||
    product.imageUrl ||
    product.image_urls?.[0] ||
    "/placeholder.png";

  const title = product.title || "Untitled Product";

  const description =
    product.description ||
    product.body_html?.replace(/<[^>]*>/g, "").substring(0, 100) ||
    "No description available";

  const category =
    product.category || product.product_type || product.vendor;

  const handleCardClick = () => {
    router.push(ROUTES.PRODUCT_DETAIL(product.id));
  };

  return (
    <Card 
      className="flex flex-col h-full hover:shadow-lg transition-shadow cursor-pointer"
      onClick={handleCardClick}
    >
      <CardHeader className="shrink-0">
        <div className="w-full overflow-hidden rounded-lg bg-[#EEECEB] mb-4 relative h-[200px] flex items-center justify-center">
          <Image
            src={imageSrc}
            alt={title}
            width={800}
            height={800}
            className="object-contain w-full h-full"
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
            loading="lazy"
            placeholder="blur"
            blurDataURL="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAwIiBoZWlnaHQ9IjgwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PC9zdmc+"
            onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
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
      <CardFooter className="shrink-0 flex flex-col gap-2 relative z-10">
        <div onClick={(e) => e.stopPropagation()}>
          <AddToCartButton 
            product={product} 
            size="sm"
            className="w-full"
          />
        </div>
        <div onClick={(e) => e.stopPropagation()}>
          <Button 
            className="w-full" 
            variant="outline"
            onClick={(e) => {
              e.stopPropagation();
              handleCardClick();
            }}
            aria-label={`View details for ${title}`}
          >
            View Details
          </Button>
        </div>
        <div onClick={(e) => e.stopPropagation()}>
          <CompareButton 
            product={product} 
            variant="outline"
            size="sm"
            className="w-full"
          />
        </div>
      </CardFooter>
    </Card>
  );
}

