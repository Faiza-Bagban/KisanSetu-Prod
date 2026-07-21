import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { motion } from "framer-motion";
import {
  LogOut,
  LayoutDashboard,
  ShieldCheck,
  MessageSquare,
  Map as MapIcon,
  BrainCircuit
} from "lucide-react";

export default function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  if (!user) return null;

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const isActive = (path) => location.pathname === path;

  // 🔥 CLEAN ROLE CONFIG
  const ROLE_NAV = {
    Farmer: [
      { path: "/", label: "Portal", icon: <LayoutDashboard size={18} /> }
    ],
    "Field Officer": [
      { path: "/", label: "Portal", icon: <LayoutDashboard size={18} /> },
      { path: "/officer", label: "Officer Desk", icon: <ShieldCheck size={18} /> }
    ],
    "District Officer": [
      { path: "/officer", label: "Officer Desk", icon: <ShieldCheck size={18} /> },
      { path: "/grievance", label: "Grievances", icon: <MessageSquare size={18} /> },
      { path: "/map", label: "Risk Map", icon: <MapIcon size={18} /> },
      { path: "/intelligence", label: "Intelligence", icon: <BrainCircuit size={18} /> }
    ],
    Admin: [
      { path: "/", label: "Portal", icon: <LayoutDashboard size={18} /> },
      { path: "/officer", label: "Officer Desk", icon: <ShieldCheck size={18} /> },
      { path: "/grievance", label: "Grievances", icon: <MessageSquare size={18} /> },
      { path: "/map", label: "Risk Map", icon: <MapIcon size={18} /> },
      { path: "/intelligence", label: "Intelligence", icon: <BrainCircuit size={18} /> }
    ]
  };

  const navItems = ROLE_NAV[user.role] || [];

  return (
    <nav style={navStyle}>
      
      {/* 🔥 PREMIUM LOGO */}
      <Link to="/" style={logoLink}>
        <span style={logoEmoji}>🌾</span>
        <span style={logoText}>
          KISAN <span style={logoGlow}>SETU</span>
        </span>
      </Link>

      {/* 🔥 NAVIGATION - Now calling the sub-component defined below */}
      <div style={navLinks}>
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            icon={item.icon}
            label={item.label}
            active={isActive(item.path)}
          />
        ))}
      </div>

      {/* 🔥 USER + LOGOUT */}
      <div style={userSection}>
        <div style={userInfo}>
          <span style={userName}>{user.name}</span>
          <span style={userRole}>{user.role}</span>
        </div>

        <button 
          onClick={handleLogout} 
          style={logoutBtn}
          className="logout-button-premium"
          title="Secure Logout"
        >
          <LogOut size={18} />
        </button>
      </div>

      <style>{`
        .logout-button-premium {
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          cursor: pointer;
        }
        .logout-button-premium:hover {
          transform: scale(1.1);
          background: rgba(239, 68, 68, 0.15) !important;
          box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
        }
        .logout-button-premium:active {
          transform: scale(0.95);
        }
      `}</style>
    </nav>
  );
}

/* ✅ RESTORED: NAV LINK SUB-COMPONENT */
function NavLink({ to, icon, label, active }) {
  return (
    <Link to={to} style={{ ...linkStyle, color: active ? "#10b981" : "#94a3b8" }}>
      <motion.div whileHover={{ y: -2 }} style={linkInner}>
        {icon}
        <span>{label}</span>

        {active && (
          <motion.div
            layoutId="nav-underline"
            style={activeLine}
          />
        )}
      </motion.div>
    </Link>
  );
}

/* ---------------- STYLES ---------------- */

const navStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "15px 50px",
  background: "rgba(2, 6, 23, 0.85)",
  backdropFilter: "blur(20px)",
  borderBottom: "1px solid rgba(255,255,255,0.08)",
  position: "sticky",
  top: 0,
  zIndex: 1000
};

const logoLink = { display: "flex", alignItems: "center", gap: "10px", textDecoration: "none" };
const logoEmoji = { fontSize: "24px" };

const logoText = {
  color: "#fff",
  fontWeight: 900,
  fontSize: "20px",
  letterSpacing: "-0.5px"
};

const logoGlow = {
  color: "#10b981",
  marginLeft: "4px",
  textShadow: "0 0 12px rgba(16,185,129,0.8)"
};

const navLinks = { display: "flex", gap: "35px", alignItems: "center" };

const linkStyle = {
  textDecoration: "none",
  fontSize: "14px",
  fontWeight: "700",
  position: "relative"
};

const linkInner = {
  display: "flex",
  alignItems: "center",
  gap: "8px"
};

const activeLine = {
  position: "absolute",
  bottom: "-22px",
  left: 0,
  right: 0,
  height: "3px",
  background: "linear-gradient(90deg, #10b981, #22c55e)",
  borderRadius: "10px",
  boxShadow: "0 0 10px rgba(16,185,129,0.6)"
};

const userSection = {
  display: "flex",
  alignItems: "center",
  gap: "15px"
};

const userInfo = {
  display: "flex",
  flexDirection: "column",
  alignItems: "flex-end"
};

const userName = {
  color: "#fff",
  fontSize: "14px",
  fontWeight: "700"
};

const userRole = {
  color: "#10b981",
  fontSize: "10px",
  fontWeight: "800",
  textTransform: "uppercase",
  letterSpacing: "1px"
};

const logoutBtn = {
  background: "rgba(239, 68, 68, 0.08)",
  color: "#ef4444",
  border: "1px solid rgba(239, 68, 68, 0.2)",
  padding: "10px",
  borderRadius: "12px",
  cursor: "pointer",
  transition: "0.3s ease"
};