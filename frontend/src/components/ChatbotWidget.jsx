// frontend/src/components/ChatbotWidget.jsx
// Week 9 (Sakshi) — RAG Chatbot widget
// Floating chat button, opens panel, supports English/Hindi/Marathi

import { useState, useRef, useEffect } from "react";
import { askChatbot } from "../utils/api";

export default function ChatbotWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: "bot", text: "Namaste! Ask me about government schemes, crop risk, or eligibility. (English/Hindi/Marathi supported)" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const query = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", text: query }]);
    setLoading(true);
    try {
      const res = await askChatbot(query);
      setMessages(prev => [...prev, {
        role: "bot",
        text: res.answer || "Sorry, I could not find an answer.",
        lang: res.detected_language,
        sources: res.sources
      }]);
    } catch {
      setMessages(prev => [...prev, { role: "bot", text: "AI unavailable right now. Please try again later." }]);
    }
    setLoading(false);
  };

  return (
    <>
      {/* Floating button */}
      <button onClick={() => setOpen(o => !o)} style={fabStyle} title="KisanSetu AI Assistant">
        🌾
      </button>

      {open && (
        <div style={panelStyle}>
          <div style={headerStyle}>
            <span>🤖 KisanSetu AI</span>
            <button onClick={() => setOpen(false)} style={closeBtn}>✕</button>
          </div>

          <div style={messagesStyle}>
            {messages.map((m, i) => (
              <div key={i} style={m.role === "user" ? userMsg : botMsg}>
                <p style={{ margin: 0 }}>{m.text}</p>
                {m.lang && <span style={langBadge}>{m.lang}</span>}
              </div>
            ))}
            {loading && <div style={botMsg}><p style={{ margin: 0 }}>Thinking...</p></div>}
            <div ref={bottomRef} />
          </div>

          <div style={inputRow}>
            <input
              style={inputStyle}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && send()}
              placeholder="Ask about schemes..."
            />
            <button onClick={send} style={sendBtn} disabled={loading}>→</button>
          </div>
        </div>
      )}
    </>
  );
}

const fabStyle = { position: "fixed", bottom: "24px", right: "24px", width: "56px", height: "56px", borderRadius: "50%", background: "#10b981", border: "none", fontSize: "24px", cursor: "pointer", zIndex: 9999, boxShadow: "0 4px 12px rgba(16,185,129,0.4)" };
const panelStyle = { position: "fixed", bottom: "90px", right: "24px", width: "340px", height: "480px", background: "#0f172a", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "16px", display: "flex", flexDirection: "column", zIndex: 9999, boxShadow: "0 8px 32px rgba(0,0,0,0.4)" };
const headerStyle = { padding: "16px", borderBottom: "1px solid rgba(255,255,255,0.1)", display: "flex", justifyContent: "space-between", alignItems: "center", color: "#fff", fontWeight: "bold" };
const closeBtn = { background: "none", border: "none", color: "#94a3b8", cursor: "pointer", fontSize: "16px" };
const messagesStyle = { flex: 1, overflowY: "auto", padding: "12px", display: "flex", flexDirection: "column", gap: "8px" };
const userMsg = { alignSelf: "flex-end", background: "#10b981", color: "#fff", padding: "8px 12px", borderRadius: "12px 12px 0 12px", maxWidth: "80%", fontSize: "14px" };
const botMsg = { alignSelf: "flex-start", background: "rgba(255,255,255,0.05)", color: "#e2e8f0", padding: "8px 12px", borderRadius: "12px 12px 12px 0", maxWidth: "85%", fontSize: "14px" };
const langBadge = { fontSize: "10px", color: "#10b981", marginTop: "4px", display: "block" };
const inputRow = { padding: "12px", borderTop: "1px solid rgba(255,255,255,0.1)", display: "flex", gap: "8px" };
const inputStyle = { flex: 1, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", padding: "8px 12px", color: "#fff", fontSize: "14px", outline: "none" };
const sendBtn = { background: "#10b981", border: "none", borderRadius: "8px", padding: "8px 14px", color: "#fff", cursor: "pointer", fontSize: "16px" };