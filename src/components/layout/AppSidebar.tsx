import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Code2, FileText, BarChart3, Settings, ChevronLeft, Flame, MessageCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const navItems = [
  { title: "Code Assistant", path: "/", icon: Code2 },
  { title: "ChatBot", path: "/chatbot", icon: MessageCircle },
  { title: "Document Assistant", path: "/documents", icon: FileText },
  { title: "Analytics", path: "/analytics", icon: BarChart3 },
  { title: "Settings", path: "/settings", icon: Settings },
];

export function AppSidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  return (
    <aside
      className={cn(
        "h-screen bg-sidebar border-r border-sidebar-border flex flex-col transition-all duration-300 ease-out",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Logo */}
      <div className="h-24 flex items-center px-4 border-b border-sidebar-border">
        <div className="flex items-center gap-3 overflow-hidden">
          <img 
            src="/chakra-logo.png" 
            alt="Chakra AI Logo" 
            className={cn(
              "flex-shrink-0 object-contain transition-all",
              collapsed ? "w-14 h-14" : "w-20 h-20"
            )}
          />
          {!collapsed && (
            <span className="font-semibold text-foreground whitespace-nowrap animate-fade-in">
              Chakra AI
            </span>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200",
                "hover:bg-sidebar-accent group",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                  : "text-sidebar-foreground"
              )}
            >
              <item.icon
                className={cn(
                  "w-5 h-5 flex-shrink-0 transition-colors",
                  isActive ? "text-primary" : "text-sidebar-foreground group-hover:text-foreground"
                )}
              />
              {!collapsed && (
                <span className="truncate animate-fade-in">{item.title}</span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Collapse button */}
      <div className="p-3 border-t border-sidebar-border">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setCollapsed(!collapsed)}
          className={cn(
            "w-full justify-start gap-3 text-sidebar-foreground hover:text-foreground",
            collapsed && "justify-center"
          )}
        >
          <ChevronLeft
            className={cn(
              "w-4 h-4 transition-transform duration-300",
              collapsed && "rotate-180"
            )}
          />
          {!collapsed && <span>Collapse</span>}
        </Button>
      </div>
    </aside>
  );
}
