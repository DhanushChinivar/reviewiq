"use client";

import { useEffect, useState } from "react";
import { useUser } from "@clerk/clerk-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LabelList, CartesianGrid,
} from "recharts";
import { API_BASE } from "./lib/config";

const PRIORITY = { red: "🔴", yellow: "🟡", green: "🟢" };

// Sentiment 0–100 → status color band (green = good, amber = mixed, red = poor).
function band(score) {
  if (score >= 67) return "#16a34a";
  if (score >= 40) return "#d97706";
  return "#dc2626";
}

export default function Dashboard() {
  const { user, isLoaded } = useUser();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isLoaded || !user) return;
    fetch(`${API_BASE}/reports?user_id=${encodeURIComponent(user.id)}`)
      .then((r) => r.json())
      .then(setData)
      .catch((e) => setError(String(e)));
  }, [isLoaded, user]);

  if (error)
    return <Wrap><div className="card empty"><p className="muted">Error: {error}</p></div></Wrap>;
  if (!isLoaded || (user && !data))
    return <Wrap><div className="card empty"><p className="muted">Loading…</p></div></Wrap>;

  const r = data?.latest;

  if (!r)
    return (
      <Wrap>
        <div className="card empty">
          <div style={{ fontSize: 40, marginBottom: 10 }}>📊</div>
          <p style={{ fontWeight: 800, fontSize: 18, margin: 0 }}>No reports yet</p>
          <p className="muted" style={{ marginTop: 6, maxWidth: 360, marginInline: "auto" }}>
            Upload reviews from the <b>Connect</b> page. Your weekly AI report will appear here.
          </p>
        </div>
      </Wrap>
    );

  const reviewCount = data.history?.[0]?.review_count ?? "—";
  const reportDate = data.history?.[0]?.report_date ?? "";

  return (
    <Wrap sub={`Latest report · ${reportDate}`}>
      <div className="kpis">
        <div className="card kpi">
          <div className="label">Sentiment</div>
          <div className="value" style={{ color: band(r.sentiment_score) }}>
            {r.sentiment_score}<span style={{ fontSize: 16, color: "var(--muted)", fontWeight: 600 }}>/100</span>
          </div>
          <div className="sub">overall this week</div>
        </div>
        <div className="card kpi">
          <div className="label">Reviews analysed</div>
          <div className="value">{reviewCount}</div>
          <div className="sub">in this report</div>
        </div>
        <div className="card kpi">
          <div className="label">Confidence</div>
          <div className="value">
            {Math.round((r.confidence_score || 0) * 100)}<span style={{ fontSize: 16, color: "var(--muted)", fontWeight: 600 }}>%</span>
          </div>
          <div className="sub">AI certainty</div>
        </div>
      </div>

      <div className="card summary">{r.week_summary}</div>

      <h2>Product sentiment</h2>
      <div className="card panel">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={r.products || []} margin={{ top: 22, right: 8, left: -14, bottom: 0 }}>
            <CartesianGrid vertical={false} stroke="#eef0f3" />
            <XAxis dataKey="product_name" tick={{ fontSize: 12, fill: "#6b7280" }} axisLine={false} tickLine={false} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 12, fill: "#6b7280" }} axisLine={false} tickLine={false} width={34} />
            <Tooltip cursor={{ fill: "rgba(0,0,0,0.03)" }} />
            <Bar dataKey="sentiment_score" radius={[6, 6, 0, 0]} maxBarSize={64}>
              {(r.products || []).map((p, i) => <Cell key={i} fill={band(p.sentiment_score)} />)}
              <LabelList dataKey="sentiment_score" position="top" style={{ fontSize: 12, fontWeight: 700, fill: "#374151" }} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <h2>Priority themes</h2>
      <div className="card" style={{ overflow: "hidden" }}>
        <table className="data">
          <thead>
            <tr><th>Theme</th><th>Mentions</th><th>Severity</th><th>Recommended actions</th></tr>
          </thead>
          <tbody>
            {(r.themes || []).map((t, i) => (
              <tr key={i}>
                <td>{PRIORITY[t.priority] || ""} <b>{t.theme}</b></td>
                <td>{t.mentions}</td>
                <td><span className={`badge ${["high", "medium", "low"].includes(t.severity) ? t.severity : "low"}`}>{t.severity}</span></td>
                <td>
                  <ul style={{ margin: 0, paddingLeft: 16 }}>
                    {(t.recommended_actions || []).map((a, j) => <li key={j} style={{ marginBottom: 3 }}>{a}</li>)}
                  </ul>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {r.anomalies?.length > 0 && (
        <>
          <h2>Anomalies</h2>
          <div className="card panel">
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              {r.anomalies.map((a, i) => <li key={i} style={{ marginBottom: 8 }}>{a}</li>)}
            </ul>
          </div>
        </>
      )}
    </Wrap>
  );
}

function Wrap({ children, sub }) {
  return (
    <main className="container">
      <h1>Dashboard</h1>
      {sub && <p className="muted" style={{ marginTop: 0 }}>{sub}</p>}
      {children}
    </main>
  );
}
