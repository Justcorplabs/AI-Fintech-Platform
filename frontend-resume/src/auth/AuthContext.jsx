import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { authAPI } from "../services/authApi";
import {
  clearAuthTokens,
  getAccessToken,
} from "../services/authStorage";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function restoreSession() {
      const accessToken = getAccessToken();

      if (!accessToken) {
        if (active) {
          setLoading(false);
        }

        return;
      }

      try {
        const response =
          await authAPI.getCurrentUser();

        if (active) {
          setUser(response.data);
        }
      } catch {
        clearAuthTokens();

        if (active) {
          setUser(null);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    restoreSession();

    return () => {
      active = false;
    };
  }, []);

  async function login(credentials) {
    await authAPI.login(credentials);

    try {
      const response =
        await authAPI.getCurrentUser();

      setUser(response.data);

      return response.data;
    } catch (error) {
      clearAuthTokens();
      setUser(null);

      throw error;
    }
  }

  function logout() {
    clearAuthTokens();
    setUser(null);
  }

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      login,
      logout,
    }),
    [user, loading]
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used within AuthProvider."
    );
  }

  return context;
}
