"use client";

import type { Product } from "@/types/product";

interface ComparisonTableProps {
  aiInsight: string;
  products: Product[];
}

export function ComparisonTable({ aiInsight, products }: ComparisonTableProps) {
  // Parse the AI insight into structured data
  const sections: Array<{ category: string; items: string[] }> = [];
  const lines = aiInsight.split('\n').filter(line => line.trim());
  
  let currentCategory = '';
  let currentItems: string[] = [];
  
  lines.forEach((line) => {
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

  if (sections.length === 0) {
    return (
      <div className="text-sm text-muted-foreground p-4">
        No comparison data available
      </div>
    );
  }

  return (
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
          {sections.map((section, sectionIdx) => {
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
          })}
        </tbody>
      </table>
    </div>
  );
}

