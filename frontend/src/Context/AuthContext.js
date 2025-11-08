import React, { createContext, useContext, useState } from "react";
import apiClient from "../api/apiClient";
import useToken from "./useToken";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const { token, setToken, removeToken, isAuthenticated } = useToken();
  const [user, setUser] = useState(() => {
    const storedUser = localStorage.getItem("user");
    return storedUser ? JSON.parse(storedUser) : null;
  });

  // Login via backend
  const login = async (email, password) => {
    try {
      const response = await apiClient.post("/auth/login", { email, password });

      if (response.data.success) {
        const { user: userData, access_token } = response.data;
        setUser(userData);
        setToken(access_token);
        localStorage.setItem("user", JSON.stringify(userData));
        return { success: true };
      } else {
        return { success: false, message: response.data.message };
      }
    } catch (err) {
      console.error("Login error:", err);
      return { success: false, message: err.message || "Login failed" };
    }
  };

  // Signup via backend
  const signup = async (name, email, password) => {
    try {
      const response = await apiClient.post("/auth/signup", { name, email, password });

      if (response.data.success) {
        const { user: userData, access_token } = response.data;
        setUser(userData);
        setToken(access_token);
        localStorage.setItem("user", JSON.stringify(userData));
        return { success: true };
      } else {
        return { success: false, message: response.data.message };
      }
    } catch (err) {
      console.error("Signup error:", err);
      return { success: false, message: err.message || "Signup failed" };
    }
  };

  // Logout via backend
  const logout = async () => {
    try {
      // optional: call backend logout endpoint
      await apiClient.post("/auth/logout", {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch (err) {
      console.warn("Backend logout failed (ignoring):", err);
    } finally {
      removeToken();
      localStorage.removeItem("user");
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{ token, isAuthenticated, user, login, signup, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
