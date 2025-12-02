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
  showCompare?: boolean;
}

export function ProductCard({ product, showCompare = true }: ProductCardProps) {
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
      className="flex flex-col h-full hover:shadow-lg transition-all duration-300 cursor-pointer border-border/50 hover:border-primary/20"
      onClick={handleCardClick}
    >
      <CardHeader className="shrink-0 pb-3">
        <div className="w-full overflow-hidden rounded-lg bg-[#EEECEA] mb-3 relative h-[220px] flex items-center justify-center group">
          <Image
            src={imageSrc}
            alt={title}
            width={800}
            height={800}
            className="object-contain w-full h-full transition-transform duration-300 group-hover:scale-105"
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
        <CardTitle className="line-clamp-2 min-h-12 text-base font-semibold leading-tight mb-1">
          {title}
        </CardTitle>
        <CardDescription className="line-clamp-1 text-xs text-muted-foreground">
          {category}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col">
        <p className="text-sm text-muted-foreground line-clamp-2 flex-1 mb-4">
          {description}
        </p>
        <div className="flex flex-col gap-1 shrink-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-2xl font-bold">
          {formatPrice(product.price)}
        </p>
            {product.compare_at_price && 
             product.compare_at_price > (product.price || 0) && (
              <p className="text-sm text-muted-foreground line-through">
                {formatPrice(product.compare_at_price)}
              </p>
            )}
          </div>
          {product.compare_at_price && 
           product.compare_at_price > (product.price || 0) && (
            <p className="text-xs text-primary font-medium">
              {Math.round(
                ((product.compare_at_price - (product.price || 0)) / product.compare_at_price) * 100
              )}% OFF
            </p>
          )}
        </div>
      </CardContent>
      <CardFooter className="shrink-0 flex flex-col gap-2.5 relative z-10 pt-4 border-t">
        {/* Add to Cart and Compare in one row */}
        <div className={`flex gap-2 w-full ${showCompare ? '' : 'flex-col'}`} onClick={(e) => e.stopPropagation()}>
          <AddToCartButton 
            product={product} 
            size="default"
            className={showCompare ? "flex-1 text-xs sm:text-sm h-9" : "w-full text-xs sm:text-sm h-9"}
          />
          {showCompare && (
            <CompareButton 
              product={product} 
              variant="outline"
              size="default"
              className="flex-1 text-xs sm:text-sm h-9"
          />
          )}
        </div>
        {/* View Details button at bottom - same width as upper buttons row */}
        <div className="w-full" onClick={(e) => e.stopPropagation()}>
          <Button 
            className="w-full text-xs sm:text-sm h-9" 
            variant="outline"
            size="default"
            onClick={(e) => {
              e.stopPropagation();
              handleCardClick();
            }}
            aria-label={`View details for ${title}`}
          >
            View Details
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}

