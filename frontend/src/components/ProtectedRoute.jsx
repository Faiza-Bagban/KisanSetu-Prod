import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { motion } from "framer-motion";

/**
 * ProtectedRoute Component
 * Logic:
 * 1. Checks if user is authenticated.
 * 2. Checks if the user's role is allowed for the specific route.
 * 3. Renders a premium "Access Denied" UI if role validation fails.
 */
export default function ProtectedRoute({ children, allowedRoles }) {
  const { user } = useAuth();
  const location = useLocation();

  // 🔐 1. SESSION CHECK: If not logged in, redirect to login
  // We save the 'from' location to redirect them back after they log in
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // 🚫 2. PERMISSION CHECK: Role not allowed for this route
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <AccessDenied role={user.role} />;
  }

  // ✅ 3. AUTHORIZED: Render the protected dashboard/page
  return children;
}

/* ---------------- ACCESS DENIED UI ---------------- */

function AccessDenied({ role }) {
  const navigate = useNavigate(); // ✅ Hook for smooth internal routing

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      style={container}
    >
      <motion.div
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        transition={{ type: "spring", damping: 15 }}
        style={card}
      >
        <div style={iconWrapper}>🚫</div>
        <h2 style={title}>Access Denied</h2>
        <p style={text}>
          Your administrative role <b>{role}</b> does not have the 
          required permissions to access this specific module.
        </p>

        <button
          onClick={() => navigate("/")}
          style={btn}
          onMouseEnter={(e) => (e.target.style.transform = "scale(1.05)")}
          onMouseLeave={(e) => (e.target.style.transform = "scale(1)")}
        >
          Return to Portal
        </button>
      </motion.div>
    </motion.div>
  );
}

/* ---------------- PREMIUM STYLES ---------------- */

const container = {
  height: "80vh",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  background: "#020617", // Matches App theme
};

const card = {
  padding: "50px",
  borderRadius: "24px",
  background: "rgba(239, 68, 68, 0.03)", // Subtle red tint
  backdropFilter: "blur(20px)",
  border: "1px solid rgba(239, 68, 68, 0.15)",
  textAlign: "center",
  maxWidth: "400px",
  boxShadow: "0 20px 40px rgba(0,0,0,0.4)",
};

const iconWrapper = {
  fontSize: "48px",
  marginBottom: "20px",
};

const title = {
  color: "#ef4444",
  fontSize: "28px",
  fontWeight: "800",
  letterSpacing: "-0.5px",
};

const text = {
  color: "#94a3b8",
  marginTop: "12px",
  marginBottom: "30px",
  lineHeight: "1.6",
  fontSize: "15px",
};

const btn = {
  padding: "14px 28px",
  background: "#10b981",
  border: "none",
  borderRadius: "12px",
  color: "#fff",
  fontWeight: "bold",
  fontSize: "15px",
  cursor: "pointer",
  transition: "all 0.3s ease",
  boxShadow: "0 10px 20px rgba(16, 185, 129, 0.2)",
};