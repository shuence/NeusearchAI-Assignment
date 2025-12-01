import Link from "next/link";
import { ROUTES } from "@/lib/constants";

export function Header() {
  return (
    <header className="border-b sticky top-0 bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/60 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link href={ROUTES.HOME} className="flex flex-col">
            <h1 className="text-2xl font-bold">Neusearch AI</h1>
            <p className="text-sm text-muted-foreground">
              Product Discovery Assistant
            </p>
          </Link>
          <nav className="flex items-center gap-4">
            <Link
              href={ROUTES.HOME}
              className="text-sm font-medium hover:text-primary transition-colors"
            >
              Products
            </Link>
            <Link
              href={ROUTES.CHAT}
              className="text-sm font-medium hover:text-primary transition-colors"
            >
              Chat
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
}

