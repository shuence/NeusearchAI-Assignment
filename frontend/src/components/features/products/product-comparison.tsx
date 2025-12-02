"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useComparison } from "@/contexts/comparison-context";
import { compareProducts } from "@/lib/api/chat";
import { getProducts, getSimilarProducts } from "@/lib/api/products";
import { ROUTES } from "@/lib/constants";
import type { Product } from "@/types/product";
import { ProductCard } from "./product-card";
import { ProductGridSkeleton } from "./product-grid-skeleton";
import { X, Loader2, Sparkles, ArrowLeft, Scale, Check, MessageSquare } from "lucide-react";
import { toast } from "sonner";

export function ProductComparison() {
  const { products, removeProduct, clearComparison, addProduct, canAddMore, isInComparison } = useComparison();
  const router = useRouter();
  const [aiInsight, setAiInsight] = useState<string | null>(null);
  const [isLoadingInsight, setIsLoadingInsight] = useState(false);
  const [availableProducts, setAvailableProducts] = useState<Product[]>([]);
  const [isLoadingProducts, setIsLoadingProducts] = useState(false);
  const [selectedProducts, setSelectedProducts] = useState<Set<string>>(new Set());
  const [similarProducts, setSimilarProducts] = useState<Product[]>([]);
  const [isLoadingSimilar, setIsLoadingSimilar] = useState(false);

  const generateAIInsight = async () => {
    if (products.length < 2) return;

    setIsLoadingInsight(true);
    try {
      const productIds = products.map((p) => p.id);
      const response = await compareProducts(productIds);
      setAiInsight(response.insight);
    } catch (error) {
      console.error("Error generating AI insight:", error);
      toast.error("Failed to generate comparison insight", {
        description: "Please try again later.",
      });
    } finally {
      setIsLoadingInsight(false);
    }
  };

  const handleSendToChat = () => {
    if (!aiInsight) {
      toast.info("No comparison insight available", {
        description: "Please wait for the insight to be generated.",
      });
      return;
    }

    // Store the comparison message in localStorage to be picked up by chat page
    const comparisonMessage = {
      role: "assistant" as const,
      content: `Product Comparison:\n\n${aiInsight}\n\nProducts compared: ${products.map((p) => p.title).join(", ")}`,
      timestamp: new Date().toISOString(),
      products: products,
    };

    // Store in a way that chat page can access
    if (typeof window !== "undefined") {
      const chatMessages = localStorage.getItem("neusearch_chat_messages");
      let messages = [];
      if (chatMessages) {
        try {
          messages = JSON.parse(chatMessages);
        } catch (e) {
          console.error("Error parsing chat messages:", e);
        }
      }
      messages.push(comparisonMessage);
      localStorage.setItem("neusearch_chat_messages", JSON.stringify(messages));
      
      toast.success("Comparison sent to chat", {
        description: "You can view it in the chat page.",
      });
      
      // Navigate to chat page
      router.push(ROUTES.CHAT);
    }
  };

  useEffect(() => {
    if (products.length >= 2) {
      generateAIInsight();
    } else {
      setAiInsight(null);
    }
  }, [products]);

  // Load similar products when products are in comparison
  useEffect(() => {
    if (products.length > 0) {
      const loadSimilarProducts = async () => {
        setIsLoadingSimilar(true);
        try {
          // Get similar products from the first product in comparison
          const similar = await getSimilarProducts(products[0].id, 8);
          // Filter out products already in comparison
          const filtered = similar.filter(
            (p) => !products.some((comp) => comp.id === p.id)
          );
          setSimilarProducts(filtered.slice(0, 6)); // Limit to 6
        } catch (error) {
          console.error("Error loading similar products:", error);
        } finally {
          setIsLoadingSimilar(false);
        }
      };
      loadSimilarProducts();
    } else {
      setSimilarProducts([]);
    }
  }, [products]);

  // Load products from API when there are no products in comparison
  useEffect(() => {
    if (products.length === 0) {
      const loadProducts = async () => {
        setIsLoadingProducts(true);
        try {
          const fetchedProducts = await getProducts();
          setAvailableProducts(fetchedProducts);
        } catch (error) {
          console.error("Error loading products:", error);
          toast.error("Failed to load products", {
            description: "Please try again later.",
          });
        } finally {
          setIsLoadingProducts(false);
        }
      };
      loadProducts();
    }
  }, [products.length]);

  const formatPrice = (price: number | null | undefined): string => {
    if (price === null || price === undefined || isNaN(price)) {
      return "N/A";
    }
    if (price === 0) return "Free";
    return `₹${Math.round(price).toLocaleString("en-IN")}`;
  };

  const toggleProductSelection = (productId: string) => {
    setSelectedProducts((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(productId)) {
        newSet.delete(productId);
      } else {
        // Check if we can add more (considering already in comparison)
        const currentInComparison = products.length;
        const newSelections = newSet.size + (newSet.has(productId) ? 0 : 1);
        if (currentInComparison + newSelections <= 4) {
          newSet.add(productId);
        } else {
          toast.warning("Maximum 4 products allowed", {
            description: "Please remove some products before adding more.",
          });
        }
      }
      return newSet;
    });
  };

  const handleCompareSelected = async () => {
    if (selectedProducts.size < 2) {
      toast.info("Select at least 2 products", {
        description: "Please select 2-4 products to compare.",
      });
      return;
    }

    if (selectedProducts.size > 4) {
      toast.warning("Too many products selected", {
        description: "Please select maximum 4 products.",
      });
      return;
    }

    const productsToCompare = availableProducts.filter((p) => 
      selectedProducts.has(p.id)
    );

    // Add products to comparison context
    productsToCompare.forEach((product) => {
      if (!isInComparison(product.id)) {
        addProduct(product);
      }
    });

    setSelectedProducts(new Set());
    
    // Generate comparison insight
    setIsLoadingInsight(true);
    try {
      const productIds = productsToCompare.map((p) => p.id);
      const response = await compareProducts(productIds);
      setAiInsight(response.insight);
    } catch (error) {
      console.error("Error comparing products:", error);
      toast.error("Failed to compare products", {
        description: "Please try again later.",
      });
    } finally {
      setIsLoadingInsight(false);
    }
  };

  const handleSelectAll = () => {
    const maxSelectable = 4 - products.length;
    if (maxSelectable <= 0) {
      toast.warning("Comparison is full", {
        description: "Please remove some products before selecting more.",
      });
      return;
    }

    const selectableProducts = availableProducts
      .filter((p) => !isInComparison(p.id))
      .slice(0, maxSelectable)
      .map((p) => p.id);

    setSelectedProducts(new Set(selectableProducts));
  };

  const handleDeselectAll = () => {
    setSelectedProducts(new Set());
  };

  if (products.length === 0) {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        <div className="container mx-auto px-4 py-8 flex-1">
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <Scale className="h-8 w-8 text-primary" />
              <h1 className="text-2xl sm:text-3xl font-bold">Product Comparison</h1>
            </div>
            <p className="text-muted-foreground">
              Select up to 4 products to compare side-by-side with AI-powered insights.
            </p>
          </div>

          {isLoadingProducts ? (
            <ProductGridSkeleton />
          ) : availableProducts.length > 0 ? (
            <div>
              <div className="mb-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <p className="text-sm text-muted-foreground">
                    {availableProducts.length} product{availableProducts.length !== 1 ? "s" : ""} available
                  </p>
                  {selectedProducts.size > 0 && (
                    <Badge variant="default" className="text-xs">
                      {selectedProducts.size} selected
                    </Badge>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {selectedProducts.size > 0 ? (
                    <>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleDeselectAll}
                      >
                        Deselect All
                      </Button>
                      <Button
                        size="sm"
                        onClick={handleCompareSelected}
                        disabled={selectedProducts.size < 2 || selectedProducts.size > 4}
                      >
                        Compare ({selectedProducts.size})
                      </Button>
                    </>
                  ) : (
                    <>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleSelectAll}
                        disabled={!canAddMore}
                      >
                        Select All
                      </Button>
                      {!canAddMore && (
                        <Badge variant="secondary" className="text-xs">
                          Maximum 4 products
                        </Badge>
                      )}
                    </>
                  )}
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {availableProducts.map((product) => {
                  const isSelected = selectedProducts.has(product.id);
                  const isInComp = isInComparison(product.id);
                  const imageSrc =
                    product.image ||
                    product.imageUrl ||
                    product.image_urls?.[0] ||
                    "/placeholder.png";

                  return (
                    <Card
                      key={product.id}
                      className={`flex flex-col h-full hover:shadow-lg transition-all cursor-pointer relative ${
                        isSelected ? "ring-2 ring-primary" : ""
                      } ${isInComp ? "opacity-60" : ""}`}
                      onClick={() => !isInComp && toggleProductSelection(product.id)}
                    >
                      {/* Selection Checkbox */}
                      <div className="absolute top-2 left-2 z-10">
                        <div
                          className={`w-6 h-6 rounded-md border-2 flex items-center justify-center transition-colors ${
                            isSelected
                              ? "bg-primary border-primary text-primary-foreground"
                              : isInComp
                              ? "bg-muted border-muted-foreground/30 cursor-not-allowed"
                              : "bg-background border-border hover:border-primary"
                          }`}
                          onClick={(e) => {
                            e.stopPropagation();
                            if (!isInComp) {
                              toggleProductSelection(product.id);
                            }
                          }}
                        >
                          {isSelected && <Check className="h-4 w-4" />}
                          {isInComp && <Check className="h-4 w-4 text-muted-foreground" />}
                        </div>
                      </div>

                      {isInComp && (
                        <div className="absolute top-2 right-2 z-10">
                          <Badge variant="secondary" className="text-xs">
                            In Comparison
                          </Badge>
                        </div>
                      )}

                      <CardHeader className="shrink-0">
                        <div className="w-full overflow-hidden rounded-lg bg-muted mb-4 relative h-[200px] flex items-center justify-center">
                          <Image
                            src={imageSrc}
                            alt={product.title}
                            width={800}
                            height={800}
                            className="object-contain w-full h-full"
                            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                            loading="lazy"
                          />
                        </div>
                        <CardTitle className="line-clamp-2 min-h-12 pr-8">
                          {product.title}
                        </CardTitle>
                        <p className="text-sm text-muted-foreground line-clamp-1">
                          {product.category || product.product_type}
                        </p>
                      </CardHeader>
                      <CardContent className="flex-1 flex flex-col">
                        <p className="text-sm text-muted-foreground line-clamp-2 flex-1">
                          {product.description || "No description available"}
                        </p>
                        <p className="text-2xl font-bold mt-4 shrink-0">
                          {formatPrice(product.price)}
                        </p>
                      </CardContent>
                      <div className="p-4 pt-0 flex flex-col gap-2">
                        <Button
                          className="w-full"
                          onClick={(e) => {
                            e.stopPropagation();
                            router.push(ROUTES.PRODUCT_DETAIL(product.id));
                          }}
                        >
                          View Details
                        </Button>
                      </div>
                    </Card>
                  );
                })}
              </div>
            </div>
          ) : (
          <div className="text-center py-12">
            <Scale className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
              <h2 className="text-2xl font-bold mb-2">No Products Available</h2>
            <p className="text-muted-foreground mb-6">
                Unable to load products from the API. Please try again later.
            </p>
            <Button onClick={() => router.push(ROUTES.HOME)}>
                Go to Home
            </Button>
          </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <div className="container mx-auto px-4 py-6 flex-1">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.back()}
              className="sm:hidden"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold">Product Comparison</h1>
              <p className="text-sm text-muted-foreground mt-1">
                Compare {products.length} product{products.length > 1 ? "s" : ""} side-by-side
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={clearComparison}
              className="hidden sm:flex"
            >
              Clear All
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={clearComparison}
              className="sm:hidden"
              aria-label="Clear all"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* AI Insight */}
        {products.length >= 2 && (
          <Card className="mb-6 border-primary/20 bg-primary/5">
            <CardHeader>
              <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                <CardTitle className="text-lg">AI Comparison Insight</CardTitle>
                </div>
                {aiInsight && ( 
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleSendToChat}
                    className="gap-2"
                  >
                    <MessageSquare className="h-4 w-4" />
                    Continue to Chat
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {isLoadingInsight ? (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Generating AI insights...</span>
                </div>
              ) : aiInsight ? (
                <div className="overflow-x-auto rounded-lg border shadow-sm">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="text-left p-4 font-semibold text-sm uppercase tracking-wider text-muted-foreground">
                          Category
                        </th>
                        {products.map((product) => (
                          <th key={product.id} className="text-left p-4 font-semibold text-sm min-w-[200px] border-l">
                            <div className="line-clamp-2 text-foreground">{product.title}</div>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {(() => {
                        // Parse the AI insight into structured data
                        const sections: Array<{ category: string; items: string[] }> = [];
                        const lines = aiInsight.split('\n').filter(line => line.trim());
                        
                        let currentCategory = '';
                        let currentItems: string[] = [];
                        
                        lines.forEach((line, lineIdx) => {
                          const trimmed = line.trim();
                          
                          // Check if it's a category header (starts with **)
                          if (trimmed.startsWith('**') && trimmed.endsWith('**')) {
                            // Save previous category if exists
                            if (currentCategory && currentItems.length > 0) {
                              sections.push({ category: currentCategory, items: [...currentItems] });
                            }
                            // Start new category
                            currentCategory = trimmed.replace(/\*\*/g, '');
                            currentItems = [];
                          } else if (trimmed.startsWith('•') || trimmed.startsWith('-')) {
                            // It's a bullet point
                            const content = trimmed.substring(1).trim();
                            if (content) {
                              // Check if this is a nested bullet (indented) - if so, append to previous item
                              const isIndented = line.startsWith(' ') || line.startsWith('\t');
                              if (isIndented && currentItems.length > 0) {
                                // Append to the last item
                                currentItems[currentItems.length - 1] += ' ' + content;
                              } else {
                                currentItems.push(content);
                              }
                            }
                          } else if (trimmed && !trimmed.startsWith('**')) {
                            // Non-bullet line that might be continuation or sub-item
                            // If it looks like a pros/cons continuation, append to last item
                            if (currentItems.length > 0 && 
                                (trimmed.toLowerCase().startsWith('pros:') || 
                                 trimmed.toLowerCase().startsWith('cons:') ||
                                 trimmed.toLowerCase().startsWith('pro:') ||
                                 trimmed.toLowerCase().startsWith('con:'))) {
                              currentItems[currentItems.length - 1] += ' ' + trimmed;
                            }
                          }
                        });
                        
                        // Save last category
                        if (currentCategory && currentItems.length > 0) {
                          sections.push({ category: currentCategory, items: [...currentItems] });
                        }
                        
                        // Group items by product
                        return sections.map((section, sectionIdx) => {
                          // Try to match items to products
                          const productData: string[][] = products.map(() => []);
                          
                          // Extract product name keywords for better matching
                          const productKeywords = products.map((product, idx) => {
                            const words = product.title.split(' ');
                            const firstWords = words.slice(0, 3).join(' ').toLowerCase();
                            return {
                              index: idx,
                              full: product.title.toLowerCase(),
                              first: words[0]?.toLowerCase() || '',
                              second: words[1]?.toLowerCase() || '',
                              third: words[2]?.toLowerCase() || '',
                              firstThree: firstWords,
                              unique: words.slice(0, 4).map(w => w.toLowerCase()).filter(w => w.length > 2),
                              // Also check for "Product X" format
                              productNumber: `product ${idx + 1}`
                            };
                          });
                          
                          section.items.forEach((item, itemIdx) => {
                            const itemLower = item.toLowerCase();
                            const itemTrimmed = item.trim();
                            
                            // Skip empty items
                            if (!itemTrimmed || itemTrimmed.length < 3) {
                              return;
                            }
                            
                            // Try to find which product this item belongs to
                            let matched = false;
                            let matchedIndices: number[] = [];
                            
                            // First, check for explicit product number format (Product 1, Product 2, etc.)
                            productKeywords.forEach((keywords) => {
                              if (itemLower.startsWith(keywords.productNumber) || 
                                  itemLower.includes(`product ${keywords.index + 1}:`)) {
                                matchedIndices.push(keywords.index);
                                matched = true;
                              }
                            });
                            
                            // If no product number match, check for product name mentions
                            if (!matched) {
                              productKeywords.forEach((keywords) => {
                                // Check if item starts with or contains product identifier
                                if (itemLower.startsWith(keywords.firstThree) ||
                                    itemLower.startsWith(keywords.first + ' ') ||
                                    itemLower.startsWith(keywords.second + ' ') ||
                                    itemLower.match(new RegExp(`^${keywords.first}\\s+${keywords.second}`, 'i')) ||
                                    keywords.unique.some(word => {
                                      const regex = new RegExp(`^${word}[\\s:]`, 'i');
                                      return regex.test(itemLower);
                                    })) {
                                  matchedIndices.push(keywords.index);
                                  matched = true;
                                }
                              });
                            }
                            
                            // Check for colon-separated format (Product Name: content)
                            if (!matched && itemTrimmed.includes(':')) {
                              const colonIndex = itemTrimmed.indexOf(':');
                              const beforeColon = itemTrimmed.substring(0, colonIndex).toLowerCase().trim();
                              
                              // Check for product number format first
                              productKeywords.forEach((keywords) => {
                                if (beforeColon === keywords.productNumber || 
                                    beforeColon.startsWith(keywords.productNumber + ' ')) {
                                  matchedIndices.push(keywords.index);
                                  matched = true;
                                }
                              });
                              
                              // Then check for product name
                              if (!matched) {
                                productKeywords.forEach((keywords) => {
                                  if (beforeColon.includes(keywords.first) || 
                                      beforeColon.includes(keywords.second) ||
                                      beforeColon.includes(keywords.firstThree) ||
                                      keywords.unique.some(word => beforeColon.includes(word))) {
                                    matchedIndices.push(keywords.index);
                                    matched = true;
                                  }
                                });
                              }
                            }
                            
                            // Special handling for Pros & Cons section - look for "Pros:" and "Cons:" patterns
                            if (!matched && section.category.toLowerCase().includes('pros')) {
                              // Try to match based on context - if previous item was matched, this might be continuation
                              if (itemIdx > 0) {
                                const prevItem = section.items[itemIdx - 1];
                                const prevItemLower = prevItem.toLowerCase();
                                
                                // Check if previous item was matched to a product
                                productKeywords.forEach((keywords) => {
                                  if (prevItemLower.includes(keywords.productNumber) ||
                                      prevItemLower.includes(keywords.first) ||
                                      prevItemLower.includes(keywords.second)) {
                                    // This pros/cons item likely belongs to the same product
                                    matchedIndices.push(keywords.index);
                                    matched = true;
                                  }
                                });
                              }
                            }
                            
                            if (matched && matchedIndices.length > 0) {
                              // If it's a "Both" or "All" statement, add to all
                              if (itemLower.includes('both') || 
                                  itemLower.includes('all') ||
                                  itemLower.includes('each') ||
                                  itemLower.includes('similar') ||
                                  itemLower.includes('same') ||
                                  itemLower.includes('identical')) {
                                products.forEach((_, idx) => {
                                  productData[idx].push(item);
                                });
                              } else {
                                // Use the best match (first one, or most specific)
                                const bestMatch = matchedIndices[0];
                                productData[bestMatch].push(item);
                              }
                            } else {
                              // Check for "Both:", "All:", "Summary" patterns
                              if (itemLower.includes('both') || 
                                  itemLower.includes('all') ||
                                  itemLower.includes('each') ||
                                  itemLower.includes('similar') ||
                                  itemLower.includes('same') ||
                                  itemLower.includes('identical') ||
                                  itemLower.includes('virtually the same')) {
                                // Add to all products
                                products.forEach((_, idx) => {
                                  productData[idx].push(item);
                                });
                              } else {
                                // Try sequential assignment as fallback
                                // Group items by their position in the list
                                const itemsPerProduct = Math.ceil(section.items.length / products.length);
                                const productIndex = Math.floor(itemIdx / itemsPerProduct);
                                if (productIndex < products.length) {
                                  productData[productIndex].push(item);
                                } else {
                                  // Last resort: add to first product
                                  productData[0].push(item);
                                }
                              }
                            }
                          });
                          
                          // Check if this is Summary section - span all columns
                          const isSummary = section.category.toLowerCase().includes('summary');
                          
                          if (isSummary) {
                            // Combine all items for summary
                            const allSummaryItems = section.items.join(' ');
                            return (
                              <tr key={sectionIdx} className="border-b bg-primary/5 hover:bg-primary/10 transition-colors">
                                <td className="p-4 font-medium text-muted-foreground align-top sticky left-0 bg-primary/5">
                                  {section.category}
                                </td>
                                <td 
                                  colSpan={products.length} 
                                  className="p-4 align-top"
                                >
                                  <p className="text-sm leading-relaxed text-foreground">
                                    {allSummaryItems}
                                  </p>
                                </td>
                              </tr>
                            );
                          }
                          
                          return (
                            <tr key={sectionIdx} className="border-b hover:bg-muted/30 transition-colors group">
                              <td className="p-4 font-semibold text-sm text-foreground align-top sticky left-0 bg-background border-r z-10">
                                {section.category}
                              </td>
                              {products.map((product, productIdx) => (
                                <td key={product.id} className="p-4 align-top border-l">
                                  {productData[productIdx].length > 0 ? (
                                    <ul className="space-y-2">
                                      {productData[productIdx].map((item, itemIdx) => {
                                        // Remove product name prefix if it exists for cleaner display
                                        const cleanItem = item.replace(/^[^:]+:\s*/, '');
                                        return (
                                          <li key={itemIdx} className="text-sm leading-relaxed flex items-start gap-2.5">
                                            <span className="text-primary mt-0.5 shrink-0 font-bold">•</span>
                                            <span className="flex-1 text-foreground">{cleanItem}</span>
                                          </li>
                                        );
                                      })}
                                    </ul>
                                  ) : (
                                    <span className="text-sm text-muted-foreground italic">-</span>
                                  )}
                                </td>
                              ))}
                            </tr>
                          );
                        });
                      })()}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Generating comparison insights...</p>
              )}
            </CardContent>
          </Card>
        )}

        {/* Side-by-Side Comparison */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg">Side-by-Side Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto -mx-4 px-4">
          <div className="inline-block min-w-full">
                <div 
                  className="grid gap-4" 
                  style={{ 
                    gridTemplateColumns: `repeat(${products.length}, minmax(280px, 1fr))`,
                    minWidth: `${products.length * 280}px`
                  }}
                >
              {products.map((product) => {
                const imageSrc =
                  product.image ||
                  product.imageUrl ||
                  product.image_urls?.[0] ||
                  "/placeholder.png";

                return (
                      <Card key={product.id} className="flex flex-col border-2">
                        <CardHeader className="relative pb-3">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="absolute top-2 right-2 z-10 h-8 w-8"
                        onClick={() => removeProduct(product.id)}
                        aria-label={`Remove ${product.title} from comparison`}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                          <div className="w-full h-64 bg-muted rounded-lg mb-4 relative overflow-hidden flex items-center justify-center">
                        <Image
                          src={imageSrc}
                          alt={product.title}
                          width={400}
                          height={400}
                          className="object-contain w-full h-full"
                              sizes="(max-width: 768px) 100vw, 33vw"
                        />
                      </div>
                          <CardTitle className="text-lg line-clamp-2 pr-8 mb-2">
                        {product.title}
                      </CardTitle>
                          <p className="text-sm text-muted-foreground">
                        {product.category || product.product_type}
                      </p>
                    </CardHeader>
                        <CardContent className="flex-1 space-y-4">
                      {/* Price */}
                          <div className="border-b pb-3">
                        <p className="text-xs font-medium text-muted-foreground mb-1">Price</p>
                            <p className="text-2xl font-bold">{formatPrice(product.price)}</p>
                        {product.compare_at_price && product.compare_at_price > (product.price || 0) && (
                              <p className="text-sm text-muted-foreground line-through mt-1">
                            {formatPrice(product.compare_at_price)}
                          </p>
                        )}
                      </div>

                      {/* Vendor */}
                      {product.vendor && (
                            <div className="border-b pb-3">
                          <p className="text-xs font-medium text-muted-foreground mb-1">Vendor</p>
                          <p className="text-sm">{product.vendor}</p>
                        </div>
                      )}

                      {/* Description */}
                          <div className="border-b pb-3">
                        <p className="text-xs font-medium text-muted-foreground mb-1">Description</p>
                            <p className="text-sm text-muted-foreground line-clamp-4">
                          {product.description || "No description available"}
                        </p>
                      </div>

                      {/* View Details Button */}
                      <Button
                        className="w-full mt-4"
                            variant="outline"
                        onClick={() => router.push(ROUTES.PRODUCT_DETAIL(product.id))}
                      >
                        View Details
                      </Button>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        </div>
          </CardContent>
        </Card>

        {/* Similar Products Section */}
        {similarProducts.length > 0 && canAddMore && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Similar Products</CardTitle>
                  <p className="text-sm text-muted-foreground mt-1">
                    Add more products to compare
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {isLoadingSimilar ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
                  {similarProducts.map((product) => {
                    const imageSrc =
                      product.image ||
                      product.imageUrl ||
                      product.image_urls?.[0] ||
                      "/placeholder.png";
                    const isInComp = isInComparison(product.id);

                    return (
                      <Card
                        key={product.id}
                        className={`flex flex-col hover:shadow-lg transition-all cursor-pointer ${
                          isInComp ? "opacity-60" : ""
                        }`}
                        onClick={() => {
                          if (!isInComp && canAddMore) {
                            addProduct(product);
                            toast.success("Product added to comparison");
                          } else if (isInComp) {
                            toast.info("Product already in comparison");
                          } else {
                            toast.warning("Maximum 4 products allowed");
                          }
                        }}
                      >
                        <CardHeader className="p-3">
                          <div className="w-full h-32 bg-muted rounded-lg mb-2 relative overflow-hidden flex items-center justify-center">
                            <Image
                              src={imageSrc}
                              alt={product.title}
                              width={200}
                              height={200}
                              className="object-contain w-full h-full"
                              sizes="(max-width: 768px) 50vw, 16vw"
                            />
                          </div>
                          <CardTitle className="text-sm line-clamp-2 mb-1">
                            {product.title}
                          </CardTitle>
                          <p className="text-xs font-bold text-primary">
                            {formatPrice(product.price)}
                          </p>
                        </CardHeader>
                        <CardContent className="p-3 pt-0">
                          {isInComp ? (
                            <Badge variant="secondary" className="w-full justify-center text-xs">
                              In Comparison
                            </Badge>
                          ) : (
                            <Button
                              size="sm"
                              variant="outline"
                              className="w-full text-xs"
                              onClick={(e) => {
                                e.stopPropagation();
                                if (canAddMore) {
                                  addProduct(product);
                                  toast.success("Product added to comparison");
                                } else {
                                  toast.warning("Maximum 4 products allowed");
                                }
                              }}
                            >
                              <Scale className="h-3 w-3 mr-1" />
                              Add to Compare
                            </Button>
                          )}
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

