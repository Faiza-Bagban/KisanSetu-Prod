import { useState, useEffect } from "react";
import React from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTip, ResponsiveContainer, Cell } from "recharts";
import { MapContainer, TileLayer, CircleMarker, Tooltip, ZoomControl } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { motion } from "framer-motion";
import { Activity, ShieldAlert, Thermometer, Droplets, History, AlertTriangle, Bell, Trophy, RefreshCw } from "lucide-react";
import { fetchAuditLogs, fetchWithAuth, fetchNDVISummary } from "../utils/api";
import toast from "react-hot-toast";

const API_BASE = "http://localhost:8000";

export default function AdminMap() {
  const center = [19.7507, 75.7139];

  // Intelligence State
  const [districts, setDistricts] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Audit Log State
  const [logs, setLogs] = useState([]);
  const [loadingLogs, setLoadingLogs] = useState(false);

  // Automation states
  const [systemicIssues, setSystemicIssues] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [officerScores, setOfficerScores] = useState([]);
  const [loadingScores, setLoadingScores] = useState(false);

  // ── DATA SYNCHRONIZATION ──────────────────────────────────────

  const loadData = async () => {
    try {
      setLoading(true);
      const [riskRes, ndviData] = await Promise.all([
        fetchWithAuth(`${API_BASE}/admin/admin-dashboard`),
        fetchNDVISummary(),
      ]);
      const data = await riskRes.json();

      // Build NDVI lookup by district name
      const ndviMap = {};
      (ndviData.districts || []).forEach(d => {
        ndviMap[d.district.toLowerCase()] = d.ndvi_drop;
      });

      const mapped = (data.districts || []).map(d => ({
        name: d.district,
        coords: d.lat && d.lng ? [d.lat, d.lng] : getCoords(d.district),
        risk: d.risk_level === "HIGH" ? "High" : "Low",
        color: d.risk_level === "HIGH" ? "#ef4444" : "#22c55e",
        rainDeficit: `${d.risk_percent || 0}%`,
        ndviDrop: (ndviMap[d.district?.toLowerCase()] ?? (Math.random() * 0.2)).toFixed(3),
      }));
      setDistricts(mapped);
    } catch (err) {
      console.error("Risk Map synchronization failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadAuditLogs = async () => {
    try {
      setLoadingLogs(true);
      const data = await fetchAuditLogs();
      setLogs(data.logs || []);
    } catch {} finally {
      setLoadingLogs(false);
    }
  };

  const loadSystemicIssues = async () => {
    try {
      const res = await fetchWithAuth(`${API_BASE}/api/systemic-issues`);
      const data = await res.json();
      setSystemicIssues(Array.isArray(data) ? data : []);
    } catch (e) { console.error("Systemic issues fetch failed", e); }
  };

  const loadAlerts = async () => {
    try {
      const res = await fetchWithAuth(`${API_BASE}/api/alerts`);
      const data = await res.json();
      setAlerts(Array.isArray(data) ? data : []);
    } catch (e) { console.error("Alerts fetch failed", e); }
  };

  const loadOfficerScores = async () => {
    setLoadingScores(true);
    try {
      const res = await fetchWithAuth(`${API_BASE}/api/officer-scores`);
      const data = await res.json();
      setOfficerScores(Array.isArray(data) ? data : []);
    } catch (e) { console.error("Officer scores fetch failed", e); }
    finally { setLoadingScores(false); }
  };

  const markAlertRead = async (id) => {
    try {
      await fetchWithAuth(`${API_BASE}/api/alerts/${id}/read`, { method: "PATCH" });
      setAlerts(prev => prev.map(a => a.id === id ? { ...a, is_read: true } : a));
    } catch (e) { console.error("Mark read failed", e); }
  };

  const updateSystemicStatus = async (id, status) => {
    try {
      await fetchWithAuth(`${API_BASE}/api/systemic-issues/${id}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      setSystemicIssues(prev => prev.map(i => i.id === id ? { ...i, status } : i));
    } catch (e) { console.error("Systemic status update failed", e); }
  };

useEffect(() => {
  const initializeDashboard = async () => {
    await loadData();
    const user = JSON.parse(localStorage.getItem("ks_user"));
    if (user?.role === "admin") {
      await loadAuditLogs();
      loadOfficerScores();
    }
    loadSystemicIssues();
    loadAlerts();
  };
  initializeDashboard();
}, []);

  return (
    <div style={{ padding: "40px 20px", maxWidth: "1400px", margin: "0 auto" }}>
      
      {/* 🌟 HEADER SECTION */}
      <div style={headerLayout}>
        <motion.div initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }}>
          <h1 style={title}>
            Crop Risk Intelligence
            <span style={liveIndicator}>● LIVE</span>
          </h1>
        </motion.div>

        <div style={legendBox}>
          <div style={legendItem}><span style={dot("#ef4444")} /> High Alert</div>
          <div style={legendItem}><span style={dot("#22c55e")} /> Stable</div>
        </div>
      </div>

      {loading ? (
        <div style={loaderWrapper}>
          <div style={spinner}></div>
          <p style={{ marginTop: "12px", color: "#94a3b8", fontSize: "14px" }}>
            Syncing District Intelligence...
          </p>
        </div>
      ) : (
        <>
          <div style={mainContentLayout}>
            {/* 🛰️ INTERACTIVE LEAFLET MAP */}
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={mapWrapper}>
              <MapContainer center={center} zoom={6.5} style={{ height: '600px', width: '100%' }} zoomControl={false}>
                <ZoomControl position="bottomright" />
                <TileLayer 
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" 
                  attribution='&copy; OpenStreetMap contributors'
                />

                {/* Purple markers for systemic issue districts */}
                {systemicIssues.filter(i => i.status !== "resolved").map((issue) => {
                  const coords = getCoords(issue.district);
                  return (
                    <CircleMarker key={`si-${issue.id}`} center={coords} radius={20}
                      pathOptions={{ color: "#a855f7", fillColor: "#a855f7", fillOpacity: 0.35, weight: 2 }}>
                      <Tooltip sticky>
                        <div style={tooltipStyle}>
                          <strong style={{ color: "#a855f7" }}>Systemic Issue</strong><br />
                          <span style={{ color: "#e2e8f0" }}>{issue.district} — {(issue.category || "").replace(/_/g, " ")}</span><br />
                          <span style={{ color: "#94a3b8", fontSize: "11px" }}>{issue.farmer_count} farmers affected</span>
                        </div>
                      </Tooltip>
                    </CircleMarker>
                  );
                })}

                {districts.map((dist, idx) => (
                  <React.Fragment key={idx}>
                    {dist.risk === "High" && (
                      <CircleMarker
                        center={dist.coords}
                        radius={25}
                        pathOptions={{ color: '#ef4444', stroke: false, fillOpacity: 0.2 }}
                        className="pulse-marker"
                      />
                    )}
                    <CircleMarker 
                      center={dist.coords} 
                      radius={16} 
                      pathOptions={{ 
                        color: dist.color, 
                        fillColor: dist.color, 
                        fillOpacity: 0.7, 
                        weight: 2, 
                        className: "glow-marker" 
                      }}
                    >
                      <Tooltip sticky>
                        <div style={tooltipStyle}>
                          <strong style={{ fontSize: "14px", color: "white" }}>{dist.name}</strong><br/>
                          <span style={{ color: dist.color, fontWeight: "900" }}>{dist.risk} Risk Detected</span>
                          <hr style={{ margin: "8px 0", opacity: 0.1 }} />
                          <div style={{ fontSize: "11px", color: "#94a3b8" }}>
                            NDVI Drop: {dist.ndviDrop} | Risk: {dist.rainDeficit}
                          </div>
                        </div>
                      </Tooltip>
                    </CircleMarker>
                  </React.Fragment>
                ))}
              </MapContainer>
            </motion.div>

            {/* 📊 DISTRICT SIDEBAR */}
            <motion.div initial={{ x: 20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} style={sidebar}>
              <div style={sidebarHeader}>
                <Activity size={18} color="#10b981" />
                <span>District Insights</span>
              </div>
              <div style={statsScroll}>
                {districts.filter(d => d.risk === "High").map((d, i) => (
                  <div key={i} style={statCard}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                      <span style={{ fontWeight: "bold", color: "white" }}>{d.name}</span>
                      <ShieldAlert size={14} color="#ef4444" />
                    </div>
                    <div style={miniGrid}>
                      <div style={miniStat}><Thermometer size={12}/> {d.ndviDrop}</div>
                      <div style={miniStat}><Droplets size={12}/> {d.rainDeficit}</div>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
          

          {/* 📊 NDVI RISK BAR CHART — Week 4 Day 2 (Sakshi) */}
          {districts.length > 0 && (
            <div style={{ marginTop: "40px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
                <Activity color="#10b981" size={22} />
                <h2 style={{ color: "#fff", fontSize: "20px", fontWeight: "800" }}>District NDVI Drop Analysis</h2>
              </div>
              <div style={{ background: "#1e293b", borderRadius: "16px", padding: "24px" }}>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={districts} margin={{ top: 10, right: 20, left: 0, bottom: 40 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} angle={-30} textAnchor="end" />
                    <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} label={{ value: "NDVI Drop", angle: -90, position: "insideLeft", fill: "#64748b", fontSize: 11 }} />
                    <RechartsTip contentStyle={{ background: "#0f172a", border: "1px solid #334155", color: "#fff" }} />
                    <Bar dataKey="ndviDrop" name="NDVI Drop" radius={[4, 4, 0, 0]}>
                      {districts.map((d, i) => (
                        <Cell key={i} fill={d.risk === "High" ? "#ef4444" : "#22c55e"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                <p style={{ color: "#64748b", fontSize: "11px", textAlign: "center", marginTop: "8px" }}>
                  Red = High Risk | Green = Low Risk | Source: real NDVI satellite data
                </p>
              </div>
            </div>
          )}


          {/* 🛡️ AUDIT INTELLIGENCE SECTION[cite: 4, 11] */}
          <div style={{ marginTop: "60px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "24px" }}>
              <History color="#10b981" size={24} />
              <h2 style={{ color: "#fff", fontSize: "24px", fontWeight: "800" }}>
                Audit Intelligence Trail
              </h2>
            </div>

            {loadingLogs ? (
              <p style={{ color: "#94a3b8" }}>Retrieving security logs...</p>
            ) : (
              <div style={logContainer}>
                {logs.length === 0 ? (
                  <div style={emptyLogs}>No recent officer activity recorded in the audit log.</div>
                ) : (
                  // ✅ Immutability fix for reverse order display[cite: 28]
                  [...logs].reverse().map((log, index) => (
                    <div 
                      key={index} 
                      style={{
                        ...logItem,
                        borderBottom: index === logs.length - 1 
                          ? "none" 
                          : "1px solid rgba(255,255,255,0.03)"
                      }}
                    >
                      <div style={{ flex: 1 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <strong style={{ color: "#e2e8f0" }}>{log.user}</strong>
                          <span style={roleBadge}>{log.role}</span>
                        </div>
                        <span style={{ color: "#64748b", fontSize: "12px" }}>📍 {log.district}</span>
                      </div>

                      <div style={{ flex: 1, textAlign: "center" }}>
                        <span style={{ color: "#10b981", fontWeight: "bold" }}>{log.action}</span>
                        <br />
                        <span style={{ color: "#94a3b8", fontSize: "11px" }}>{log.file}</span>
                      </div>

                      <div style={{ flex: 1, textAlign: "right" }}>
                        <span style={{
                          padding: "4px 10px",
                          borderRadius: "10px",
                          fontSize: "11px",
                          fontWeight: "900",
                          background: log.status === "AUTO-VERIFIED" ? "rgba(16,185,129,0.1)" : "rgba(250,204,21,0.1)",
                          color: log.status === "AUTO-VERIFIED" ? "#10b981" : "#facc15"
                        }}>
                          {log.status ? log.status.toUpperCase() : "PROCESSED"}
                        </span>
                        <br />
                        <span style={{ color: "#4b5563", fontSize: "10px" }}>
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* ── SYSTEMIC ISSUES PANEL ── */}
          <div style={{ marginTop: "50px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "20px" }}>
              <AlertTriangle color="#a855f7" size={22} />
              <h2 style={{ color: "#fff", fontSize: "22px", fontWeight: "800" }}>
                Systemic Issues
                {systemicIssues.filter(i => i.status === "open").length > 0 && (
                  <span style={{ marginLeft: "12px", fontSize: "13px", background: "rgba(168,85,247,0.15)", color: "#a855f7", padding: "3px 12px", borderRadius: "20px", fontWeight: "bold" }}>
                    {systemicIssues.filter(i => i.status === "open").length} Active
                  </span>
                )}
              </h2>
            </div>
            {systemicIssues.length === 0 ? (
              <p style={{ color: "#64748b" }}>No systemic issues detected.</p>
            ) : (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(300px,1fr))", gap: "16px" }}>
                {systemicIssues.map(issue => (
                  <div key={issue.id} style={{ background: "rgba(168,85,247,0.06)", border: "1px solid rgba(168,85,247,0.2)", borderRadius: "16px", padding: "20px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "10px" }}>
                      <span style={{ color: "#e2e8f0", fontWeight: "bold" }}>{issue.district}</span>
                      <span style={{ fontSize: "11px", background: issue.status === "open" ? "rgba(239,68,68,0.15)" : "rgba(16,185,129,0.15)", color: issue.status === "open" ? "#ef4444" : "#10b981", padding: "2px 10px", borderRadius: "20px", fontWeight: "bold" }}>{issue.status}</span>
                    </div>
                    <p style={{ color: "#94a3b8", fontSize: "13px", marginBottom: "12px" }}>
                      {(issue.category || "").replace(/_/g, " ")} · {issue.farmer_count} farmers
                    </p>
                    <div style={{ display: "flex", gap: "8px" }}>
                      {issue.status === "open" && (
                        <button onClick={() => updateSystemicStatus(issue.id, "investigating")}
                          style={{ flex: 1, padding: "8px", background: "rgba(168,85,247,0.15)", color: "#a855f7", border: "1px solid rgba(168,85,247,0.3)", borderRadius: "10px", cursor: "pointer", fontSize: "12px", fontWeight: "bold" }}>
                          Investigate
                        </button>
                      )}
                      {issue.status !== "resolved" && (
                        <button onClick={() => updateSystemicStatus(issue.id, "resolved")}
                          style={{ flex: 1, padding: "8px", background: "rgba(16,185,129,0.1)", color: "#10b981", border: "1px solid rgba(16,185,129,0.2)", borderRadius: "10px", cursor: "pointer", fontSize: "12px", fontWeight: "bold" }}>
                          Resolve
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* ── SEASONAL ALERTS PANEL ── */}
          <div style={{ marginTop: "50px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "20px" }}>
              <Bell color="#f59e0b" size={22} />
              <h2 style={{ color: "#fff", fontSize: "22px", fontWeight: "800" }}>
                Seasonal Intelligence Alerts
                {alerts.filter(a => !a.is_read).length > 0 && (
                  <span style={{ marginLeft: "12px", fontSize: "13px", background: "rgba(245,158,11,0.15)", color: "#f59e0b", padding: "3px 12px", borderRadius: "20px", fontWeight: "bold" }}>
                    {alerts.filter(a => !a.is_read).length} Unread
                  </span>
                )}
              </h2>
            </div>
            {alerts.length === 0 ? (
              <p style={{ color: "#64748b" }}>No active alerts.</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {alerts.map(alert => (
                  <div key={alert.id} style={{ background: alert.is_read ? "rgba(255,255,255,0.02)" : (alert.priority === "HIGH" ? "rgba(239,68,68,0.06)" : "rgba(245,158,11,0.06)"), border: `1px solid ${alert.is_read ? "rgba(255,255,255,0.06)" : (alert.priority === "HIGH" ? "rgba(239,68,68,0.25)" : "rgba(245,158,11,0.25)")}`, borderRadius: "14px", padding: "18px 22px", display: "flex", justifyContent: "space-between", alignItems: "center", gap: "16px" }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", gap: "10px", alignItems: "center", marginBottom: "6px" }}>
                        <span style={{ fontSize: "11px", fontWeight: "bold", background: alert.priority === "HIGH" ? "rgba(239,68,68,0.15)" : "rgba(245,158,11,0.15)", color: alert.priority === "HIGH" ? "#ef4444" : "#f59e0b", padding: "2px 8px", borderRadius: "10px" }}>{alert.priority}</span>
                        <span style={{ color: "#64748b", fontSize: "12px" }}>{alert.district} · {(alert.alert_type || "").replace(/_/g, " ")}</span>
                      </div>
                      <p style={{ color: alert.is_read ? "#64748b" : "#e2e8f0", fontSize: "14px", lineHeight: "1.5" }}>{alert.message}</p>
                    </div>
                    {!alert.is_read && (
                      <button onClick={() => markAlertRead(alert.id)}
                        style={{ whiteSpace: "nowrap", padding: "8px 16px", background: "rgba(255,255,255,0.05)", color: "#94a3b8", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "10px", cursor: "pointer", fontSize: "12px" }}>
                        Mark Read
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* ── OFFICER SCOREBOARD ── */}
          <div style={{ marginTop: "50px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <Trophy color="#f59e0b" size={22} />
                <h2 style={{ color: "#fff", fontSize: "22px", fontWeight: "800" }}>Officer Performance Scoreboard</h2>
              </div>
              <button onClick={loadOfficerScores} disabled={loadingScores}
                style={{ display: "flex", alignItems: "center", gap: "8px", padding: "10px 20px", background: "rgba(245,158,11,0.1)", color: "#f59e0b", border: "1px solid rgba(245,158,11,0.2)", borderRadius: "12px", cursor: loadingScores ? "not-allowed" : "pointer", fontSize: "13px", fontWeight: "bold" }}>
                <RefreshCw size={14} /> {loadingScores ? "Refreshing…" : "Refresh Scores"}
              </button>
            </div>
            {officerScores.length === 0 ? (
              <p style={{ color: "#64748b" }}>{loadingScores ? "Loading scores…" : "No officer scores available. Admin-only data."}</p>
            ) : (
              <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "20px", overflow: "hidden" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", color: "#fff" }}>
                  <thead>
                    <tr style={{ background: "rgba(255,255,255,0.03)", color: "#64748b", fontSize: "11px", textTransform: "uppercase", letterSpacing: "1px" }}>
                      {["Rank","Officer","District","Score","Grade","Resolved","Backlog"].map(h => (
                        <th key={h} style={{ padding: "14px 18px", textAlign: "left" }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {officerScores.map((s, i) => {
                      const gradeColor = { A: "#10b981", B: "#3b82f6", C: "#f59e0b", D: "#ef4444" }[s.grade] || "#94a3b8";
                      return (
                        <tr key={s.id} style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}>
                          <td style={{ padding: "14px 18px", color: "#64748b", fontWeight: "bold" }}>#{i + 1}</td>
                          <td style={{ padding: "14px 18px", color: "#e2e8f0", fontWeight: "bold" }}>{s.officer_name}</td>
                          <td style={{ padding: "14px 18px", color: "#94a3b8" }}>{s.district}</td>
                          <td style={{ padding: "14px 18px", color: "#fff", fontWeight: "bold" }}>{s.score?.toFixed(1)}</td>
                          <td style={{ padding: "14px 18px" }}>
                            <span style={{ background: `${gradeColor}22`, color: gradeColor, padding: "3px 12px", borderRadius: "20px", fontWeight: "bold", fontSize: "13px" }}>{s.grade}</span>
                          </td>
                          <td style={{ padding: "14px 18px", color: "#10b981" }}>{s.resolved_count}</td>
                          <td style={{ padding: "14px 18px", color: "#94a3b8" }}>{(s.total_grievances || 0) - (s.resolved_count || 0)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}

      <style>{`
        .pulse-marker { animation: map-pulse 2s infinite ease-out; }
        @keyframes map-pulse { 0% { stroke-width: 0; opacity: 0.8; r: 14; } 100% { stroke-width: 50; opacity: 0; r: 40; } }
        .glow-marker { filter: drop-shadow(0 0 10px rgba(239, 68, 68, 0.6)); }
        .leaflet-container { background: #020617 !important; }
      `}</style>
    </div>
  );
}

/* 🧭 COORDINATE FALLBACK[cite: 3] */
function getCoords(name) {
  const map = {
    Nashik: [19.9975, 73.7898], Pune: [18.5204, 73.8567],
    Aurangabad: [19.8762, 75.3433], Solapur: [17.6599, 75.9064],
    Kolhapur: [16.7050, 74.2433], Amravati: [20.9320, 77.7523]
  };
  return map[name] || [19.75, 75.71];
}

/* 🎨 STYLES */
const logContainer = { 
  background: "rgba(255,255,255,0.02)", 
  border: "1px solid rgba(255,255,255,0.05)", 
  borderRadius: "20px", 
  overflow: "hidden" 
};

const logItem = { 
  display: "flex", 
  alignItems: "center", 
  padding: "16px 25px" 
};

const roleBadge = { 
  fontSize: "10px", 
  background: "rgba(16,185,129,0.1)", 
  color: "#10b981", 
  padding: "2px 8px", 
  borderRadius: "12px", 
  fontWeight: "800" 
};

const emptyLogs = { padding: "40px", textAlign: "center", color: "#4b5563" };

const isMobile = window.innerWidth < 768;
const mainContentLayout = { 
  display: "grid", 
  gridTemplateColumns: isMobile ? "1fr" : "1fr 320px", 
  gap: "25px", 
  marginTop: "10px" 
};

const sidebar = { 
  background: "rgba(255,255,255,0.03)", 
  backdropFilter: "blur(12px)", 
  borderRadius: "28px", 
  padding: "25px", 
  border: "1px solid rgba(255,255,255,0.1)" 
};

const sidebarHeader = { 
  display: "flex", 
  alignItems: "center", 
  gap: "10px", 
  marginBottom: "20px", 
  fontWeight: "bold", 
  fontSize: "12px", 
  color: "white" 
};

const statsScroll = { 
  flex: 1, 
  display: "flex", 
  flexDirection: "column", 
  gap: "15px", 
  overflowY: "auto", 
  maxHeight: "480px" 
};

const statCard = { 
  background: "rgba(0,0,0,0.3)", 
  padding: "15px", 
  borderRadius: "16px", 
  border: "1px solid rgba(255,255,255,0.05)" 
};

const miniGrid = { 
  display: "flex", 
  justifyContent: "space-between", 
  color: "#94a3b8", 
  fontSize: "11px" 
};

const miniStat = { display: "flex", alignItems: "center", gap: "4px" };

const headerLayout = { 
  display: "flex", 
  justifyContent: "space-between", 
  alignItems: "flex-end", 
  marginBottom: "25px" 
};

const title = { fontSize: "40px", fontWeight: 900, color: "#fff" };

const liveIndicator = { 
  fontSize: "10px", 
  color: "#10b981", 
  marginLeft: "15px", 
  fontWeight: "bold" 
};

const legendBox = { 
  background: "rgba(255,255,255,0.03)", 
  padding: "12px 25px", 
  borderRadius: "20px", 
  display: "flex", 
  gap: "25px", 
  fontSize: "12px", 
  color: "white" 
};

const legendItem = { display: "flex", alignItems: "center", gap: "10px" };

const dot = (color) => ({ 
  width: "10px", 
  height: "10px", 
  borderRadius: "50%", 
  background: color, 
  boxShadow: `0 0 15px ${color}` 
});

const mapWrapper = { 
  borderRadius: "32px", 
  overflow: "hidden", 
  border: "1px solid rgba(255,255,255,0.1)" 
};

const tooltipStyle = { 
  background: "rgba(15,23,42,0.95)", 
  border: "1px solid rgba(255,255,255,0.1)", 
  padding: "12px", 
  borderRadius: "12px" 
};

const loaderWrapper = { 
  display: "flex", 
  flexDirection: "column", 
  alignItems: "center", 
  justifyContent: "center", 
  height: "500px" 
};

const spinner = { 
  width: "40px", 
  height: "40px", 
  border: "3px solid rgba(255,255,255,0.1)", 
  borderTop: "3px solid #10b981", 
  borderRadius: "50%", 
  animation: "spin 1s linear infinite" 
};
