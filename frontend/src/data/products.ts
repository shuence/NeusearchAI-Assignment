import type { Product } from "@/types/product";

export const dummyProducts: Product[] = [
  {
    id: "1",
    title: "Premium Office Chair",
    price: 12999,
    description: "Ergonomic office chair with lumbar support",
    image: "https://images.unsplash.com/photo-1586953208448-b95a79798f07?w=400&h=300&fit=crop",
    category: "Furniture",
    features: [
      "Ergonomic design with lumbar support",
      "Adjustable height and armrests",
      "360-degree swivel",
      "Premium padding and materials",
      "5-year warranty",
    ],
    attributes: {
      Material: "Mesh & Foam",
      Weight: "15 kg",
      Dimensions: "60 x 60 x 120 cm",
      Color: "Black",
    },
  },
  {
    id: "2",
    title: "Modern Sofa Set",
    price: 45999,
    description: "3-seater sofa with premium fabric upholstery",
    image: "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=400&h=300&fit=crop",
    category: "Furniture",
    features: [
      "Premium fabric upholstery",
      "Comfortable seating for 3",
      "Modern design",
      "Durable construction",
    ],
    attributes: {
      Material: "Fabric",
      Seating: "3-seater",
      Dimensions: "220 x 90 x 85 cm",
      Color: "Grey",
    },
  },
  {
    id: "3",
    title: "Wooden Dining Table",
    price: 24999,
    description: "Solid wood dining table for 6 people",
    image: "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400&h=300&fit=crop",
    category: "Furniture",
    features: [
      "Solid wood construction",
      "Seats 6 people comfortably",
      "Classic design",
      "Easy to maintain",
    ],
    attributes: {
      Material: "Solid Wood",
      Seating: "6 people",
      Dimensions: "180 x 90 x 75 cm",
      Color: "Natural Wood",
    },
  },
  {
    id: "4",
    title: "Study Desk",
    price: 8999,
    description: "Compact study desk with storage drawers",
    image: "https://images.unsplash.com/photo-1586953208448-b95a79798f07?w=400&h=300&fit=crop",
    category: "Furniture",
    features: [
      "Compact design",
      "Storage drawers",
      "Perfect for small spaces",
      "Durable construction",
    ],
    attributes: {
      Material: "Engineered Wood",
      Storage: "2 drawers",
      Dimensions: "120 x 60 x 75 cm",
      Color: "White",
    },
  },
  {
    id: "5",
    title: "Bookshelf",
    price: 12999,
    description: "5-tier bookshelf with adjustable shelves",
    image: "https://images.unsplash.com/photo-1586953208448-b95a79798f07?w=400&h=300&fit=crop",
    category: "Furniture",
    features: [
      "5 adjustable shelves",
      "Spacious storage",
      "Sturdy construction",
      "Modern design",
    ],
    attributes: {
      Material: "Engineered Wood",
      Shelves: "5 tiers",
      Dimensions: "90 x 30 x 180 cm",
      Color: "Brown",
    },
  },
  {
    id: "6",
    title: "Coffee Table",
    price: 6999,
    description: "Modern glass top coffee table",
    image: "https://images.unsplash.com/photo-1586953208448-b95a79798f07?w=400&h=300&fit=crop",
    category: "Furniture",
    features: [
      "Glass top surface",
      "Modern design",
      "Sturdy base",
      "Easy to clean",
    ],
    attributes: {
      Material: "Glass & Metal",
      Top: "Tempered Glass",
      Dimensions: "120 x 60 x 45 cm",
      Color: "Clear Glass",
    },
  },
];

// Helper function to get product by ID
export function getDummyProductById(id: string): Product | undefined {
  return dummyProducts.find((product) => product.id === id);
}

// Helper function to get all products
export function getAllDummyProducts(): Product[] {
  return dummyProducts;
}

