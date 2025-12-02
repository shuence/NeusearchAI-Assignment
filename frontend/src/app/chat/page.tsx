"use client";

import { useState, useRef, useEffect } from "react";
import { Header } from "@/components/layout/header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ProductCarousel } from "@/components/features/products/product-carousel";
import { sendChatMessage, type ChatMessage } from "@/lib/api/chat";
import type { Product } from "@/types/product";
import { Send, Loader2, Sparkles } from "lucide-react";

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
    <div className="min-h-screen bg-background flex flex-col">
      <Header />

      <main className="container mx-auto px-4 py-8 flex-1 flex flex-col max-w-4xl">
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="h-6 w-6 text-primary" />
            <h2 className="text-3xl font-bold">AI Chat Assistant</h2>
          </div>
          <p className="text-muted-foreground">
            Ask me anything about our products. I can help you find what you're looking for!
          </p>
        </div>

        <Card className="flex-1 flex flex-col overflow-hidden shadow-lg">
          <CardContent className="flex-1 flex flex-col p-0">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-gradient-to-b from-background to-muted/20">
              {messages.map((message, index) => (
                <div key={index} className="space-y-3">
                  {/* Message Bubble with Products Integrated */}
                  <div
                    className={`flex ${
                      message.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-[85%] ${
                        message.role === "user"
                          ? "bg-primary text-primary-foreground rounded-2xl px-4 py-3 shadow-md"
                          : message.products && message.products.length > 0
                          ? "bg-card border border-border/50 backdrop-blur-sm rounded-2xl overflow-hidden shadow-md"
                          : "bg-muted text-foreground rounded-2xl px-4 py-3 shadow-sm"
                      }`}
                    >
                      {/* Message Text */}
                      <div className={message.products && message.products.length > 0 ? "px-4 pt-4 pb-2" : ""}>
                        <p className="whitespace-pre-wrap text-sm leading-relaxed">
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
              <div className="border-t border-border/50 px-4 pt-4 pb-2">
                <p className="text-xs font-medium text-muted-foreground mb-3">
                  Try asking:
                </p>
                <div className="flex flex-wrap gap-2">
                  {SUGGESTIONS.map((suggestion, index) => (
                    <Badge
                      key={index}
                      variant="outline"
                      className="cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors text-xs py-1.5 px-3"
                      onClick={() => handleSuggestionClick(suggestion)}
                    >
                      {suggestion}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Input Area */}
            <div className="border-t border-border/50 bg-background p-4">
              <div className="flex gap-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask about products... (e.g., 'Looking for something I can wear in the gym and also in meetings')"
                  className="flex-1 rounded-lg border border-input bg-background px-4 py-2.5 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-all"
                  disabled={isLoading}
                />
                <Button
                  onClick={handleSend}
                  disabled={!input.trim() || isLoading}
                  size="icon"
                  className="shrink-0"
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-2 text-center">
                Press Enter to send, Shift+Enter for new line
              </p>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
