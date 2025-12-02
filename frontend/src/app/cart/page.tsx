"use client";

import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { useCart } from "@/contexts/cart-context";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import Image from "next/image";
import Link from "next/link";
import { ROUTES } from "@/lib/constants";
import { ShoppingCart, Plus, Minus, Trash2, ArrowLeft } from "lucide-react";
import { toast } from "sonner";

export default function CartPage() {
  const {
    items,
    removeItem,
    updateQuantity,
    clearCart,
    getTotalItems,
    getTotalPrice,
  } = useCart();

  const handleQuantityChange = (productId: string, newQuantity: number) => {
    if (newQuantity < 1) {
      removeItem(productId);
      toast.success("Item removed from cart");
      return;
    }
    updateQuantity(productId, newQuantity);
  };

  const handleIncrement = (productId: string, currentQuantity: number) => {
    handleQuantityChange(productId, currentQuantity + 1);
  };

  const handleDecrement = (productId: string, currentQuantity: number) => {
    handleQuantityChange(productId, currentQuantity - 1);
  };

  const handleRemove = (productId: string, productTitle: string) => {
    removeItem(productId);
    toast.success("Removed from cart", {
      description: `${productTitle} has been removed from your cart.`,
    });
  };

  const handleClearCart = () => {
    if (items.length === 0) return;
    
    clearCart();
    toast.success("Cart cleared", {
      description: "All items have been removed from your cart.",
    });
  };

  if (items.length === 0) {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        <Header />
        <main className="container mx-auto px-4 py-8 flex-1 flex flex-col items-center justify-center">
          <div className="text-center space-y-4 max-w-md">
            <ShoppingCart className="h-16 w-16 mx-auto text-muted-foreground" />
            <h1 className="text-3xl font-bold">Your cart is empty</h1>
            <p className="text-muted-foreground">
              Looks like you haven't added any items to your cart yet.
            </p>
            <Link href={ROUTES.HOME}>
              <Button size="lg" className="mt-4">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Continue Shopping
              </Button>
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header />
      <main className="container mx-auto px-4 py-8 flex-1">
        <div className="mb-6">
          <Link
            href={ROUTES.HOME}
            className="text-sm text-muted-foreground hover:text-foreground mb-6 inline-flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Continue Shopping
          </Link>
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold">Shopping Cart</h1>
            <Button
              variant="outline"
              size="sm"
              onClick={handleClearCart}
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Clear Cart
            </Button>
          </div>
          <p className="text-muted-foreground mt-2">
            {getTotalItems()} {getTotalItems() === 1 ? "item" : "items"} in your cart
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Cart Items */}
          <div className="lg:col-span-2 space-y-4">
            {items.map((item) => {
              const imageSrc =
                item.product.image ||
                item.product.imageUrl ||
                item.product.image_urls?.[0] ||
                "/placeholder.png";

              return (
                <Card key={item.product.id}>
                  <CardContent className="p-4">
                    <div className="flex gap-4">
                      <Link
                        href={ROUTES.PRODUCT_DETAIL(item.product.id)}
                        className="shrink-0"
                      >
                        <div className="w-24 h-24 md:w-32 md:h-32 rounded-lg overflow-hidden bg-[#EEECEB] relative">
                          <Image
                            src={imageSrc}
                            alt={item.product.title}
                            fill
                            className="object-contain"
                            sizes="(max-width: 768px) 96px, 128px"
                          />
                        </div>
                      </Link>

                      <div className="flex-1 flex flex-col justify-between min-w-0">
                        <div>
                          <Link
                            href={ROUTES.PRODUCT_DETAIL(item.product.id)}
                            className="hover:text-primary"
                          >
                            <h3 className="font-semibold text-lg line-clamp-2">
                              {item.product.title}
                            </h3>
                          </Link>
                          <p className="text-sm text-muted-foreground mt-1">
                            {item.product.category || item.product.vendor}
                          </p>
                          <p className="text-xl font-bold mt-2">
                            ₹{item.product.price.toLocaleString()}
                          </p>
                        </div>

                        <div className="flex items-center justify-between mt-4">
                          {/* Quantity Controls */}
                          <div className="flex items-center gap-2">
                            <Button
                              variant="outline"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => handleDecrement(item.product.id, item.quantity)}
                              aria-label="Decrease quantity"
                            >
                              <Minus className="h-4 w-4" />
                            </Button>
                            <Input
                              type="number"
                              min="1"
                              value={item.quantity}
                              onChange={(e) => {
                                const value = parseInt(e.target.value, 10);
                                if (!isNaN(value)) {
                                  handleQuantityChange(item.product.id, value);
                                }
                              }}
                              className="w-16 text-center h-8"
                            />
                            <Button
                              variant="outline"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => handleIncrement(item.product.id, item.quantity)}
                              aria-label="Increase quantity"
                            >
                              <Plus className="h-4 w-4" />
                            </Button>
                          </div>

                          {/* Remove Button */}
                          <Button 
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemove(item.product.id, item.product.title)}
                            className="text-destructive hover:text-destructive bg-destructive/10"
                            aria-label={`Remove ${item.product.title} from cart`}
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Remove
                          </Button>
                        </div>
                      </div>

                      {/* Item Total */}
                      <div className="text-right shrink-0">
                        <p className="text-lg font-bold">
                          ₹{(item.product.price * item.quantity).toLocaleString()}
                        </p>
                        {item.quantity > 1 && (
                          <p className="text-sm text-muted-foreground">
                            ₹{item.product.price.toLocaleString()} each
                          </p>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Order Summary */}
          <div className="lg:col-span-1">
            <Card className="sticky top-24">
              <CardHeader>
                <CardTitle>Order Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Subtotal ({getTotalItems()} items)</span>
                    <span className="font-medium">₹{getTotalPrice().toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Shipping</span>
                    <span className="font-medium">Calculated at checkout</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Tax</span>
                    <span className="font-medium">Calculated at checkout</span>
                  </div>
                </div>
                <div className="border-t pt-4">
                  <div className="flex justify-between text-lg font-bold">
                    <span>Total</span>
                    <span>₹{getTotalPrice().toLocaleString()}</span>
                  </div>
                </div>
                <Link href={ROUTES.CHECKOUT}>
                  <Button size="lg" className="w-full mt-4">
                    Proceed to Checkout
                  </Button>
                </Link>
                <div className="flex flex-col gap-2"></div>
                <Link href={ROUTES.HOME}>
                  <Button variant="outline" size="lg" className="w-full">
                    Continue Shopping
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}

