"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useComparison } from "@/contexts/comparison-context";
import { ROUTES } from "@/lib/constants";
import type { Product } from "@/types/product";
import { Scale, Check } from "lucide-react";
import { toast } from "sonner";

interface CompareButtonProps {
  product: Product;
  variant?: "default" | "outline" | "ghost";
  size?: "default" | "sm" | "lg" | "icon";
  className?: string;
}

export function CompareButton({ 
  product, 
  variant = "outline", 
  size = "default",
  className = "" 
}: CompareButtonProps) {
  const router = useRouter();
  const { addProduct, removeProduct, isInComparison, canAddMore, products } = useComparison();
  const inComparison = isInComparison(product.id);

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (inComparison) {
      removeProduct(product.id);
      toast.success("Removed from comparison", {
        description: `${product.title} has been removed from comparison.`,
      });
    } else {
      if (!canAddMore) {
        toast.error("Comparison limit reached", {
          description: "You can compare up to 4 products at a time. Remove a product to add another.",
          action: {
            label: "View Comparison",
            onClick: () => router.push(ROUTES.COMPARE),
          },
        });
        return;
      }
      addProduct(product);
      const newCount = products.length + 1;
      toast.success("Added to comparison", {
        description: `${product.title} has been added. ${newCount} of 4 products selected.`,
        action: newCount >= 2 ? {
          label: "Compare Now",
          onClick: () => router.push(ROUTES.COMPARE),
        } : undefined,
      });
    }
  };

  return (
    <Button
      variant={inComparison ? "default" : variant}
      size={size}
      onClick={handleClick}
      className={className}
      aria-label={inComparison ? "Remove from comparison" : "Add to comparison"}
    >
      {inComparison ? (
        <>
          <Check className="h-4 w-4 mr-2" />
          In Comparison
        </>
      ) : (
        <>
          <Scale className="h-4 w-4 mr-2" />
          Compare
        </>
      )}
    </Button>
  );
}

