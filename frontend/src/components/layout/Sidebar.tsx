import { Info, LayoutDashboard, MessageSquareText, Telescope, UploadCloud } from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";

const ASK_PATHS = ["/", "/evidence", "/answer", "/trace"];

const NAV_ITEMS = [
  { to: "/", label: "Ask", icon: MessageSquareText },
  { to: "/search", label: "Search", icon: Telescope },
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/ingest", label: "Ingest", icon: UploadCloud },
  { to: "/about", label: "About", icon: Info },
] as const;

export function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  const location = useLocation();

  return (
    <nav className="flex flex-col gap-1 px-3">
      {NAV_ITEMS.map(({ to, label, icon: Icon }) => {
        const isActive = to === "/" ? ASK_PATHS.includes(location.pathname) : location.pathname.startsWith(to);
        return (
          <NavLink
            key={to}
            to={to}
            onClick={onNavigate}
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              isActive
                ? "bg-sidebar-accent text-sidebar-accent-foreground"
                : "text-sidebar-foreground/80 hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground",
            )}
          >
            <Icon className="size-4 shrink-0" aria-hidden="true" />
            {label}
          </NavLink>
        );
      })}
    </nav>
  );
}

export default function Sidebar() {
  return (
    <aside className="hidden w-60 shrink-0 flex-col border-r border-sidebar-border bg-sidebar md:flex">
      <div className="flex h-16 items-center gap-2 border-b border-sidebar-border px-5">
        <span className="font-heading text-lg font-semibold tracking-tight text-sidebar-foreground">وقاية</span>
        <span className="text-sm text-sidebar-foreground/60">Wiqaya</span>
      </div>
      <div className="flex-1 overflow-y-auto py-4">
        <SidebarNav />
      </div>
    </aside>
  );
}
