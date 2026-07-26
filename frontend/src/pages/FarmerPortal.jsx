import { motion } from "framer-motion";
import { useAuth } from "../context/AuthContext";
import { useState, useEffect, useRef } from "react";
import RiskBadge from "../components/RiskBadge";
import ConfidenceBadge from "../components/ConfidenceBadge";

import {
  checkEligibility,
  predictCropRisk,
  submitGrievance
} from "../utils/api";

import toast from "react-hot-toast";

import {
  CloudSun,
  Droplets,
  ChevronRight,
  Sprout,
  Download,
  Star,
  CheckCircle2,
  Calendar,
  ArrowUpRight,
  CloudRain
} from "lucide-react";

// Coordinates for Maharashtra districts — module-level so it's stable
const DISTRICT_COORDS = {
  "Pune":        { lat: 18.5204, lon: 73.8567 },
  "Nashik":      { lat: 20.0059, lon: 73.7897 },
  "Nagpur":      { lat: 21.1458, lon: 79.0882 },
  "Aurangabad":  { lat: 19.8762, lon: 75.3433 },
  "Kolhapur":    { lat: 16.7050, lon: 74.2433 },
  "Solapur":     { lat: 17.6805, lon: 75.9064 },
  "Amravati":    { lat: 20.9320, lon: 77.7523 },
  "Satara":      { lat: 17.6805, lon: 74.0183 },
  "Sangli":      { lat: 16.8524, lon: 74.5815 },
  "Latur":       { lat: 18.4088, lon: 76.5604 },
  "Jalgaon":     { lat: 21.0077, lon: 75.5626 },
  "Ahmednagar":  { lat: 19.0952, lon: 74.7496 },
  "Nanded":      { lat: 19.1383, lon: 77.3210 },
  "Raigad":      { lat: 18.5158, lon: 73.1783 },
  "Thane":       { lat: 19.2183, lon: 72.9781 },
  "Mumbai":      { lat: 19.0760, lon: 72.8777 },
};

