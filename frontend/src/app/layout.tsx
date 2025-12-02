import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { ComparisonProvider } from "@/contexts/comparison-context";
import { CartProvider } from "@/contexts/cart-context";
import { OrderProvider } from "@/contexts/order-context";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "Neusearch AI - Product Discovery Assistant",
    template: "%s | Neusearch AI",
  },
  description: "AI-powered product discovery assistant with RAG capabilities. Find the perfect products using natural language queries.",
  keywords: ["AI", "product discovery", "RAG", "e-commerce", "product recommendations", "semantic search"],
  authors: [{ name: "Neusearch AI" }],
  creator: "Neusearch AI",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://neusearch.ai",
    siteName: "Neusearch AI",
    title: "Neusearch AI - Product Discovery Assistant",
    description: "AI-powered product discovery assistant with RAG capabilities",
  },
  twitter: {
    card: "summary_large_image",
    title: "Neusearch AI - Product Discovery Assistant",
    description: "AI-powered product discovery assistant with RAG capabilities",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <ComparisonProvider>
            <CartProvider>
              <OrderProvider>
                {children}
                <Toaster />
              </OrderProvider>
            </CartProvider>
          </ComparisonProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
