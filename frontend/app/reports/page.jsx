"use client";

import { useEffect, useState } from "react";
import { API_BASE, USER_ID } from "../lib/config";

const wrap = { fontFamily: "system-ui, sans-serif", maxWidth: 900, margin: "0 auto", padding: 24 };
const th = { padding: 8, borderBottom: "2px solid #eee", textAlign: "left" };
const td = { padding: 8, borderBottom: "1px solid #eee", verticalAlign: "top" };

export default function Reports() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/reports?user_id=${USER_ID}`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => setData({ history: [] }));
  }, []);

  const history = data?.history || [];

  return (
    <main style={wrap}>
      <h1>Report history</h1>
      {!data ? (
        <p>Loading…</p>
      ) : history.length === 0 ? (
        <p>No reports yet.</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
          <thead>
            <tr style={{ background: "#fafafa" }}>
              <th style={th}>Date</th>
              <th style={th}>Sentiment</th>
              <th style={th}>Reviews</th>
              <th style={th}>Summary</th>
            </tr>
          </thead>
          <tbody>
            {history.map((h, i) => (
              <tr key={i}>
                <td style={td}>{h.report_date}</td>
                <td style={td}>{h.sentiment_score}/100</td>
                <td style={td}>{h.review_count}</td>
                <td style={td}>{h.summary}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