export default function FarmerPortal() {

  const { user } = useAuth();

  const [isExporting, setIsExporting] = useState(false);

  const [schemes, setSchemes] = useState([]);

  const [districtIntel, setDistrictIntel] = useState(null);

  const [grievanceText, setGrievanceText] = useState("");

  const [grievanceResult, setGrievanceResult] = useState(null);

  const [grievanceLoading, setGrievanceLoading] = useState(false);

  const [cropRiskLoading, setCropRiskLoading] = useState(false);

  const [cropRisk, setCropRisk] = useState({
    risk_level: "LOW",
    risk_percent: 0,
    recommendation: "No immediate action required"
  });

  const rainRef = useRef(0);

  const [farmerData, setFarmerData] = useState({
    cropType: "Grapes (Export Grade)",
    riskLevel: "LOW",
    lastUpdate: "Initializing...",
    healthIndex: 84,
    temp: 0,
    humidity: 0,
    rain: 0
  });

  /* ---------------- WEATHER ENGINE ---------------- */

  useEffect(() => {

    const fetchWeather = async () => {

      try {

        const city = user?.district || "Pune";
        const { lat, lon } = DISTRICT_COORDS[city] ?? DISTRICT_COORDS["Pune"];

        const res = await fetch(
          `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,precipitation&timezone=Asia%2FKolkata`
        );

        const data = await res.json();

        const current = data?.current;

        if (!current) throw new Error("Invalid weather data");

        const temp     = parseFloat(current.temperature_2m);
        const humidity = parseInt(current.relative_humidity_2m);
        const rain     = parseFloat(current.precipitation);

        rainRef.current = rain;

        let riskScore = 0;

        if (humidity > 70) riskScore += 1;

        if (temp > 35) riskScore += 1;

        if (rain > 5) riskScore += 2;

        let risk = "LOW";

        if (riskScore >= 3) risk = "HIGH";
        else if (riskScore >= 1) risk = "MEDIUM";

        const healthIndex = Math.max(40, 100 - riskScore * 15);

        setFarmerData((prev) => ({
          ...prev,
          temp,
          humidity,
          rain,
          riskLevel: risk,
          healthIndex,
          lastUpdate: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit"
          })
        }));

      } catch (err) {

        console.log(err);
      }
    };

    fetchWeather();

    const interval = setInterval(fetchWeather, 60000);

    return () => clearInterval(interval);

  }, [user?.district]);

  /* ---------------- ELIGIBILITY ---------------- */

  const handleEligibility = async () => {

    try {

      const data = await checkEligibility({
        land_size: 2,
        income: 120000,
        crop_type: "wheat",
        district: user?.district || "Pune"
      });

      console.log("ELIGIBILITY RESPONSE:", data);

      setSchemes(
        Array.isArray(data?.eligibility_results?.schemes)
          ? data.eligibility_results.schemes
          : []
      );

      setDistrictIntel(data?.district_intelligence || null);

      toast.success("Eligibility analyzed");

    } catch (err) {

      console.log(err);

      toast.error(err.message || "Eligibility failed");
    }
  };

  /* ---------------- GRIEVANCE ---------------- */

  const handleGrievance = async () => {

    try {

      setGrievanceLoading(true);

      const data = await submitGrievance(grievanceText);

      console.log("GRIEVANCE RESPONSE:", data);

      setGrievanceResult(data);

      toast.success("Grievance analyzed successfully");

    } catch (err) {

      console.log(err);

      toast.error(err.message || "Grievance failed");

    } finally {

      setGrievanceLoading(false);
    }
  };

  /* ---------------- CROP RISK ---------------- */

  const handleCropRisk = async () => {

    try {

      setCropRiskLoading(true);

      const data = await predictCropRisk({
        district: "Pune",
        crop_type: "wheat",
        rainfall_deficit: 40,
        temp_anomaly: 2.1,
        ndvi_drop: 0.3,
        soil_moisture: 25,
        days_since_rain: 20
      });

      console.log("FULL API RESPONSE:", data);

      setCropRisk({
        risk_level:
          data.risk_level ||
          "LOW",

        risk_percent:
          data.risk_percent ||
          0,

        recommendation:
          data.relief_draft?.action ||
          "No immediate action required"
      });

      toast.success("Crop risk predicted");

    } catch (err) {

      console.log(err);

      toast.error(err.message || "Crop risk failed");

    } finally {

      setCropRiskLoading(false);
    }
  };

  /* ---------------- EXPORT ---------------- */

  const handleExport = () => {

    setIsExporting(true);

    setTimeout(() => {

      window.print();

      setIsExporting(false);

    }, 1200);
  };

  const getGreeting = () => {

    if (user?.role === "Admin")
      return `Welcome, ${user?.name || "Admin"} 👋`;

    if (user?.role === "District Officer")
      return `Namaste, ${user?.name?.split(" ")[0] || "Officer"} 👋`;

    if (user?.role === "Field Officer")
      return `Namaste, ${user?.name?.split(" ")[0] || "Officer"} 👋`;

    return `Jai Hind!, ${user?.name?.split(" ")[0] || "Farmer"} 👋`;
  };

  return (

    <div style={container}>

      <div style={blob1} />

      <div style={blob2} />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        style={content}
      >

        {/* HEADER */}

        <section style={profileCard}>

          <div style={profileMain}>

            <div style={avatarLarge}>
              {user?.name?.[0] || "U"}
            </div>

            <div>

              <h1 style={greeting}>
                {getGreeting()}
              </h1>

              <div style={metaRow}>

                <span style={metaItem}>
                  📍 {user?.district || "Maharashtra"}
                </span>

                <span style={metaDivider}>|</span>

                <span style={metaItem}>
                  <Sprout size={14} color="#10b981" />
                  {farmerData.cropType}
                </span>

                <span style={metaDivider}>|</span>

                <span style={metaItem}>
                  <Calendar size={14} />
                  Sync: {farmerData.lastUpdate}
                </span>

              </div>
            </div>
          </div>

          <button
            style={eligibilityBtn}
            onClick={handleEligibility}
          >
            Check Eligibility
            <ChevronRight size={16} />
          </button>

        </section>

        {/* SENSOR GRID */}

        <div style={statsGrid}>

          <StatCard
            icon={<CloudSun color="#fbbf24" />}
            label="Temp"
            val={`${farmerData.temp}°C`}
            sub="Predictive Engine"
          />

          <StatCard
            icon={<Droplets color="#38bdf8" />}
            label="Humidity"
            val={`${farmerData.humidity}%`}
            sub="Relative Air"
          />

          <StatCard
            icon={<CloudRain color="#60a5fa" />}
            label="Rainfall"
            val={`${farmerData.rain} mm`}
            sub="Last Hour"
          />

          <StatCard
            icon={<CheckCircle2 color="#10b981" />}
            label="Health Index"
            val={`${farmerData.healthIndex}%`}
            sub="Stability: Robust"
          />

        </div>

        {/* CROP RISK */}

        <div style={{ marginTop: "40px" }}>
        <button
          style={eligibilityBtn}
          onClick={handleCropRisk}
        >
          {cropRiskLoading
            ? "Analyzing..."
            : "Predict Crop Risk"}
        </button>

          <motion.div
  initial={{ opacity: 0, y: 15 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.4 }}
  style={{
    ...schemeCard,
    marginTop: "24px",
    overflow: "hidden",
    position: "relative"
  }}
>

  {/* Glow Effect */}
  <div style={{
    position: "absolute",
    top: "-80px",
    right: "-80px",
    width: "220px",
    height: "220px",
    background:
      cropRisk?.risk_level === "HIGH"
        ? "rgba(239,68,68,0.12)"
        : cropRisk?.risk_level === "MEDIUM"
        ? "rgba(245,158,11,0.12)"
        : "rgba(16,185,129,0.10)",
    filter: "blur(80px)",
    borderRadius: "50%"
  }} />

  {/* Header */}
  <div style={{
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: "28px",
    position: "relative",
    zIndex: 2
  }}>

    <div>

      <p style={{
        color: "#a0aec0",
        fontSize: "12px",
        textTransform: "uppercase",
        letterSpacing: "1px",
        fontWeight: "700",
        marginBottom: "8px"
      }}>
        AI Predictive Engine
      </p>

      <h2 style={{
        color: "#fff",
        fontSize: "32px",
        fontWeight: "800",
        margin: 0
      }}>
        Crop Risk Analysis
      </h2>

    </div>

    <RiskBadge
      level={cropRisk?.risk_level || "LOW"}
      percent={cropRisk?.risk_percent || 0}
      size="lg"
    />

  </div>

  {/* Metrics */}
  <div style={{
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))",
    gap: "18px",
    marginBottom: "28px",
    position: "relative",
    zIndex: 2
  }}>

    {/* Risk Card */}
    <div style={riskMetricCard}>

      <p style={metricLabel}>
        Risk Probability
      </p>

      <p style={metricValue}>
        {cropRisk?.risk_percent || 0}%
      </p>

      <div style={{ marginTop: "12px" }}>
        <ConfidenceBadge
          value={cropRisk?.risk_percent || 0}
        />
      </div>

      {/* Animated Bar */}
      <div style={{
        marginTop: "18px",
        height: "8px",
        borderRadius: "20px",
        background: "rgba(255,255,255,0.05)",
        overflow: "hidden"
      }}>

        <motion.div
          initial={{ width: 0 }}
          animate={{
            width: `${cropRisk?.risk_percent || 0}%`
          }}
          transition={{ duration: 0.8 }}
          style={{
            height: "100%",
            borderRadius: "20px",
            background:
              cropRisk?.risk_level === "HIGH"
                ? "#ef4444"
                : cropRisk?.risk_level === "MEDIUM"
                ? "#f59e0b"
                : "#10b981"
          }}
        />

      </div>

    </div>

    {/* Status Card */}
    <div style={riskMetricCard}>

      <p style={metricLabel}>
        Current Status
      </p>

      <h2 style={{
        color:
          cropRisk?.risk_level === "HIGH"
            ? "#ef4444"
            : cropRisk?.risk_level === "MEDIUM"
            ? "#f59e0b"
            : "#10b981",
        fontSize: "28px",
        fontWeight: "800",
        marginTop: "10px"
      }}>
        {cropRisk?.risk_level || "LOW"}
      </h2>

      <p style={{
        color: "#b0bec5",
        marginTop: "12px",
        lineHeight: "1.6",
        fontSize: "13px"
      }}>
        AI-generated agricultural stability index based on climate and rainfall intelligence.
      </p>

    </div>

  </div>

  {/* Recommendation */}
  <div style={{
    position: "relative",
    zIndex: 2,
    background: "rgba(255,255,255,0.03)",
    border: "1px solid rgba(255,255,255,0.05)",
    padding: "20px",
    borderRadius: "20px"
  }}>

    <p style={{
      color: "#a0aec0",
      fontSize: "11px",
      textTransform: "uppercase",
      letterSpacing: "1px",
      fontWeight: "700",
      marginBottom: "10px"
    }}>
      AI Recommendation
    </p>

    <p style={{
      color: "#e2e8f0",
      lineHeight: "1.7",
      fontSize: "14px",
      margin: 0
    }}>
      {cropRisk?.recommendation ||
        "No immediate action required"}
    </p>

  </div>

