import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

import {
  Send,
  Clock,
  UserCheck,
  ShieldCheck,
  MessageSquare,
  List,
  Info,
  Loader2,
  Activity,
  FileCheck
} from "lucide-react";

import { fetchWithAuth } from "../utils/api";
import toast from "react-hot-toast";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

// ── STATUS BADGE COLOURS ─────────────────────────────────────
const STATUS_BADGE = {
  "Pending":      { bg: "rgba(100,116,139,0.15)", color: "#94a3b8" },
  "Under Review": { bg: "rgba(234,179,8,0.15)",   color: "#ca8a04" },
  "Resolved":     { bg: "rgba(16,185,129,0.15)",  color: "#10b981" },
  "Escalated":    { bg: "rgba(239,68,68,0.15)",   color: "#ef4444" },
};

// ── CATEGORY COLOUR BADGES (UI logic, not data) ──────────────
const CATEGORY_COLORS = {
  payment_issue:      { bg: "rgba(239,68,68,0.15)",   color: "#ef4444" },
  scheme_delay:       { bg: "rgba(249,115,22,0.15)",  color: "#f97316" },
  document_rejection: { bg: "rgba(234,179,8,0.15)",   color: "#eab308" },
  officer_misconduct: { bg: "rgba(239,68,68,0.15)",   color: "#ef4444" },
  other:              { bg: "rgba(100,116,139,0.15)", color: "#64748b" },
};

const PAGE_LOAD_TIME = Date.now();

function slaStatus(deadline, nowMs) {
  if (!deadline) return null;
  const diffH = (new Date(deadline).getTime() - nowMs) / 3_600_000;
  if (diffH < 0)  return { label: "SLA Breached", color: "#ef4444" };
  if (diffH < 24) return { label: `${Math.ceil(diffH)}h left`, color: "#f59e0b" };
  return { label: `${Math.ceil(diffH / 24)}d left`, color: "#10b981" };
}

