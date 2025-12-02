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

  const handleVariantClick = (variant: Variant, variantIndex: number) => {
    if (!api) return;
    
    if (variant.featured_image?.src) {
      const variantImageUrl = variant.featured_image.src;
      const imageIndex = allImages.findIndex((img) => img === variantImageUrl);
      
      if (imageIndex !== -1) {
        api.scrollTo(imageIndex);
        return;
      }
    }
    
    if (allImages.length > 0) {
      const imageIndex = variantIndex;
      const targetIndex = Math.min(imageIndex, allImages.length - 1);
      api.scrollTo(targetIndex);
    }
  };

  return (
    <div className="w-full space-y-4">
      <Carousel setApi={setApi} className="w-full">
        <CarouselContent>
          {allImages.map((imageUrl, index) => (
            <CarouselItem key={index}>
              <div className="w-full overflow-hidden rounded-lg bg-muted relative min-h-[400px] flex items-center justify-center">
                <Image
                  src={imageUrl || "/placeholder.png"}
                  alt={`Product image ${index + 1}`}
                  width={1200}
                  height={1200}
                  className="object-contain w-full h-auto max-h-[600px]"
                  sizes="(max-width: 768px) 100vw, 50vw"
                  unoptimized
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
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-muted-foreground">Variants</h3>
          <div className="flex flex-wrap gap-2">
            {variants.map((variant, index) => {
              const variantLabel = [
                variant.option1,
                variant.option2,
                variant.option3,
              ]
                .filter(Boolean)
                .join(" / ") || variant.title || `Variant ${index + 1}`;
              
              const isActive = variant.featured_image?.src 
                ? selectedImage === variant.featured_image.src
                : current === index + 1;
              
              return (
                <button
                  key={index}
                  type="button"
                  onClick={() => handleVariantClick(variant, index)}
                  className={`px-4 py-2 rounded-md border transition-all cursor-pointer ${
                    isActive
                      ? "border-primary bg-primary/10"
                      : "border-muted hover:border-primary/50"
                  }`}
                  title={`Click to view ${variantLabel}`}
                >
                  <span className="text-sm">{variantLabel}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

