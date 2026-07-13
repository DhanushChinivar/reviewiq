"use client";

import { useEffect, useState } from "react";

const wrap = { fontFamily: "system-ui, sans-serif", maxWidth: 560, margin: "0 auto", padding: 24 };
const card = { background: "#fff", border: "1px solid #eee", borderRadius: 8, padding: 20 };
const lbl = { display: "block", marginTop: 12, marginBottom: 4, fontSize: 13, color: "#555" };
const inp = { width: "100%", padding: 8, border: "1px solid #ddd", borderRadius: 6, fontSize: 14, boxSizing: "border-box" };
const btn = { marginTop: 16, background: "#c0392b", color: "#fff", border: "none", borderRadius: 6, padding: "10px 16px", cursor: "pointer", fontSize: 14 };

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export default function Settings() {
  const [email, setEmail] = useState("");
  const [day, setDay] = useState("Monday");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    try {
      const s = JSON.parse(localStorage.getItem("reviewiq_settings") || "{}");
      if (s.email) setEmail(s.email);
      if (s.day) setDay(s.day);
    } catch {}
  }, []);

  const save = () => {
    localStorage.setItem("reviewiq_settings", JSON.stringify({ email, day }));
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <main style={wrap}>
      <h1>Settings</h1>
      <div style={card}>
        <label style={lbl}>Report email</label>
        <input style={inp} value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />

        <label style={lbl}>Send day</label>
        <select style={inp} value={day} onChange={(e) => setDay(e.target.value)}>
          {DAYS.map((d) => <option key={d}>{d}</option>)}
        </select>

        <div>
          <button style={btn} onClick={save}>Save preferences</button>
          {saved && <span style={{ marginLeft: 12, color: "#2e7d32" }}>Saved ✓</span>}
        </div>
        <p style={{ color: "#999", fontSize: 12, marginTop: 16 }}>
          Stored locally in your browser (demo). Phase 6 wires this to a subscription API.
        </p>
      </div>
    </main>
  );
}
