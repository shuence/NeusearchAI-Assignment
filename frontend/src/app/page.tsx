import { Header } from "@/components/layout/header";
import { ProductGrid } from "@/components/features/products/product-grid";
import { getProducts } from "@/lib/api/products";

export default async function Home() {
  const products = await getProducts(true);

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold mb-2">All Products</h2>
          <p className="text-muted-foreground">
            Browse our collection of products
          </p>
        </div>

        {products.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground mb-4">
              No products available at the moment.
            </p>
            <p className="text-sm text-muted-foreground">
              Please check if the backend API is running and the database is properly configured.
            </p>
          </div>
        ) : (
          <ProductGrid products={products} />
        )}
      </main>
    </div>
  );
}
