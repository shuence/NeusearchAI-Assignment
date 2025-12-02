"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ProductCarousel } from "@/components/features/products/product-carousel";
import { sendChatMessage, type ChatMessage } from "@/lib/api/chat";
import { Send, Loader2, Sparkles, X, MessageCircle, Maximize2 } from "lucide-react";
import { toast } from "sonner";
import { ROUTES } from "@/lib/constants";

const SUGGESTIONS = [
  "Show me gym wear that works for meetings",
  "I need something for a formal event",
  "What are your best sellers?",
  "Show me casual everyday wear",
];

const STORAGE_KEY = "neusearch_chat_messages";

const getDefaultMessage = (): ChatMessage => ({
  role: "assistant",
  content: "Hello! I'm your product recommendation assistant. How can I help you find the perfect products today?",
  timestamp: new Date().toISOString(),
});

// Load messages from localStorage
const loadMessagesFromStorage = (): ChatMessage[] => {
  if (typeof window === "undefined") return [];
  
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed;
      }
    }
  } catch (error) {
    console.error("Error loading messages from localStorage:", error);
  }
  return [getDefaultMessage()];
};

// Save messages to localStorage
const saveMessagesToStorage = (messages: ChatMessage[]) => {
  if (typeof window === "undefined") return;
  
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  } catch (error) {
    console.error("Error saving messages to localStorage:", error);
  }
};

