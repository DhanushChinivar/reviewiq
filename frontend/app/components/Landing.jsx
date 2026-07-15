"use client";

import { SignUpButton } from "@clerk/clerk-react";

const FEATURES = [
  ["🔌", "Connect in minutes", "Pull reviews automatically from Shopify, or upload a CSV/Excel export. Set it once and forget it."],
  ["🧠", "AI that actually reads them", "Claude analyzes every review — sentiment, recurring themes, severity, and anomalies you'd otherwise miss."],
  ["📋", "Prioritized actions", "Not just charts. Every issue is ranked 🔴🟡🟢 with concrete recommended fixes you can act on today."],
  ["📬", "Weekly, on autopilot", "A clean intelligence report lands in your inbox and dashboard every week. Zero effort after setup."],
];

const STEPS = [
  ["1", "Connect your reviews", "Shopify or a CSV upload."],
  ["2", "AI analyzes the week", "Sentiment, themes, anomalies, actions."],
  ["3", "Get your report", "In your inbox and dashboard, every week."],
];

export default function Landing() {
  return (
    <main className="container" style={{ maxWidth: 880 }}>
      {/* Hero */}
      <section style={{ textAlign: "center", padding: "48px 0 36px" }}>
        <div style={{ display: "inline-block", fontSize: 12, fontWeight: 700, color: "var(--brand)", background: "#eef0ff", padding: "5px 12px", borderRadius: 999, letterSpacing: "0.03em", marginBottom: 18 }}>
          AI REVIEW INTELLIGENCE
        </div>
        <h1 style={{ fontSize: 40, lineHeight: 1.1, letterSpacing: "-0.03em", maxWidth: 640, margin: "0 auto 16px" }}>
          Turn a week of reviews into a 2-minute action plan.
        </h1>
        <p className="muted" style={{ fontSize: 18, lineHeight: 1.6, maxWidth: 560, margin: "0 auto 28px" }}>
          reviewiq reads every customer review, finds what's breaking and what's winning, and emails you a
          prioritized report — automatically, every week.
        </p>
        <SignUpButton mode="modal">
          <button className="btn" style={{ fontSize: 16, padding: "13px 26px" }}>Get started free →</button>
        </SignUpButton>
        <p className="muted" style={{ fontSize: 12, marginTop: 12 }}>No credit card. Connect a store or upload a CSV.</p>
      </section>

      {/* Features */}
      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 14 }}>
        {FEATURES.map(([icon, title, body], i) => (
          <div key={i} className="card panel">
            <div style={{ fontSize: 26 }}>{icon}</div>
            <div style={{ fontWeight: 700, fontSize: 16, margin: "8px 0 4px" }}>{title}</div>
            <div className="muted" style={{ fontSize: 14, lineHeight: 1.55 }}>{body}</div>
          </div>
        ))}
      </section>

      {/* How it works */}
      <h2 style={{ textAlign: "center", marginTop: 40 }}>How it works</h2>
      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 14 }}>
        {STEPS.map(([n, title, body], i) => (
          <div key={i} className="card panel" style={{ textAlign: "center" }}>
            <div style={{ width: 34, height: 34, borderRadius: 999, background: "var(--brand)", color: "#fff", fontWeight: 800, display: "inline-flex", alignItems: "center", justifyContent: "center", marginBottom: 10 }}>{n}</div>
            <div style={{ fontWeight: 700, fontSize: 15 }}>{title}</div>
            <div className="muted" style={{ fontSize: 13, marginTop: 4 }}>{body}</div>
          </div>
        ))}
      </section>

      {/* Closing CTA */}
      <section className="card" style={{ marginTop: 26, padding: "26px 24px", textAlign: "center", background: "linear-gradient(180deg, #ffffff, #f5f6ff)" }}>
        <div style={{ fontWeight: 800, fontSize: 18, letterSpacing: "-0.01em" }}>Built for sellers who don't have time to read 500 reviews.</div>
        <p className="muted" style={{ maxWidth: 520, margin: "8px auto 16px", fontSize: 14 }}>
          Know exactly what to fix and what's working — without lifting a finger.
        </p>
        <SignUpButton mode="modal"><button className="btn">Get started →</button></SignUpButton>
      </section>

      <footer className="muted" style={{ textAlign: "center", fontSize: 12, marginTop: 40 }}>
        reviewiq · serverless AI on AWS · your review data stays private & encrypted
      </footer>
    </main>
  );
}
