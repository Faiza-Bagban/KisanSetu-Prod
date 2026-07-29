import { createContext, useContext, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("ks_user")) || null;
    } catch {
      return null;
    }
  });

  /* ---------------- REGISTER (DISABLED — admin provisioning only) ---------------- */
  const register = () => {
    return {
      success: false,
      message: "Account creation requires admin provisioning. Contact your District Agriculture Office."
    };
  };

  /* ---------------- LOGIN (BACKEND) ---------------- */
  const login = async (email, password) => {
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ email, password })
      });

      if (!res.ok) return false;

      const data = await res.json();

      localStorage.setItem("ks_token", data.access_token);
      localStorage.setItem("ks_user", JSON.stringify(data.user));

      setUser(data.user);
      return true;

    } catch (err) {
      console.error("Login error:", err);
      return false;
    }
  };

  /* ---------------- LOGOUT ---------------- */
  const logout = () => {
    setUser(null);
    localStorage.removeItem("ks_user");
    localStorage.removeItem("ks_token");
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);