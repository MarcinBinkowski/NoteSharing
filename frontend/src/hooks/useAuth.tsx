import { createContext, useContext, useCallback, useMemo, type ReactNode } from "react";
import {
  logout as logoutApi,
  useGetCurrentUser,
  type UserResponse,
} from "@/api/generated";

export type User = UserResponse;

interface AuthContextType {
  user: User | null;
  login: () => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const currentUserQuery = useGetCurrentUser({
    query: {
      staleTime: 0,
      gcTime: 0,
      refetchOnMount: "always",
    },
  });
  const user = currentUserQuery.data ?? null;

  const login = useCallback(() => {
    window.location.href = "/api/auth/login/google";
  }, []);

  const logout = useCallback(async () => {
    await logoutApi();
    window.location.assign("/login");
  }, []);

  const contextValue = useMemo(() => ({ user, login, logout }), [user, login, logout]);

  return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within <AuthProvider>");
  }
  return ctx;
}