export function FloatingChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isMounted, setIsMounted] = useState(false);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load messages from localStorage only on client side after mount
  useEffect(() => {
    setIsMounted(true);
    const loadedMessages = loadMessagesFromStorage();
    if (loadedMessages.length === 0) {
      setMessages([getDefaultMessage()]);
    } else {
      setMessages(loadedMessages);
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Save messages to localStorage whenever they change
  useEffect(() => {
    if (isMounted) {
      saveMessagesToStorage(messages);
    }
  }, [messages, isMounted]);

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
      // Focus input when opened
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [messages, isOpen]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      role: "user",
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const conversationHistory = messages
        .filter((msg) => msg.role !== "assistant" || !msg.products)
        .map((msg) => ({
          role: msg.role,
          content: msg.content,
        }));

      const response = await sendChatMessage({
        message: userMessage.content,
        conversation_history: conversationHistory,
        max_results: 5,
        similarity_threshold: 0.6,
      });

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.response,
        timestamp: new Date().toISOString(),
        products: response.products.length > 0 ? response.products : undefined,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      
      if (error instanceof Error) {
        if (error.message.includes("429")) {
          toast.error("Rate limit exceeded", {
            description: "Please wait a moment before sending another message.",
          });
        } else if (error.message.includes("NetworkError") || error.message.includes("Failed to fetch")) {
          toast.error("Network error", {
            description: "Please check your internet connection and try again.",
          });
        } else {
          toast.error("Failed to send message", {
            description: error.message || "Please try again later.",
          });
        }
      } else {
        toast.error("An unexpected error occurred", {
          description: "Please try again later.",
        });
      }
      
      const errorMessage: ChatMessage = {
        role: "assistant",
        content: "I'm sorry, I encountered an error. Please try again.",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
    inputRef.current?.focus();
  };

  return (
    <>
      {/* Floating Chat Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-50 h-12 w-12 sm:h-14 sm:w-14 rounded-full bg-primary text-primary-foreground shadow-lg hover:shadow-xl transition-all hover:scale-110 active:scale-95 flex items-center justify-center group touch-manipulation"
          aria-label="Open chat assistant"
        >
          <MessageCircle className="h-5 w-5 sm:h-6 sm:w-6" />
          <span className="absolute -top-1 -right-1 h-2.5 w-2.5 sm:h-3 sm:w-3 bg-red-500 rounded-full animate-pulse" />
        </button>
      )}

      {/* Chat Widget Overlay */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/50 z-40"
            onClick={() => setIsOpen(false)}
            aria-hidden="true"
          />
          
          {/* Chat Widget */}
          <div className="fixed inset-0 sm:inset-auto sm:bottom-6 sm:right-6 z-50 w-full sm:w-[420px] h-full sm:h-[600px] flex flex-col shadow-2xl rounded-none sm:rounded-lg overflow-hidden bg-background border-0 sm:border border-border">
            {/* Header */}
            <div className="bg-primary text-primary-foreground px-4 py-3 flex items-center justify-between shrink-0">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                <h3 className="font-semibold">AI Assistant</h3>
              </div>
              <div className="flex items-center gap-2">
                <Link
                  href={ROUTES.CHAT}
                  onClick={() => setIsOpen(false)}
                  className="group flex items-center gap-1.5 px-2.5 py-1.5 rounded-md hover:bg-primary-foreground/20 transition-all duration-300 hover:scale-105 active:scale-95"
                  aria-label="Open full chat page"
                >
                  <Maximize2 className="h-3.5 w-3.5 text-primary-foreground group-hover:scale-110 transition-transform duration-300" />
                  <span className="text-xs font-medium text-primary-foreground hidden sm:inline">
                    Expand
                  </span>
                </Link>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setIsOpen(false)}
                  className="h-8 w-8 text-primary-foreground hover:bg-primary-foreground/20"
                  aria-label="Close chat"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-3 sm:space-y-4 bg-background min-h-0">
              {messages.map((message, index) => (
                <div key={index} className="space-y-2">
                  <div
                    className={`flex ${
                      message.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-[90%] sm:max-w-[85%] ${
                        message.role === "user"
                          ? "bg-primary text-primary-foreground rounded-2xl px-3 py-2 text-sm shadow-md"
                          : message.products && message.products.length > 0
                          ? "bg-card border border-border/50 rounded-2xl overflow-hidden shadow-md"
                          : "bg-muted text-foreground rounded-2xl px-3 py-2 text-sm shadow-sm"
                      }`}
                    >
                      <div className={message.products && message.products.length > 0 ? "px-3 pt-3 pb-2" : ""}>
                        <p className="whitespace-pre-wrap text-sm leading-relaxed">
                          {message.content}
                        </p>
                        {message.timestamp && isMounted && (
                          <p
                            className={`text-xs mt-1 ${
                              message.role === "user"
                                ? "text-primary-foreground/70"
                                : "text-muted-foreground"
                            }`}
                          >
                            {new Date(message.timestamp).toLocaleTimeString()}
                          </p>
                        )}
                      </div>

                      {message.role === "assistant" && message.products && message.products.length > 0 && (
                        <div className="px-2 pb-2 pt-1 border-t border-border/50 mt-2">
                          <ProductCarousel products={message.products} cardWidth={320} />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-muted rounded-2xl px-3 py-2 flex items-center gap-2 shadow-sm">
                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                    <span className="text-sm text-muted-foreground">
                      Thinking...
                    </span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Suggestions */}
            {messages.filter((msg) => msg.role === "user").length === 0 && !isLoading && (
              <div className="border-t border-border/50 px-4 pt-3 pb-2 shrink-0 bg-background">
                <p className="text-xs font-medium text-muted-foreground mb-2">
                  Try asking:
                </p>
                <div className="flex flex-wrap gap-2">
                  {SUGGESTIONS.map((suggestion, index) => (
                    <Badge
                      key={index}
                      variant="outline"
                      className="cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors text-xs py-1 px-2"
                      onClick={() => handleSuggestionClick(suggestion)}
                    >
                      {suggestion}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Input Area */}
            <div className="border-t border-border/50 bg-background p-2.5 sm:p-3 shrink-0">
              <div className="flex gap-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask about products..."
                  className="flex-1 rounded-lg border border-input bg-background px-3 py-2 text-sm focus:outline-none focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50 transition-all touch-manipulation"
                  disabled={isLoading}
                  aria-label="Chat message input"
                />
                <Button
                  onClick={handleSend}
                  disabled={!input.trim() || isLoading}
                  size="icon"
                  className="shrink-0 h-9 w-9 sm:h-10 sm:w-10 touch-manipulation"
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}

