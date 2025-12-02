"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { ROUTES } from "@/lib/constants";
import { CheckCircle2, Package, Mail, Phone, MapPin, ArrowLeft, Home, History } from "lucide-react";
import { useOrders } from "@/contexts/order-context";

interface OrderData {
  customer: {
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
  };
  shipping: {
    address: string;
    city: string;
    state: string;
    zipCode: string;
    country: string;
  };
  payment: {
    method: string;
    cardNumber?: string;
  };
  items: Array<{
    productId: string;
    productTitle: string;
    quantity: number;
    price: number;
    total: number;
  }>;
  total: number;
  notes?: string;
  orderDate: string;
}

export default function OrderSuccessPage() {
  const router = useRouter();
  const { getOrderByNumber } = useOrders();
  const [orderData, setOrderData] = useState<OrderData | null>(null);
  const [orderNumber, setOrderNumber] = useState<string>("");

  useEffect(() => {
    // Load order data from localStorage
    const stored = localStorage.getItem("neusearch_last_order");
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setOrderData(parsed);
        setOrderNumber(parsed.orderNumber || `ORD-${Date.now()}`);
      } catch (error) {
        console.error("Error parsing order data:", error);
        router.push(ROUTES.HOME);
      }
    } else {
      // No order data, redirect to home
      router.push(ROUTES.HOME);
    }
  }, [router]);

  if (!orderData) {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        <Header />
        <main className="container mx-auto px-4 py-8 flex-1 flex items-center justify-center">
          <div className="text-center">
            <p className="text-muted-foreground">Loading order details...</p>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  const subtotal = orderData.items.reduce((sum, item) => sum + item.total, 0);
  const shippingCost = (orderData as any).shippingCost || 50;
  const tax = (orderData as any).tax || subtotal * 0.18;
  const total = (orderData as any).total || subtotal + shippingCost + tax;

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header />
      <main className="container mx-auto px-4 py-8 flex-1">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Success Header */}
          <div className="text-center space-y-4">
            <div className="flex justify-center">
              <div className="rounded-full bg-green-100 dark:bg-green-900/20 p-4">
                <CheckCircle2 className="h-16 w-16 text-green-600 dark:text-green-400" />
              </div>
            </div>
            <h1 className="text-4xl font-bold">Order Confirmed!</h1>
            <p className="text-muted-foreground text-lg">
              Thank you for your purchase. Your order has been received and is being processed.
            </p>
            <Badge variant="secondary" className="text-lg px-4 py-2">
              Order Number: {orderNumber}
            </Badge>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Order Details */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Package className="h-5 w-5" />
                  Order Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground">Order Date</p>
                  <p className="font-medium">
                    {new Date(orderData.orderDate).toLocaleDateString("en-IN", {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Items Ordered</p>
                  <div className="space-y-2">
                    {orderData.items.map((item, index) => (
                      <div key={index} className="flex justify-between text-sm">
                        <span>
                          {item.productTitle} × {item.quantity}
                        </span>
                        <span className="font-medium">₹{item.total.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="border-t pt-4 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Subtotal</span>
                    <span className="font-medium">₹{subtotal.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Shipping</span>
                    <span className="font-medium">₹{shippingCost.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Tax (GST 18%)</span>
                    <span className="font-medium">₹{Math.round(tax).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-lg font-bold border-t pt-2">
                    <span>Total</span>
                    <span>₹{Math.round(total).toLocaleString()}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Customer & Shipping Information */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MapPin className="h-5 w-5" />
                  Delivery Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Customer</p>
                  <p className="font-medium">
                    {orderData.customer.firstName} {orderData.customer.lastName}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1 flex items-center gap-1">
                    <Mail className="h-3 w-3" />
                    Email
                  </p>
                  <p className="font-medium">{orderData.customer.email}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1 flex items-center gap-1">
                    <Phone className="h-3 w-3" />
                    Phone
                  </p>
                  <p className="font-medium">{orderData.customer.phone}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Shipping Address</p>
                  <p className="font-medium">
                    {orderData.shipping.address}
                    <br />
                    {orderData.shipping.city}, {orderData.shipping.state} {orderData.shipping.zipCode}
                    <br />
                    {orderData.shipping.country}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Payment Method</p>
                  <p className="font-medium">
                    {orderData.payment.method === "cod"
                      ? "Cash on Delivery"
                      : `Card ending in ${orderData.payment.cardNumber || "****"}`}
                  </p>
                </div>
                {orderData.notes && (
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Order Notes</p>
                    <p className="font-medium">{orderData.notes}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Next Steps */}
          <Card>
            <CardHeader>
              <CardTitle>What's Next?</CardTitle>
              <CardDescription>
                Here's what happens after you place your order
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex gap-3">
                  <div className="shrink-0 w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">
                    1
                  </div>
                  <div>
                    <p className="font-medium">Order Confirmation</p>
                    <p className="text-sm text-muted-foreground">
                      You'll receive an email confirmation with your order details.
                    </p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="shrink-0 w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">
                    2
                  </div>
                  <div>
                    <p className="font-medium">Order Processing</p>
                    <p className="text-sm text-muted-foreground">
                      We'll prepare your order for shipment within 1-2 business days.
                    </p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="shrink-0 w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">
                    3
                  </div>
                  <div>
                    <p className="font-medium">Shipping</p>
                    <p className="text-sm text-muted-foreground">
                      You'll receive tracking information once your order ships.
                    </p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="shrink-0 w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">
                    4
                  </div>
                  <div>
                    <p className="font-medium">Delivery</p>
                    <p className="text-sm text-muted-foreground">
                      Your order will arrive within 5-7 business days.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href={ROUTES.HOME}>
              <Button size="lg" variant="default">
                <Home className="h-4 w-4 mr-2" />
                Continue Shopping
              </Button>
            </Link>
            <Link href={ROUTES.ORDER_HISTORY}>
              <Button size="lg" variant="outline">
                <History className="h-4 w-4 mr-2" />
                View Order History
              </Button>
            </Link>
            <Button
              size="lg"
              variant="outline"
              onClick={() => window.print()}
            >
              Print Order Details
            </Button>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}