</motion.div>
</div>

        {/* SCHEMES */}

        {schemes.length > 0 && (

          <div style={{ marginTop: "50px" }}>

            <div style={schemeHeader}>

              <h2 style={{ color: "#fff" }}>
                AI-Matched Schemes
              </h2>

              <button
                disabled={isExporting}
                style={{
                  ...exportBtn,
                  opacity: isExporting ? 0.6 : 1,
                  cursor: isExporting
                    ? "not-allowed"
                    : "pointer"
                }}
                onClick={handleExport}
              >
                <Download size={14} />

                {isExporting
                  ? "Processing..."
                  : "Export Report"}
              </button>
            </div>

            <div style={schemeGrid}>

              {schemes.map((s, i) => (

                <div key={i} style={schemeCard}>

                  {i === 0 && (
                    <div style={topBadge}>
                      <Star size={10} fill="white" />
                      {" "}RECOMMENDED
                    </div>
                  )}

                  <h3 style={schemeTitle}>
                    {s.scheme ||
                    s.name ||
                    s.scheme_name ||
                    s.title ||
                    "Government Scheme"}
                  </h3>

                  <p style={schemeDesc}>
                    {s.description}
                  </p>

                  <div style={matchContainer}>

                    <div style={matchText}>
                      Match Score: {s.score || 90}%
                    </div>

                    <div style={progressBg}>

                      <div
                        style={{
                          ...progressFill,
                          width: `${s.score || 90}%`
                        }}
                      />

                    </div>
                  </div>

                  <button style={applyBtn}>
                    Apply Now
                    <ArrowUpRight size={14} />
                  </button>

                </div>
              ))}
            </div>
          </div>
        )}

        {/* GRIEVANCE */}

        <div style={{ marginTop: "60px" }}>

          <h2 style={{ color: "#fff" }}>
            AI Grievance Assistant
          </h2>

          <textarea
            value={grievanceText}
            onChange={(e) =>
              setGrievanceText(e.target.value)
            }
            placeholder="Describe your issue..."
            style={{
              width: "100%",
              height: "120px",
              marginTop: "20px",
              background: "rgba(255,255,255,0.03)",
              color: "#fff",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: "20px",
              padding: "16px"
            }}
          />

          <button
            style={{
              ...eligibilityBtn,
              marginTop: "20px"
            }}
            onClick={handleGrievance}
          >
            {grievanceLoading
              ? "Analyzing..."
              : "Submit Grievance"}
          </button>

          {grievanceResult && (

            <div
              style={{
                ...schemeCard,
                marginTop: "20px"
              }}
            >

              <div
                style={{
                  background: "rgba(16,185,129,0.15)",
                  color: "#10b981",
                  padding: "6px 12px",
                  borderRadius: "12px",
                  display: "inline-block",
                  marginBottom: "15px",
                  fontSize: "12px",
                  fontWeight: "700"
                }}
              >
                AI Analysis Complete
              </div>

              <p style={{ color: "#fff" }}>
                <b>Category:</b>{" "}
                {grievanceResult.category}
              </p>

              <p style={{ color: "#fff" }}>
                <b>Priority:</b>{" "}
                {grievanceResult.priority}
              </p>

              <p style={{ color: "#fff" }}>
                <b>Resolution Time:</b>{" "}
                {grievanceResult.resolution_days}
              </p>

              <p style={{ color: "#fff" }}>
                <b>Assigned Officer:</b>{" "}
                {grievanceResult.assigned_officer}
              </p>

              {grievanceResult.suggested_action && (
  <p
    style={{
      color: "#10b981",
      marginTop: "14px",
      lineHeight: "1.6",
      fontSize: "14px"
    }}
  >
    <b>Suggested Action:</b>{" "}
    {grievanceResult.suggested_action}
  </p>
)}
              
            </div>
          )}
        </div>

      </motion.div>
    </div>
  );
}

