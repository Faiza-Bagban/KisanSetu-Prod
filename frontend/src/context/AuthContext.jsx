import { createContext, useContext, useState } from "react";

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("ks_user")) || null;
    } catch {
      return null;
    }
  });

  /* ---------------- REGISTER (LOCAL ONLY) ---------------- */
  const register = (name, email, password, role, district) => {
    const users = JSON.parse(localStorage.getItem("ks_users")) || [];

    if (users.find(u => u.email === email)) {
      return { success: false, message: "User already exists" };
    }

    const newUser = { name, email, password, role, district };
    localStorage.setItem("ks_users", JSON.stringify([...users, newUser]));

    return { success: true };
  };

  /* ---------------- LOGIN (BACKEND ONLY) ---------------- */
  const login = async (email, password) => {
    try {
      const res = await fetch("http://localhost:8000/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        // ✅ Role removed — backend decides role from DB
        body: JSON.stringify({ email, password })
      });

      if (!res.ok) return false;

      const data = await res.json();

      // ✅ FIX: was data.token before (undefined), backend returns access_token
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