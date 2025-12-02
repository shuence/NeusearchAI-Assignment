import Link from "next/link";
import { ROUTES } from "@/lib/constants";
import { Sparkles, Github, Mail } from "lucide-react";

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t bg-background mt-auto">
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand Section */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-primary" />
              <h3 className="text-xl font-bold">Neusearch AI</h3>
            </div>
            <p className="text-sm text-muted-foreground">
              AI-powered product discovery assistant with RAG capabilities. 
              Find the perfect products using natural language queries.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="font-semibold mb-4">Quick Links</h4>
            <ul className="space-y-2">
              <li>
                <Link
                  href={ROUTES.HOME}
                  className="text-sm text-muted-foreground hover:text-primary transition-colors"
                >
                  All Products
                </Link>
              </li>
              <li>
                <Link
                  href={ROUTES.CHAT}
                  className="text-sm text-muted-foreground hover:text-primary transition-colors"
                >
                  AI Chat Assistant
                </Link>
              </li>
              <li>
                <Link
                  href={ROUTES.COMPARE}
                  className="text-sm text-muted-foreground hover:text-primary transition-colors"
                >
                  Compare Products
                </Link>
              </li>
              <li>
                <a
                  href="https://neusearchai.shuence.com/docs"
                  className="text-sm text-muted-foreground hover:text-primary transition-colors"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  API Documentation
                </a>
              </li>
            </ul>
          </div>

          {/* Features */}
          <div>
            <h4 className="font-semibold mb-4">Features</h4>
            <ul className="space-y-2">
              <li className="text-sm text-muted-foreground">
                Semantic Search
              </li>
              <li className="text-sm text-muted-foreground">
                AI Recommendations
              </li>
              <li className="text-sm text-muted-foreground">
                Product Filtering
              </li>
              <li className="text-sm text-muted-foreground">
                Similar Products
              </li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="font-semibold mb-4">Contact</h4>
            <ul className="space-y-2">
              <li>
                <a
                  href="mailto:shubhampitekar2323@gmail.com"
                  className="text-sm text-muted-foreground hover:text-primary transition-colors flex items-center gap-2"
                >
                  <Mail className="h-4 w-4" />
                  shubhampitekar2323@gmail.com
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/shuence/NeusearchAI-Assignment"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-muted-foreground hover:text-primary transition-colors flex items-center gap-2"
                >
                  <Github className="h-4 w-4" />
                  GitHub Repository
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-muted-foreground">
            © {currentYear} Neusearch AI. All rights reserved.
          </p>
          <div className="flex items-center gap-6 text-sm text-muted-foreground">
            <Link
              href="#"
              className="hover:text-primary transition-colors"
            >
              Privacy Policy
            </Link>
            <Link
              href="#"
              className="hover:text-primary transition-colors"
            >
              Terms of Service
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}

