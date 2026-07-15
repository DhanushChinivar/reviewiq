"use client";

import { useState } from "react";

export default function Connect() {
  const [file, setFile] = useState(null);

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
        <input type="file" accept=".csv,.xlsx" onChange={(e) => setFile(e.target.files?.[0]?.name || null)} />
        {file && <p style={{ marginTop: 8 }}>Selected: <b>{file}</b></p>}
        <p className="muted" style={{ fontSize: 12, marginBottom: 0 }}>
          The CSV → SQS → worker → DynamoDB pipeline works via the API. Live browser upload needs
          presigned S3 URLs + a CORS route (planned).
        </p>
      </div>
    </main>
  );
}
