import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate, Link } from "react-router-dom";
import { User, Mail, Lock, UserCircle, MapPin, ArrowRight, Zap } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const DISTRICTS = ["Nashik", "Pune", "Aurangabad", "Solapur", "Kolhapur", "Amravati"];

export default function Signup() {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    role: "Farmer",
    district: ""
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFocus = (e) => {
    e.target.style.border = "1px solid #10b981";
    e.target.style.boxShadow = "0 0 10px rgba(16, 185, 129, 0.2)";
  };

  const handleBlur = (e) => {
    e.target.style.border = "1px solid rgba(255, 255, 255, 0.1)";
    e.target.style.boxShadow = "none";
  };

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleSignup = async (e) => {
  e.preventDefault();
  setError("");

  if (!formData.name || !formData.email || !formData.password || !formData.district) {
    setError("Please fill all fields before initializing.");
    return;
  }

  setLoading(true);

  try {
    await new Promise(r => setTimeout(r, 1200));

    const res = register(
      formData.name,
      formData.email,
      formData.password,
      formData.role,
      formData.district
    );

    if (res.success) {
      navigate("/login");
    } else {
      setError(res.message);
    }

  } catch {
    setError("Account initialization failed.");
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
        transition={{ duration: 0.5 }}
        style={glassCard}
      >
        {/* 🌾 BRANDING (same as login) */}
        <div style={brandSection}>
          <motion.div
            animate={{ y: [0, -5, 0] }}
            transition={{ repeat: Infinity, duration: 3 }}
            style={logoIcon}
          >
            🌾
          </motion.div>

          <h1 style={brandName}>
            KISAN
            <span style={setuGlow}> SETU</span>
          </h1>

          <p style={brandTagline}>
            Intelligent Agriculture Administration
          </p>
        </div>

        <form onSubmit={handleSignup} style={form}>
          
          <Input name="name" labelText="Full Name" icon={<User size={14} />} {...{handleChange, handleFocus, handleBlur}} />
          <Input name="email" type="email" labelText="Email Address" icon={<Mail size={14} />} {...{handleChange, handleFocus, handleBlur}} />
          <Input name="password" type="password" labelText="Password" icon={<Lock size={14} />} {...{handleChange, handleFocus, handleBlur}} />

          <div style={grid}>
            <div style={inputGroup}>
              <label style={label}><UserCircle size={14}/> Role</label>
              <select name="role" onChange={handleChange} onFocus={handleFocus} onBlur={handleBlur} style={select}>
                <option value="Farmer">Farmer</option>
                <option value="Field Officer">Field Officer</option>
                <option value="District Officer">District Officer</option>
                <option value="Admin">Admin</option>
              </select>
            </div>

            <div style={inputGroup}>
              <label style={label}><MapPin size={14}/> District</label>
              <select name="district" onChange={handleChange} onFocus={handleFocus} onBlur={handleBlur} style={select}>
                <option value="">Select</option>
                {DISTRICTS.map(d => <option key={d}>{d}</option>)}
              </select>
            </div>
          </div>

          <AnimatePresence>
            {error && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                style={errorText}
              >
                ⚠️ {error}
              </motion.p>
            )}
          </AnimatePresence>

          {/* 🔥 BUTTON */}
          <button style={btn} disabled={loading} className="premium-btn">
            {loading ? (
              <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1 }}>
                  <Zap size={18} />
                </motion.div>
                Creating...
              </div>
            ) : (
              <>
                Initialize Account
                <ArrowRight size={18} style={{ marginLeft: "8px" }} />
              </>
            )}
          </button>
        </form>

        <p style={footer}>
          Already have an account? <Link to="/login" style={link}>Login</Link>
        </p>
      </motion.div>

      <style>{`
        .premium-btn {
          transition: all 0.3s ease;
        }
        .premium-btn:hover:not(:disabled) {
          transform: scale(1.02);
          box-shadow: 0 15px 30px rgba(16,185,129,0.3);
        }
        .premium-btn:disabled {
          transform: none !important;
          box-shadow: none !important;
        }
      `}</style>
    </div>
  );
}

/* INPUT COMPONENT */
function Input({ name, labelText, icon, type="text", handleChange, handleFocus, handleBlur }) {
  return (
    <div style={inputGroup}>
      <label style={label}>{icon} {labelText}</label>
      <input
        name={name}
        type={type}
        onChange={handleChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
        style={input}
        required
      />
    </div>
  );
}

/* STYLES */
const container = { height:"100vh", display:"flex", justifyContent:"center", alignItems:"center", background:"#020617", position:"relative", overflow:"hidden" };

const glassCard = { width:"100%", maxWidth:"460px", padding:"50px", background:"rgba(255,255,255,0.02)", backdropFilter:"blur(25px)", borderRadius:"32px", border:"1px solid rgba(255,255,255,0.08)", boxShadow:"0 25px 50px rgba(0,0,0,0.6)" };

const brandSection = { textAlign:"center", marginBottom:"40px" };
const logoIcon = { fontSize:"48px", marginBottom:"12px", filter:"drop-shadow(0 0 10px rgba(16,185,129,0.4))" };

const brandName = { fontSize:"34px", fontWeight:900, letterSpacing:"-1.5px", color:"#fff" };

const setuGlow = {
  color:"#10b981",
  marginLeft:"8px",
  textShadow:"0 0 12px rgba(16,185,129,0.5)"
};

const brandTagline = { color:"#94a3b8", fontSize:"14px", marginTop:"5px" };

const form = { display:"flex", flexDirection:"column", gap:"24px" };
const grid = { display:"grid", gridTemplateColumns:"1fr 1fr", gap:"12px" };

const inputGroup = { display:"flex", flexDirection:"column", gap:"10px" };
const label = { fontSize:"12px", color:"#64748b", fontWeight:"800", textTransform:"uppercase", letterSpacing:"1.2px", display:"flex", alignItems:"center", gap:"8px" };

const input = { padding:"16px", borderRadius:"14px", background:"rgba(0,0,0,0.4)", border:"1px solid rgba(255,255,255,0.1)", color:"#fff", fontSize:"15px", outline:"none" };

const select = { ...input, cursor:"pointer" };

const btn = { padding:"18px", borderRadius:"14px", border:"none", background:"linear-gradient(135deg,#10b981,#059669)", color:"#fff", fontWeight:"900", fontSize:"16px", display:"flex", justifyContent:"center", alignItems:"center" };

const errorText = { color:"#ef4444", fontSize:"13px", textAlign:"center", fontWeight:"700" };

const footer = { textAlign:"center", marginTop:"20px", color:"#94a3b8" };
const link = { color:"#10b981", fontWeight:"bold", textDecoration:"none" };

const blob1 = { position:"absolute", width:"500px", height:"500px", background:"rgba(16,185,129,0.12)", filter:"blur(100px)", borderRadius:"50%", top:"-10%", left:"10%" };
const blob2 = { position:"absolute", width:"400px", height:"400px", background:"rgba(59,130,246,0.08)", filter:"blur(100px)", borderRadius:"50%", bottom:"0%", right:"5%" };