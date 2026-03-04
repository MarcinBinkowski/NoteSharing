import { createRouter, createRoute, createRootRouteWithContext, Link, redirect } from "@tanstack/react-router";
import { type QueryClient } from "@tanstack/react-query";
import { Layout } from "@/components/Layout";
import { CreateNotePage } from "@/pages/CreateNotePage";
import { ViewNotePage } from "@/pages/ViewNotePage";
import { MyNotesPage } from "@/pages/MyNotesPage";
import { LoginPage } from "@/pages/LoginPage";
import { getGetCurrentUserQueryOptions } from "@/api/generated";

export interface RouterContext {
  queryClient: QueryClient;
}

const rootRoute = createRootRouteWithContext<RouterContext>()({
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
  beforeLoad: async ({ context }) => {
    try {
      await context.queryClient.ensureQueryData(getGetCurrentUserQueryOptions());
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
  context: {
    queryClient: undefined!,
  },
});

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}
