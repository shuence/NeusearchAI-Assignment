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

  // Extract variants from product features and find variant with color in title/option1
  const getVariantColorImage = (): string | null => {
    if (!product.features) return null;
    
    const variantsKey = Object.keys(product.features).find(
      (key) => key.toLowerCase() === "variants"
    );
    
    if (variantsKey) {
      const variantsValue = product.features[variantsKey];
      if (Array.isArray(variantsValue)) {
        // Find any variant that has a color in its title and has a featured image
        const colorVariant = variantsValue.find((v: unknown) => {
          const variant = v as Record<string, unknown>;
          const title = variant.title as string | undefined;
          const featuredImage = variant.featured_image as Record<string, unknown> | undefined;
          
          // Must have both a title and a featured image
          if (!title || !featuredImage?.src) return false;
          
          // Common color keywords
          const colorKeywords = [
            'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'brown',
            'black', 'white', 'gray', 'grey', 'beige', 'navy', 'maroon', 'burgundy',
            'coral', 'ivory', 'cream', 'tan', 'khaki', 'magenta', 'cyan', 'teal',
            'olive', 'lime', 'gold', 'silver', 'bronze', 'copper', 'amber',
            'deep', 'light', 'dark', 'bright', 'pale', 'vibrant', 'rose', 'peach',
            'mint', 'lavender', 'indigo', 'turquoise', 'salmon', 'champagne'
          ];
          
          // Check if title contains any color keyword
          const titleLower = title.toLowerCase();
          return colorKeywords.some(keyword => titleLower.includes(keyword));
        });
        
        if (colorVariant) {
          const variant = colorVariant as Record<string, unknown>;
          const featuredImage = variant.featured_image as Record<string, unknown> | undefined;
          if (featuredImage?.src) {
            return String(featuredImage.src);
          }
        }
      }
    }
    return null;
  };

  // Get image source - prioritize variant color image if available
  const variantColorImage = getVariantColorImage();
  const imageSrc =
    variantColorImage ||
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
  
  const shouldShowCategory = category && category.toLowerCase() !== "uncategorized";

  const handleCardClick = () => {
    router.push(ROUTES.PRODUCT_DETAIL(product.id));
  };

  return (
    <Card 
      className="flex flex-col h-full hover:shadow-lg transition-all duration-300 cursor-pointer border-border/50 hover:border-primary/20"
      onClick={handleCardClick}
    >
      <CardHeader className="shrink-0 pb-2 lg:pb-3">
        <div className="w-full overflow-hidden rounded-lg bg-[#EEECEA] mb-2 lg:mb-3 relative h-[180px] lg:h-[200px] flex items-center justify-center group">
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
        <CardTitle className="line-clamp-3 min-h-12 lg:min-h-14 text-sm lg:text-base font-semibold leading-tight mb-1">
          {title}
        </CardTitle>
        {shouldShowCategory && (
          <CardDescription className="line-clamp-1 text-xs text-muted-foreground">
            {category}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent className="flex-1 flex flex-col">
        <p className="text-xs lg:text-sm text-muted-foreground line-clamp-2 flex-1 mb-3 lg:mb-4">
          {description}
        </p>
        <div className="flex flex-col gap-1 shrink-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-xl lg:text-2xl font-bold">
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
      <CardFooter className="shrink-0 flex flex-col gap-2 lg:gap-2.5 relative z-10 pt-3 lg:pt-4 border-t">
        {/* Add to Cart and Compare in one row */}
        <div className={`flex gap-2 w-full ${showCompare ? '' : 'flex-col'}`} onClick={(e) => e.stopPropagation()}>
          <AddToCartButton 
            product={product} 
            size="default"
            className={showCompare ? "flex-1 text-xs lg:text-xs h-8 lg:h-9" : "w-full text-xs lg:text-xs h-8 lg:h-9"}
          />
          {showCompare && (
            <CompareButton 
              product={product} 
              variant="outline"
              size="default"
              className="flex-1 text-xs lg:text-xs h-8 lg:h-9"
          />
          )}
        </div>
        {/* View Details button at bottom - same width as upper buttons row */}
        <div className="w-full" onClick={(e) => e.stopPropagation()}>
          <Button 
            className="w-full text-xs lg:text-xs h-8 lg:h-9" 
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

