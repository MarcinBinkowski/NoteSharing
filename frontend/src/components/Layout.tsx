import { Outlet, Link, useNavigate } from "@tanstack/react-router";
import { FileText, LogIn, LogOut, FolderOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";

export function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="container mx-auto flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-4">
            <Link
              to="/"
              className="flex items-center gap-2 font-semibold text-lg hover:opacity-80 transition-opacity"
            >
              <FileText className="h-5 w-5" />
              <span>Notes</span>
            </Link>
            {user && (
              <nav className="flex items-center gap-2 ml-4">
                <Button variant="ghost" size="sm" asChild>
                  <Link to="/notes/mine">
                    <FolderOpen className="h-4 w-4 mr-1" />
                    My Notes
                  </Link>
                </Button>
              </nav>
            )}
          </div>
          <div className="flex items-center gap-2">
            {user ? (
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">{user.email}</span>
                <Button variant="ghost" size="sm" onClick={() => void logout()}>
                  <LogOut className="h-4 w-4 mr-1" />
                  Logout
                </Button>
              </div>
            ) : (
              <Button variant="outline" size="sm" onClick={() => navigate({ to: "/login" })}>
                <LogIn className="h-4 w-4 mr-1" />
                Sign In
              </Button>
            )}
          </div>
        </div>
      </header>
      <main className="container mx-auto px-4 py-8 max-w-2xl">
        <Outlet />
      </main>
    </div>
  );
}
