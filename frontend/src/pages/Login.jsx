import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "../context/AuthContext";
import { useNavigate, Link } from "react-router-dom";
import { Mail, Lock, Zap, ShieldCheck } from "lucide-react";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleFocus = (e) => {
    e.target.style.border = "1px solid #10b981";
    e.target.style.boxShadow = "0 0 10px rgba(16, 185, 129, 0.2)";
  };

  const handleBlur = (e) => {
    e.target.style.border = "1px solid rgba(255, 255, 255, 0.1)";
    e.target.style.boxShadow = "none";
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(false);

    try {
      const success = await login(email, password);

      if (!success) {
        setError(true);
        setLoading(false);
        return;
      }

      // ✅ FIX: read from localStorage directly — avoids async state timing issue
      const loggedUser = JSON.parse(localStorage.getItem("ks_user"));

      const routeMap = {
        "Farmer":           "/",
        "Field Officer":    "/officer",
        "District Officer": "/grievance",
        "Admin":            "/map"
      };

      const targetPath = routeMap[loggedUser?.role] || "/";
      console.log(`✅ Redirecting ${loggedUser?.role} → ${targetPath}`);
      navigate(targetPath, { replace: true });

    } catch (err) {
      console.error("Auth Error:", err);
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={container}>
      <div style={blob1} />
      <div style={blob2} />

      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        style={glassCard}
      >
        <div style={brandSection}>
          <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 3 }} style={logoIcon}>
            🌾
          </motion.div>
          <h1 style={brandName}>
            KISAN
            <span style={setuGlow}>SETU</span>
          </h1>
          <p style={brandTagline}>Intelligent Agriculture Administration</p>
        </div>

        <form onSubmit={handleLogin} style={form}>
          <div style={inputGroup}>
            <label style={label}><Mail size={14} /> Email Address</label>
            <input
              type="email"
              placeholder="name@kisansetu.gov"
              value={email}
              onFocus={handleFocus}
              onBlur={handleBlur}
              onChange={(e) => setEmail(e.target.value)}
              style={input}
              required
            />
          </div>

          <div style={inputGroup}>
            <label style={label}><Lock size={14} /> Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onFocus={handleFocus}
              onBlur={handleBlur}
              onChange={(e) => setPassword(e.target.value)}
              style={input}
              required
            />
          </div>

          <AnimatePresence>
            {error && (
              <motion.p
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                style={errorText}
              >
                ⚠️ Login failed. Please check your credentials.
              </motion.p>
            )}
          </AnimatePresence>

          <button
            style={loginBtn}
            disabled={loading || !email || !password}
            className="premium-login-button"
          >
            {loading ? (
              <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }}>
                  <Zap size={18} />
                </motion.div>
                <span>Authenticating...</span>
              </div>
            ) : (
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span>Secure Login</span>
                <ShieldCheck size={18} />
              </div>
            )}
          </button>
        </form>

        <div style={footerNote}>
          Don't have an account?{" "}
          <Link
            to="/signup"
            style={signupLink}
            onMouseEnter={(e) => e.target.style.textShadow = "0 0 8px rgba(16,185,129,0.6)"}
            onMouseLeave={(e) => e.target.style.textShadow = "none"}
          >
            Create one
          </Link>
        </div>
      </motion.div>

      <style>{`
        .premium-login-button { transition: all 0.3s ease; }
        .premium-login-button:hover:not(:disabled) {
          transform: scale(1.02);
          box-shadow: 0 15px 30px rgba(16, 185, 129, 0.3);
        }
      `}</style>
    </div>
  );
}

/* ---------------- STYLES ---------------- */
const container = { height: "100vh", display: "flex", justifyContent: "center", alignItems: "center", position: "relative", overflow: "hidden", background: "#020617" };
const glassCard = { width: "100%", maxWidth: "460px", padding: "50px", background: "rgba(255, 255, 255, 0.02)", backdropFilter: "blur(25px)", borderRadius: "32px", border: "1px solid rgba(255, 255, 255, 0.08)", boxShadow: "0 25px 50px rgba(0,0,0,0.6)", zIndex: 10, margin: "20px" };
const brandSection = { textAlign: "center", marginBottom: "40px" };
const logoIcon = { fontSize: "48px", marginBottom: "12px", filter: "drop-shadow(0 0 10px rgba(16, 185, 129, 0.4))" };
const brandName = { fontSize: "34px", fontWeight: 900, letterSpacing: "-1.5px", color: "#fff" };
const setuGlow = { marginLeft: "8px", color: "#10b981", textShadow: "0 0 12px rgba(16,185,129,0.5)" };
const brandTagline = { color: "#94a3b8", fontSize: "14px", marginTop: "5px" };
const form = { display: "flex", flexDirection: "column", gap: "24px" };
const inputGroup = { display: "flex", flexDirection: "column", gap: "10px" };
const label = { fontSize: "12px", color: "#64748b", fontWeight: "800", textTransform: "uppercase", letterSpacing: "1.2px", display: "flex", alignItems: "center", gap: "8px" };
const input = { padding: "16px", borderRadius: "14px", background: "rgba(0,0,0,0.4)", border: "1px solid rgba(255, 255, 255, 0.1)", color: "#fff", fontSize: "15px", outline: "none" };
const loginBtn = { padding: "18px", borderRadius: "14px", border: "none", background: "linear-gradient(135deg, #10b981, #059669)", color: "#fff", fontWeight: "900", cursor: "pointer", display: "flex", justifyContent: "center", alignItems: "center" };
const errorText = { color: "#ef4444", fontSize: "13px", textAlign: "center", fontWeight: "700" };
const footerNote = { textAlign: "center", marginTop: "28px", color: "#94a3b8", fontSize: "13px" };
const signupLink = { color: "#10b981", fontWeight: "bold", marginLeft: "6px", textDecoration: "none" };
const blob1 = { position: "absolute", width: "500px", height: "500px", background: "rgba(16, 185, 129, 0.12)", filter: "blur(100px)", borderRadius: "50%", top: "-10%", left: "10%" };
const blob2 = { position: "absolute", width: "400px", height: "400px", background: "rgba(59, 130, 246, 0.08)", filter: "blur(100px)", borderRadius: "50%", bottom: "0%", right: "5%" };