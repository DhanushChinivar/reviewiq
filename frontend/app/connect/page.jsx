"use client";

import { useState } from "react";
import { useUser } from "@clerk/clerk-react";
import { API_BASE } from "../lib/config";

export default function Connect() {
  const { user } = useUser();
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState(null); // {kind: 'ok'|'err'|'busy', msg}

  async function fileToCsv(f) {
    // .csv → read as text; .xlsx → parse first sheet to CSV in the browser
    if (f.name.toLowerCase().endsWith(".csv")) {
      return await f.text();
    }
    const XLSX = await import("xlsx");
    const buf = await f.arrayBuffer();
    const wb = XLSX.read(buf, { type: "array" });
    const sheet = wb.Sheets[wb.SheetNames[0]];
    return XLSX.utils.sheet_to_csv(sheet);
  }

  async function handleUpload() {
    if (!file || !user) return;
    setStatus({ kind: "busy", msg: "Reading file…" });
    try {
      const csv = await fileToCsv(file);
      if (!csv.trim()) throw new Error("The file looks empty.");

      setStatus({ kind: "busy", msg: "Uploading…" });
      const res = await fetch(`${API_BASE}/reviews/upload`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: user.id, filename: file.name, csv }),
      });
      if (!res.ok) throw new Error(`Upload failed (${res.status})`);
      const data = await res.json();
      setStatus({
        kind: "ok",
        msg: `Uploaded — your reviews are queued for analysis (job ${data.job_id.slice(0, 8)}).`,
      });
      setFile(null);
    } catch (e) {
      setStatus({ kind: "err", msg: e.message || "Something went wrong." });
    }
  }

  return (
    <main className="container">
      <h1>Connect your reviews</h1>
      <p className="muted" style={{ marginTop: 0 }}>Two ways to get reviews into reviewiq.</p>

      <div className="card panel" style={{ marginTop: 18 }}>
        <h2 style={{ marginTop: 0 }}>🛍️ Shopify</h2>
        <p className="muted" style={{ marginTop: 4 }}>Connect your store to pull reviews automatically every week.</p>
        <button className="btn">Connect Shopify</button>
        <p className="muted" style={{ fontSize: 12, marginBottom: 0 }}>
          Backend wired: OAuth callback (KMS-encrypted token) + weekly Judge.me pull (simulated).
        </p>
      </div>

      <div className="card panel" style={{ marginTop: 14 }}>
        <h2 style={{ marginTop: 0 }}>📄 Upload CSV / Excel</h2>
        <p className="muted" style={{ marginTop: 4 }}>Supported: .csv, .xlsx</p>

        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <input
            type="file"
            accept=".csv,.xlsx"
            onChange={(e) => {
              setFile(e.target.files?.[0] || null);
              setStatus(null);
            }}
          />
          <button
            className="btn"
            onClick={handleUpload}
            disabled={!file || !user || status?.kind === "busy"}
            style={{ opacity: !file || !user || status?.kind === "busy" ? 0.5 : 1 }}
          >
            {status?.kind === "busy" ? "Uploading…" : "Upload"}
          </button>
        </div>

        {file && <p style={{ marginTop: 10, marginBottom: 0 }}>Selected: <b>{file.name}</b></p>}

        {status && (
          <p
            style={{
              marginTop: 10,
              marginBottom: 0,
              fontSize: 14,
              fontWeight: 600,
              color: status.kind === "ok" ? "var(--good)" : status.kind === "err" ? "var(--bad)" : "var(--muted)",
            }}
          >
            {status.kind === "ok" ? "✓ " : status.kind === "err" ? "⚠ " : ""}
            {status.msg}
          </p>
        )}

        <p className="muted" style={{ fontSize: 12, marginTop: 12, marginBottom: 0 }}>
          Expected columns: <code>product_id, product_name, rating, review_text, date, platform</code>.
          Flow: browser → API → S3 → SQS → worker → DynamoDB.
        </p>
      </div>
    </main>
  );
}
