"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useUser } from "@clerk/clerk-react";
import { API_BASE } from "../lib/config";
import { fmtDate } from "../lib/format";

export default function Reports() {
  const { user, isLoaded } = useUser();
  const router = useRouter();
  const [data, setData] = useState(null);

  useEffect(() => {
    if (!isLoaded || !user) return;
    fetch(`${API_BASE}/reports?user_id=${encodeURIComponent(user.id)}`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => setData({ history: [] }));
  }, [isLoaded, user]);

  const history = data?.history || [];

  function open(reportDate) {
    router.push(`/?report=${encodeURIComponent(reportDate)}`);
  }

  return (
    <main className="container">
      <h1>Report history</h1>
      <p className="muted" style={{ marginTop: 0 }}>
        Every report generated for your account. Click a row to view it on the dashboard.
      </p>

      {!data ? (
        <div className="card empty"><p className="muted">Loading…</p></div>
      ) : history.length === 0 ? (
        <div className="card empty"><p className="muted">No reports yet.</p></div>
      ) : (
        <div className="card" style={{ overflow: "hidden" }}>
          <table className="data">
            <thead>
              <tr><th>Generated</th><th>Sentiment</th><th>Reviews</th><th>Summary</th><th></th></tr>
            </thead>
            <tbody>
              {history.map((h, i) => (
                <tr
                  key={i}
                  onClick={() => open(h.report_date)}
                  className="rowlink"
                  style={{ cursor: "pointer" }}
                >
                  <td style={{ whiteSpace: "nowrap" }}>
                    {fmtDate(h.report_date)}
                    {i === 0 && <span className="badge low" style={{ marginLeft: 8 }}>Latest</span>}
                  </td>
                  <td><b>{h.sentiment_score}</b><span className="muted">/100</span></td>
                  <td>{h.review_count}</td>
                  <td>{h.summary}</td>
                  <td style={{ whiteSpace: "nowrap", color: "var(--brand)", fontWeight: 600 }}>View →</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
