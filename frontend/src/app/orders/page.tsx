"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { useOrders } from "@/contexts/order-context";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { ROUTES } from "@/lib/constants";
import { History, Package, ArrowLeft, Eye, Calendar } from "lucide-react";
import Image from "next/image";

export default function OrderHistoryPage() {
  const router = useRouter();
  const { orders, getOrdersByStatus } = useOrders();
  const [statusFilter, setStatusFilter] = useState<
    "all" | "pending" | "processing" | "shipped" | "delivered" | "cancelled"
  >("all");

  const filteredOrders =
    statusFilter === "all"
      ? orders
      : getOrdersByStatus(statusFilter as "pending" | "processing" | "shipped" | "delivered" | "cancelled");

  const getStatusColor = (status: string) => {
    switch (status) {
      case "pending":
        return "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400";
      case "processing":
        return "bg-blue-500/10 text-blue-600 dark:text-blue-400";
      case "shipped":
        return "bg-purple-500/10 text-purple-600 dark:text-purple-400";
      case "delivered":
        return "bg-green-500/10 text-green-600 dark:text-green-400";
      case "cancelled":
        return "bg-red-500/10 text-red-600 dark:text-red-400";
      default:
        return "bg-gray-500/10 text-gray-600 dark:text-gray-400";
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-IN", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (orders.length === 0) {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        <Header />
        <main className="container mx-auto px-4 py-8 flex-1 flex flex-col items-center justify-center">
          <div className="text-center space-y-4 max-w-md">
            <History className="h-16 w-16 mx-auto text-muted-foreground" />
            <h1 className="text-3xl font-bold">No Orders Yet</h1>
            <p className="text-muted-foreground">
              You haven't placed any orders yet. Start shopping to see your order history here.
            </p>
            <Link href={ROUTES.HOME}>
              <Button size="lg" className="mt-4">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Start Shopping
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
            Back to Home
          </Link>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-2">
                <History className="h-8 w-8" />
                Order History
              </h1>
              <p className="text-muted-foreground mt-2">
                {orders.length} {orders.length === 1 ? "order" : "orders"} total
              </p>
            </div>
          </div>
        </div>

        {/* Status Filter */}
        <div className="mb-6 flex flex-wrap gap-2">
          {(["all", "pending", "processing", "shipped", "delivered", "cancelled"] as const).map(
            (status) => (
              <Button
                key={status}
                variant={statusFilter === status ? "default" : "outline"}
                size="sm"
                onClick={() => setStatusFilter(status)}
                className="capitalize"
              >
                {status === "all" ? "All Orders" : status}
                {status !== "all" && (
                  <Badge variant="secondary" className="ml-2">
                    {getOrdersByStatus(status as any).length}
                  </Badge>
                )}
              </Button>
            )
          )}
        </div>

        {/* Orders List */}
        <div className="space-y-4">
          {filteredOrders.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Package className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">
                  No orders found with status: <strong>{statusFilter}</strong>
                </p>
              </CardContent>
            </Card>
          ) : (
            filteredOrders.map((order) => (
              <Card key={order.id} className="hover:shadow-lg transition-shadow">
                <CardContent className="p-6">
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        <h3 className="text-lg font-semibold">{order.orderNumber}</h3>
                        <Badge className={getStatusColor(order.status)}>
                          {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          {formatDate(order.orderDate)}
                        </div>
                        <div className="flex items-center gap-1">
                          <Package className="h-4 w-4" />
                          {order.items.length} {order.items.length === 1 ? "item" : "items"}
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2 mb-3">
                        {order.items.slice(0, 3).map((item, index) => {
                          const imageSrc = item.image || "/placeholder.png";
                          return (
                            <div
                              key={index}
                              className="w-12 h-12 rounded-lg overflow-hidden bg-[#EEECEB] relative"
                            >
                              <Image
                                src={imageSrc}
                                alt={item.productTitle}
                                fill
                                className="object-contain"
                                sizes="48px"
                              />
                            </div>
                          );
                        })}
                        {order.items.length > 3 && (
                          <div className="w-12 h-12 rounded-lg bg-muted flex items-center justify-center text-xs font-medium">
                            +{order.items.length - 3}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-3">
                      <div className="text-right">
                        <p className="text-2xl font-bold">₹{Math.round(order.total).toLocaleString()}</p>
                        <p className="text-sm text-muted-foreground">
                          {order.items.reduce((sum, item) => sum + item.quantity, 0)} items
                        </p>
                      </div>
                      <Link href={ROUTES.ORDER_DETAIL(order.id)}>
                        <Button variant="outline" size="sm">
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </Button>
                      </Link>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}

