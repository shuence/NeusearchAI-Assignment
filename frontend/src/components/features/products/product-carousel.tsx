"use client";

import { useRef } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ProductCard } from "./product-card";
import type { Product } from "@/types/product";

interface ProductCarouselProps {
  products: Product[];
  cardWidth?: number; // Optional card width in pixels (default responsive)
}

export function ProductCarousel({ products, cardWidth }: ProductCarouselProps) {
  // Responsive card width: smaller on mobile, larger on desktop
  const responsiveCardWidth = cardWidth || 280;
  const scrollRef = useRef<HTMLDivElement>(null);

  const scroll = (direction: "left" | "right") => {
    if (scrollRef.current) {
      const scrollAmount = responsiveCardWidth + 12;
      const currentScroll = scrollRef.current.scrollLeft;
      const newScroll =
        direction === "left"
          ? currentScroll - scrollAmount
          : currentScroll + scrollAmount;
      scrollRef.current.scrollTo({
        left: newScroll,
        behavior: "smooth",
      });
    }
  };

  if (products.length === 0) return null;

  return (
    <div className="relative group">
      {/* Scrollable Container */}
      <div
        ref={scrollRef}
        className="flex gap-3 overflow-x-auto pb-12 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none] snap-x snap-mandatory items-stretch"
      >
        {products.map((product) => (
          <div
            key={product.id}
            className="shrink-0 snap-start flex"
            style={{ width: `${responsiveCardWidth}px` }}
          >
            <ProductCard product={product} showCompare={false} />
          </div>
        ))}
      </div>

      {/* Bottom Arrows */}
      {products.length > 1 && (
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 flex gap-2 z-10 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity">
          <Button
            variant="outline"
            size="icon"
            className="h-9 w-9 sm:h-8 sm:w-8 rounded-full bg-background dark:bg-card backdrop-blur-sm shadow-lg border-2 border-border hover:bg-muted dark:hover:bg-muted/50 text-foreground touch-manipulation"
            onClick={() => scroll("left")}
            aria-label="Scroll left"
          >
            <ChevronLeft className="h-4 w-4 sm:h-4 sm:w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="h-9 w-9 sm:h-8 sm:w-8 rounded-full bg-background dark:bg-card backdrop-blur-sm shadow-lg border-2 border-border hover:bg-muted dark:hover:bg-muted/50 text-foreground touch-manipulation"
            onClick={() => scroll("right")}
            aria-label="Scroll right"
          >
            <ChevronRight className="h-4 w-4 sm:h-4 sm:w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}

