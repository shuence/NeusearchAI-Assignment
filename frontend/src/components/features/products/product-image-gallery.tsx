"use client";

import { useState } from "react";
import Image from "next/image";

interface Variant {
  title?: string;
  sku?: string;
  price?: number | string;
  compare_at_price?: number | string;
  option1?: string;
  option2?: string;
  option3?: string;
  available?: boolean;
  featured_image?: {
    src?: string;
    id?: number;
    alt?: string;
  };
}

interface ProductImageGalleryProps {
  mainImage: string;
  imageUrls?: string[];
  variants?: Variant[];
}

export function ProductImageGallery({
  mainImage,
  imageUrls,
  variants,
}: ProductImageGalleryProps) {
  const [selectedImage, setSelectedImage] = useState(mainImage);

  // Extract variant images
  const variantImages = variants
    ?.map((variant) => variant.featured_image?.src)
    .filter((src): src is string => Boolean(src)) || [];

  // Combine all available images
  const allImages = [
    mainImage,
    ...(imageUrls || []),
    ...variantImages,
  ].filter((img, index, self) => self.indexOf(img) === index); // Remove duplicates

  const handleVariantClick = (variant: Variant) => {
    if (variant.featured_image?.src) {
      setSelectedImage(variant.featured_image.src);
    }
  };

  const handleThumbnailClick = (imageUrl: string) => {
    setSelectedImage(imageUrl);
  };

  return (
    <div className="w-full space-y-4">
      {/* Main Image */}
      <div className="w-full overflow-hidden rounded-lg bg-[#EEECEB] relative min-h-[400px] flex items-center justify-center">
        <Image
          src={selectedImage || mainImage || "/placeholder.png"}
          alt="Product"
          width={1200}
          height={1200}
          className="object-contain w-full h-auto max-h-[600px]"
          sizes="(max-width: 768px) 100vw, 50vw"
          unoptimized
        />
      </div>

      {/* Variants Section */}
      {variants && variants.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-muted-foreground">Variants</h3>
          <div className="flex flex-wrap gap-2">
            {variants.map((variant, index) => {
              const variantLabel = [
                variant.option1,
                variant.option2,
                variant.option3,
              ]
                .filter(Boolean)
                .join(" / ") || variant.title || `Variant ${index + 1}`;

              const hasImage = Boolean(variant.featured_image?.src);

              return (
                <button
                  key={index}
                  onClick={() => handleVariantClick(variant)}
                  className={`px-4 py-2 rounded-md border transition-all ${
                    selectedImage === variant.featured_image?.src
                      ? "border-primary bg-primary/10"
                      : "border-muted hover:border-primary/50"
                  } ${!hasImage ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
                  disabled={!hasImage}
                  title={hasImage ? `Click to view ${variantLabel} image` : "No image available"}
                >
                  <span className="text-sm">{variantLabel}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Image Thumbnails Gallery */}
      {allImages.length > 1 && (
        <div className="grid grid-cols-4 gap-2">
          {allImages.map((imageUrl, index) => (
            <button
              key={index}
              onClick={() => handleThumbnailClick(imageUrl)}
              className={`w-full overflow-hidden rounded-lg bg-[#EEECEB] relative min-h-[100px] flex items-center justify-center cursor-pointer hover:opacity-80 transition-opacity ${
                selectedImage === imageUrl ? "ring-2 ring-primary" : ""
              }`}
            >
              <Image
                src={imageUrl || "/placeholder.png"}
                alt={`Product image ${index + 1}`}
                width={300}
                height={300}
                className="object-contain w-full h-auto"
                sizes="(max-width: 768px) 25vw, 12.5vw"
                unoptimized
              />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

