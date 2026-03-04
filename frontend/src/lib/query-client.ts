import { QueryClient } from "@tanstack/react-query";
import { getStatusCode } from "@/lib/error";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        if (failureCount >= 2) return false;
        const status = getStatusCode(error);
        if (status && status >= 400 && status < 500) return false;
        return true;
      },
      refetchOnWindowFocus: false,
      staleTime: 0,
      gcTime: 0,
      refetchOnMount: "always",
    },
  },
});
