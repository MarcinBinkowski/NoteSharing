import { createRouter, createRoute, createRootRoute, Link, redirect } from "@tanstack/react-router";
import { Layout } from "@/components/Layout";
import { CreateNotePage } from "@/pages/CreateNotePage";
import { ViewNotePage } from "@/pages/ViewNotePage";
import { MyNotesPage } from "@/pages/MyNotesPage";
import { LoginPage } from "@/pages/LoginPage";
import { getCurrentUser } from "@/api/generated";

const rootRoute = createRootRoute({
  component: Layout,
  notFoundComponent: () => (
    <div className="py-12 text-center space-y-4">
      <p className="text-muted-foreground">Page not found.</p>
      <Link to="/" className="underline text-sm">
        Go to home
      </Link>
    </div>
  ),
});

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: CreateNotePage,
});

const viewNoteRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/notes/$noteId",
  component: ViewNotePage,
});

const myNotesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/notes/mine",
  beforeLoad: async () => {
    try {
      await getCurrentUser();
    } catch {
      throw redirect({ to: "/login" });
    }
  },
  component: MyNotesPage,
});

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/login",
  component: LoginPage,
});

const routeTree = rootRoute.addChildren([
  indexRoute,
  myNotesRoute,
  viewNoteRoute,
  loginRoute,
]);

export const router = createRouter({
  routeTree,
});

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}
