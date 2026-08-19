import { Menu } from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { useHealthCheck } from "@/hooks/useHealthCheck";
import { cn } from "@/lib/utils";

const ASK_PATHS = ["/", "/recommendation", "/evidence", "/citations", "/confidence", "/chunks", "/trace"];

const NAV_ITEMS = [
  { to: "/", label: "Ask" },
  { to: "/search", label: "Search" },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/ingest", label: "Ingest" },
  { to: "/about", label: "About" },
] as const;

function isItemActive(to: string, pathname: string) {
  return to === "/" ? ASK_PATHS.includes(pathname) : pathname.startsWith(to);
}

export function MainNav({ onNavigate, stacked = false }: { onNavigate?: () => void; stacked?: boolean }) {
  const location = useLocation();

  return (
    <nav className={cn("flex gap-1", stacked && "flex-col px-3")} aria-label="Main">
      {NAV_ITEMS.map(({ to, label }) => {
        const active = isItemActive(to, location.pathname);
        return (
          <NavLink
            key={to}
            to={to}
            onClick={onNavigate}
            className={cn(
              "rounded-lg border border-transparent px-4 py-2 text-sm transition-colors",
              stacked && "text-left",
              active
                ? "border-primary bg-primary text-primary-foreground font-semibold"
                : "text-foreground/80 hover:border-border hover:bg-accent hover:text-foreground",
            )}
          >
            {label}
          </NavLink>
        );
      })}
    </nav>
  );
}

export default function Header() {
  const health = useHealthCheck();

  return (
    <header className="sticky top-0 z-30 flex h-[74px] items-center justify-between gap-3 border-b border-border bg-background/90 px-4 backdrop-blur md:px-6">
      <div className="flex items-center gap-4">
        <div className="grid size-9 shrink-0 place-items-center rounded-xl bg-primary font-heading text-lg font-black text-primary-foreground">
          W
        </div>
        <div>
          <div className="font-heading font-bold tracking-tight">WIQAYA</div>
          <div className="tiny hidden text-muted-foreground sm:block">evidence before confidence</div>
        </div>
      </div>

      <div className="hidden md:block">
        <MainNav />
      </div>

      <div className="flex items-center gap-3">
        <span
          className="flex items-center gap-1.5 font-data text-[10px] text-muted-foreground"
          title={health.isSuccess ? "API reachable" : health.isError ? "API unreachable" : "Checking API..."}
        >
          <span
            className={cn(
              "size-2 rounded-full",
              health.isSuccess && "bg-primary",
              health.isError && "bg-destructive",
              health.isPending && "animate-pulse bg-muted-foreground",
            )}
            aria-hidden="true"
          />
          <span className="hidden sm:inline">
            {health.isSuccess ? "API ONLINE" : health.isError ? "API OFFLINE" : "CHECKING..."}
          </span>
        </span>

        <Sheet>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" className="md:hidden" aria-label="Open navigation">
              <Menu className="size-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="right" className="w-64 bg-card p-0">
            <SheetHeader className="border-b border-border">
              <SheetTitle className="font-heading">وقاية Wiqaya</SheetTitle>
            </SheetHeader>
            <div className="py-4">
              <MainNav stacked />
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </header>
  );
}