export default function GrievanceDashboard() {
  // ── GRIEVANCE FILING ─────────────────────────────────────
  const [isAnalyzing, setIsAnalyzing]   = useState(false);
  const [showResult, setShowResult]     = useState(false);
  const [grievanceText, setGrievanceText] = useState("");
  const [result, setResult]             = useState(null);

  const isResolved = result?.status?.toLowerCase() === "resolved";

  // ── GRIEVANCE QUEUE ───────────────────────────────────────
  const [grievanceQueue, setGrievanceQueue] = useState([]);
  const [loadingQueue, setLoadingQueue]     = useState(true);
  const [queueError, setQueueError]         = useState(null);

  // ── ANALYTICS ────────────────────────────────────────────
  const [analytics, setAnalytics]         = useState(null);
  const [loadingAnalytics, setLoadingAnalytics] = useState(true);

  // ── STATUS TRACKER ────────────────────────────────────────
  const [trackerInput, setTrackerInput]   = useState("");
  const [trackerResult, setTrackerResult] = useState(null);
  const [loadingTracker, setLoadingTracker] = useState(false);

  // ── ESCALATED TAB ─────────────────────────────────────────
  const [viewMode, setViewMode]           = useState("all"); // "all" | "escalated"
  const [escalatedQueue, setEscalatedQueue] = useState([]);
  const [loadingEscalated, setLoadingEscalated] = useState(false);

  // ── SELECTED GRIEVANCE (for action buttons) ───────────────
  const [selectedId, setSelectedId]     = useState(null);
  const [btnLoading, setBtnLoading]     = useState({});      // { resolve, underReview, escalate }
  const [escalateConfirm, setEscalateConfirm] = useState(false);
  const [actionMsg, setActionMsg]       = useState(null);

  // ── SUBMIT ────────────────────────────────────────────────
  const handleSubmit = async () => {
    if (!grievanceText.trim()) return;

    setIsAnalyzing(true);
    setShowResult(false);

    try {
      const res = await fetchWithAuth(`${API_BASE}/api/grievance`, {
        method: "POST",
        body: JSON.stringify({ text: grievanceText })
      });
      const data = await res.json();

      setResult({
  category: data.category,

  priority: data.priority || "Normal",

  confidence:
    data.confidence != null
      ? Math.round(data.confidence)
      : null,

  status: data.status,

  status_label:
    `Assigned Officer: ${data.assigned_officer}`,

  grievance_id: data.grievance_id,

  suggested_action: data.suggested_action,
});
      setShowResult(true);
      // Refresh queue and analytics after a new submission
      fetchQueue();
      fetchAnalytics();
    } catch (err) {
      console.error("Grievance API Error:", err);
      setResult({
        category:     "System Communication Error",
        priority:     "N/A",
        confidence:   null,
        status:       "Error",
        status_label: "Service Offline - Try Later",
      });
      setShowResult(true);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // ── FETCH QUEUE ───────────────────────────────────────────
  const fetchQueue = async () => {
    setLoadingQueue(true);
    try {
      const res = await fetchWithAuth(`${API_BASE}/api/grievance`);
      const items = await res.json();
      setGrievanceQueue(Array.isArray(items) ? items : []);
      setQueueError(null);
    } catch (err) {
      setQueueError(err.message || "Failed to load grievance queue");
    } finally {
      setLoadingQueue(false);
    }
  };

  // ── FETCH ANALYTICS ───────────────────────────────────────
  const fetchAnalytics = async () => {
    setLoadingAnalytics(true);
    try {
      const res = await fetchWithAuth(`${API_BASE}/api/grievance/analytics`);
      setAnalytics(await res.json());
    } catch (err) {
      console.error("Analytics fetch failed:", err);
    } finally {
      setLoadingAnalytics(false);
    }
  };

  // ── FETCH ESCALATED ──────────────────────────────────────
  const fetchEscalated = async () => {
    setLoadingEscalated(true);
    try {
      const res = await fetchWithAuth(`${API_BASE}/api/grievance/escalated`);
      const items = await res.json();
      setEscalatedQueue(Array.isArray(items) ? items : []);
    } catch (err) {
      console.error("Escalated fetch failed:", err);
    } finally {
      setLoadingEscalated(false);
    }
  };

  // ── TRACK GRIEVANCE ───────────────────────────────────────
  const handleTrackGrievance = async () => {
    if (!trackerInput.trim()) return;
    setLoadingTracker(true);
    setTrackerResult(null);
    try {
      const res = await fetchWithAuth(
        `${API_BASE}/api/grievance/${encodeURIComponent(trackerInput.trim())}`
      );
      setTrackerResult(await res.json());
    } catch (err) {
      setTrackerResult({ error: err.message || "Lookup failed" });
    } finally {
      setLoadingTracker(false);
    }
  };

  // ── SET STATUS (Under Review / Resolved) ─────────────────
  const handleSetStatus = async (status) => {
    if (!selectedId) return;
    const key = status === "Resolved" ? "resolve" : "underReview";
    setBtnLoading(prev => ({ ...prev, [key]: true }));
    setActionMsg(null);
    try {
      const res = await fetchWithAuth(`${API_BASE}/api/grievance/${selectedId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      if (!res.ok) {
        const d = await res.json();
        setActionMsg(d.detail || "Action failed");
        return;
      }
      const updateRow = (g) => g.id === selectedId ? { ...g, status } : g;
      setGrievanceQueue(prev => prev.map(updateRow));
      setEscalatedQueue(prev => prev.map(updateRow));
      if (status === "Resolved") {
        setAnalytics(prev => prev ? {
          ...prev,
          resolved_count: (prev.resolved_count || 0) + 1,
          open_count: Math.max((prev.open_count || 0) - 1, 0),
        } : prev);
      }
      toast.success(status === "Resolved" ? "Grievance Resolved ✓" : "Marked as Under Review");
      setActionMsg(`Grievance #${selectedId} → ${status}`);
    } catch (err) {
      setActionMsg(err.message || "Action failed");
    } finally {
      setBtnLoading(prev => ({ ...prev, [key]: false }));
    }
  };

  // ── ESCALATE ──────────────────────────────────────────────
  const handleEscalate = async () => {
    if (!selectedId) return;
    setBtnLoading(prev => ({ ...prev, escalate: true }));
    setEscalateConfirm(false);
    setActionMsg(null);
    try {
      const res = await fetchWithAuth(`${API_BASE}/api/grievance/${selectedId}/escalate`, {
        method: "PATCH",
        body: JSON.stringify({ reason: "Manual escalation by officer" }),
      });
      const data = await res.json();
      if (res.status === 400) {
        setActionMsg(data.detail || "Already at highest escalation level");
        return;
      }
      if (!res.ok) {
        setActionMsg(data.detail || "Escalation failed");
        return;
      }
      const updateRow = (g) => g.id === selectedId
        ? { ...g, status: "Escalated", escalation_level: data.escalation_level, routed_officer: data.routed_officer }
        : g;
      setGrievanceQueue(prev => prev.map(updateRow));
      setEscalatedQueue(prev => prev.map(updateRow));
      const levelMsg = data.escalation_level === 1
        ? "⚠ Escalated to District Officer"
        : "🔴 Escalated to State Dept";
      setActionMsg(levelMsg);
      toast.success("Case Escalated ✓");
    } catch (err) {
      setActionMsg(err.message || "Escalation failed");
    } finally {
      setBtnLoading(prev => ({ ...prev, escalate: false }));
    }
  };

  // ── ON MOUNT ──────────────────────────────────────────────
  useEffect(() => {
    fetchQueue();
    fetchAnalytics();
  }, []);

  // ── SELECTED ITEM ─────────────────────────────────────────
  const selectedItem =
    grievanceQueue.find(g => g.id === selectedId) ||
    escalatedQueue.find(g => g.id === selectedId) ||
    null;

  // ── TAB SWITCH ────────────────────────────────────────────
  const switchTab = (mode) => {
    setViewMode(mode);
    if (mode === "escalated" && escalatedQueue.length === 0) {
      fetchEscalated();
    }
  };

  // ── ANALYTICS CARD DATA ───────────────────────────────────
  const analyticsCards = analytics
    ? [
        { title: "Total Grievances", value: analytics.total    ?? "—" },
        { title: "Open Cases",       value: analytics.open_count ?? "—" },
        { title: "Resolved",         value: analytics.resolved_count ?? "—" },
        { title: "Avg Resolution",   value: analytics.avg_resolution_days != null ? `${analytics.avg_resolution_days}d` : "—" },
      ]
    : [
        { title: "Total Grievances", value: loadingAnalytics ? "…" : "—" },
        { title: "Open Cases",       value: loadingAnalytics ? "…" : "—" },
        { title: "Resolved",         value: loadingAnalytics ? "…" : "—" },
        { title: "Avg Resolution",   value: loadingAnalytics ? "…" : "—" },
      ];

  // ── AUDIT TIMELINE from queue ─────────────────────────────
  const timelineEntries = grievanceQueue.slice(0, 4).map((g) => {
    const ts = g.created_at
      ? new Date(g.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      : "—";
    return `${ts} → GRV-2026-${String(g.id).padStart(4, "0")} filed (${(g.category || "other").replace(/_/g, " ")})`;
  });

  return (
    <div style={container}>
      {/* HEADER */}
      <motion.div
        initial={{ y: -30, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        style={headerSection}
      >
        <h1 style={title}>
          Grievance Intelligence{" "}
          <span style={highlightText}>Portal</span>
        </h1>
      </motion.div>

      {/* MAIN GRID */}
      <div style={grid}>
        {/* LEFT */}
        <div style={panelColumn}>
          <motion.div
            whileHover={{
              scale: 1.01,
              boxShadow: "0 0 30px rgba(16, 185, 129, 0.15)"
            }}
            style={glassCard}
          >
            <div style={sectionHeader}>
              <MessageSquare size={18} color="#10b981" />
              <span>File New Grievance</span>
            </div>

            <p style={label}>
              Describe your issue in detail
              (English/Marathi supported)
            </p>

            <textarea
              placeholder="e.g., Canal irrigation water hasn't reached farms..."
              style={textarea}
              value={grievanceText}
              onChange={(e) => setGrievanceText(e.target.value)}
            />

            <button
              style={{
                ...premiumBtn,
                opacity:
                  grievanceText.trim() && !isAnalyzing ? 1 : 0.5,
                cursor:
                  grievanceText.trim() && !isAnalyzing
                    ? "pointer"
                    : "not-allowed"
              }}
              onClick={handleSubmit}
              disabled={isAnalyzing || !grievanceText.trim()}
            >
              {isAnalyzing ? (
                <Loader2 size={18} className="spin" color="#fff" />
              ) : (
                <Send size={16} />
              )}
              <span style={{ marginLeft: "12px" }}>
                {isAnalyzing
                  ? "AI Classification in Progress..."
                  : "Submit to KisanSetu AI"}
              </span>
            </button>
          </motion.div>
        </div>

        {/* RIGHT */}
        <div style={panelColumn}>
          <AnimatePresence mode="wait">
            {showResult && result ? (
              <motion.div
                key="result"
                initial={{ opacity: 0, x: 40 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -40 }}
                transition={{ duration: 0.5 }}
              >
                <div
                  style={{
                    ...glassCard,
                    borderLeft: `4px solid ${isResolved ? "#10b981" : "#f59e0b"}`,
                    boxShadow: `0 0 40px ${
                      isResolved
                        ? "rgba(16,185,129,0.2)"
                        : "rgba(245,158,11,0.2)"
                    }`
                  }}
                >
                  <div style={resultRow}>
                    <ShieldCheck
                      color={isResolved ? "#10b981" : "#f59e0b"}
                      size={30}
                    />
                    <div>
                      <div
                        style={{
                          ...aiBadge,
                          color: isResolved ? "#10b981" : "#f59e0b"
                        }}
                      >
                        {result.priority} Priority
                        {result.confidence != null
                          ? ` • ${result.confidence}% AI Confidence`
                          : ""}
                      </div>
                      <h3 style={categoryText}>
                        {(result.category || "other").replace(/_/g, " ")}
                      </h3>
                      {result.grievance_id && (
                        <p style={{ color: "#60a5fa", fontSize: "11px", fontFamily: "monospace", marginTop: "4px" }}>
                          {result.grievance_id}
                        </p>
                      )}
                    </div>
                  </div>

                  <div style={divider} />

                  <div style={infoGrid}>
                    <div style={infoItem}>
                      <Clock size={16} color="#94a3b8" />
                      <div>
                        <p style={infoLabel}>Priority</p>
                        <p
                          style={{
                            ...infoValue,
                            color:
                              result.priority === "High"
                                ? "#ef4444"
                                : "#fff"
                          }}
                        >
                          {result.priority}
                        </p>
                      </div>
                    </div>

                    <div style={infoItem}>
                      <UserCheck size={16} color="#94a3b8" />
                      <div>
                        <p style={infoLabel}>Routing Status</p>
                        <p
                          style={{
                            ...infoValue,
                            color: isResolved ? "#10b981" : "#f59e0b",
                            fontSize: "14px"
                          }}
                        >
                          {result.status_label || result.status}
                        </p>
                        {result.suggested_action && (
                        <p
                          style={{
                            color: "#10b981",
                            fontSize: "12px",
                            marginTop: "8px",
                            lineHeight: "1.6"
                          }}
                        >
                          {result.suggested_action}
                        </p>
                      )}
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                style={emptyCard}
              >
                {isAnalyzing ? (
                  <Loader2 size={40} color="#10b981" className="spin" />
                ) : (
                  <Info size={40} color="rgba(255,255,255,0.05)" />
                )}
                <h4 style={{ color: "#e2e8f0", marginTop: "15px" }}>
                  Waiting for Input
                </h4>
                <p style={{ color: "#64748b", maxWidth: "250px" }}>
                  Describe your issue to see how AI routes your grievance.
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* STATUS TRACKER */}
          <motion.div
            whileHover={{ y: -4, boxShadow: "0 0 25px rgba(16, 185, 129, 0.15)" }}
            style={glassCard}
          >
            <div style={sectionHeader}>
              <List size={18} color="#f59e0b" />
              <span>Grievance Lifecycle</span>
            </div>

            <div style={statusWrapper}>
              <div style={statusStep(true)}>
                <FileCheck size={14} />
                Submitted
              </div>
              <div style={statusLine(true)} />
              <div style={statusStep(showResult && !isResolved)}>
                <Activity size={14} />
                Processing
              </div>
              <div style={statusLine(isResolved)} />
              <div style={statusStep(isResolved)}>
                <ShieldCheck size={14} />
                Resolved
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* ANALYTICS CARDS */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px,1fr))",
          gap: "20px",
          marginTop: "40px"
        }}
      >
        {analyticsCards.map((card, i) => (
          <div key={i} style={glassCard}>
            <p style={{ color: "#64748b", fontSize: "13px" }}>{card.title}</p>
            <h2 style={{ color: "#fff", marginTop: "10px" }}>{card.value}</h2>
          </div>
        ))}
      </div>

      {/* AI QUEUE */}
      <div style={{ ...glassCard, marginTop: "35px" }}>
        <div style={{ ...sectionHeader, justifyContent: "space-between", marginBottom: "20px" }}>
          <span style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <Activity size={18} color="#10b981" />
            AI Grievance Queue
          </span>
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            {/* Tab buttons */}
            {[
              { mode: "all",       label: "All" },
              { mode: "escalated", label: `Escalated${escalatedQueue.length > 0 ? ` (${escalatedQueue.length})` : ""}` },
            ].map(({ mode, label }) => (
              <button
                key={mode}
                onClick={() => switchTab(mode)}
                style={{
                  background: viewMode === mode ? "rgba(239,68,68,0.15)" : "rgba(255,255,255,0.05)",
                  color: viewMode === mode ? "#ef4444" : "#64748b",
                  border: `1px solid ${viewMode === mode ? "rgba(239,68,68,0.3)" : "rgba(255,255,255,0.08)"}`,
                  borderRadius: "10px",
                  padding: "6px 14px",
                  cursor: "pointer",
                  fontSize: "12px",
                  fontWeight: "bold",
                }}
              >
                {label}
              </button>
            ))}
            <button
              onClick={() => viewMode === "all" ? fetchQueue() : fetchEscalated()}
              disabled={viewMode === "all" ? loadingQueue : loadingEscalated}
              style={{
                background: "rgba(16,185,129,0.1)",
                color: "#10b981",
                border: "1px solid rgba(16,185,129,0.2)",
                borderRadius: "10px",
                padding: "6px 14px",
                cursor: "pointer",
                fontSize: "12px",
                fontWeight: "bold",
              }}
            >
              ↻ Refresh
            </button>
          </div>
        </div>

        {queueError && (
          <div style={{ padding: "12px 16px", background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: "10px", color: "#ef4444", fontSize: "13px", marginBottom: "16px" }}>
            {queueError}
          </div>
        )}

        {(viewMode === "all" ? loadingQueue : loadingEscalated) ? (
          <p style={{ color: "#64748b", textAlign: "center", padding: "30px 0" }}>
            Loading grievances…
          </p>
        ) : (() => {
          const rows = viewMode === "all" ? grievanceQueue : escalatedQueue;
          const thStyle = { padding: "10px 0", fontSize: "11px", textTransform: "uppercase", letterSpacing: "1px" };
          return (
            <table style={{ width: "100%", borderCollapse: "collapse", color: "#fff" }}>
              <thead>
                <tr style={{ color: "#64748b", textAlign: "left" }}>
                  <th style={thStyle}>Grievance ID</th>
                  <th style={thStyle}>Category</th>
                  <th style={thStyle}>SLA</th>
                  <th style={thStyle}>Routed To</th>
                  <th style={thStyle}>Status</th>
                  {viewMode === "escalated" && <th style={thStyle}>Level</th>}
                </tr>
              </thead>
              <tbody>
                {rows.length === 0 ? (
                  <tr>
                    <td colSpan={viewMode === "escalated" ? 6 : 5} style={{ padding: "30px 0", textAlign: "center", color: "#64748b" }}>
                      {viewMode === "escalated" ? "No escalated grievances" : "No grievances found"}
                    </td>
                  </tr>
                ) : (
                  rows.map((item) => {
                    const cat = item.category || "other";
                    const colors = CATEGORY_COLORS[cat] || CATEGORY_COLORS.other;
                    const grvId = item.grievance_id || `GRV-2026-${String(item.id).padStart(4, "0")}`;
                    const isSelected = selectedId === item.id;
                    const sla = slaStatus(item.sla_deadline, PAGE_LOAD_TIME);
                    return (
                      <tr
                        key={item.id}
                        onClick={() => setSelectedId(isSelected ? null : item.id)}
                        style={{
                          borderTop: "1px solid rgba(255,255,255,0.05)",
                          cursor: "pointer",
                          background: isSelected ? "rgba(16,185,129,0.08)" : "transparent",
                        }}
                      >
                        <td style={{ padding: "14px 0", fontFamily: "monospace", color: "#60a5fa", fontSize: "12px" }}>
                          {grvId}
                        </td>
                        <td>
                          <span style={{ padding: "4px 10px", borderRadius: "20px", fontSize: "11px", fontWeight: "bold", background: colors.bg, color: colors.color }}>
                            {cat.replace(/_/g, " ")}
                          </span>
                        </td>
                        <td style={{ fontSize: "12px", fontWeight: "bold", color: sla ? sla.color : "#64748b" }}>
                          {sla ? sla.label : (item.resolution_days ? `${item.resolution_days}d` : "—")}
                        </td>
                        <td style={{ color: "#e2e8f0", fontSize: "13px" }}>{item.routed_officer}</td>
                        <td>
                          {(() => {
                            const s = item.status || "Pending";
                            const c = STATUS_BADGE[s] || STATUS_BADGE["Pending"];
                            return (
                              <span style={{ padding: "3px 10px", borderRadius: "20px", fontSize: "11px", fontWeight: "bold", background: c.bg, color: c.color }}>
                                {s}
                              </span>
                            );
                          })()}
                        </td>
                        {viewMode === "escalated" && (
                          <td>
                            <span style={{ background: "rgba(239,68,68,0.15)", color: "#ef4444", borderRadius: "20px", padding: "3px 10px", fontSize: "11px", fontWeight: "bold" }}>
                              L{item.escalation_level}
                            </span>
                          </td>
                        )}
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          );
        })()}
      </div>

      {/* ACTION CENTER */}
      <div style={{ ...glassCard, marginTop: "35px" }}>
        <div style={{ ...sectionHeader, marginBottom: "20px" }}>
          <UserCheck size={18} color="#10b981" />
          <span>Officer Actions</span>
        </div>

        {!selectedId ? (
          <p style={{ color: "#64748b", fontSize: "13px" }}>
            Click a row in the queue above to select a grievance, then take action.
          </p>
        ) : (
          <>
            {/* Selected grievance info row */}
            <div style={{ display: "flex", gap: "16px", alignItems: "center", marginBottom: "20px", flexWrap: "wrap" }}>
              <span style={{ fontFamily: "monospace", color: "#60a5fa", fontWeight: "bold", fontSize: "14px" }}>
                GRV-2026-{String(selectedId).padStart(4, "0")}
              </span>
              {selectedItem && (() => {
                const s = selectedItem.status || "Pending";
                const c = STATUS_BADGE[s] || STATUS_BADGE["Pending"];
                return (
                  <span style={{ padding: "3px 12px", borderRadius: "20px", fontSize: "12px", fontWeight: "bold", background: c.bg, color: c.color }}>
                    {s}
                  </span>
                );
              })()}
              {(selectedItem?.escalation_level || 0) > 0 && (
                <span style={{ padding: "3px 12px", borderRadius: "20px", fontSize: "12px", fontWeight: "bold", background: "rgba(239,68,68,0.15)", color: "#ef4444" }}>
                  {selectedItem.escalation_level === 1 ? "⚠ District Officer" : "🔴 State Dept"}
                </span>
              )}
            </div>

            {/* Inline escalation confirmation */}
            {escalateConfirm && (
              <div style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.25)", borderRadius: "14px", padding: "16px 20px", marginBottom: "16px" }}>
                <p style={{ color: "#ef4444", fontWeight: "bold", marginBottom: "12px", fontSize: "14px" }}>
                  Escalate to {(selectedItem?.escalation_level || 0) >= 1 ? "State Agriculture Department" : "District Officer"}?
                </p>
                <div style={{ display: "flex", gap: "10px" }}>
                  <button
                    onClick={handleEscalate}
                    disabled={btnLoading.escalate}
                    style={{ padding: "8px 22px", background: "#ef4444", color: "#fff", border: "none", borderRadius: "10px", cursor: btnLoading.escalate ? "not-allowed" : "pointer", fontWeight: "bold", fontSize: "13px", opacity: btnLoading.escalate ? 0.6 : 1 }}
                  >
                    {btnLoading.escalate ? "Escalating…" : "Confirm Escalation"}
                  </button>
                  <button
                    onClick={() => setEscalateConfirm(false)}
                    style={{ padding: "8px 22px", background: "rgba(255,255,255,0.05)", color: "#94a3b8", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "10px", cursor: "pointer", fontSize: "13px" }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {/* Action result message */}
            {actionMsg && (
              <div style={{ padding: "10px 14px", background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.2)", borderRadius: "10px", color: "#10b981", fontSize: "13px", marginBottom: "16px" }}>
                {actionMsg}
              </div>
            )}

            {/* Action buttons */}
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
              <button
                onClick={() => { handleSetStatus("Under Review"); }}
                disabled={btnLoading.underReview || selectedItem?.status === "Under Review"}
                style={{ padding: "12px 24px", background: "rgba(234,179,8,0.1)", color: "#ca8a04", border: "1px solid rgba(234,179,8,0.25)", borderRadius: "14px", fontWeight: "bold", cursor: btnLoading.underReview || selectedItem?.status === "Under Review" ? "not-allowed" : "pointer", opacity: btnLoading.underReview || selectedItem?.status === "Under Review" ? 0.5 : 1, fontSize: "13px" }}
              >
                {btnLoading.underReview ? "Marking…" : "Under Review"}
              </button>

              <button
                onClick={() => { handleSetStatus("Resolved"); }}
                disabled={btnLoading.resolve || selectedItem?.status === "Resolved"}
                style={{ padding: "12px 24px", background: "rgba(16,185,129,0.1)", color: "#10b981", border: "1px solid rgba(16,185,129,0.25)", borderRadius: "14px", fontWeight: "bold", cursor: btnLoading.resolve || selectedItem?.status === "Resolved" ? "not-allowed" : "pointer", opacity: btnLoading.resolve || selectedItem?.status === "Resolved" ? 0.5 : 1, fontSize: "13px" }}
              >
                {btnLoading.resolve ? "Resolving…" : "Resolve"}
              </button>

              <button
                onClick={() => {
                  if ((selectedItem?.escalation_level || 0) >= 2) {
                    setActionMsg("Already at highest escalation level");
                    return;
                  }
                  setActionMsg(null);
                  setEscalateConfirm(true);
                }}
                disabled={btnLoading.escalate || escalateConfirm || (selectedItem?.escalation_level || 0) >= 2}
                style={{ padding: "12px 24px", background: "rgba(239,68,68,0.1)", color: "#ef4444", border: "1px solid rgba(239,68,68,0.25)", borderRadius: "14px", fontWeight: "bold", cursor: btnLoading.escalate || escalateConfirm || (selectedItem?.escalation_level || 0) >= 2 ? "not-allowed" : "pointer", opacity: btnLoading.escalate || (selectedItem?.escalation_level || 0) >= 2 ? 0.5 : 1, fontSize: "13px" }}
              >
                {btnLoading.escalate ? "Escalating…" : "Escalate Case"}
              </button>
            </div>
          </>
        )}
      </div>

      {/* FARMER STATUS TRACKER */}
      <div style={{ ...glassCard, marginTop: "35px" }}>
        <div style={sectionHeader}>
          <List size={18} color="#3b82f6" />
          <span>Farmer Status Tracker</span>
        </div>
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <input
            type="text"
            placeholder="Enter Grievance ID (e.g. GRV-2026-0001 or 1)"
            value={trackerInput}
            onChange={(e) => setTrackerInput(e.target.value)}
            style={{
              flex: 1,
              background: "rgba(0,0,0,0.3)",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: "12px",
              padding: "14px 16px",
              color: "#fff",
              outline: "none",
              fontSize: "14px"
            }}
          />
          <button
            onClick={handleTrackGrievance}
            disabled={loadingTracker || !trackerInput.trim()}
            style={{
              ...premiumBtn,
              marginTop: 0,
              width: "auto",
              padding: "14px 28px",
              opacity: !trackerInput.trim() || loadingTracker ? 0.5 : 1,
              cursor: !trackerInput.trim() ? "not-allowed" : "pointer"
            }}
          >
            {loadingTracker ? "Looking up…" : "Track"}
          </button>
        </div>

        {trackerResult && (
          <div
            style={{
              marginTop: "20px",
              padding: "18px",
              background: "rgba(0,0,0,0.2)",
              borderRadius: "12px",
              border: "1px solid rgba(255,255,255,0.06)"
            }}
          >
            {trackerResult.error ? (
              <p style={{ color: "#ef4444" }}>{trackerResult.error}</p>
            ) : trackerResult.detail === "Grievance not found" ? (
              <p style={{ color: "#94a3b8" }}>Grievance ID not found in the database.</p>
            ) : (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "10px",
                  fontSize: "14px"
                }}
              >
                <div>
                  <span style={{ color: "#64748b" }}>ID: </span>
                  <span style={{ color: "#60a5fa", fontFamily: "monospace" }}>
                    {trackerResult.grievance_id}
                  </span>
                </div>
                <div>
                  <span style={{ color: "#64748b" }}>Status: </span>
                  <span style={{ color: "#10b981", fontWeight: "bold" }}>
                    {trackerResult.status}
                  </span>
                </div>
                <div>
                  <span style={{ color: "#64748b" }}>Category: </span>
                  <span style={{ color: "#e2e8f0" }}>
                    {(trackerResult.category || "other").replace(/_/g, " ")}
                  </span>
                </div>
                <div>
                  <span style={{ color: "#64748b" }}>ETA: </span>
                  <span style={{ color: "#f59e0b" }}>{trackerResult.eta}</span>
                </div>
                <div>
                  <span style={{ color: "#64748b" }}>Officer: </span>
                  <span style={{ color: "#e2e8f0" }}>{trackerResult.routed_officer}</span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* AUDIT TIMELINE */}
      <div style={{ ...glassCard, marginTop: "35px" }}>
        <div style={sectionHeader}>
          <Clock size={18} color="#f59e0b" />
          <span>Audit Timeline</span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
          {timelineEntries.length === 0 ? (
            <p style={{ color: "#64748b", fontSize: "13px" }}>
              No grievances filed yet. Timeline will appear after the first submission.
            </p>
          ) : (
            timelineEntries.map((item, i) => (
              <div
                key={i}
                style={{
                  color: "#cbd5e1",
                  padding: "12px",
                  background: "rgba(255,255,255,0.03)",
                  borderRadius: "12px"
                }}
              >
                {item}
              </div>
            ))
          )}
        </div>
      </div>

      <style>{`
        .spin {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

/* ---------------- STYLES ---------------- */

const container = {
  maxWidth: "1200px",
  margin: "auto",
  padding: "60px 20px"
};

const headerSection = {
  textAlign: "left",
  marginBottom: "50px"
};

const title = {
  fontSize: "48px",
  fontWeight: "900",
  color: "#fff",
  letterSpacing: "-1.5px"
};

const highlightText = {
  color: "#10b981"
};

const grid = {
  display: "grid",
  gap: "35px",
  gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))"
};

const panelColumn = {
  display: "flex",
  flexDirection: "column",
  gap: "25px"
};

const glassCard = {
  background: "rgba(255, 255, 255, 0.03)",
  backdropFilter: "blur(20px)",
  padding: "35px",
  borderRadius: "28px",
  border: "1px solid rgba(255, 255, 255, 0.08)",
  boxShadow: "0 10px 40px rgba(0,0,0,0.3)",
  transition: "0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)"
};

const sectionHeader = {
  display: "flex",
  alignItems: "center",
  gap: "12px",
  marginBottom: "30px",
  fontWeight: "800",
  textTransform: "uppercase",
  fontSize: "11px",
  letterSpacing: "2px",
  color: "#64748b"
};

const label = {
  fontSize: "14px",
  color: "#94a3b8",
  marginBottom: "15px"
};

const textarea = {
  width: "100%",
  height: "180px",
  background: "rgba(0,0,0,0.3)",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: "20px",
  padding: "20px",
  color: "#fff",
  outline: "none",
  resize: "none",
  fontSize: "15px"
};

const premiumBtn = {
  marginTop: "25px",
  padding: "20px",
  background: "#10b981",
  color: "white",
  border: "none",
  borderRadius: "20px",
  fontWeight: "800",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  boxShadow: "0 15px 30px rgba(16, 185, 129, 0.2)",
  transition: "0.3s ease",
  cursor: "pointer"
};

const emptyCard = {
  ...glassCard,
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
  textAlign: "center",
  minHeight: "320px"
};

const resultRow = {
  display: "flex",
  alignItems: "center",
  gap: "20px"
};

const aiBadge = {
  fontSize: "11px",
  fontWeight: "900",
  textTransform: "uppercase",
  letterSpacing: "1.5px"
};

const categoryText = {
  fontSize: "28px",
  fontWeight: "800",
  color: "#fff",
  marginTop: "6px"
};

const divider = {
  margin: "30px 0",
  height: "1px",
  background: "rgba(255,255,255,0.05)"
};

const infoGrid = {
  display: "flex",
  justifyContent: "space-between"
};

const infoItem = {
  display: "flex",
  gap: "15px",
  alignItems: "center"
};

const infoLabel = {
  fontSize: "11px",
  color: "#64748b",
  fontWeight: "bold"
};

const infoValue = {
  fontSize: "18px",
  fontWeight: "800",
  color: "#fff"
};

const statusWrapper = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  marginTop: "20px"
};

const statusStep = (active) => ({
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  fontSize: "11px",
  fontWeight: "800",
  color: active ? "#10b981" : "#334155"
});

const statusLine = (active) => ({
  flex: 1,
  height: "2px",
  background: active ? "#10b981" : "#1e293b",
  margin: "0 15px"
});
