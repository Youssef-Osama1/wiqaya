import { Menu } from "lucide-react";
import { useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { SidebarNav } from "@/components/layout/Sidebar";
import ThemeToggle from "@/components/layout/ThemeToggle";
import { useHealthCheck } from "@/hooks/useHealthCheck";
import { cn } from "@/lib/utils";

const PAGE_TITLES: Record<string, string> = {
  "/": "Ask",
  "/evidence": "Ask — Evidence",
  "/answer": "Ask — Answer",
  "/trace": "Ask — Trace",
  "/search": "Search",
  "/dashboard": "Dashboard",
  "/ingest": "Ingest",
  "/about": "About",
};

export default function Header() {
  const location = useLocation();
  const health = useHealthCheck();
  const title = PAGE_TITLES[location.pathname] ?? "Wiqaya";

  return (
    <header className="flex h-16 items-center gap-3 border-b border-border bg-card px-4 md:px-6">
      <Sheet>
        <SheetTrigger asChild>
          <Button variant="ghost" size="icon" className="md:hidden" aria-label="Open navigation">
            <Menu className="size-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-64 bg-sidebar p-0">
          <SheetHeader className="border-b border-sidebar-border">
            <SheetTitle className="font-heading text-sidebar-foreground">وقاية Wiqaya</SheetTitle>
          </SheetHeader>
          <div className="py-4">
            <SidebarNav />
          </div>
        </SheetContent>
      </Sheet>

      <h1 className="font-heading text-lg font-semibold">{title}</h1>

      <div className="ml-auto flex items-center gap-3">
        <span
          className="flex items-center gap-1.5 text-xs text-muted-foreground"
          title={health.isSuccess ? "API reachable" : health.isError ? "API unreachable" : "Checking API..."}
        >
          <span
            className={cn(
              "size-2 rounded-full",
              health.isSuccess && "bg-success",
              health.isError && "bg-destructive",
              health.isPending && "bg-muted-foreground animate-pulse",
            )}
            aria-hidden="true"
          />
          <span className="hidden sm:inline">{health.isSuccess ? "API online" : health.isError ? "API offline" : "Checking..."}</span>
        </span>
        <ThemeToggle />
      </div>
    </header>
  );
}
