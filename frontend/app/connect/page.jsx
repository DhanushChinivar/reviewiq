"use client";

import { useState } from "react";

const wrap = { fontFamily: "system-ui, sans-serif", maxWidth: 720, margin: "0 auto", padding: 24 };
const card = { background: "#fff", border: "1px solid #eee", borderRadius: 8, padding: 20, marginBottom: 16 };
const btn = { background: "#c0392b", color: "#fff", border: "none", borderRadius: 6, padding: "10px 16px", cursor: "pointer", fontSize: 14 };
const note = { color: "#999", fontSize: 12, marginTop: 8 };

export default function Connect() {
  const [file, setFile] = useState(null);

  return (
    <main style={wrap}>
      <h1>Connect your reviews</h1>

      <div style={card}>
        <h2 style={{ marginTop: 0 }}>🛍️ Shopify</h2>
        <p>Connect your Shopify store to pull reviews automatically every week.</p>
        <button style={btn}>Connect Shopify</button>
        <p style={note}>Backend wired: OAuth callback (KMS-encrypted token) + weekly Judge.me pull (simulated).</p>
      </div>

      <div style={card}>
        <h2 style={{ marginTop: 0 }}>📄 Upload CSV / Excel</h2>
        <p>Upload a reviews file. Supported: .csv, .xlsx.</p>
        <input type="file" accept=".csv,.xlsx" onChange={(e) => setFile(e.target.files?.[0]?.name || null)} />
        {file && <p style={{ marginTop: 8 }}>Selected: <b>{file}</b></p>}
        <p style={note}>
          The CSV → SQS → worker → DynamoDB pipeline already works via the API. Live browser upload
          needs presigned S3 URLs + a CORS preflight route (Phase 6).
        </p>
      </div>
    </main>
  );
}