function StatCard({ icon, label, val, sub }) {

  return (

    <div style={sCard}>

      <div style={sIconBox}>
        {icon}
      </div>

      <div>

        <p style={sLabel}>
          {label}
        </p>

        <p style={sVal}>
          {val}
        </p>

        <p style={sSub}>
          {sub}
        </p>

      </div>
    </div>
  );
}

/* ---------------- STYLES ---------------- */
const riskMetricCard = {
  background: "rgba(255,255,255,0.03)",
  border: "1px solid rgba(255,255,255,0.05)",
  borderRadius: "22px",
  padding: "24px",
  backdropFilter: "blur(12px)"
};

const metricLabel = {
  color: "#a0aec0",
  fontSize: "11px",
  fontWeight: "800",
  textTransform: "uppercase",
  letterSpacing: "1px"
};

const metricValue = {
  color: "#fff",
  fontSize: "42px",
  fontWeight: "900",
  marginTop: "10px",
  marginBottom: "0"
};

const container = {
  padding: "60px 20px",
  background: "#020617",
  minHeight: "100vh",
  display: "flex",
  justifyContent: "center",
  position: "relative",
  overflow: "hidden"
};

const blob1 = {
  position: "absolute",
  width: "500px",
  height: "500px",
  background: "rgba(16, 185, 129, 0.05)",
  filter: "blur(100px)",
  top: "-10%",
  left: "-10%"
};

