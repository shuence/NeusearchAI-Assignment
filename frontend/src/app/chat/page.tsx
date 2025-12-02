"use client";

import { useState, useRef, useEffect } from "react";
import { Header } from "@/components/layout/header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ProductCarousel } from "@/components/features/products/product-carousel";
import { sendChatMessage, type ChatMessage } from "@/lib/api/chat";
import type { Product } from "@/types/product";
import { Send, Loader2, Sparkles, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { ROUTES } from "@/lib/constants";

const SUGGESTIONS = [
  "Show me gym wear that works for meetings",
  "I need something for a formal event",
  "What are your best sellers?",
  "Show me casual everyday wear",
  "I'm looking for workout clothes",
  "What's trending right now?",
];

const STORAGE_KEY = "neusearch_chat_messages";

const DEFAULT_MESSAGE: ChatMessage = {
  role: "assistant",
  content: "Hello! I'm your product recommendation assistant. How can I help you find the perfect products today?",
  timestamp: new Date().toISOString(),
};

// Load messages from localStorage
const loadMessagesFromStorage = (): ChatMessage[] => {
  if (typeof window === "undefined") return [DEFAULT_MESSAGE];
  
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      // Validate it's an array
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed;
      }
    }
  } catch (error) {
    console.error("Error loading messages from localStorage:", error);
  }
  return [DEFAULT_MESSAGE];
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

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>(loadMessagesFromStorage);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Save messages to localStorage whenever they change
  useEffect(() => {
    saveMessagesToStorage(messages);
  }, [messages]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
      // Build conversation history
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
      
      // Show toast notification
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

  const handleClearHistory = () => {
    if (confirm("Are you sure you want to clear the chat history?")) {
      const defaultMessages = [DEFAULT_MESSAGE];
      setMessages(defaultMessages);
      saveMessagesToStorage(defaultMessages);
      toast.success("Chat history cleared");
    }
  };

  return (
    <div className="h-screen bg-background flex flex-col overflow-hidden">
      <Header />

      <main className="flex-1 flex flex-col overflow-hidden">
        <div className="container mx-auto px-3 sm:px-4 py-3 sm:py-4 shrink-0 border-b">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-1.5 sm:gap-2">
              <Sparkles className="h-4 w-4 sm:h-5 sm:w-5 text-primary" />
              <h2 className="text-lg sm:text-xl font-bold">AI Chat Assistant</h2>
            </div>
            {messages.length > 1 && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleClearHistory}
                className="flex items-center gap-1.5 sm:gap-2 text-xs sm:text-sm"
              >
                <Trash2 className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                <span className="hidden sm:inline">Clear History</span>
                <span className="sm:hidden">Clear</span>
              </Button>
            )}
          </div>
        </div>

        <div className="container mx-auto px-3 sm:px-4 flex-1 flex flex-col overflow-hidden">
          <Card className="flex-1 flex flex-col overflow-hidden shadow-lg my-2 sm:my-4 mb-0 rounded-t-lg">
            <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
              {/* Messages Area */}
              <div className="flex-1 overflow-y-auto px-3 sm:px-4 pt-4 sm:pt-6 pb-6 sm:pb-8 space-y-4 sm:space-y-6 bg-linear-to-b from-background to-muted/20 min-h-0">
              {messages.map((message, index) => (
                <div key={index} className="space-y-2 sm:space-y-3">
                  {/* Message Bubble with Products Integrated */}
                  <div
                    className={`flex ${
                      message.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-[90%] sm:max-w-[85%] ${
                        message.role === "user"
                          ? "bg-primary text-primary-foreground rounded-2xl px-3 py-2 sm:px-4 sm:py-3 shadow-md text-sm"
                          : message.products && message.products.length > 0
                          ? "bg-card border border-border/50 backdrop-blur-sm rounded-2xl overflow-hidden shadow-md"
                          : "bg-muted text-foreground rounded-2xl px-3 py-2 sm:px-4 sm:py-3 shadow-sm text-sm"
                      }`}
                    >
                      {/* Message Text */}
                      <div className={message.products && message.products.length > 0 ? "px-3 sm:px-4 pt-3 sm:pt-4 pb-2" : ""}>
                        <p className="whitespace-pre-wrap text-sm sm:text-base leading-relaxed">
                          {message.content}
                        </p>
                        {message.timestamp && (
                          <p
                            className={`text-xs mt-2 ${
                              message.role === "user"
                                ? "text-primary-foreground/70"
                                : "text-muted-foreground"
                            }`}
                          >
                            {new Date(message.timestamp).toLocaleTimeString()}
                          </p>
                        )}
                      </div>

                      {/* Product Carousel - Blended with message bubble */}
                      {message.role === "assistant" && message.products && message.products.length > 0 && (
                        <div className="px-2 pb-3 pt-2 border-t border-border/50 mt-2">
                          <ProductCarousel products={message.products} />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-muted rounded-2xl px-4 py-3 flex items-center gap-2 shadow-sm">
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
              <div className="border-t border-border/50 px-3 sm:px-4 pt-3 sm:pt-4 pb-2 shrink-0">
                <p className="text-xs font-medium text-muted-foreground mb-2 sm:mb-3">
                  Try asking:
                </p>
                <div className="flex flex-wrap gap-1.5 sm:gap-2">
                  {SUGGESTIONS.map((suggestion, index) => (
                    <Badge
                      key={index}
                      variant="outline"
                      className="cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors text-[10px] sm:text-xs py-1 sm:py-1.5 px-2 sm:px-3 touch-manipulation"
                      onClick={() => handleSuggestionClick(suggestion)}
                    >
                      {suggestion}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Input Area */}
            <div className="border-t border-border/50 bg-background px-3 sm:px-4 pt-3 sm:pt-4 pb-4 sm:pb-6 shrink-0">
              <div className="flex gap-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask about products..."
                  className="flex-1 rounded-lg border border-input bg-background px-3 sm:px-4 py-2 sm:py-2.5 text-sm focus:outline-none focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50 transition-all touch-manipulation"
                  disabled={isLoading}
                  aria-label="Chat message input"
                  aria-describedby="chat-input-help"
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
              <p id="chat-input-help" className="text-xs text-muted-foreground mt-2 text-center hidden sm:block">
                Press Enter to send, Shift+Enter for new line
              </p>
            </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
