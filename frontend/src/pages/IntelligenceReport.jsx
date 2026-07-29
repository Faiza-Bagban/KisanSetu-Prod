import { useState, useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, Tooltip as LTip } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RTip,
  ResponsiveContainer, Cell,
} from "recharts";
import { fetchDistrictRisks, fetchNDVISummary } from "../utils/api";
import { cachedFetch } from "../utils/cache";

// ── THEME ─────────────────────────────────────────────────────────────────────
const BG    = "#EAE5DA";
const GREEN = "#2D4A3E";
const HIGH  = "#C0392B";
const LOW   = "#27AE60";
const DC    = { Nashik:"#3B82F6", Aurangabad:"#EF4444", Solapur:"#F97316", Pune:"#22C55E", Kolhapur:"#14B8A6", Amravati:"#A855F7" };
const MAH_CENTER = [19.0, 75.7];

const districtColor = (name) => DC[name] || GREEN;
const riskColor = (level) => level === "HIGH" ? HIGH : LOW;

// ── SECTION CARD ──────────────────────────────────────────────────────────────
function SectionCard({ title, badge, children }) {
  return (
    <div className="ir-section">
      <div className="ir-section-header">
        <div style={{ display:"flex", alignItems:"center", gap:12 }}>
          <div className="ir-section-badge">{badge}</div>
          <span className="ir-section-title">{title}</span>
        </div>
      </div>
      <div style={{ padding:"26px 32px" }}>{children}</div>
    </div>
  );
}

// ── STAT CARD ─────────────────────────────────────────────────────────────────
function StatCard({ label, value, unit, color, icon }) {
  return (
    <div className="ir-stat-card" style={{ borderTop:`4px solid ${color}` }}>
      <div className="ir-stat-icon" style={{ background:`${color}18`, color }}>{icon}</div>
      <div style={{ fontSize:34, fontWeight:900, color, lineHeight:1, marginTop:8 }}>
        {value}
        <span style={{ fontSize:14, fontWeight:500, color:"#bbb", marginLeft:3 }}>{unit}</span>
      </div>
      <div style={{ fontSize:11, color:"#777", marginTop:5, fontWeight:700, letterSpacing:"0.4px", textTransform:"uppercase" }}>{label}</div>
    </div>
  );
}

const tbl = { width:"100%", borderCollapse:"collapse", fontSize:13 };
const th  = { padding:"11px 14px", textAlign:"left", fontWeight:700, fontSize:11, letterSpacing:"0.4px", textTransform:"uppercase" };
const td  = { padding:"12px 14px", color:"#4a5568" };