const blob2 = {
  position: "absolute",
  width: "400px",
  height: "400px",
  background: "rgba(59, 130, 246, 0.05)",
  filter: "blur(100px)",
  bottom: "0%",
  right: "0%"
};

const content = {
  width: "100%",
  maxWidth: "1100px",
  zIndex: 1
};

const profileCard = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  background: "rgba(255,255,255,0.02)",
  backdropFilter: "blur(20px)",
  padding: "40px",
  borderRadius: "32px",
  border: "1px solid rgba(255,255,255,0.08)",
  marginBottom: "40px"
};

const profileMain = {
  display: "flex",
  gap: "25px",
  alignItems: "center"
};

const avatarLarge = {
  width: "70px",
  height: "70px",
  borderRadius: "18px",
  background: "#10b981",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  fontSize: "28px",
  color: "#fff",
  fontWeight: "900"
};

const greeting = {
  color: "#fff",
  fontSize: "28px",
  margin: 0
};

const metaRow = {
  display: "flex",
  gap: "12px",
  marginTop: "8px",
  alignItems: "center"
};

const metaItem = {
  color: "#b0bec5",
  fontSize: "14px",
  fontWeight: "600",
  display: "flex",
  alignItems: "center",
  gap: "6px"
};

const metaDivider = {
  color: "#334155"
};

const eligibilityBtn = {
  background: "#10b981",
  border: "none",
  padding: "12px 20px",
  borderRadius: "14px",
  color: "#fff",
  fontWeight: "bold",
  cursor: "pointer",
  display: "flex",
  alignItems: "center",
  gap: "8px"
};

const statsGrid = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
  gap: "20px"
};

const sCard = {
  padding: "24px",
  borderRadius: "24px",
  background: "rgba(255,255,255,0.02)",
  border: "1px solid rgba(255,255,255,0.05)",
  display: "flex",
  gap: "18px",
  alignItems: "center"
};

const sIconBox = {
  padding: "12px",
  background: "rgba(255,255,255,0.03)",
  borderRadius: "14px"
};

const sLabel = {
  color: "#a0aec0",
  fontSize: "11px",
  fontWeight: "800",
  textTransform: "uppercase"
};

const sVal = {
  color: "#fff",
  fontSize: "24px",
  fontWeight: "800",
  margin: "4px 0"
};

const sSub = {
  color: "#b0bec5",
  fontSize: "12px"
};

const schemeHeader = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: "30px"
};

const exportBtn = {
  background: "rgba(255,255,255,0.05)",
  border: "none",
  padding: "10px 18px",
  borderRadius: "12px",
  color: "#fff",
  cursor: "pointer",
  display: "flex",
  alignItems: "center",
  gap: "8px",
  fontWeight: "700"
};

const schemeGrid = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
  gap: "25px"
};

const schemeCard = {
  padding: "30px",
  borderRadius: "28px",
  background: "rgba(255,255,255,0.02)",
  border: "1px solid rgba(255,255,255,0.06)",
  position: "relative"
};

const topBadge = {
  position: "absolute",
  top: "-12px",
  right: "20px",
  fontSize: "10px",
  fontWeight: "900",
  background: "linear-gradient(90deg, #10b981, #059669)",
  padding: "6px 12px",
  borderRadius: "20px",
  color: "#fff"
};

const schemeTitle = {
  color: "#fff",
  fontSize: "18px",
  margin: "15px 0 8px 0"
};

const schemeDesc = {
  color: "#b0bec5",
  fontSize: "13px",
  lineHeight: "1.5"
};

const matchContainer = {
  marginTop: "20px"
};

const matchText = {
  fontSize: "11px",
  color: "#10b981",
  fontWeight: "800",
  marginBottom: "8px"
};

const progressBg = {
  height: "6px",
  background: "rgba(255,255,255,0.05)",
  borderRadius: "10px",
  overflow: "hidden"
};

const progressFill = {
  height: "100%",
  background: "#10b981",
  borderRadius: "10px"
};

const applyBtn = {
  marginTop: "25px",
  width: "100%",
  padding: "14px",
  borderRadius: "14px",
  border: "1px solid #10b981",
  background: "transparent",
  color: "#10b981",
  fontWeight: "800",
  cursor: "pointer",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  gap: "8px"
};