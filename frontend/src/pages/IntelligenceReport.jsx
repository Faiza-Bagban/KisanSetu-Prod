import { useState, useEffect, useRef } from "react";
import { MapContainer, TileLayer, CircleMarker, Tooltip as LTip } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RTip,
  ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  AreaChart, Area, LineChart, Line, PieChart, Pie, Cell,
  ComposedChart, ReferenceLine, ReferenceArea, Legend,
} from "recharts";

// ── THEME ─────────────────────────────────────────────────────────────────────
const BG    = "#EAE5DA";
const GREEN = "#2D4A3E";
const HIGH  = "#C0392B";
const MED   = "#E67E22";
const LOW   = "#27AE60";
const DC    = { Nashik:"#3B82F6", Aurangabad:"#EF4444", Solapur:"#F97316", Pune:"#22C55E", Kolhapur:"#14B8A6", Amravati:"#A855F7" };

const fragColor     = s => s > 70 ? HIGH : s > 50 ? MED : LOW;
const irrigColor    = s => s > 60 ? LOW  : s > 40 ? MED : HIGH;
const distressColor = s => s > 65 ? HIGH : s > 45 ? MED : LOW;
const climateColor  = s => s > 65 ? HIGH : s > 45 ? MED : LOW;
const exportColor   = s => s > 65 ? HIGH : s > 45 ? MED : LOW;
const gradeColor    = { A: LOW, B: "#3B82F6", C: MED, D: HIGH };

// ── DATA ──────────────────────────────────────────────────────────────────────
const DISTRICTS = [
  { name:"Pune",       lat:18.52, lng:73.85, fragIndex:72, irrigPct:58, phLoss:28, exportRisk:65, distress:45, climate:52 },
  { name:"Nashik",     lat:20.00, lng:73.79, fragIndex:85, irrigPct:42, phLoss:35, exportRisk:78, distress:68, climate:71 },
  { name:"Aurangabad", lat:19.88, lng:75.34, fragIndex:61, irrigPct:35, phLoss:42, exportRisk:55, distress:72, climate:65 },
  { name:"Solapur",    lat:17.69, lng:75.90, fragIndex:54, irrigPct:48, phLoss:31, exportRisk:48, distress:58, climate:43 },
  { name:"Kolhapur",   lat:16.70, lng:74.24, fragIndex:43, irrigPct:71, phLoss:22, exportRisk:35, distress:32, climate:38 },
  { name:"Amravati",   lat:20.93, lng:77.75, fragIndex:78, irrigPct:29, phLoss:48, exportRisk:82, distress:81, climate:77 },
];

const IRRIG_RADAR = {
  Pune:       [{ s:"Coverage",v:58},{s:"Drip%",v:42},{s:"Canal%",v:35},{s:"Ground.",v:68},{s:"Effic.",v:61}],
  Nashik:     [{ s:"Coverage",v:42},{s:"Drip%",v:55},{s:"Canal%",v:28},{s:"Ground.",v:51},{s:"Effic.",v:48}],
  Aurangabad: [{ s:"Coverage",v:35},{s:"Drip%",v:31},{s:"Canal%",v:22},{s:"Ground.",v:41},{s:"Effic.",v:38}],
  Solapur:    [{ s:"Coverage",v:48},{s:"Drip%",v:38},{s:"Canal%",v:44},{s:"Ground.",v:55},{s:"Effic.",v:52}],
  Kolhapur:   [{ s:"Coverage",v:71},{s:"Drip%",v:62},{s:"Canal%",v:58},{s:"Ground.",v:74},{s:"Effic.",v:78}],
  Amravati:   [{ s:"Coverage",v:29},{s:"Drip%",v:24},{s:"Canal%",v:18},{s:"Ground.",v:38},{s:"Effic.",v:32}],
};

const PH_PIE    = [
  { name:"Storage Loss",value:38 },
  { name:"Transport",   value:27 },
  { name:"Market",      value:20 },
  { name:"Processing",  value:15 },
];
const PH_COLORS = [HIGH, MED, "#3B82F6", "#8B5CF6"];

const NREGA_DATA = [
  { month:"Dec", workers:12400, days:8.2 },
  { month:"Jan", workers:15200, days:9.1 },
  { month:"Feb", workers:18900, days:10.3 },
  { month:"Mar", workers:22100, days:11.8 },
  { month:"Apr", workers:28600, days:14.2 },
  { month:"May", workers:31400, days:15.7 },
];

const CLIMATE_DATA = {
  "30d": [
    { week:"Apr W1", rain:12, temp:38.2 },
    { week:"Apr W2", rain:8,  temp:39.1 },
    { week:"Apr W3", rain:22, temp:37.5 },
    { week:"Apr W4", rain:5,  temp:40.3 },
    { week:"May W1", rain:31, temp:38.9 },
    { week:"May W2", rain:18, temp:37.8 },
  ],
  "60d": [
    { week:"Mar W1", rain:9,  temp:36.1 },
    { week:"Mar W2", rain:15, temp:36.8 },
    { week:"Mar W3", rain:7,  temp:37.2 },
    { week:"Mar W4", rain:3,  temp:38.0 },
    { week:"Apr W1", rain:12, temp:38.2 },
    { week:"Apr W2", rain:8,  temp:39.1 },
    { week:"Apr W3", rain:22, temp:37.5 },
    { week:"Apr W4", rain:5,  temp:40.3 },
    { week:"May W1", rain:31, temp:38.9 },
    { week:"May W2", rain:18, temp:37.8 },
  ],
};

const COMPOSITE = [
  { rank:1, district:"Kolhapur",   score:82, grade:"A" },
  { rank:2, district:"Pune",       score:67, grade:"B" },
  { rank:3, district:"Solapur",    score:61, grade:"B" },
  { rank:4, district:"Aurangabad", score:48, grade:"C" },
  { rank:5, district:"Nashik",     score:42, grade:"C" },
  { rank:6, district:"Amravati",   score:31, grade:"D" },
];

const MAH_CENTER = [19.0, 75.7];

