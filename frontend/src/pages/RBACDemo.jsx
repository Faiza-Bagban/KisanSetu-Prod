import { motion } from "framer-motion";
import { useAuth } from "../context/AuthContext";
import { ShieldCheck, Eye, EyeOff, MapPin, Inbox, Database } from "lucide-react";

export default function RBACDemo() {
  const { user } = useAuth();

  const modules = [
    {
      title: "Nashik Field Records",
      icon: <Database size={20} />,
      description: "Localized farmer data (Nashik only)",
      allowed:
        user.role === "Admin" ||
        (user.role === "Field Officer" && user.district === "Nashik"),
      rule: "Field Officer (Nashik) OR Admin"
    },
    {
      title: "Pune District Data",
      icon: <MapPin size={20} />,
      description: "Restricted administrative dataset",
      allowed:
        user.role === "Admin" ||
        (user.role === "District Officer" && user.district === "Pune"),
      rule: "District Officer (Pune) OR Admin"
    },
    {
      title: "Grievance Inbox",
      icon: <Inbox size={20} />,
      description: "Sensitive farmer complaints",
      allowed: ["District Officer", "Admin"].includes(user.role),
      rule: "District Officer OR Admin"
    }
  ];

  return (
    <div style={container}>
      
      {/* HEADER */}
      <div style={header}>
        <div style={userInfo}>
          <div style={avatar}>{user.name[0]}</div>
          <div>
            <h2 style={name}>{user.name}</h2>
            <p style={role}>{user.role} • {user.district}</p>
          </div>
        </div>

        <div style={live}>
          <span style={pulse} />
          LIVE RBAC ENGINE
        </div>
      </div>

      {/* GRID */}
      <div style={grid}>
        {modules.map((m, i) => (
          <motion.div
            key={i}
            whileHover={{ y: -5 }}
            style={{
              ...card,
              border: `1px solid ${
                m.allowed
                  ? "rgba(16,185,129,0.3)"
                  : "rgba(239,68,68,0.3)"
              }`
            }}
          >
            {/* TOP */}
            <div style={top}>
              <div style={m.allowed ? iconPass : iconFail}>{m.icon}</div>

              <div style={{
                ...status,
                color: m.allowed ? "#10b981" : "#ef4444"
              }}>
                {m.allowed ? <Eye size={14}/> : <EyeOff size={14}/>}
                {m.allowed ? "ACCESS GRANTED" : "ACCESS DENIED"}
              </div>
            </div>

            {/* CONTENT */}
            <h3 style={title}>{m.title}</h3>
            <p style={desc}>{m.description}</p>

            {/* RULE BOX */}
            <div style={ruleBox}>
              <span style={ruleLabel}>Access Rule:</span>
              <span style={ruleText}>{m.rule}</span>
            </div>

            {/* EXTRA EXPLANATION */}
            {!m.allowed && (
              <div style={denyBox}>
                🚫 You don't meet required role/district
              </div>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
}

/* ---------------- STYLES ---------------- */

const container = {
  padding: "50px 20px",
  maxWidth: "1100px",
  margin: "auto"
};

const header = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: "40px"
};

const userInfo = { display: "flex", gap: "15px", alignItems: "center" };

const avatar = {
  width: "50px",
  height: "50px",
  borderRadius: "12px",
  background: "#10b981",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontWeight: "bold",
  color: "#fff",
  fontSize: "20px"
};

const name = { color: "#fff", margin: 0 };
const role = { color: "#10b981", fontSize: "12px", fontWeight: "800" };

const live = {
  fontSize: "11px",
  fontWeight: "900",
  color: "#64748b",
  display: "flex",
  alignItems: "center",
  gap: "8px"
};

const pulse = {
  width: "8px",
  height: "8px",
  borderRadius: "50%",
  background: "#10b981",
  boxShadow: "0 0 10px #10b981"
};

const grid = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit,minmax(300px,1fr))",
  gap: "25px"
};

const card = {
  padding: "30px",
  borderRadius: "24px",
  background: "rgba(255,255,255,0.02)",
  backdropFilter: "blur(10px)",
  display: "flex",
  flexDirection: "column",
  gap: "15px"
};

const top = {
  display: "flex",
  justifyContent: "space-between"
};

const iconPass = {
  padding: "12px",
  background: "rgba(16,185,129,0.1)",
  color: "#10b981",
  borderRadius: "12px"
};

const iconFail = {
  padding: "12px",
  background: "rgba(239,68,68,0.1)",
  color: "#ef4444",
  borderRadius: "12px"
};

const status = {
  display: "flex",
  alignItems: "center",
  gap: "6px",
  fontSize: "11px",
  fontWeight: "900"
};

const title = { color: "#fff", fontSize: "18px", fontWeight: "700" };
const desc = { color: "#94a3b8", fontSize: "14px" };

const ruleBox = {
  padding: "12px",
  background: "rgba(0,0,0,0.3)",
  borderRadius: "12px"
};

const ruleLabel = {
  fontSize: "10px",
  color: "#64748b",
  textTransform: "uppercase"
};

const ruleText = {
  fontSize: "13px",
  color: "#cbd5e1",
  fontWeight: "600"
};

const denyBox = {
  marginTop: "10px",
  padding: "10px",
  borderRadius: "10px",
  background: "rgba(239,68,68,0.1)",
  color: "#ef4444",
  fontSize: "12px",
  fontWeight: "600"
};