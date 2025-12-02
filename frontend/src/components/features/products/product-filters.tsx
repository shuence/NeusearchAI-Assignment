"use client";

import { useState, useMemo, useRef, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Product } from "@/types/product";
import { Search, X, Filter, CheckCircle2 } from "lucide-react";

export interface FilterState {
  searchQuery: string;
  selectedCategory: string | null;
  selectedVendor: string | null;
  priceRange: [number, number] | null;
  sortBy: "price-asc" | "price-desc" | "title-asc" | "title-desc" | "none";
}

interface ProductFiltersProps {
  products: Product[];
  filteredProducts: Product[];
  filterState: FilterState;
  onFilterChange: (filters: FilterState) => void;
}

export function ProductFilters({
  products,
  filteredProducts,
  filterState,
  onFilterChange,
}: ProductFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [searchHighlight, setSearchHighlight] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Extract unique categories and vendors
  const categories = useMemo(() => {
    const cats = new Set<string>();
    products.forEach((p) => {
      if (p.category) cats.add(p.category);
      if (p.product_type) cats.add(p.product_type);
    });
    return Array.from(cats).sort();
  }, [products]);

  const vendors = useMemo(() => {
    const vends = new Set<string>();
    products.forEach((p) => {
      if (p.vendor) vends.add(p.vendor);
    });
    return Array.from(vends).sort();
  }, [products]);

  const priceRange = useMemo(() => {
    const prices = products.map((p) => p.price).filter((p) => p > 0);
    if (prices.length === 0) return [0, 1000];
    return [Math.min(...prices), Math.max(...prices)];
  }, [products]);

  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filterState.searchQuery) count++;
    if (filterState.selectedCategory) count++;
    if (filterState.selectedVendor) count++;
    if (filterState.priceRange) count++;
    if (filterState.sortBy !== "none") count++;
    return count;
  }, [filterState]);

  // Generate search suggestions based on products
  const searchSuggestions = useMemo(() => {
    if (!filterState.searchQuery || filterState.searchQuery.length < 2) return [];
    
    const query = filterState.searchQuery.toLowerCase();
    const suggestions = new Set<string>();
    
    // Get suggestions from product titles, categories, and tags
    products.forEach((product) => {
      if (product.title?.toLowerCase().includes(query)) {
        const words = product.title.split(/\s+/);
        words.forEach((word) => {
          if (word.toLowerCase().startsWith(query) && word.length > query.length) {
            suggestions.add(word);
          }
        });
      }
      if (product.category?.toLowerCase().includes(query)) {
        suggestions.add(product.category);
      }
      if (product.tags) {
        product.tags.forEach((tag) => {
          if (tag.toLowerCase().includes(query)) {
            suggestions.add(tag);
          }
        });
      }
    });
    
    return Array.from(suggestions).slice(0, 5);
  }, [filterState.searchQuery, products]);

  // Show visual feedback when search results change
  useEffect(() => {
    if (filterState.searchQuery) {
      setSearchHighlight(true);
      const timer = setTimeout(() => setSearchHighlight(false), 500);
      return () => clearTimeout(timer);
    }
  }, [filteredProducts.length, filterState.searchQuery]);

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node) &&
        searchInputRef.current &&
        !searchInputRef.current.contains(event.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSearchChange = (value: string) => {
    onFilterChange({ ...filterState, searchQuery: value });
    setShowSuggestions(value.length >= 2);
  };

  const handleSuggestionClick = (suggestion: string) => {
    onFilterChange({ ...filterState, searchQuery: suggestion });
    setShowSuggestions(false);
    searchInputRef.current?.focus();
  };

  const handleCategoryChange = (category: string | null) => {
    onFilterChange({ ...filterState, selectedCategory: category });
  };

  const handleVendorChange = (vendor: string | null) => {
    onFilterChange({ ...filterState, selectedVendor: vendor });
  };

  const handlePriceRangeChange = (min: number, max: number) => {
    if (min === priceRange[0] && max === priceRange[1]) {
      onFilterChange({ ...filterState, priceRange: null });
    } else {
      onFilterChange({ ...filterState, priceRange: [min, max] });
    }
  };

  const handleSortChange = (sortBy: FilterState["sortBy"]) => {
    onFilterChange({ ...filterState, sortBy });
  };

  const clearFilters = () => {
    onFilterChange({
      searchQuery: "",
      selectedCategory: null,
      selectedVendor: null,
      priceRange: null,
      sortBy: "none",
    });
  };

  return (
    <div className="space-y-3 lg:space-y-3 mb-4 lg:mb-6">
      {/* Search Bar */}
      <div className="relative">
        <Search className={`absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 transition-colors ${
          searchHighlight ? "text-primary animate-pulse" : "text-muted-foreground"
        }`} aria-hidden="true" />
        <Input
          ref={searchInputRef}
          type="text"
          placeholder="Search products by name, description, or tags..."
          value={filterState.searchQuery}
          onChange={(e) => handleSearchChange(e.target.value)}
          onFocus={() => setShowSuggestions(filterState.searchQuery.length >= 2)}
          className={`pl-10 pr-10 transition-all ${
            searchHighlight ? "ring-2 ring-primary ring-offset-2" : ""
          }`}
          aria-label="Search products"
          aria-expanded={showSuggestions}
          aria-haspopup="listbox"
        />
        {filterState.searchQuery && (
          <button
            onClick={() => {
              handleSearchChange("");
              setShowSuggestions(false);
            }}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Clear search"
          >
            <X className="h-4 w-4" />
          </button>
        )}
        
        {/* Search Suggestions Dropdown */}
        {showSuggestions && searchSuggestions.length > 0 && (
          <div
            ref={suggestionsRef}
            className="absolute z-50 w-full mt-1 bg-background border border-border rounded-lg shadow-lg max-h-60 overflow-y-auto"
            role="listbox"
          >
            {searchSuggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                className="w-full text-left px-4 py-2 hover:bg-muted transition-colors flex items-center gap-2 text-sm"
                role="option"
              >
                <Search className="h-3.5 w-3.5 text-muted-foreground" />
                <span>{suggestion}</span>
              </button>
            ))}
          </div>
        )}
        
        {/* Search Results Feedback */}
        {filterState.searchQuery && (
          <div className={`absolute -bottom-6 left-0 text-xs text-muted-foreground flex items-center gap-1 transition-opacity ${
            searchHighlight ? "opacity-100" : "opacity-70"
          }`}>
            <CheckCircle2 className={`h-3 w-3 transition-colors ${
              searchHighlight ? "text-primary" : "text-muted-foreground"
            }`} />
            <span>
              Found {filteredProducts.length} {filteredProducts.length === 1 ? "product" : "products"}
            </span>
          </div>
        )}
      </div>

      {/* Filter Toggle and Active Filters */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <Button
          variant="outline"
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2"
          aria-label={`${isExpanded ? 'Hide' : 'Show'} filters`}
          aria-expanded={isExpanded}
        >
          <Filter className="h-4 w-4" aria-hidden="true" />
          Filters
          {activeFilterCount > 0 && (
            <Badge variant="secondary" className="ml-1" aria-label={`${activeFilterCount} active filters`}>
              {activeFilterCount}
            </Badge>
          )}
        </Button>

        {activeFilterCount > 0 && (
          <Button variant="ghost" onClick={clearFilters} size="sm" aria-label="Clear all filters">
            Clear all filters
          </Button>
        )}

        <div className="flex items-center gap-2 ml-auto">
          <span className="text-sm text-muted-foreground">
            {filteredProducts.length} of {products.length} products
          </span>
        </div>
      </div>

      {/* Expanded Filters */}
      {isExpanded && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Filter Products</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Category Filter */}
            <div>
              <label className="text-sm font-medium mb-2 block">Category</label>
              <div className="flex flex-wrap gap-2">
                <Button
                  variant={filterState.selectedCategory === null ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleCategoryChange(null)}
                >
                  All
                </Button>
                {categories.map((cat) => (
                  <Button
                    key={cat}
                    variant={filterState.selectedCategory === cat ? "default" : "outline"}
                    size="sm"
                    onClick={() => handleCategoryChange(cat)}
                  >
                    {cat}
                  </Button>
                ))}
              </div>
            </div>

            {/* Vendor Filter */}
            {vendors.length > 0 && (
              <div>
                <label className="text-sm font-medium mb-2 block">Vendor</label>
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant={filterState.selectedVendor === null ? "default" : "outline"}
                    size="sm"
                    onClick={() => handleVendorChange(null)}
                  >
                    All
                  </Button>
                  {vendors.map((vendor) => (
                    <Button
                      key={vendor}
                      variant={filterState.selectedVendor === vendor ? "default" : "outline"}
                      size="sm"
                      onClick={() => handleVendorChange(vendor)}
                    >
                      {vendor}
                    </Button>
                  ))}
                </div>
              </div>
            )}

            {/* Price Range Filter */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Price Range: ₹{Math.round(filterState.priceRange?.[0] ?? priceRange[0])} - ₹{Math.round(filterState.priceRange?.[1] ?? priceRange[1])}
              </label>
              <div className="flex items-center gap-4 flex-wrap">
                <Input
                  type="number"
                  placeholder="Min"
                  min={priceRange[0]}
                  max={priceRange[1]}
                  value={Math.round(filterState.priceRange?.[0] ?? priceRange[0])}
                  onChange={(e) => {
                    const min = Math.max(priceRange[0], Math.min(priceRange[1], Number(e.target.value) || priceRange[0]));
                    const max = filterState.priceRange?.[1] ?? priceRange[1];
                    handlePriceRangeChange(min, max);
                  }}
                  className="w-32"
                />
                <span className="text-muted-foreground">to</span>
                <Input
                  type="number"
                  placeholder="Max"
                  min={priceRange[0]}
                  max={priceRange[1]}
                  value={Math.round(filterState.priceRange?.[1] ?? priceRange[1])}
                  onChange={(e) => {
                    const max = Math.max(priceRange[0], Math.min(priceRange[1], Number(e.target.value) || priceRange[1]));
                    const min = filterState.priceRange?.[0] ?? priceRange[0];
                    handlePriceRangeChange(min, max);
                  }}
                  className="w-32"
                />
                {filterState.priceRange && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onFilterChange({ ...filterState, priceRange: null })}
                  >
                    Reset
                  </Button>
                )}
              </div>
            </div>

            {/* Sort Options */}
            <div>
              <label className="text-sm font-medium mb-2 block">Sort By</label>
              <div className="flex flex-wrap gap-2">
                <Button
                  variant={filterState.sortBy === "none" ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleSortChange("none")}
                >
                  Default
                </Button>
                <Button
                  variant={filterState.sortBy === "price-asc" ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleSortChange("price-asc")}
                >
                  Price: Low to High
                </Button>
                <Button
                  variant={filterState.sortBy === "price-desc" ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleSortChange("price-desc")}
                >
                  Price: High to Low
                </Button>
                <Button
                  variant={filterState.sortBy === "title-asc" ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleSortChange("title-asc")}
                >
                  Name: A-Z
                </Button>
                <Button
                  variant={filterState.sortBy === "title-desc" ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleSortChange("title-desc")}
                >
                  Name: Z-A
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

