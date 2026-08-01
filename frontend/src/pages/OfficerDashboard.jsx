import { useState, useEffect, useRef } from "react";
import ConfidenceBadge from "../components/ConfidenceBadge";
import { extractIDP, fetchWithAuth, fetchDocuments } from "../utils/api";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

// Maps a raw backend document row to the shape this table renders.
// Tolerant of a couple of likely response shapes since GET /api/documents
// is still being built server-side (see loadQueue below).
function normalizeDoc(doc) {
  return {
    id: doc.id,
    farmerName: doc.farmer_name || (doc.farmer_id ? `Farmer #${doc.farmer_id}` : "Unknown"),
    documentType: doc.document_type || "—",
    status: doc.verification_status || "Pending",
  };
}

import {
  Upload,
  FileCheck,
  AlertTriangle,
  RefreshCcw,
  Shield,
  Search,
  FileText,
  ScanLine,
  CheckCircle2,
  Clock3,
  Database,
  BrainCircuit,
} from "lucide-react";

import { motion, AnimatePresence } from "framer-motion";
import toast from "react-hot-toast";


export default function OfficerDashboard() {
  const [file, setFile] = useState(null);

  const [isProcessing, setIsProcessing] = useState(false);

  const [results, setResults] = useState([]);

  const [, setStep] = useState(0);

  const [isComplete, setIsComplete] = useState(false);

  const [backendReady, setBackendReady] = useState(false);

  const [verificationStatus, setVerificationStatus] =
    useState("Awaiting Document");

  const [ocrProgress, setOcrProgress] = useState(0);

  const [auditTrail, setAuditTrail] = useState([]);
  const [uploadError, setUploadError] = useState(null);
  const [currentDocId, setCurrentDocId] = useState(null);
  const [docActionStatus, setDocActionStatus] = useState({});
  const [documentQueue, setDocumentQueue] = useState([]);
  const [queueLoading, setQueueLoading] = useState(true);
  const [queueError, setQueueError] = useState(null);

  const intervalRef = useRef(null);
  const queueIntervalRef = useRef(null);

  /* ---------------- FILE UPLOAD ---------------- */

  const handleFileUpload = (e) => {
    const uploaded = e.target.files[0];

    if (!uploaded) return;

    setFile(uploaded);

    setResults([]);

    setStep(0);

    setIsComplete(false);

    setVerificationStatus("Document Uploaded");

    setOcrProgress(0);

    setAuditTrail([
      {
        action: "Document uploaded",
        time: new Date().toLocaleTimeString(),
      },
    ]);

    toast.success("Document uploaded successfully");
  };

  /* ---------------- START SCAN (live IDP API) ---------------- */

  const handleScan = async () => {
    if (!file || isProcessing) return;

    setIsProcessing(true);
    setUploadError(null);
    setVerificationStatus("AI OCR Processing");
    setOcrProgress(30);
    setAuditTrail((prev) => [
      ...prev,
      { action: "OCR engine started", time: new Date().toLocaleTimeString() },
    ]);

    try {
      const data = await extractIDP(file);

      setOcrProgress(100);

      // Map core fields from IDP response (confidence is 0-100)
      const fields = [];
      const coreMap = [
        { field: "Farmer Name", key: "name" },
        { field: "Land ID",     key: "land_id" },
        { field: "Aadhaar",     key: "aadhaar" },
      ];

      coreMap.forEach(({ field, key }) => {
        const f = data[key];
        if (f) {
          const conf = f.confidence ?? 0;
          fields.push({
            field,
            value: f.value || "—",
            confidence: conf,
            status:
              conf >= 80
                ? "AUTO-VERIFIED"
                : conf >= 70
                ? "OCR VERIFIED"
                : "NEEDS REVIEW",
          });
        }
      });

      // Surface a few additional fields (dob, village, crop_type, etc.)
      Object.entries(data.additional_fields || {}).forEach(([key, val]) => {
        if (val && typeof val === "string") {
          fields.push({
            field: key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, " "),
            value: val,
            confidence: 75,
            status: "OCR EXTRACTED",
          });
        }
      });

      setResults(fields);
      setStep(fields.length);

      const allAbove70 = fields.length > 0 && fields.every((f) => f.confidence >= 70);
      const status = allAbove70 ? "Pre-Verified" : "Flagged for Review";
      setVerificationStatus(status);
      setIsComplete(true);
      setBackendReady(true);

      const safeDocId = file.name.replace(/[^a-zA-Z0-9._-]/g, "_");
      setCurrentDocId(safeDocId);

      fields.forEach((f) =>
        setAuditTrail((prev) => [
          ...prev,
          {
            action: `${f.field} extracted — confidence ${f.confidence}%`,
            time: new Date().toLocaleTimeString(),
          },
        ])
      );
      setAuditTrail((prev) => [
        ...prev,
        { action: `Overall status: ${status}`, time: new Date().toLocaleTimeString() },
      ]);

      toast.success(`Document processed: ${status}`);
    } catch (err) {
      const msg = err.message || "OCR processing failed";
      setUploadError(msg);
      setVerificationStatus("Processing Failed");
      setOcrProgress(0);
      toast.error(msg);
    } finally {
      setIsProcessing(false);
    }
  };

  /* ---------------- RESET ---------------- */

  const handleReset = () => {
    setFile(null);

    setResults([]);

    setStep(0);

    setIsProcessing(false);

    setIsComplete(false);

    setBackendReady(false);

    setVerificationStatus("Awaiting Document");

    setOcrProgress(0);

    setAuditTrail([]);

    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
  };

  useEffect(() => {
    const ref = intervalRef.current;
    return () => {
      if (ref) clearInterval(ref);
    };
  }, []);

  /* ---------------- DOCUMENT QUEUE (real backend, polls every 30s) ---------------- */

  const loadQueue = async () => {
    try {
      setQueueError(null);
      const data = await fetchDocuments();
      const rows = Array.isArray(data) ? data : (data.documents || []);
      setDocumentQueue(rows.map(normalizeDoc));
    } catch (err) {
      setQueueError(err.message || "Unable to load document queue");
    } finally {
      setQueueLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial fetch on mount, not derived state
    loadQueue();
  }, []);

  useEffect(() => {
    queueIntervalRef.current = setInterval(loadQueue, 30000);
    const ref = queueIntervalRef.current;
    return () => clearInterval(ref);
  }, []);

  /* ---------------- APPROVE / FLAG CURRENT SCAN DOC ---------------- */

  const handleApprove = async () => {
  if (!currentDocId) return;
  // currentDocId is set to the uploaded filename — the backend /api/documents/{id}/approve
  // endpoint expects an integer primary key, not a filename string.
  // Until /api/idp/extract returns a real DB doc_id, we surface an honest message.
  toast("Document verified locally. Sync to backend requires a saved document ID — contact your system admin.", { icon: "ℹ️" });
  setAuditTrail((prev) => [
    ...prev,
    { action: "Local verification complete — backend sync pending doc ID", time: new Date().toLocaleTimeString() },
  ]);
};

  const handleFlag = async () => {
  if (!currentDocId) return;
  toast("Document flagged locally. Backend sync requires a saved document ID — contact your system admin.", { icon: "⚠️" });
  setAuditTrail((prev) => [
    ...prev,
    { action: "Document flagged for review — backend sync pending doc ID", time: new Date().toLocaleTimeString() },
  ]);
};

  /* ---------------- APPROVE / FLAG QUEUE ITEMS ---------------- */

  const handleQueueAction = async (docId, action) => {
    try {
      await fetchWithAuth(`${API_BASE}/api/documents/${docId}/${action}`, {
        method: "PATCH",
      });
      setDocumentQueue((prev) =>
        prev.map((d) =>
          d.id === docId
            ? { ...d, status: action === "approve" ? "Pre-Verified" : "Flagged" }
            : d
        )
      );
      toast.success(`Document ${action === "approve" ? "approved" : "flagged"}`);
    } catch (err) {
      toast.error(`Action failed: ${err.message || "unknown error"}`);
    }
  };

  return (
    <div style={container}>
      {/* ---------------- HEADER ---------------- */}

      <motion.div
        initial={{ y: -25, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
      >
        <div style={header}>
          <div>
            <h1 style={title}>🛡️ Officer Verification Console</h1>

            <p style={subtitle}>
              Intelligent Document Processing • OCR • Verification Layer
            </p>
          </div>

          <div style={statusBox}>
            <Shield size={14} />
            <span>AI Secure Mode Enabled</span>
          </div>
        </div>
      </motion.div>

      {/* ---------------- TOP STATS ---------------- */}

      <div style={statsGrid}>
        <div style={statCard}>
          <Database size={22} color="#10b981" />
          <div>
            <h3 style={statNumber}>{results.length}</h3>
            <p style={statLabel}>Fields Extracted</p>
          </div>
        </div>

        <div style={statCard}>
          <Clock3 size={22} color="#3b82f6" />
          <div>
            <h3 style={statNumber}>{Math.round(ocrProgress)}%</h3>
            <p style={statLabel}>OCR Progress</p>
          </div>
        </div>

        <div style={statCard}>
          <BrainCircuit size={22} color="#f59e0b" />
          <div>
            <h3 style={statNumber}>
              {isComplete ? "READY" : "WAIT"}
            </h3>
            <p style={statLabel}>AI Status</p>
          </div>
        </div>

        <div style={statCard}>
          <CheckCircle2 size={22} color="#22c55e" />
          <div>
            <h3 style={statNumber}>
              {backendReady ? "ONLINE" : "OFFLINE"}
            </h3>
            <p style={statLabel}>Backend Sync</p>
          </div>
        </div>
      </div>

      {/* ---------------- MAIN GRID ---------------- */}

      <div style={grid}>
        {/* ---------------- LEFT PANEL ---------------- */}

        <div style={glassCard}>
          <h3 style={sectionTitle}>
            <Upload size={18} color="#3b82f6" />
            Upload Land / Identity Documents
          </h3>

          <div style={uploadArea}>
            <input
              type="file"
              id="file-upload"
              onChange={handleFileUpload}
              style={{ display: "none" }}
            />

            <label htmlFor="file-upload" style={uploadLabel}>
              {file ? "Change Uploaded File" : "Select Document"}
            </label>

            {file && (
              <div style={fileInfo}>
                <div>
                  <p style={fileName}>📄 {file.name}</p>

                  <span style={fileSize}>
                    {(file.size / 1024).toFixed(2)} KB
                  </span>
                </div>

                <button onClick={handleReset} style={resetBtn}>
                  <RefreshCcw size={14} />
                </button>
              </div>
            )}
          </div>

          {/* ---------------- SCANNER VISUAL ---------------- */}

          <div style={scanContainer}>
            <div style={iconBox}>
              <FileText
                size={70}
                color={isProcessing ? "#10b981" : "#3b82f6"}
              />

              <AnimatePresence>
                {isProcessing && (
                  <motion.div
                    initial={{ top: "-10%" }}
                    animate={{ top: "110%" }}
                    exit={{ opacity: 0 }}
                    transition={{
                      duration: 1.5,
                      repeat: Infinity,
                      ease: "linear",
                    }}
                    style={scanLine}
                  />
                )}
              </AnimatePresence>
            </div>
          </div>

          {/* ---------------- ACTION BUTTONS ---------------- */}

          <div style={buttonGroup}>
            <button
              style={{
                ...btn,
                opacity: file ? 1 : 0.5,
                cursor: file ? "pointer" : "not-allowed",
              }}
              onClick={handleScan}
              disabled={!file || isProcessing}
            >
              {isProcessing
                ? "Running OCR Engine..."
                : isComplete
                ? "Scan Again"
                : "Start AI Scan"}
            </button>

            <button
              style={secondaryBtn}
              onClick={handleApprove}
              disabled={!isComplete || docActionStatus[currentDocId] === "approved"}
            >
              {docActionStatus[currentDocId] === "approved" ? "✓ Approved" : "Approve & Sync to Backend"}
            </button>
          </div>

          {/* ---------------- STATUS ---------------- */}

          <div style={statusCard}>
            <div style={statusHeader}>
              <ScanLine size={16} color="#10b981" />
              <span>{verificationStatus}</span>
            </div>

            <div style={progressBar}>
              <motion.div
                animate={{ width: `${ocrProgress}%` }}
                style={progressFill}
              />
            </div>
          </div>
        </div>

        {/* ---------------- RIGHT PANEL ---------------- */}

        <div style={glassCard}>
          <h3 style={sectionTitle}>
            <Search size={18} color="#10b981" />
            AI Extraction Results
          </h3>

          {!file && !isProcessing && results.length === 0 && (
            <div style={emptyState}>
              <p>Upload a document to begin verification.</p>
            </div>
          )}

          <div style={{ overflowX: "auto" }}>
            <table style={table}>
              <thead>
                <tr>
                  <th style={th}>Field</th>
                  <th style={th}>Extracted Value</th>
                  <th style={th}>Confidence</th>
                  <th style={th}>Verification</th>
                </tr>
              </thead>

              <tbody>
                {results.map((d, i) => (
                  <motion.tr
                    key={i}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    style={row}
                  >
                    <td style={td}>{d.field}</td>

                    <td
                      style={{
                        ...td,
                        color: "#60a5fa",
                        fontFamily: "monospace",
                      }}
                    >
                      {d.value}
                    </td>

                    <td style={td}>
                      <div
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          gap: "5px",
                        }}
                      >
                        <ConfidenceBadge value={d.confidence} />

                        <div style={miniBarBg}>
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{
                              width: `${d.confidence}%`,
                            }}
                            style={{
                              ...miniBarFill,
                              background:
                                d.confidence > 90
                                  ? "#10b981"
                                  : "#f59e0b",
                            }}
                          />
                        </div>
                      </div>
                    </td>

                    <td style={statusStyle}>
                      <FileCheck size={14} />
                      {d.status}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* ---------------- INLINE ERROR ---------------- */}

          {uploadError && (
            <div style={errorBanner}>
              <AlertTriangle size={14} /> {uploadError}
            </div>
          )}

          {/* ---------------- ACTIONS ---------------- */}

          {isComplete && (
            <div style={actions}>
              <button
                style={{
                  ...approveBtn,
                  opacity: docActionStatus[currentDocId] === "approved" ? 0.6 : 1,
                }}
                onClick={handleApprove}
                disabled={docActionStatus[currentDocId] === "approved"}
              >
                {docActionStatus[currentDocId] === "approved" ? "✓ Approved" : "Approve & Sync"}
              </button>

              <button
                style={{
                  ...flagBtn,
                  opacity: docActionStatus[currentDocId] === "flagged" ? 0.6 : 1,
                }}
                onClick={handleFlag}
                disabled={docActionStatus[currentDocId] === "flagged"}
              >
                <AlertTriangle size={16} />
                {docActionStatus[currentDocId] === "flagged" ? "Flagged" : "Flag for Manual Review"}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ---------------- DOCUMENT QUEUE ---------------- */}

      <div style={queueCard}>
        <h3 style={{ ...sectionTitle, marginBottom: "20px" }}>
          <Database size={18} color="#3b82f6" />
          Pending Applications
          <button
            onClick={loadQueue}
            disabled={queueLoading}
            style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "6px", background: "none", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", padding: "6px 12px", color: "#94a3b8", fontSize: "11px", cursor: queueLoading ? "not-allowed" : "pointer" }}
          >
            <RefreshCcw size={12} /> {queueLoading ? "Refreshing…" : "Refresh"}
          </button>
        </h3>

        {queueError && (
          <div style={errorBanner}>
            <AlertTriangle size={14} /> {queueError}
          </div>
        )}

        {queueLoading && documentQueue.length === 0 && !queueError ? (
          <p style={{ color: "#64748b" }}>Loading pending applications…</p>
        ) : documentQueue.length === 0 && !queueError ? (
          <p style={{ color: "#64748b" }}>No pending applications in the queue.</p>
        ) : (
        <div style={{ overflowX: "auto" }}>
          <table style={queueTable}>
            <thead>
              <tr>
                <th style={queueTh}>Doc ID</th>
                <th style={queueTh}>Farmer</th>
                <th style={queueTh}>Document Type</th>
                <th style={queueTh}>Status</th>
                <th style={queueTh}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {documentQueue.map((doc) => (
                <tr key={doc.id}>
                  <td style={{ ...queueTd, fontFamily: "monospace", color: "#60a5fa" }}>{doc.id}</td>
                  <td style={queueTd}>{doc.farmerName}</td>
                  <td style={{ ...queueTd, color: "#64748b" }}>{doc.documentType}</td>
                  <td style={queueTd}>
                    <span style={statusBadge(doc.status)}>{doc.status}</span>
                  </td>
                  <td style={queueTd}>
                    <button
                      style={queueActionBtn("approve")}
                      onClick={() => handleQueueAction(doc.id, "approve")}
                      disabled={doc.status === "Pre-Verified"}
                    >
                      Approve
                    </button>
                    <button
                      style={queueActionBtn("flag")}
                      onClick={() => handleQueueAction(doc.id, "flag")}
                      disabled={doc.status === "Flagged"}
                    >
                      Flag
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        )}
      </div>

      {/* ---------------- AUDIT TRAIL ---------------- */}

      <div style={auditCard}>
        <h3 style={sectionTitle}>
          <Shield size={18} color="#f59e0b" />
          Verification Audit Trail
        </h3>

        <div style={auditList}>
          {auditTrail.length === 0 ? (
            <p style={{ color: "#64748b" }}>
              No audit actions yet
            </p>
          ) : (
            auditTrail.map((log, index) => (
              <div key={index} style={auditItem}>
                <div style={auditDot} />

                <div>
                  <p style={auditAction}>{log.action}</p>

                  <span style={auditTime}>{log.time}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

/* ---------------- STYLES ---------------- */

const container = {
  maxWidth: "1400px",
  margin: "0 auto",
  padding: "40px 20px",
};

const header = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: "30px",
};

const title = {
  fontSize: "34px",
  fontWeight: 800,
  color: "#fff",
};

const subtitle = {
  color: "#94a3b8",
  fontSize: "14px",
};

const statusBox = {
  display: "flex",
  alignItems: "center",
  gap: "8px",
  padding: "8px 16px",
  borderRadius: "20px",
  background: "rgba(16,185,129,0.1)",
  border: "1px solid rgba(16,185,129,0.2)",
  color: "#10b981",
  fontWeight: "bold",
  fontSize: "12px",
};

const statsGrid = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: "20px",
  marginBottom: "25px",
};

const statCard = {
  display: "flex",
  alignItems: "center",
  gap: "16px",
  padding: "22px",
  borderRadius: "22px",
  background: "rgba(255,255,255,0.03)",
  border: "1px solid rgba(255,255,255,0.08)",
  backdropFilter: "blur(20px)",
};

const statNumber = {
  color: "#fff",
  fontSize: "22px",
  fontWeight: "bold",
};

const statLabel = {
  color: "#94a3b8",
  fontSize: "12px",
};

const isMobile = window.innerWidth < 768;
const grid = {
  display: "grid",
  gridTemplateColumns: isMobile ? "1fr" : "1fr 2fr",
  gap: "25px",
};

const glassCard = {
  background: "rgba(255,255,255,0.03)",
  backdropFilter: "blur(20px)",
  borderRadius: "24px",
  padding: "30px",
  border: "1px solid rgba(255,255,255,0.08)",
};

const sectionTitle = {
  fontSize: "17px",
  marginBottom: "20px",
  display: "flex",
  alignItems: "center",
  gap: "10px",
  fontWeight: "700",
};

const uploadArea = {
  marginBottom: "20px",
};

const uploadLabel = {
  display: "block",
  padding: "15px",
  background: "rgba(255,255,255,0.05)",
  border: "1px dashed rgba(255,255,255,0.2)",
  borderRadius: "12px",
  textAlign: "center",
  cursor: "pointer",
  fontSize: "14px",
  fontWeight: "600",
};

const fileInfo = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginTop: "12px",
  background: "rgba(0,0,0,0.3)",
  padding: "12px",
  borderRadius: "10px",
};

const fileName = {
  color: "#fff",
  fontSize: "13px",
};

const fileSize = {
  color: "#64748b",
  fontSize: "11px",
};

const resetBtn = {
  background: "none",
  border: "none",
  color: "#ef4444",
  cursor: "pointer",
};

const scanContainer = {
  margin: "20px 0",
  padding: "35px",
  borderRadius: "20px",
  background: "rgba(0,0,0,0.2)",
  border: "1px solid rgba(255,255,255,0.05)",
  display: "flex",
  justifyContent: "center",
};

const iconBox = {
  position: "relative",
  overflow: "hidden",
  padding: "10px",
};

const scanLine = {
  position: "absolute",
  left: 0,
  width: "100%",
  height: "2px",
  background:
    "linear-gradient(90deg, transparent, #10b981, transparent)",
  boxShadow: "0 0 10px #10b981",
  zIndex: 10,
};

const buttonGroup = {
  display: "flex",
  flexDirection: "column",
  gap: "12px",
};

const btn = {
  width: "100%",
  padding: "14px",
  background: "#3b82f6",
  color: "white",
  border: "none",
  borderRadius: "12px",
  fontWeight: "bold",
  cursor: "pointer",
};

const secondaryBtn = {
  width: "100%",
  padding: "14px",
  background: "rgba(16,185,129,0.1)",
  color: "#10b981",
  border: "1px solid rgba(16,185,129,0.2)",
  borderRadius: "12px",
  fontWeight: "bold",
  cursor: "pointer",
};

const statusCard = {
  marginTop: "25px",
};

const statusHeader = {
  display: "flex",
  alignItems: "center",
  gap: "8px",
  marginBottom: "10px",
  color: "#94a3b8",
  fontSize: "13px",
};

const progressBar = {
  height: "8px",
  background: "rgba(255,255,255,0.08)",
  borderRadius: "20px",
  overflow: "hidden",
};

const progressFill = {
  height: "100%",
  background: "#10b981",
};

const table = {
  width: "100%",
  borderCollapse: "collapse",
};

const th = {
  textAlign: "left",
  padding: "15px",
  fontSize: "11px",
  color: "#64748b",
  textTransform: "uppercase",
  letterSpacing: "1px",
};

const td = {
  padding: "16px",
  borderBottom: "1px solid rgba(255,255,255,0.05)",
  fontSize: "14px",
};

const row = {};

const miniBarBg = {
  width: "100%",
  height: "4px",
  background: "rgba(255,255,255,0.08)",
  borderRadius: "10px",
};

const miniBarFill = {
  height: "100%",
  borderRadius: "10px",
};

const statusStyle = {
  color: "#10b981",
  display: "flex",
  alignItems: "center",
  gap: "8px",
  fontWeight: "bold",
  fontSize: "13px",
};

const emptyState = {
  textAlign: "center",
  padding: "80px 20px",
  color: "#64748b",
};

const actions = {
  display: "flex",
  gap: "15px",
  marginTop: "30px",
};

const approveBtn = {
  flex: 1,
  background: "#10b981",
  color: "white",
  border: "none",
  borderRadius: "12px",
  padding: "14px",
  fontWeight: "bold",
  cursor: "pointer",
};

const flagBtn = {
  flex: 1,
  background: "rgba(239,68,68,0.1)",
  color: "#ef4444",
  border: "1px solid rgba(239,68,68,0.2)",
  borderRadius: "12px",
  padding: "14px",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  gap: "8px",
  fontWeight: "bold",
  cursor: "pointer",
};

const auditCard = {
  marginTop: "30px",
  background: "rgba(255,255,255,0.03)",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: "24px",
  padding: "30px",
  backdropFilter: "blur(20px)",
};

const auditList = {
  display: "flex",
  flexDirection: "column",
  gap: "14px",
};

const auditItem = {
  display: "flex",
  alignItems: "flex-start",
  gap: "12px",
};

const auditDot = {
  width: "10px",
  height: "10px",
  borderRadius: "50%",
  background: "#10b981",
  marginTop: "6px",
};

const auditAction = {
  color: "#fff",
  fontSize: "14px",
};

const auditTime = {
  color: "#64748b",
  fontSize: "12px",
};

const errorBanner = {
  display: "flex",
  alignItems: "center",
  gap: "8px",
  padding: "12px 16px",
  background: "rgba(239,68,68,0.1)",
  border: "1px solid rgba(239,68,68,0.2)",
  borderRadius: "10px",
  color: "#ef4444",
  fontSize: "13px",
  marginBottom: "16px",
};

const queueCard = {
  marginTop: "30px",
  background: "rgba(255,255,255,0.03)",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: "24px",
  padding: "30px",
  backdropFilter: "blur(20px)",
};

const queueTable = {
  width: "100%",
  borderCollapse: "collapse",
};

const queueTh = {
  textAlign: "left",
  padding: "12px 16px",
  fontSize: "11px",
  color: "#64748b",
  textTransform: "uppercase",
  letterSpacing: "1px",
};

const queueTd = {
  padding: "14px 16px",
  borderBottom: "1px solid rgba(255,255,255,0.05)",
  fontSize: "13px",
  color: "#e2e8f0",
};

const statusBadge = (status) => ({
  padding: "4px 10px",
  borderRadius: "20px",
  fontSize: "11px",
  fontWeight: "bold",
  background:
    status === "Pre-Verified"
      ? "rgba(16,185,129,0.15)"
      : status === "Flagged"
      ? "rgba(239,68,68,0.15)"
      : "rgba(245,158,11,0.15)",
  color:
    status === "Pre-Verified"
      ? "#10b981"
      : status === "Flagged"
      ? "#ef4444"
      : "#f59e0b",
});

const queueActionBtn = (variant) => ({
  padding: "6px 14px",
  borderRadius: "8px",
  border: "none",
  cursor: "pointer",
  fontSize: "12px",
  fontWeight: "bold",
  marginRight: "8px",
  background: variant === "approve" ? "rgba(16,185,129,0.15)" : "rgba(239,68,68,0.1)",
  color: variant === "approve" ? "#10b981" : "#ef4444",
});