// ── ANIMATED COUNTER HOOK ─────────────────────────────────────────────────────
function useAnimatedCounter(target, active, duration = 1400) {
  const [val, setVal] = useState(0);
  const rafRef = useRef(null);
  useEffect(() => {
    if (!active) return;
    const t0 = performance.now();
    const tick = (now) => {
      const p = Math.min((now - t0) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 4);
      setVal(Math.round(eased * target));
      if (p < 1) rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [active, target, duration]);
  return val;
}

// ── PERIOD BUTTON ─────────────────────────────────────────────────────────────
function PeriodBtn({ val, active, onChange }) {
  return (
    <button onClick={() => onChange(val)} className="ir-period-btn" data-active={active}>
      {val}
    </button>
  );
}

// ── GAUGE SVG ─────────────────────────────────────────────────────────────────
function Gauge({ score, label, color }) {
  const c = Math.min(Math.max(score, 0), 99.9);
  const a = Math.PI * (1 - c / 100);
  const x = (100 + 80 * Math.cos(a)).toFixed(2);
  const y = (100 - 80 * Math.sin(a)).toFixed(2);
  return (
    <svg width="170" height="110" viewBox="0 0 200 120">
      <path d="M 20 100 A 80 80 0 0 1 100 20 A 80 80 0 0 1 180 100"
        fill="none" stroke="rgba(0,0,0,0.08)" strokeWidth={16} strokeLinecap="round" />
      <path d={`M 20 100 A 80 80 0 0 1 ${x} ${y}`}
        fill="none" stroke={color} strokeWidth={16} strokeLinecap="round" />
      <circle cx="100" cy="100" r="52" fill="white" />
      <text x="100" y="96" textAnchor="middle" fontSize="26" fontWeight="900" fill={color}>{score}</text>
      <text x="100" y="112" textAnchor="middle" fontSize="9.5" fill="#888" fontWeight="600" letterSpacing="0.5">{label.toUpperCase()}</text>
    </svg>
  );
}

// ── STAT CARD ─────────────────────────────────────────────────────────────────
function StatCard({ label, value, unit, color, active, icon }) {
  const displayed = useAnimatedCounter(value, active);
  const riskLabel = color === HIGH ? "HIGH RISK" : color === MED ? "MODERATE" : "LOW RISK";
  return (
    <div className="ir-stat-card" style={{ borderTop:`4px solid ${color}` }}>
      <div className="ir-stat-icon" style={{ background:`${color}18`, color }}>{icon}</div>
      <div style={{ fontSize:34, fontWeight:900, color, lineHeight:1, marginTop:8 }}>
        {displayed}
        <span style={{ fontSize:14, fontWeight:500, color:"#bbb", marginLeft:3 }}>{unit}</span>
      </div>
      <div style={{ fontSize:11, color:"#777", marginTop:5, fontWeight:700, letterSpacing:"0.4px", textTransform:"uppercase" }}>{label}</div>
      <div style={{ margin:"10px 0 4px", height:4, background:"rgba(0,0,0,0.06)", borderRadius:99, overflow:"hidden" }}>
        <div className="ir-stat-bar" style={{ width: active ? `${Math.min(value, 100)}%` : "0%", background:`linear-gradient(90deg, ${color}aa, ${color})` }} />
      </div>
      <div style={{ fontSize:10, fontWeight:800, color, letterSpacing:"0.5px" }}>{riskLabel}</div>
    </div>
  );
}

// ── SECTION CARD ──────────────────────────────────────────────────────────────
function SectionCard({ title, id, badge, risk, collapsed, onToggle, children }) {
  const riskColor = risk === "HIGH" ? HIGH : risk === "MED" ? MED : LOW;
  return (
    <div id={id} className="ir-section reveal">
      <div className="ir-section-header" onClick={onToggle}>
        <div style={{ display:"flex", alignItems:"center", gap:12 }}>
          <div className="ir-section-badge">{badge}</div>
          <span className="ir-section-title">{title}</span>
          {risk && (
            <span className="ir-risk-pill" style={{ background:`${riskColor}18`, color:riskColor, borderColor:`${riskColor}40` }}>
              {risk === "HIGH" ? "⚠ HIGH RISK" : risk === "MED" ? "◆ MODERATE" : "✓ LOW RISK"}
            </span>
          )}
        </div>
        <span className="ir-chevron" style={{ transform: collapsed ? "rotate(0deg)" : "rotate(180deg)" }}>▼</span>
      </div>
      <div style={{ maxHeight: collapsed ? 0 : 9999, overflow:"hidden", transition:"max-height 0.45s cubic-bezier(0.4,0,0.2,1)" }}>
        <div style={{ padding:"26px 32px" }}>{children}</div>
      </div>
    </div>
  );
}

// ── SHARED STYLES ─────────────────────────────────────────────────────────────
const sLabel  = { fontSize:12, fontWeight:700, color:GREEN, marginBottom:10, textTransform:"uppercase", letterSpacing:"0.5px" };
const insight = { background:"rgba(45,74,62,0.055)", border:"1px solid rgba(45,74,62,0.14)", borderRadius:10, padding:"14px 18px", marginTop:18, fontSize:13, color:"#444", lineHeight:1.7 };
const tbl     = { width:"100%", borderCollapse:"collapse", fontSize:13 };
const th      = { padding:"11px 14px", textAlign:"left", fontWeight:700, fontSize:11, letterSpacing:"0.4px", textTransform:"uppercase" };
const td      = { padding:"12px 14px", color:"#4a5568" };

// ── PAGE ──────────────────────────────────────────────────────────────────────
export default function IntelligenceReport() {
  const [sel, setSel]             = useState("All");
  const [period, setPeriod]       = useState("30d");
  const [nregaMode, setNregaMode] = useState("all");
  const [collapsed, setCollapsed] = useState({});
  const [loading, setLoading]     = useState(true);
  const [loadPct, setLoadPct]     = useState(0);
  const [loadText, setLoadText]   = useState("Initialising systems...");
  const [statsVisible, setStatsVisible] = useState(false);
  const [clock, setClock]         = useState(() => new Date().toLocaleTimeString("en-IN", { hour:"2-digit", minute:"2-digit", hour12:true }));
  const statBarRef = useRef(null);

  const toggle = key => setCollapsed(p => ({ ...p, [key]: !p[key] }));

  const filtered  = sel === "All" ? DISTRICTS : DISTRICTS.filter(d => d.name === sel);
  const radarDist = sel === "All" ? "Pune" : sel;
  const nregaData = nregaMode === "recent" ? NREGA_DATA.slice(-3) : NREGA_DATA;
  const climData  = CLIMATE_DATA[period];

  const avg = key => Math.round(DISTRICTS.reduce((a, d) => a + d[key], 0) / DISTRICTS.length);

  const STATS = [
    { label:"Land Fragmentation", value:avg("fragIndex"),  unit:"/100", color:fragColor(avg("fragIndex")),    icon:"🌱" },
    { label:"Irrigation Coverage", value:avg("irrigPct"),  unit:"%",    color:irrigColor(avg("irrigPct")),    icon:"💧" },
    { label:"Post-Harvest Loss",   value:avg("phLoss"),    unit:"%",    color:HIGH,                           icon:"📦" },
    { label:"Export Risk Index",   value:avg("exportRisk"),unit:"/100", color:exportColor(avg("exportRisk")), icon:"🚢" },
    { label:"Distress Index",      value:avg("distress"),  unit:"/100", color:distressColor(avg("distress")), icon:"🆘" },
    { label:"Climate Shock",       value:avg("climate"),   unit:"/100", color:climateColor(avg("climate")),   icon:"🌡" },
  ];

  const highAlerts = DISTRICTS.filter(d => d.distress > 65 || d.exportRisk > 70 || d.climate > 70);

  // Live clock
  useEffect(() => {
    const fmt = () => new Date().toLocaleTimeString("en-IN", { hour:"2-digit", minute:"2-digit", hour12:true });
    const id = setInterval(() => setClock(fmt()), 30000);
    return () => clearInterval(id);
  }, []);

  // Loading sequence
  useEffect(() => {
    const TEXTS = [
      "Fetching district profiles...",
      "Running climate models...",
      "Computing risk indices...",
      "Generating intelligence report...",
    ];
    let i = 0;
    const interval = setInterval(() => {
      i = Math.min(i + 1, TEXTS.length - 1);
      setLoadText(TEXTS[i]);
      setLoadPct(p => Math.min(p + 26, 100));
    }, 380);
    const done = setTimeout(() => {
      clearInterval(interval);
      setLoadPct(100);
      setTimeout(() => setLoading(false), 250);
    }, 1600);
    return () => { clearInterval(interval); clearTimeout(done); };
  }, []);

  // Scroll reveal after loading
  useEffect(() => {
    if (loading) return;
    const observer = new IntersectionObserver(
      (entries) => entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add("in"); observer.unobserve(e.target); } }),
      { threshold: 0.08 }
    );
    document.querySelectorAll(".reveal").forEach(el => observer.observe(el));
    return () => observer.disconnect();
  }, [loading]);

  // Stat counter trigger
  useEffect(() => {
    if (loading) return;
    const el = statBarRef.current;
    if (!el) return;
    const obs = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) { setStatsVisible(true); obs.disconnect(); }
    }, { threshold: 0.4 });
    obs.observe(el);
    return () => obs.disconnect();
  }, [loading]);

  return (
    <div style={{ background:BG, minHeight:"100vh", paddingBottom:80 }}>

      {/* ── LOADING OVERLAY ── */}
      {loading && (
        <div className="ir-loader">
          <div style={{ textAlign:"center" }}>
            <div style={{ fontSize:72, marginBottom:16, animation:"ir-bounce 1s ease infinite" }}>🌾</div>
            <div style={{ color:"#fff", fontSize:30, fontWeight:900, letterSpacing:"-0.5px" }}>KisanSetu</div>
            <div style={{ color:"rgba(255,255,255,0.5)", fontSize:14, marginTop:4, letterSpacing:"2px", textTransform:"uppercase" }}>Intelligence Platform</div>
            <div className="ir-loader-bar-track">
              <div className="ir-loader-bar-fill" style={{ width:`${loadPct}%` }} />
            </div>
            <div style={{ color:"rgba(255,255,255,0.55)", fontSize:13, marginTop:14, minHeight:20 }}>{loadText}</div>
            <div style={{ color:"rgba(255,255,255,0.25)", fontSize:28, fontWeight:900, marginTop:6 }}>{loadPct}%</div>
          </div>
        </div>
      )}

      {/* ── HEADER ── */}
      <div className="ir-header">
        <div style={{ display:"flex", alignItems:"center", gap:14 }}>
          <div className="ir-header-logo">🌾</div>
          <div>
            <div style={{ color:"#fff", fontSize:22, fontWeight:900, letterSpacing:"-0.3px", lineHeight:1.1 }}>Dhurandhar Report</div>
            <div style={{ color:"rgba(255,255,255,0.55)", fontSize:12, marginTop:3, letterSpacing:"0.5px" }}>
              Maharashtra Agricultural Intelligence • {clock}
            </div>
          </div>
        </div>
        <div style={{ display:"flex", gap:10, alignItems:"center" }}>
          <div className="ir-period-toggle">
            {["30d","60d"].map(p => (
              <button key={p} onClick={() => setPeriod(p)} className="ir-period-btn" data-active={period === p}>{p}</button>
            ))}
          </div>
          <button onClick={() => window.print()} className="ir-print-btn no-print">🖨 Print PDF</button>
        </div>
      </div>

      {/* ── ALERT BANNER ── */}
      {highAlerts.length > 0 && !loading && (
        <div className="ir-alert-banner reveal">
          <div style={{ display:"flex", alignItems:"center", gap:10, flexWrap:"wrap" }}>
            <span className="ir-alert-badge">⚠ CRITICAL ALERT</span>
            <span style={{ fontSize:13, fontWeight:600 }}>
              {highAlerts.map(d => d.name).join(" · ")} — Multiple HIGH-risk indicators detected requiring immediate attention
            </span>
          </div>
          <div style={{ display:"flex", gap:6 }}>
            {highAlerts.map(d => (
              <span key={d.name} className="ir-alert-chip">{d.name}</span>
            ))}
          </div>
        </div>
      )}

      {/* ── DISTRICT CHIPS ── */}
      {!loading && (
        <div className="ir-chip-bar reveal">
          {["All", ...DISTRICTS.map(d => d.name)].map(n => (
            <button key={n} onClick={() => setSel(n)}
              className="ir-chip"
              data-active={sel === n}
              style={sel === n ? { background:GREEN, color:"#fff", borderColor:GREEN } : {}}>
              {n !== "All" && <span className="ir-chip-dot" style={{ background: sel===n ? "#fff" : DC[n] }} />}
              {n === "All" ? "🗺 All Districts" : n}
            </button>
          ))}
        </div>
      )}

      {/* ── STAT BAR ── */}
      {!loading && (
        <div className="ir-stat-grid reveal" ref={statBarRef}>
          {STATS.map(s => (
            <StatCard key={s.label} {...s} active={statsVisible} />
          ))}
        </div>
      )}

      {/* ── SECTION DIVIDER ── */}
      {!loading && (
        <div style={{ padding:"8px 48px 4px", display:"flex", alignItems:"center", gap:12 }}>
          <div style={{ height:2, flex:1, background:"rgba(45,74,62,0.1)", borderRadius:99 }} />
          <span style={{ fontSize:11, fontWeight:800, color:"rgba(45,74,62,0.4)", letterSpacing:"2px", textTransform:"uppercase" }}>Intelligence Sections</span>
          <div style={{ height:2, flex:1, background:"rgba(45,74,62,0.1)", borderRadius:99 }} />
        </div>
      )}

      {/* ── SECTIONS ── */}
      {!loading && (
        <div style={{ padding:"12px 48px 0" }}>

          {/* S1: LAND FRAGMENTATION */}
          <SectionCard title="Land Fragmentation Index" id="frag" badge="01" risk="HIGH"
            collapsed={collapsed.frag} onToggle={() => toggle("frag")}>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:28 }}>
              <div>
                <div style={sLabel}>Fragmentation Risk Map</div>
                <div className="ir-map-wrap">
                  <MapContainer center={MAH_CENTER} zoom={6} style={{ height:"100%", borderRadius:10 }} scrollWheelZoom={false}>
                    <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; OSM" />
                    {filtered.map(d => (
                      <CircleMarker key={d.name} center={[d.lat,d.lng]} radius={d.fragIndex/5.5}
                        color={fragColor(d.fragIndex)} fillColor={fragColor(d.fragIndex)} fillOpacity={0.7} weight={2}>
                        <LTip permanent={false}><strong>{d.name}</strong><br/>Fragmentation: {d.fragIndex}/100</LTip>
                      </CircleMarker>
                    ))}
                  </MapContainer>
                </div>
              </div>
              <div>
                <div style={sLabel}>Index by District</div>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart layout="vertical" data={filtered} margin={{ left:10, right:20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
                    <XAxis type="number" domain={[0,100]} tick={{ fontSize:11, fill:"#888" }} />
                    <YAxis type="category" dataKey="name" width={90} tick={{ fontSize:12, fill:"#555", fontWeight:600 }} />
                    <RTip contentStyle={{ borderRadius:10, border:"none", boxShadow:"0 4px 20px rgba(0,0,0,0.12)", fontSize:12 }} />
                    <Bar dataKey="fragIndex" name="Frag Index" radius={[0,6,6,0]} maxBarSize={28}>
                      {filtered.map(d => <Cell key={d.name} fill={fragColor(d.fragIndex)} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div style={insight}>
              <strong style={{ color:GREEN }}>Key Finding:</strong> Nashik (85) and Amravati (78) show critical fragmentation — farms under 1.2 ha average. Kolhapur (43) has the most consolidated landholdings, correlating directly with higher productivity and lower distress scores.
            </div>
          </SectionCard>

          {/* S2: IRRIGATION */}
          <SectionCard title="Irrigation Efficiency" id="irrig" badge="02" risk="MED"
            collapsed={collapsed.irrig} onToggle={() => toggle("irrig")}>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:28 }}>
              <div>
                <div style={sLabel}>Profile — {radarDist}</div>
                <ResponsiveContainer width="100%" height={290}>
                  <RadarChart data={IRRIG_RADAR[radarDist]}>
                    <PolarGrid stroke="rgba(45,74,62,0.12)" />
                    <PolarAngleAxis dataKey="s" tick={{ fontSize:12, fill:"#555", fontWeight:600 }} />
                    <PolarRadiusAxis domain={[0,100]} tick={false} axisLine={false} />
                    <Radar name={radarDist} dataKey="v" stroke={GREEN} fill={GREEN} fillOpacity={0.25} strokeWidth={2} />
                    <RTip contentStyle={{ borderRadius:10, border:"none", boxShadow:"0 4px 20px rgba(0,0,0,0.12)", fontSize:12 }} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
              <div>
                <div style={sLabel}>Coverage % by District</div>
                <ResponsiveContainer width="100%" height={290}>
                  <BarChart layout="vertical" data={filtered} margin={{ left:10, right:20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
                    <XAxis type="number" domain={[0,100]} tick={{ fontSize:11, fill:"#888" }} />
                    <YAxis type="category" dataKey="name" width={90} tick={{ fontSize:12, fill:"#555", fontWeight:600 }} />
                    <RTip contentStyle={{ borderRadius:10, border:"none", boxShadow:"0 4px 20px rgba(0,0,0,0.12)", fontSize:12 }} />
                    <Bar dataKey="irrigPct" name="Coverage %" radius={[0,6,6,0]} maxBarSize={28}>
                      {filtered.map(d => <Cell key={d.name} fill={irrigColor(d.irrigPct)} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            <table style={{ ...tbl, marginTop:22 }}>
              <thead>
                <tr style={{ background:GREEN }}>
                  {["District","Coverage %","Drip %","Canal %","Groundwater %","Efficiency"].map(h => (
                    <th key={h} style={{ ...th, color:"rgba(255,255,255,0.85)" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((d,i) => {
                  const r = IRRIG_RADAR[d.name];
                  return (
                    <tr key={d.name} className="ir-table-row" style={{ background: i%2 ? "#fafaf8" : "#fff" }}>
                      <td style={{ ...td, fontWeight:700, color:GREEN }}>{d.name}</td>
                      {r.map(x => (
                        <td key={x.s} style={td}>
                          <span className="ir-val-pill" style={{ background:`${irrigColor(x.v)}15`, color:irrigColor(x.v) }}>{x.v}%</span>
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </SectionCard>

          {/* S3: POST-HARVEST LOSS */}
          <SectionCard title="Post-Harvest Loss Analysis" id="phLoss" badge="03" risk="HIGH"
            collapsed={collapsed.phLoss} onToggle={() => toggle("phLoss")}>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:28 }}>
              <div>
                <div style={sLabel}>Loss Intensity Map</div>
                <div className="ir-map-wrap">
                  <MapContainer center={MAH_CENTER} zoom={6} style={{ height:"100%", borderRadius:10 }} scrollWheelZoom={false}>
                    <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; OSM" />
                    {filtered.map(d => (
                      <CircleMarker key={d.name} center={[d.lat,d.lng]} radius={d.phLoss * 0.75}
                        color={HIGH} fillColor={HIGH} fillOpacity={0.2} weight={1.5}>
                        <LTip><strong>{d.name}</strong><br/>Loss: {d.phLoss}%</LTip>
                      </CircleMarker>
                    ))}
                  </MapContainer>
                </div>
              </div>
              <div>
                <div style={sLabel}>Breakdown by Stage</div>
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie data={PH_PIE} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={88} innerRadius={44}
                      label={({ value }) => `${value}%`} labelLine={false} paddingAngle={3}>
                      {PH_PIE.map((e,i) => <Cell key={i} fill={PH_COLORS[i]} />)}
                    </Pie>
                    <RTip contentStyle={{ borderRadius:10, border:"none", boxShadow:"0 4px 20px rgba(0,0,0,0.12)", fontSize:12 }} />
                    <Legend iconType="circle" iconSize={9} wrapperStyle={{ fontSize:12 }} />
                  </PieChart>
                </ResponsiveContainer>
                <div style={insight}>
                  <strong style={{ color:HIGH }}>⚠ Critical Finding:</strong> Storage infrastructure gaps account for 38% of all losses. Cold-chain investment in Amravati (48% loss rate) could save an estimated <strong>₹420 Cr annually</strong>.
                </div>
              </div>
            </div>
          </SectionCard>

          {/* S4: EXPORT RISK */}
          <SectionCard title="Export Risk Assessment" id="export" badge="04" risk="HIGH"
            collapsed={collapsed.export} onToggle={() => toggle("export")}>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:28 }}>
              <div>
                <div style={sLabel}>Risk Index vs Distress (threshold: 65)</div>
                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart data={filtered} margin={{ left:10, right:20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
                    <XAxis dataKey="name" tick={{ fontSize:11, fill:"#888" }} />
                    <YAxis domain={[0,100]} tick={{ fontSize:11, fill:"#888" }} />
                    <RTip contentStyle={{ borderRadius:10, border:"none", boxShadow:"0 4px 20px rgba(0,0,0,0.12)", fontSize:12 }} />
                    <Legend iconSize={9} wrapperStyle={{ fontSize:12 }} />
                    <Bar dataKey="exportRisk" name="Export Risk" radius={[5,5,0,0]} maxBarSize={36}>
                      {filtered.map(d => <Cell key={d.name} fill={exportColor(d.exportRisk)} />)}
                    </Bar>
                    <Line type="monotone" dataKey="distress" name="Distress Index" stroke="#8B5CF6" strokeWidth={2.5} dot={{ r:4, fill:"#8B5CF6" }} />
                    <ReferenceLine y={65} stroke={HIGH} strokeDasharray="5 3"
                      label={{ value:"HIGH RISK ZONE", fill:HIGH, fontSize:10, fontWeight:700 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
              <div>
                <div style={sLabel}>Risk Gauges — Top 3</div>
                <div style={{ display:"flex", gap:8, justifyContent:"center", paddingTop:8, flexWrap:"wrap" }}>
                  {[...DISTRICTS].sort((a,b) => b.exportRisk - a.exportRisk).slice(0,3).map(d => (
                    <div key={d.name} className="ir-gauge-card">
                      <div style={{ fontSize:13, fontWeight:800, color:GREEN, marginBottom:2 }}>{d.name}</div>
                      <Gauge score={d.exportRisk} label="Risk Score" color={exportColor(d.exportRisk)} />
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div style={{ display:"flex", gap:14, marginTop:22, flexWrap:"wrap" }}>
              {filtered.filter(d => d.exportRisk > 65).map(d => (
                <div key={d.name} className="ir-risk-card">
                  <div style={{ color:HIGH, fontWeight:900, fontSize:14 }}>⚠ {d.name}</div>
                  <div style={{ fontSize:13, color:"#555", marginTop:6 }}>Export Risk: <strong>{d.exportRisk}/100</strong></div>
                  <div style={{ fontSize:11, color:"#888", marginTop:6, lineHeight:1.5 }}>Diversify to domestic markets; prioritise cold-chain subsidy.</div>
                </div>
              ))}
              {filtered.filter(d => d.exportRisk > 65).length === 0 && (
                <div style={{ color:LOW, fontWeight:700, padding:14, fontSize:14 }}>✓ No HIGH-risk districts in current filter.</div>
              )}
            </div>
          </SectionCard>

          {/* S5: FARMER DISTRESS */}
          <SectionCard title="Farmer Distress Indicators" id="distress" badge="05" risk="HIGH"
            collapsed={collapsed.distress} onToggle={() => toggle("distress")}>
            <div style={{ display:"flex", gap:10, marginBottom:20, alignItems:"center" }}>
              <span style={{ fontSize:12, fontWeight:700, color:"#888", textTransform:"uppercase", letterSpacing:"0.5px" }}>NREGA Period:</span>
              {[["all","All 6 Months"],["recent","Recent 3 Months"]].map(([v,l]) => (
                <button key={v} onClick={() => setNregaMode(v)} className="ir-period-btn" data-active={nregaMode === v}>{l}</button>
              ))}
            </div>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:28 }}>
              <div>
                <div style={sLabel}>NREGA Workers Enrolled</div>
                <ResponsiveContainer width="100%" height={260}>
                  <AreaChart data={nregaData} margin={{ left:10, right:10 }}>
                    <defs>
                      <linearGradient id="distressGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor={MED} stopOpacity={0.4} />
                        <stop offset="95%" stopColor={MED} stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
                    <XAxis dataKey="month" tick={{ fontSize:11, fill:"#888" }} />
                    <YAxis tick={{ fontSize:11, fill:"#888" }} />
                    <RTip contentStyle={{ borderRadius:10, border:"none", boxShadow:"0 4px 20px rgba(0,0,0,0.12)", fontSize:12 }} />
                    <Area type="monotone" dataKey="workers" name="Workers" stroke={MED} fill="url(#distressGrad)" strokeWidth={2.5} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
              <div>
                <div style={sLabel}>Distress Index by District</div>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart layout="vertical" data={filtered} margin={{ left:10, right:20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
                    <XAxis type="number" domain={[0,100]} tick={{ fontSize:11, fill:"#888" }} />
                    <YAxis type="category" dataKey="name" width={90} tick={{ fontSize:12, fill:"#555", fontWeight:600 }} />
                    <RTip contentStyle={{ borderRadius:10, border:"none", boxShadow:"0 4px 20px rgba(0,0,0,0.12)", fontSize:12 }} />
                    <Bar dataKey="distress" name="Distress" radius={[0,6,6,0]} maxBarSize={28}>
                      {filtered.map(d => <Cell key={d.name} fill={distressColor(d.distress)} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            <table style={{ ...tbl, marginTop:22 }}>
              <thead>
                <tr style={{ background:GREEN }}>
                  {["District","Distress Index","NREGA Workers","Avg Days","Alert Level"].map(h => (
                    <th key={h} style={{ ...th, color:"rgba(255,255,255,0.85)" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((d,i) => (
                  <tr key={d.name} className="ir-table-row" style={{ background: i%2 ? "#fafaf8" : "#fff" }}>
                    <td style={{ ...td, fontWeight:700, color:GREEN }}>{d.name}</td>
                    <td style={td}>
                      <span className="ir-val-pill" style={{ background:`${distressColor(d.distress)}15`, color:distressColor(d.distress), fontWeight:800, fontSize:14 }}>{d.distress}</span>
                    </td>
                    <td style={td}>{Math.round(31400 * d.distress / 81).toLocaleString()}</td>
                    <td style={td}>{(15.7 * d.distress / 81).toFixed(1)}</td>
                    <td style={td}>
                      <span className="ir-alert-level" style={{ background:`${distressColor(d.distress)}15`, color:distressColor(d.distress) }}>
                        {d.distress > 65 ? "🔴 HIGH" : d.distress > 45 ? "🟡 MEDIUM" : "🟢 LOW"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </SectionCard>

          {/* S6: CLIMATE SHOCK */}
          <SectionCard title="Climate Shock Risk" id="climate" badge="06" risk="MED"
            collapsed={collapsed.climate} onToggle={() => toggle("climate")}>
            <div style={{ display:"flex", gap:10, marginBottom:20, alignItems:"center" }}>
              <span style={{ fontSize:12, fontWeight:700, color:"#888", textTransform:"uppercase", letterSpacing:"0.5px" }}>Period:</span>
              <PeriodBtn val="30d" active={period === "30d"} onChange={setPeriod} />
              <PeriodBtn val="60d" active={period === "60d"} onChange={setPeriod} />
            </div>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:28 }}>
              <div>
                <div style={sLabel}>Rainfall & Temperature ({period})</div>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={climData} margin={{ left:10, right:30 }}>
                    <defs>
                      <linearGradient id="rainGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor="#3B82F6" stopOpacity={0.15} />
                        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
                    <XAxis dataKey="week" tick={{ fontSize:10, fill:"#888" }} />
                    <YAxis yAxisId="L" tick={{ fontSize:11, fill:"#888" }} label={{ value:"mm", angle:-90, position:"insideLeft", fontSize:10, fill:"#aaa" }} />
                    <YAxis yAxisId="R" orientation="right" domain={[34,42]} tick={{ fontSize:11, fill:"#888" }} label={{ value:"°C", angle:90, position:"insideRight", fontSize:10, fill:"#aaa" }} />
                    <RTip contentStyle={{ borderRadius:10, border:"none", boxShadow:"0 4px 20px rgba(0,0,0,0.12)", fontSize:12 }} />
                    <Legend iconSize={9} wrapperStyle={{ fontSize:12 }} />
                    <ReferenceArea yAxisId="R" y1={39} y2={42} fill={HIGH} fillOpacity={0.07}
                      label={{ value:"Heat stress", position:"insideTopRight", fill:HIGH, fontSize:10 }} />
                    <Line yAxisId="L" type="monotone" dataKey="rain" name="Rainfall (mm)" stroke="#3B82F6" strokeWidth={2.5} dot={{ r:4, fill:"#3B82F6" }} activeDot={{ r:6 }} />
                    <Line yAxisId="R" type="monotone" dataKey="temp" name="Temp (°C)" stroke={HIGH} strokeWidth={2.5} strokeDasharray="4 2" dot={{ r:4, fill:HIGH }} activeDot={{ r:6 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div>
                <div style={sLabel}>Intensity Map</div>
                <div className="ir-map-wrap">
                  <MapContainer center={MAH_CENTER} zoom={6} style={{ height:"100%", borderRadius:10 }} scrollWheelZoom={false}>
                    <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; OSM" />
                    {filtered.map(d => (
                      <CircleMarker key={d.name} center={[d.lat,d.lng]} radius={d.climate/5}
                        color={climateColor(d.climate)} fillColor={climateColor(d.climate)} fillOpacity={0.65} weight={2}>
                        <LTip><strong>{d.name}</strong><br/>Climate Shock: {d.climate}/100</LTip>
                      </CircleMarker>
                    ))}
                  </MapContainer>
                </div>
              </div>
            </div>
            <div style={{ display:"flex", gap:16, marginTop:22, flexWrap:"wrap" }}>
              {[
                { p:"30d", rain:"18.5 mm avg", temp:"38.6°C avg", events:"2 heat stress weeks", weeks:6 },
                { p:"60d", rain:"12.8 mm avg", temp:"37.9°C avg", events:"3 heat stress weeks", weeks:10 },
              ].map(c => (
                <div key={c.p} className="ir-climate-card" data-active={period === c.p}
                  style={{ borderColor: period===c.p ? GREEN : "rgba(45,74,62,0.12)", background: period===c.p ? "rgba(45,74,62,0.05)" : "#fff" }}>
                  <div style={{ fontWeight:900, color:GREEN, fontSize:18, marginBottom:10 }}>{c.p} Window</div>
                  <div style={{ fontSize:13, color:"#3B82F6", fontWeight:600 }}>🌧 {c.rain}</div>
                  <div style={{ fontSize:13, color:HIGH, marginTop:6, fontWeight:600 }}>🌡 {c.temp}</div>
                  <div style={{ fontSize:13, color:MED, marginTop:6, fontWeight:600 }}>⚡ {c.events}</div>
                  {period === c.p && <div style={{ marginTop:10, fontSize:10, fontWeight:800, color:GREEN, textTransform:"uppercase", letterSpacing:"1px" }}>● Active</div>}
                </div>
              ))}
            </div>
          </SectionCard>

          {/* S7: COMPOSITE SUMMARY */}
          <SectionCard title="Composite Intelligence Score" id="composite" badge="07" risk={null}
            collapsed={collapsed.composite} onToggle={() => toggle("composite")}>
            <div className="ir-radar-grid">
              {DISTRICTS.map(d => {
                const profile = [
                  { s:"Land",    v: 100 - d.fragIndex },
                  { s:"Water",   v: d.irrigPct },
                  { s:"PH",      v: 100 - d.phLoss },
                  { s:"Export",  v: 100 - d.exportRisk },
                  { s:"Welfare", v: 100 - d.distress },
                  { s:"Climate", v: 100 - d.climate },
                ];
                const cs = COMPOSITE.find(c => c.district === d.name);
                return (
                  <div key={d.name} className="ir-district-radar">
                    <div style={{ fontSize:14, fontWeight:900, color:GREEN }}>{d.name}</div>
                    <div style={{ fontSize:12, fontWeight:800, color:gradeColor[cs?.grade], marginBottom:4 }}>
                      Score: {cs?.score} &nbsp;
                      <span style={{ background:`${gradeColor[cs?.grade]}20`, padding:"1px 8px", borderRadius:99, fontSize:11 }}>Grade {cs?.grade}</span>
                    </div>
                    <ResponsiveContainer width="100%" height={165}>
                      <RadarChart data={profile}>
                        <PolarGrid stroke="rgba(0,0,0,0.08)" />
                        <PolarAngleAxis dataKey="s" tick={{ fontSize:9, fill:"#777" }} />
                        <PolarRadiusAxis domain={[0,100]} tick={false} axisLine={false} />
                        <Radar dataKey="v" stroke={DC[d.name] || GREEN} fill={DC[d.name] || GREEN} fillOpacity={0.3} strokeWidth={2} />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                );
              })}
            </div>

            <table style={{ ...tbl, marginTop:28 }}>
              <thead>
                <tr style={{ background:GREEN }}>
                  {["Rank","District","Score","Grade","Land","Water","PH","Export","Welfare","Climate"].map(h => (
                    <th key={h} style={{ ...th, color:"rgba(255,255,255,0.85)" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {COMPOSITE.map((c,i) => {
                  const d = DISTRICTS.find(x => x.name === c.district);
                  return (
                    <tr key={c.district} className="ir-table-row" style={{ background: i%2 ? "#fafaf8" : "#fff" }}>
                      <td style={{ ...td, fontWeight:900, color:GREEN, fontSize:16 }}>#{c.rank}</td>
                      <td style={{ ...td, fontWeight:700 }}>{c.district}</td>
                      <td style={td}>
                        <span style={{ fontSize:20, fontWeight:900, color:gradeColor[c.grade] }}>{c.score}</span>
                      </td>
                      <td style={td}>
                        <span className="ir-grade-badge" style={{ background:`${gradeColor[c.grade]}20`, color:gradeColor[c.grade] }}>{c.grade}</span>
                      </td>
                      <td style={td}>{100 - d.fragIndex}</td>
                      <td style={td}>{d.irrigPct}</td>
                      <td style={td}>{100 - d.phLoss}</td>
                      <td style={td}>{100 - d.exportRisk}</td>
                      <td style={td}>{100 - d.distress}</td>
                      <td style={td}>{100 - d.climate}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </SectionCard>

        </div>
      )}

      {/* ── CSS ── */}
      <style>{`
        /* ── LOADER ── */
        .ir-loader {
          position: fixed; inset: 0; background: ${GREEN};
          z-index: 9999; display: flex; align-items: center; justify-content: center;
        }
        .ir-loader-bar-track {
          width: 300px; height: 5px; background: rgba(255,255,255,0.12);
          border-radius: 99px; overflow: hidden; margin: 20px auto 0;
        }
        .ir-loader-bar-fill {
          height: 100%; background: linear-gradient(90deg, #22c55e, #10b981);
          border-radius: 99px; transition: width 0.38s cubic-bezier(0.4,0,0.2,1);
        }
        @keyframes ir-bounce {
          0%,100% { transform: translateY(0); }
          50%      { transform: translateY(-10px); }
        }

        /* ── HEADER ── */
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

        /* ── PERIOD TOGGLE ── */
        .ir-period-toggle {
          display: flex; background: rgba(255,255,255,0.1);
          border-radius: 99px; padding: 3px; gap: 2px;
        }
        .ir-period-btn {
          padding: 7px 18px; border: none; border-radius: 99px;
          cursor: pointer; font-weight: 700; font-size: 12px;
          transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
          background: transparent; color: rgba(255,255,255,0.65);
          letter-spacing: 0.3px;
        }
        .ir-period-btn[data-active="true"] {
          background: #fff; color: ${GREEN}; box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }
        .ir-print-btn {
          padding: 9px 18px; background: rgba(255,255,255,0.12);
          color: #fff; border: 1px solid rgba(255,255,255,0.25);
          border-radius: 10px; cursor: pointer; font-weight: 700; font-size: 13px;
          transition: all 0.2s;
        }
        .ir-print-btn:hover { background: rgba(255,255,255,0.2); }
        .ir-print-btn:active { transform: scale(0.96); }

        /* ── ALERT BANNER ── */
        .ir-alert-banner {
          background: linear-gradient(90deg, rgba(192,57,43,0.07) 0%, rgba(192,57,43,0.04) 100%);
          border-bottom: 2px solid rgba(192,57,43,0.2);
          padding: 12px 48px; display: flex; align-items: center;
          justify-content: space-between; flex-wrap: wrap; gap: 10px;
          animation: ir-slidedown 0.4s ease;
        }
        @keyframes ir-slidedown {
          from { transform: translateY(-100%); opacity:0; }
          to   { transform: translateY(0); opacity:1; }
        }
        .ir-alert-badge {
          background: ${HIGH}; color: #fff; padding: 3px 10px;
          border-radius: 5px; font-size: 10px; font-weight: 900;
          letter-spacing: 0.5px; animation: ir-pulse 1.6s ease infinite;
        }
        .ir-alert-chip {
          background: rgba(192,57,43,0.1); color: ${HIGH}; border: 1px solid rgba(192,57,43,0.3);
          padding: 3px 10px; border-radius: 99px; font-size: 11px; font-weight: 700;
        }
        @keyframes ir-pulse { 0%,100%{opacity:1} 50%{opacity:0.65} }

        /* ── DISTRICT CHIPS ── */
        .ir-chip-bar {
          display: flex; gap: 8px; padding: 16px 48px;
          flex-wrap: wrap; align-items: center;
        }
        .ir-chip {
          padding: 7px 16px; border-radius: 99px;
          border: 2px solid rgba(45,74,62,0.2);
          background: #fff; color: ${GREEN};
          cursor: pointer; font-size: 13px; font-weight: 700;
          transition: all 0.22s cubic-bezier(0.4,0,0.2,1);
          display: flex; align-items: center; gap: 7px;
        }
        .ir-chip:hover { transform: translateY(-2px); box-shadow: 0 4px 14px rgba(45,74,62,0.15); }
        .ir-chip[data-active="true"] { box-shadow: 0 4px 16px rgba(45,74,62,0.25); }
        .ir-chip-dot {
          width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0;
        }

        /* ── STAT CARDS ── */
        .ir-stat-grid {
          display: flex; gap: 14px; padding: 0 48px 20px; flex-wrap: wrap;
        }
        .ir-stat-card {
          flex: 1 1 140px; background: #fff; border-radius: 14px;
          padding: 18px 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.07);
          transition: all 0.28s cubic-bezier(0.4,0,0.2,1); cursor: default;
        }
        .ir-stat-card:hover {
          transform: translateY(-5px) scale(1.02);
          box-shadow: 0 14px 40px rgba(45,74,62,0.15);
        }
        .ir-stat-icon {
          width: 36px; height: 36px; border-radius: 10px;
          display: flex; align-items: center; justify-content: center; font-size: 18px;
        }
        .ir-stat-bar {
          height: 100%; border-radius: 99px;
          transition: width 1.6s cubic-bezier(0.4,0,0.2,1);
        }

        /* ── SECTION CARDS ── */
        .ir-section {
          background: #fff; border-radius: 16px; margin-bottom: 20px;
          box-shadow: 0 4px 24px rgba(45,74,62,0.07);
          border: 1px solid rgba(45,74,62,0.07);
          overflow: hidden;
          transition: box-shadow 0.25s ease;
        }
        .ir-section:hover { box-shadow: 0 8px 36px rgba(45,74,62,0.12); }
        .ir-section-header {
          padding: 20px 32px; cursor: pointer;
          background: linear-gradient(135deg, #f9f8f5 0%, #f4f2ec 100%);
          border-left: 5px solid ${GREEN};
          display: flex; justify-content: space-between; align-items: center;
          transition: background 0.2s;
        }
        .ir-section-header:hover { background: linear-gradient(135deg, #f4f2ec 0%, #eeebe3 100%); }
        .ir-section-badge {
          width: 30px; height: 30px; border-radius: 9px; background: ${GREEN};
          display: flex; align-items: center; justify-content: center;
          font-size: 12px; font-weight: 900; color: rgba(255,255,255,0.9);
          letter-spacing: 0.3px; flex-shrink: 0;
        }
        .ir-section-title { font-weight: 800; font-size: 16px; color: ${GREEN}; }
        .ir-risk-pill {
          padding: 3px 10px; border-radius: 99px; font-size: 10px; font-weight: 800;
          text-transform: uppercase; letter-spacing: 0.5px; border: 1px solid;
        }
        .ir-chevron {
          color: ${GREEN}; font-size: 16px; display: inline-block;
          transition: transform 0.35s cubic-bezier(0.4,0,0.2,1);
        }

        /* ── MAP ── */
        .ir-map-wrap {
          height: 300px; border-radius: 12px; overflow: hidden;
          box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        }
        .leaflet-interactive:hover { stroke-width: 5 !important; }

        /* ── GAUGES ── */
        .ir-gauge-card {
          background: #f9f8f5; border-radius: 12px; padding: 14px 10px;
          text-align: center; border: 1px solid rgba(45,74,62,0.08);
          transition: all 0.25s ease;
        }
        .ir-gauge-card:hover {
          transform: translateY(-3px); box-shadow: 0 8px 24px rgba(45,74,62,0.12);
        }

        /* ── RISK CARDS ── */
        .ir-risk-card {
          flex: 1 1 180px; background: rgba(192,57,43,0.04);
          border: 1px solid rgba(192,57,43,0.25); border-radius: 12px; padding: 16px;
          transition: all 0.22s ease;
        }
        .ir-risk-card:hover {
          transform: translateY(-3px); box-shadow: 0 8px 24px rgba(192,57,43,0.14);
        }

        /* ── CLIMATE CARDS ── */
        .ir-climate-card {
          flex: 1 1 200px; border-radius: 12px; padding: 18px;
          border: 2px solid; transition: all 0.25s ease;
        }
        .ir-climate-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(45,74,62,0.1); }

        /* ── COMPOSITE GRID ── */
        .ir-radar-grid {
          display: grid; grid-template-columns: repeat(3,1fr); gap: 16px; margin-bottom: 28px;
        }
        .ir-district-radar {
          background: #fafaf8; border-radius: 12px; padding: 14px 10px;
          text-align: center; border: 1px solid rgba(45,74,62,0.08);
          transition: all 0.25s ease;
        }
        .ir-district-radar:hover {
          transform: translateY(-3px); box-shadow: 0 8px 24px rgba(45,74,62,0.12);
        }

        /* ── TABLE ── */
        .ir-table-row { transition: background 0.15s ease; }
        .ir-table-row:hover { background: rgba(45,74,62,0.04) !important; }
        .ir-val-pill {
          padding: 4px 11px; border-radius: 99px; font-size: 12px; font-weight: 700;
          display: inline-block;
        }
        .ir-alert-level {
          padding: 4px 11px; border-radius: 99px; font-size: 12px; font-weight: 700;
          display: inline-block;
        }
        .ir-grade-badge {
          padding: 3px 12px; border-radius: 99px; font-size: 13px; font-weight: 900;
          display: inline-block;
        }

        /* ── SCROLL REVEAL ── */
        .reveal { opacity: 0; transform: translateY(22px); transition: opacity 0.6s cubic-bezier(0.4,0,0.2,1), transform 0.6s cubic-bezier(0.4,0,0.2,1); }
        .reveal.in  { opacity: 1; transform: translateY(0); }

        /* ── INSIGHT BOX ── */
        .ir-section-badge + .ir-section-title { }

        /* ── PRINT ── */
        @media print {
          .no-print, .ir-header { display: none !important; }
          .ir-section { box-shadow: none !important; break-inside: avoid; }
          body { background: white !important; }
        }

        /* ── RECHARTS TOOLTIP ── */
        .recharts-tooltip-wrapper { outline: none !important; }

        select option { background: ${GREEN}; color: white; }
      `}</style>
    </div>
  );
}
