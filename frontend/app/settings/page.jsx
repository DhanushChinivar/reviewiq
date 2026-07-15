"use client";

import { useEffect, useState } from "react";
import { useUser } from "@clerk/clerk-react";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export default function Settings() {
  const { user } = useUser();
  const [email, setEmail] = useState("");
  const [day, setDay] = useState("Monday");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    try {
      const s = JSON.parse(localStorage.getItem("reviewiq_settings") || "{}");
      if (s.email) setEmail(s.email);
      else if (user?.primaryEmailAddress?.emailAddress) setEmail(user.primaryEmailAddress.emailAddress);
      if (s.day) setDay(s.day);
    } catch {}
  }, [user]);

  const save = () => {
    localStorage.setItem("reviewiq_settings", JSON.stringify({ email, day }));
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <main className="container" style={{ maxWidth: 560 }}>
      <h1>Settings</h1>
      <p className="muted" style={{ marginTop: 0 }}>Your report preferences.</p>

      <div className="card panel" style={{ marginTop: 18 }}>
        <label className="field">Report email</label>
        <input className="control" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />

        <label className="field">Send day</label>
        <select className="control" value={day} onChange={(e) => setDay(e.target.value)}>
          {DAYS.map((d) => <option key={d}>{d}</option>)}
        </select>

        <div style={{ marginTop: 18, display: "flex", alignItems: "center", gap: 12 }}>
          <button className="btn" onClick={save}>Save preferences</button>
          {saved && <span style={{ color: "var(--good)", fontWeight: 600, fontSize: 14 }}>Saved ✓</span>}
        </div>
        <p className="muted" style={{ fontSize: 12, marginTop: 16, marginBottom: 0 }}>
          Stored locally in your browser (demo). A subscription API would persist this server-side.
        </p>
      </div>
    </main>
  );
}
