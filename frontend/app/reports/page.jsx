"use client";

import { useEffect, useState } from "react";
import { useUser } from "@clerk/clerk-react";
import { API_BASE } from "../lib/config";

export default function Reports() {
  const { user, isLoaded } = useUser();
  const [data, setData] = useState(null);

  useEffect(() => {
    if (!isLoaded || !user) return;
    fetch(`${API_BASE}/reports?user_id=${encodeURIComponent(user.id)}`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => setData({ history: [] }));
  }, [isLoaded, user]);

  const history = data?.history || [];

  return (
    <main className="container">
      <h1>Report history</h1>
      <p className="muted" style={{ marginTop: 0 }}>Every weekly report generated for your account.</p>

      {!data ? (
        <div className="card empty"><p className="muted">Loading…</p></div>
      ) : history.length === 0 ? (
        <div className="card empty"><p className="muted">No reports yet.</p></div>
      ) : (
        <div className="card" style={{ overflow: "hidden" }}>
          <table className="data">
            <thead>
              <tr><th>Date</th><th>Sentiment</th><th>Reviews</th><th>Summary</th></tr>
            </thead>
            <tbody>
              {history.map((h, i) => (
                <tr key={i}>
                  <td style={{ whiteSpace: "nowrap" }}>{h.report_date}</td>
                  <td><b>{h.sentiment_score}</b><span className="muted">/100</span></td>
                  <td>{h.review_count}</td>
                  <td>{h.summary}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