// ── PAGE ──────────────────────────────────────────────────────────────────────
export default function IntelligenceReport() {
  const [districts, setDistricts]   = useState([]);
  const [ndviRows, setNdviRows]     = useState([]);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState(null);
  const [sel, setSel]               = useState("All");
  const [clock, setClock]           = useState(() => new Date().toLocaleTimeString("en-IN", { hour:"2-digit", minute:"2-digit", hour12:true }));

  useEffect(() => {
    const fmt = () => new Date().toLocaleTimeString("en-IN", { hour:"2-digit", minute:"2-digit", hour12:true });
    const id = setInterval(() => setClock(fmt()), 30000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [riskData, ndviData] = await Promise.all([
          fetchDistrictRisks(),
          cachedFetch("ndvi-summary-report", fetchNDVISummary, 5 * 60_000),
        ]);
        if (cancelled) return;
        setDistricts(Array.isArray(riskData?.districts) ? riskData.districts : []);
        setNdviRows(Array.isArray(ndviData?.districts) ? ndviData.districts : []);
      } catch (e) {
        if (!cancelled) setError(e.message || "Failed to load district risk data");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const ndviByDistrict = {};
  ndviRows.forEach((r) => { ndviByDistrict[r.district] = r; });

  const filtered = sel === "All" ? districts : districts.filter(d => d.district === sel);
  const highRiskDistricts = districts.filter(d => d.risk_level === "HIGH");
  const avgRisk = districts.length
    ? Math.round(districts.reduce((a, d) => a + (d.risk_percent || 0), 0) / districts.length)
    : 0;
  const pendingRelief = districts.filter(d => d.relief_draft && d.relief_draft.status === "PRE_FILLED");

  const STATS = [
    { label:"Districts Tracked",      value: districts.length, unit:"",  color: GREEN, icon:"🗺" },
    { label:"High-Risk Districts",    value: highRiskDistricts.length, unit:"", color: HIGH, icon:"⚠" },
    { label:"Avg Risk Score",         value: avgRisk, unit:"%", color: avgRisk > 60 ? HIGH : LOW, icon:"📊" },
    { label:"NDVI Data Coverage",     value: ndviRows.length, unit:`/${districts.length || 0}`, color:"#3B82F6", icon:"🛰" },
  ];

  return (
    <div style={{ background:BG, minHeight:"100vh", paddingBottom:80 }}>

      {/* ── HEADER ── */}
      <div className="ir-header">
        <div style={{ display:"flex", alignItems:"center", gap:14 }}>
          <div className="ir-header-logo">🌾</div>
          <div>
            <div style={{ color:"#fff", fontSize:22, fontWeight:900, letterSpacing:"-0.3px", lineHeight:1.1 }}>District Risk Summary</div>
            <div style={{ color:"rgba(255,255,255,0.55)", fontSize:12, marginTop:3, letterSpacing:"0.5px" }}>
              Maharashtra Crop Risk & Relief Overview • {clock}
            </div>
          </div>
        </div>
        <button onClick={() => window.print()} className="ir-print-btn no-print">🖨 Print PDF</button>
      </div>

      {loading ? (
        <div style={{ display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", height:"400px" }}>
          <div className="ir-spinner" />
          <p style={{ marginTop:14, color:"#666", fontSize:14 }}>Loading district risk data…</p>
        </div>
      ) : error ? (
        <div style={{ margin:"40px 48px", padding:20, background:"rgba(192,57,43,0.08)", border:"1px solid rgba(192,57,43,0.3)", borderRadius:12, color:HIGH, fontWeight:600 }}>
          ⚠ {error} — the district risk dashboard could not be reached. Try refreshing, or check that the backend is running.
        </div>
      ) : districts.length === 0 ? (
        <div style={{ margin:"40px 48px", padding:20, background:"rgba(45,74,62,0.06)", border:"1px solid rgba(45,74,62,0.2)", borderRadius:12, color:GREEN, fontWeight:600 }}>
          No precomputed district risk data is available yet.
        </div>
      ) : (
        <>
          {/* ── ALERT BANNER ── */}
          {highRiskDistricts.length > 0 && (
            <div className="ir-alert-banner">
              <div style={{ display:"flex", alignItems:"center", gap:10, flexWrap:"wrap" }}>
                <span className="ir-alert-badge">⚠ HIGH RISK</span>
                <span style={{ fontSize:13, fontWeight:600 }}>
                  {highRiskDistricts.map(d => d.district).join(" · ")} — elevated crop-loss risk detected
                  {pendingRelief.length > 0 ? `, ${pendingRelief.length} relief draft${pendingRelief.length > 1 ? "s" : ""} pending officer review` : ""}
                </span>
              </div>
            </div>
          )}

          {/* ── DISTRICT CHIPS ── */}
          <div className="ir-chip-bar">
            {["All", ...districts.map(d => d.district)].map(n => (
              <button key={n} onClick={() => setSel(n)}
                className="ir-chip"
                data-active={sel === n}
                style={sel === n ? { background:GREEN, color:"#fff", borderColor:GREEN } : {}}>
                {n !== "All" && <span className="ir-chip-dot" style={{ background: sel===n ? "#fff" : districtColor(n) }} />}
                {n === "All" ? "🗺 All Districts" : n}
              </button>
            ))}
          </div>

          {/* ── STAT BAR ── */}
          <div className="ir-stat-grid">
            {STATS.map(s => <StatCard key={s.label} {...s} />)}
          </div>

          <div style={{ padding:"12px 48px 0" }}>

            {/* S1: DISTRICT RISK & RELIEF STATUS */}
            <SectionCard title="District Risk & Relief Status" badge="01">
              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:28 }}>
                <div>
                  <div className="ir-label">Risk Map</div>
                  <div className="ir-map-wrap">
                    <MapContainer center={MAH_CENTER} zoom={6} style={{ height:"100%", borderRadius:10 }} scrollWheelZoom={false}>
                      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; OSM" />
                      {filtered.filter(d => d.lat && d.lng).map(d => (
                        <CircleMarker key={d.district} center={[d.lat, d.lng]} radius={Math.max((d.risk_percent || 0) / 5, 6)}
                          color={riskColor(d.risk_level)} fillColor={riskColor(d.risk_level)} fillOpacity={0.6} weight={2}>
                          <LTip><strong>{d.district}</strong><br/>{d.crop_type} · {d.risk_level} ({d.risk_percent}%)</LTip>
                        </CircleMarker>
                      ))}
                    </MapContainer>
                  </div>
                </div>
                <div>
                  <div className="ir-label">Risk % by District</div>
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart layout="vertical" data={filtered} margin={{ left:10, right:20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
                      <XAxis type="number" domain={[0,100]} tick={{ fontSize:11, fill:"#888" }} />
                      <YAxis type="category" dataKey="district" width={90} tick={{ fontSize:12, fill:"#555", fontWeight:600 }} />
                      <RTip contentStyle={{ borderRadius:10, border:"none", boxShadow:"0 4px 20px rgba(0,0,0,0.12)", fontSize:12 }} />
                      <Bar dataKey="risk_percent" name="Risk %" radius={[0,6,6,0]} maxBarSize={28}>
                        {filtered.map(d => <Cell key={d.district} fill={riskColor(d.risk_level)} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <table style={{ ...tbl, marginTop:22 }}>
                <thead>
                  <tr style={{ background:GREEN }}>
                    {["District","Crop","Risk Level","Risk %","Relief Draft Status","Recommended Action"].map(h => (
                      <th key={h} style={{ ...th, color:"rgba(255,255,255,0.85)" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((d,i) => (
                    <tr key={d.district} style={{ background: i%2 ? "#fafaf8" : "#fff" }}>
                      <td style={{ ...td, fontWeight:700, color:GREEN }}>{d.district}</td>
                      <td style={{ ...td, textTransform:"capitalize" }}>{d.crop_type || "—"}</td>
                      <td style={td}>
                        <span className="ir-val-pill" style={{ background:`${riskColor(d.risk_level)}18`, color:riskColor(d.risk_level) }}>{d.risk_level}</span>
                      </td>
                      <td style={{ ...td, fontWeight:700 }}>{d.risk_percent}%</td>
                      <td style={td}>
                        {d.relief_draft
                          ? <span className="ir-val-pill" style={{ background:"rgba(230,126,34,0.15)", color:"#E67E22" }}>{d.relief_draft.status}</span>
                          : <span style={{ color:"#999" }}>—</span>}
                      </td>
                      <td style={{ ...td, fontSize:12 }}>{d.relief_draft?.action || "No immediate action required"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="ir-note">
                Source: precomputed risk assessment (backend/data/district_risks.json). This reflects the last district-wide
                assessment run, not a live per-request recomputation — the underlying crop-loss model is currently trained and
                validated only for Pune, so figures for other districts should be treated as directional until retrained on
                multi-district data.
              </div>
            </SectionCard>

            {/* S2: NDVI / SOIL MOISTURE */}
            <SectionCard title="NDVI & Soil Moisture Snapshot" badge="02">
              {ndviRows.length === 0 ? (
                <p style={{ color:"#888" }}>No live satellite/soil data available yet.</p>
              ) : (
                <table style={tbl}>
                  <thead>
                    <tr style={{ background:GREEN }}>
                      {["District","NDVI Drop","Rainfall Deficit","Temp Anomaly","Soil Moisture","As Of"].map(h => (
                        <th key={h} style={{ ...th, color:"rgba(255,255,255,0.85)" }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {ndviRows.map((r,i) => (
                      <tr key={r.district} style={{ background: i%2 ? "#fafaf8" : "#fff" }}>
                        <td style={{ ...td, fontWeight:700, color:GREEN }}>{r.district}</td>
                        <td style={td}>{r.ndvi_drop}</td>
                        <td style={td}>{r.rainfall_deficit}%</td>
                        <td style={td}>{r.temp_anomaly}°C</td>
                        <td style={td}>{r.soil_moisture ?? "—"}</td>
                        <td style={{ ...td, color:"#888" }}>{r.date}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
              {districts.length > ndviRows.length && (
                <div className="ir-note">
                  Live NDVI/rainfall/soil data is currently only ingested for {ndviRows.map(r => r.district).join(", ") || "no districts yet"}.
                  {" "}{districts.filter(d => !ndviByDistrict[d.district]).map(d => d.district).join(", ")} {districts.filter(d => !ndviByDistrict[d.district]).length === 1 ? "does" : "do"} not
                  yet have live sensor data flowing into this dashboard.
                </div>
              )}
            </SectionCard>

          </div>
        </>
      )}

      {/* ── CSS ── */}
      <style>{`
        .ir-header {
          background: linear-gradient(135deg, ${GREEN} 0%, #3d6b57 100%);
          padding: 22px 48px; display: flex; align-items: center;
          justify-content: space-between; flex-wrap: wrap; gap: 16px;
          box-shadow: 0 4px 24px rgba(0,0,0,0.18);
          position: sticky; top: 0; z-index: 100;
        }
        .ir-header-logo {
          width: 44px; height: 44px; background: rgba(255,255,255,0.12);
          border-radius: 12px; display: flex; align-items: center;
          justify-content: center; font-size: 24px; border: 1px solid rgba(255,255,255,0.18);
        }
        .ir-print-btn {
          padding: 9px 18px; background: rgba(255,255,255,0.12);
          color: #fff; border: 1px solid rgba(255,255,255,0.25);
          border-radius: 10px; cursor: pointer; font-weight: 700; font-size: 13px;
          transition: all 0.2s;
        }
        .ir-print-btn:hover { background: rgba(255,255,255,0.2); }

        .ir-spinner {
          width: 40px; height: 40px; border: 3px solid rgba(45,74,62,0.15);
          border-top: 3px solid ${GREEN}; border-radius: 50%; animation: ir-spin 1s linear infinite;
        }
        @keyframes ir-spin { to { transform: rotate(360deg); } }

        .ir-alert-banner {
          background: linear-gradient(90deg, rgba(192,57,43,0.07) 0%, rgba(192,57,43,0.04) 100%);
          border-bottom: 2px solid rgba(192,57,43,0.2);
          padding: 12px 48px; display: flex; align-items: center;
          justify-content: space-between; flex-wrap: wrap; gap: 10px;
        }
        .ir-alert-badge {
          background: ${HIGH}; color: #fff; padding: 3px 10px;
          border-radius: 5px; font-size: 10px; font-weight: 900; letter-spacing: 0.5px;
        }

        .ir-chip-bar { display: flex; gap: 8px; padding: 16px 48px; flex-wrap: wrap; align-items: center; }
        .ir-chip {
          padding: 7px 16px; border-radius: 99px; border: 2px solid rgba(45,74,62,0.2);
          background: #fff; color: ${GREEN}; cursor: pointer; font-size: 13px; font-weight: 700;
          transition: all 0.2s; display: flex; align-items: center; gap: 7px;
        }
        .ir-chip:hover { transform: translateY(-2px); box-shadow: 0 4px 14px rgba(45,74,62,0.15); }
        .ir-chip-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }

        .ir-stat-grid { display: flex; gap: 14px; padding: 0 48px 20px; flex-wrap: wrap; }
        .ir-stat-card {
          flex: 1 1 160px; background: #fff; border-radius: 14px;
          padding: 18px 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.07);
        }
        .ir-stat-icon {
          width: 36px; height: 36px; border-radius: 10px;
          display: flex; align-items: center; justify-content: center; font-size: 18px;
        }

        .ir-section {
          background: #fff; border-radius: 16px; margin-bottom: 20px;
          box-shadow: 0 4px 24px rgba(45,74,62,0.07); border: 1px solid rgba(45,74,62,0.07);
          overflow: hidden;
        }
        .ir-section-header {
          padding: 20px 32px; background: linear-gradient(135deg, #f9f8f5 0%, #f4f2ec 100%);
          border-left: 5px solid ${GREEN};
        }
        .ir-section-badge {
          width: 30px; height: 30px; border-radius: 9px; background: ${GREEN};
          display: flex; align-items: center; justify-content: center;
          font-size: 12px; font-weight: 900; color: rgba(255,255,255,0.9);
        }
        .ir-section-title { font-weight: 800; font-size: 16px; color: ${GREEN}; }
        .ir-label { font-size:12px; font-weight:700; color:${GREEN}; margin-bottom:10px; text-transform:uppercase; letter-spacing:0.5px; }
        .ir-map-wrap { height: 300px; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
        .ir-val-pill { padding: 4px 11px; border-radius: 99px; font-size: 12px; font-weight: 700; display: inline-block; }
        .ir-note { background:rgba(45,74,62,0.055); border:1px solid rgba(45,74,62,0.14); border-radius:10px; padding:"14px 18px"; margin-top:18px; font-size:12px; color:#555; line-height:1.6; padding: 14px 18px; }

        @media print {
          .no-print, .ir-header { display: none !important; }
          .ir-section { box-shadow: none !important; break-inside: avoid; }
          body { background: white !important; }
        }
      `}</style>
    </div>
  );
}
