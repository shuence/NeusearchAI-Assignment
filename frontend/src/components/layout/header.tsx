"use client";

import Link from "next/link";
import { useState } from "react";
import { useComparison } from "@/contexts/comparison-context";
import { useCart } from "@/contexts/cart-context";
import { useOrders } from "@/contexts/order-context";
import { ROUTES } from "@/lib/constants";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Scale, ShoppingCart, History } from "lucide-react";

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { products } = useComparison();
  const { getTotalItems } = useCart();
  const { getTotalOrders } = useOrders();
  const comparisonCount = products.length;
  const cartCount = getTotalItems();
  const orderCount = getTotalOrders();

  return (
    <header className="border-b sticky top-0 bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/60 z-50">
      <div className="container mx-auto px-4 py-3 sm:py-4">
        <div className="flex items-center justify-between">
          <Link href={ROUTES.HOME} className="flex flex-col">
            <h1 className="text-xl sm:text-2xl font-bold">Neusearch AI</h1>
            <p className="hidden sm:block text-sm text-muted-foreground">
              Product Discovery Assistant
            </p>
          </Link>
          
          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-4">
            <Link
              href={ROUTES.HOME}
              className="text-sm font-medium hover:text-primary transition-colors"
            >
              Products
            </Link>
            <Link
              href={ROUTES.CHAT}
              className="text-sm font-medium hover:text-primary transition-colors"
            >
              Chat
            </Link>
            <Link
              href={ROUTES.COMPARE}
              className="text-sm font-medium hover:text-primary transition-colors flex items-center gap-2 relative"
            >
              <Scale className="h-4 w-4" />
              Compare
              {comparisonCount > 0 && (
                <Badge 
                  variant="default" 
                  className="h-5 w-5 p-0 flex items-center justify-center text-xs absolute -top-2 -right-2"
                >
                  {comparisonCount}
                </Badge>
              )}
            </Link>
            <Link
              href={ROUTES.CART}
              className="text-sm font-medium hover:text-primary transition-colors flex items-center gap-2 relative"
            >
              <ShoppingCart className="h-4 w-4" />
              Cart
              {cartCount > 0 && (
                <Badge 
                  variant="default" 
                  className="h-5 w-5 p-0 flex items-center justify-center text-xs absolute -top-2 -right-2"
                >
                  {cartCount}
                </Badge>
              )}
            </Link>
            <Link
              href={ROUTES.ORDER_HISTORY}
              className="text-sm font-medium hover:text-primary transition-colors flex items-center gap-2"
              title="Order History"
            >
              <History className="h-4 w-4" />
              Orders
              {orderCount > 0 && (
                <Badge variant="secondary" className="ml-1">
                  {orderCount}
                </Badge>
              )}
            </Link>
            <ThemeToggle />
          </nav>

          {/* Mobile Navigation */}
          <div className="flex md:hidden items-center gap-2">
            <ThemeToggle />
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle menu"
            >
              <svg
                className="h-6 w-6"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                {mobileMenuOpen ? (
                  <path d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </Button>
          </div>
        </div>

        {/* Mobile Menu Dropdown */}
        {mobileMenuOpen && (
          <nav className="md:hidden mt-4 pb-2 border-t pt-4 flex flex-col gap-3">
            <Link
              href={ROUTES.HOME}
              className="text-sm font-medium hover:text-primary transition-colors py-2"
              onClick={() => setMobileMenuOpen(false)}
            >
              Products
            </Link>
            <Link
              href={ROUTES.CHAT}
              className="text-sm font-medium hover:text-primary transition-colors py-2"
              onClick={() => setMobileMenuOpen(false)}
            >
              Chat
            </Link>
            <Link
              href={ROUTES.COMPARE}
              className="text-sm font-medium hover:text-primary transition-colors py-2 flex items-center gap-2"
              onClick={() => setMobileMenuOpen(false)}
            >
              <Scale className="h-4 w-4" />
              Compare
              {comparisonCount > 0 && (
                <Badge 
                  variant="default" 
                  className="h-5 w-5 p-0 flex items-center justify-center text-xs"
                >
                  {comparisonCount}
                </Badge>
              )}
            </Link>
            <Link
              href={ROUTES.CART}
              className="text-sm font-medium hover:text-primary transition-colors py-2 flex items-center gap-2"
              onClick={() => setMobileMenuOpen(false)}
            >
              <ShoppingCart className="h-4 w-4" />
              Cart
              {cartCount > 0 && (
                <Badge 
                  variant="default" 
                  className="h-5 w-5 p-0 flex items-center justify-center text-xs"
                >
                  {cartCount}
                </Badge>
              )}
            </Link>
            <Link
              href={ROUTES.ORDER_HISTORY}
              className="text-sm font-medium hover:text-primary transition-colors py-2 flex items-center gap-2"
              onClick={() => setMobileMenuOpen(false)}
            >
              <History className="h-4 w-4" />
              Orders
              {orderCount > 0 && (
                <Badge variant="secondary" className="ml-1">
                  {orderCount}
                </Badge>
              )}
            </Link>
          </nav>
        )}
      </div>
    </header>
  );
}

