"use client";

import { useMemo } from "react";
import Image from "next/image";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
  type CarouselApi,
} from "@/components/ui/carousel";
import { useState, useEffect } from "react";

interface Variant {
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
}

interface ProductImageCarouselProps {
  mainImage: string;
  imageUrls?: string[];
  variants?: Variant[];
}

export function ProductImageCarousel({
  mainImage,
  imageUrls,
  variants,
}: ProductImageCarouselProps) {
  const variantImages = variants
    ?.map((variant) => variant.featured_image?.src)
    .filter((src): src is string => Boolean(src)) || [];

  const allImages = useMemo(() => {
    const images = [
      mainImage,
      ...(imageUrls || []),
      ...variantImages,
    ].filter((img, index, self) => img && self.indexOf(img) === index);
    
    return images;
  }, [mainImage, imageUrls, variantImages]);

  const [api, setApi] = useState<CarouselApi>();
  const [current, setCurrent] = useState(0);
  const [count, setCount] = useState(0);
  const [selectedColor, setSelectedColor] = useState<string | null>(null);
  const [selectedSize, setSelectedSize] = useState<string | null>(null);

  useEffect(() => {
    if (!api) {
      return;
    }

    setCount(api.scrollSnapList().length);
    setCurrent(api.selectedScrollSnap() + 1);

    api.on("select", () => {
      setCurrent(api.selectedScrollSnap() + 1);
    });
  }, [api]);


  const selectedImage = allImages[current - 1] || allImages[0] || mainImage;

  const scrollToImage = (imageUrl: string) => {
    if (!api) return;
    
    // Try exact match first
    let imageIndex = allImages.findIndex((img) => {
      const imgStr = String(img);
      return imgStr === imageUrl || imgStr.trim() === imageUrl.trim();
    });
    
    // If not found, try partial match (in case URLs are slightly different)
    if (imageIndex === -1) {
      imageIndex = allImages.findIndex((img) => {
        const imgStr = String(img);
        // Normalize URLs for comparison
        const normalizedVariant = imageUrl.replace(/^https?:\/\//, '').split('?')[0];
        const normalizedImg = imgStr.replace(/^https?:\/\//, '').split('?')[0];
        return normalizedImg.includes(normalizedVariant) || normalizedVariant.includes(normalizedImg);
      });
    }
    
    // If still not found, try to match by extracting filename or key parts
    if (imageIndex === -1) {
      const variantUrlParts = imageUrl.split('/').pop()?.split('?')[0]?.toLowerCase();
      imageIndex = allImages.findIndex((img) => {
        const imgStr = String(img);
        const imgParts = imgStr.split('/').pop()?.split('?')[0]?.toLowerCase();
        return variantUrlParts && imgParts && variantUrlParts === imgParts;
      });
    }
    
    if (imageIndex !== -1) {
      // Use requestAnimationFrame to ensure carousel is ready
      requestAnimationFrame(() => {
        try {
          api.scrollTo(imageIndex);
        } catch (error) {
          // Fallback: try with a small delay
          setTimeout(() => {
            try {
              api.scrollTo(imageIndex);
            } catch (e) {
              // Silently fail if still can't scroll
            }
          }, 150);
        }
      });
    }
  };

  const handleColorClick = (color: string) => {
    setSelectedColor(color);
    
    // If size is already selected, find exact variant
    if (selectedSize && variants) {
      const matchingVariant = variants.find(
        (v) => v.option1 === color && v.option2 === selectedSize
      );
      if (matchingVariant?.featured_image?.src) {
        scrollToImage(String(matchingVariant.featured_image.src));
        return;
      }
    }
    
    // Otherwise, find first variant with this color and show its image
    if (variants) {
      const colorVariant = variants.find((v) => v.option1 === color);
      if (colorVariant?.featured_image?.src) {
        scrollToImage(String(colorVariant.featured_image.src));
      }
    }
  };

  const handleSizeClick = (size: string) => {
    setSelectedSize(size);
    
    // If color is already selected, find exact variant
    if (selectedColor && variants) {
      const matchingVariant = variants.find(
        (v) => v.option1 === selectedColor && v.option2 === size
      );
      if (matchingVariant?.featured_image?.src) {
        scrollToImage(String(matchingVariant.featured_image.src));
      }
    }
  };

  return (
    <div className="w-full space-y-4">
      <Carousel setApi={setApi} className="w-full">
        <CarouselContent>
          {allImages.map((imageUrl, index) => (
            <CarouselItem key={index}>
              <div className="w-full overflow-hidden rounded-lg bg-[#EEECEB] relative min-h-[400px] flex items-center justify-center">
                <Image
                  src={imageUrl || "/placeholder.png"}
                  alt={`Product image ${index + 1}`}
                  width={1200}
                  height={1200}
                  className="object-contain w-full h-auto max-h-[600px]"
                  sizes="(max-width: 768px) 100vw, 50vw"
                  loading="lazy"
                  placeholder="blur"
                  blurDataURL="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIwMCIgaGVpZ2h0PSIxMjAwIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9IiNkZGQiLz48L3N2Zz4="
                />
              </div>
            </CarouselItem>
          ))}
        </CarouselContent>
        {allImages.length > 1 && (
          <>
            <CarouselPrevious className="left-4" />
            <CarouselNext className="right-4" />
          </>
        )}
      </Carousel>

      {allImages.length > 1 && (
        <div className="text-center text-sm text-muted-foreground">
          Image {current} of {count}
        </div>
      )}

      {variants && variants.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-foreground">Color & Size</h3>
          
          {/* Colors Row */}
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">Color</p>
            <div className="flex flex-wrap gap-2">
              {(() => {
                const uniqueColors = Array.from(
                  new Set(variants.map((v) => v.option1).filter((c): c is string => Boolean(c)))
                );
                return uniqueColors.map((color) => (
                  <button
                    key={color}
                    type="button"
                    onClick={() => handleColorClick(color)}
                    className={`px-4 py-2 rounded-md border text-sm transition-all cursor-pointer ${
                      selectedColor === color
                        ? "border-primary bg-primary text-primary-foreground"
                        : "border-muted hover:border-primary/50 hover:bg-primary/5"
                    }`}
                  >
                    {color}
                  </button>
                ));
              })()}
            </div>
          </div>

          {/* Sizes Row */}
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">Size</p>
            <div className="flex flex-wrap gap-2">
              {(() => {
                // Filter sizes based on selected color if one is selected
                const availableSizes = selectedColor
                  ? Array.from(
                      new Set(
                        variants
                          .filter((v) => v.option1 === selectedColor)
                          .map((v) => v.option2)
                          .filter((s): s is string => Boolean(s))
                      )
                    )
                  : Array.from(
                      new Set(variants.map((v) => v.option2).filter((s): s is string => Boolean(s)))
                    );

                return availableSizes.map((size) => {
                  // Check if this size is available for selected color
                  const isAvailable = selectedColor
                    ? variants.some(
                        (v) =>
                          v.option1 === selectedColor &&
                          v.option2 === size &&
                          v.available !== false
                      )
                    : variants.some(
                        (v) => v.option2 === size && v.available !== false
                      );

                  return (
                    <button
                      key={size}
                      type="button"
                      onClick={() => handleSizeClick(size)}
                      className={`px-3 py-1.5 rounded-md border text-sm transition-all cursor-pointer ${
                        selectedSize === size
                          ? "border-primary bg-primary text-primary-foreground"
                          : !isAvailable
                          ? "border-muted bg-muted text-muted-foreground opacity-50 cursor-not-allowed"
                          : "border-muted hover:border-primary/50 hover:bg-primary/5"
                      }`}
                      disabled={!isAvailable}
                      title={size + (!isAvailable ? " (Out of stock)" : "")}
                    >
                      {size}
                    </button>
                  );
                });
              })()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

