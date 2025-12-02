"use client";

import { Button } from "@/components/ui/button";
import { useCart } from "@/contexts/cart-context";
import type { Product } from "@/types/product";
import { ShoppingCart, Check } from "lucide-react";
import { toast } from "sonner";

interface AddToCartButtonProps {
  product: Product;
  variant?: "default" | "outline" | "ghost" | "link" | "destructive" | "secondary";
  size?: "default" | "sm" | "lg" | "icon";
  className?: string;
  quantity?: number;
  showIcon?: boolean;
}

export function AddToCartButton({
  product,
  variant = "default",
  size = "default",
  className = "",
  quantity = 1,
  showIcon = true,
}: AddToCartButtonProps) {
  const { addItem, isInCart, getItemQuantity } = useCart();
  const inCart = isInCart(product.id);
  const cartQuantity = getItemQuantity(product.id);

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    
    addItem(product, quantity);
    const newQuantity = cartQuantity + quantity;
    
    toast.success("Added to cart", {
      description: `${product.title} has been added to your cart.${newQuantity > 1 ? ` (${newQuantity} in cart)` : ""}`,
    });
  };

  return (
    <Button
      variant={inCart ? "secondary" : variant}
      size={size}
      onClick={handleClick}
      className={`relative z-10 ${className}`}
      aria-label={inCart ? `Update quantity of ${product.title} in cart` : `Add ${product.title} to cart`}
      type="button"
    >
      {showIcon && (
        <>
          {inCart ? (
            <Check className="h-4 w-4 mr-2" />
          ) : (
            <ShoppingCart className="h-4 w-4 mr-2" />
          )}
        </>
      )}
      {inCart ? `In Cart (${cartQuantity})` : "Add to Cart"}
    </Button>
  );
}

