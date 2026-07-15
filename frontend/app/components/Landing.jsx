"use client";

import { SignUpButton } from "@clerk/clerk-react";

const FEATURES = [
  ["🔌", "#eef0ff", "Connect in minutes", "Pull reviews automatically from Shopify, or upload a CSV/Excel export. Set it once and forget it."],
  ["🧠", "#f3e8ff", "AI that actually reads them", "Claude analyzes every review — sentiment, recurring themes, severity, and anomalies you'd otherwise miss."],
  ["📋", "#dcfce7", "Prioritized actions", "Not just charts. Every issue is ranked 🔴🟡🟢 with concrete recommended fixes you can act on today."],
  ["📬", "#fef3c7", "Weekly, on autopilot", "A clean intelligence report lands in your inbox and dashboard every week. Zero effort after setup."],
];

const STEPS = [
  ["1", "Connect your reviews", "Shopify or a CSV upload — takes a minute."],
  ["2", "AI analyzes the week", "Sentiment, themes, anomalies, and actions."],
  ["3", "Get your report", "In your inbox and dashboard, automatically."],
];

const INTEGRATIONS = ["Shopify", "Amazon", "Judge.me", "Trustpilot", "CSV / Excel"];

const TESTIMONIALS = [
  { img: "/avatars/priya.jpg", name: "Priya S.", role: "Shopify store owner", quote: "I used to skim reviews on Sunday nights. Now reviewiq hands me the three things to fix — I got my weekends back." },
  { img: "/avatars/marcus.jpg", name: "Marcus T.", role: "DTC founder", quote: "It flagged a battery-defect trend two weeks before we'd have caught it ourselves. That's real money saved." },
  { img: "/avatars/elena.jpg", name: "Elena R.", role: "E-commerce manager", quote: "The recommended actions are shockingly specific — it reads like an analyst wrote the report." },
];

const STATS = [
  ["2 min", "from a week of reviews to an action plan"],
  ["500+", "reviews analyzed in a single report"],
  ["100%", "of reviews read — never skim again"],
  ["Weekly", "reports delivered fully on autopilot"],
];

export default function Landing() {
  return (
    <div className="landing">
      {/* decorative background blobs */}
      <div className="blob" style={{ width: 420, height: 420, background: "#c7d2fe", top: -120, right: -80 }} />
      <div className="blob" style={{ width: 360, height: 360, background: "#e9d5ff", top: 240, left: -140 }} />

      <main className="container section" style={{ maxWidth: 1040 }}>
        {/* Hero */}
        <section className="hero-grid">
          <div>
            <span className="eyebrow">AI REVIEW INTELLIGENCE</span>
            <h1 className="hero-title">
              Turn a week of reviews into a <span className="grad-text">2-minute action plan.</span>
            </h1>
            <p className="hero-sub">
              reviewiq reads every customer review, finds what's breaking and what's winning, and emails you a
              prioritized report — automatically, every week.
            </p>
            <div className="cta-row">
              <SignUpButton mode="modal">
                <button className="btn btn-lg">Get started free →</button>
              </SignUpButton>
              <a href="#how" className="btn-ghost2">See how it works</a>
            </div>
            <p className="muted" style={{ fontSize: 12, marginTop: 14 }}>No credit card · Connect a store or upload a CSV</p>
          </div>
          <DashboardMock />
        </section>

        {/* Integrations */}
        <section className="section center" style={{ marginTop: 40 }}>
          <p className="muted" style={{ fontSize: 13, fontWeight: 600, letterSpacing: "0.03em" }}>WORKS WITH THE TOOLS YOU ALREADY USE</p>
          <div className="logos">
            {INTEGRATIONS.map((n) => <span key={n} className="chip">{n}</span>)}
          </div>
        </section>

        {/* Stats */}
        <section className="section stats-strip card" style={{ marginTop: 40 }}>
          {STATS.map(([num, label], i) => (
            <div key={i} className="center">
              <div className="stat-num">{num}</div>
              <div className="muted" style={{ fontSize: 12.5, marginTop: 4, lineHeight: 1.4 }}>{label}</div>
            </div>
          ))}
        </section>

        {/* Features */}
        <section className="section" style={{ marginTop: 48 }}>
          <h2 className="center" style={{ fontSize: 24, marginBottom: 20 }}>Everything you need to act on feedback</h2>
          <div className="feat-grid">
            {FEATURES.map(([icon, bg, title, body], i) => (
              <div key={i} className="card panel">
                <div className="feat-icon" style={{ background: bg }}>{icon}</div>
                <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 4 }}>{title}</div>
                <div className="muted" style={{ fontSize: 14, lineHeight: 1.55 }}>{body}</div>
              </div>
            ))}
          </div>
        </section>

        {/* Story */}
        <section className="section" style={{ marginTop: 52 }}>
          <h2 className="center" style={{ fontSize: 24, marginBottom: 6 }}>Sound familiar?</h2>
          <p className="muted center" style={{ maxWidth: 520, margin: "0 auto 22px", fontSize: 15 }}>Every seller knows the Monday-morning review pile.</p>
          <div className="story-grid">
            <div className="card panel">
              <div style={{ fontSize: 26 }}>😵‍💫</div>
              <div style={{ fontWeight: 700, marginTop: 8, marginBottom: 6 }}>Before reviewiq</div>
              <p className="muted" style={{ fontSize: 14.5, lineHeight: 1.6, margin: 0 }}>
                It's Monday. 240 new reviews since last week. Somewhere in there is why returns spiked —
                but who has time to read them all? So the problem quietly festers, unnoticed, until it's
                a trend you can't ignore.
              </p>
            </div>
            <div className="card panel" style={{ background: "linear-gradient(180deg,#ffffff,#f5f6ff)", borderColor: "#dfe1f5" }}>
              <div style={{ fontSize: 26 }}>✨</div>
              <div style={{ fontWeight: 700, marginTop: 8, marginBottom: 6, color: "var(--brand)" }}>With reviewiq</div>
              <p style={{ fontSize: 14.5, lineHeight: 1.6, margin: 0 }}>
                You open one email and <b>know</b>: what's breaking, what's winning, and exactly what to do
                next — ranked by priority, with recommended fixes. The homework's already done.
              </p>
            </div>
          </div>
        </section>

        {/* How it works */}
        <section id="how" className="section" style={{ marginTop: 52 }}>
          <h2 className="center" style={{ fontSize: 24, marginBottom: 20 }}>How it works</h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))", gap: 16 }}>
            {STEPS.map(([n, title, body], i) => (
              <div key={i} className="card panel center">
                <div style={{ width: 38, height: 38, borderRadius: 999, background: "var(--brand)", color: "#fff", fontWeight: 800, display: "inline-flex", alignItems: "center", justifyContent: "center", marginBottom: 10 }}>{n}</div>
                <div style={{ fontWeight: 700, fontSize: 15 }}>{title}</div>
                <div className="muted" style={{ fontSize: 13, marginTop: 4 }}>{body}</div>
              </div>
            ))}
          </div>
        </section>

        {/* Testimonials */}
        <section className="section" style={{ marginTop: 52 }}>
          <h2 className="center" style={{ fontSize: 24, marginBottom: 20 }}>Loved by busy sellers</h2>
          <div className="feat-grid">
            {TESTIMONIALS.map((t, i) => (
              <div key={i} className="card panel">
                <div className="stars">★★★★★</div>
                <p style={{ fontSize: 14.5, lineHeight: 1.6, margin: "10px 0 16px" }}>&ldquo;{t.quote}&rdquo;</p>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <img className="avatar" src={t.img} alt={t.name} width={46} height={46} loading="lazy" />
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 14 }}>{t.name}</div>
                    <div className="muted" style={{ fontSize: 12 }}>{t.role}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Closing CTA */}
        <section className="section cta-banner" style={{ marginTop: 52 }}>
          <div style={{ fontSize: 26, fontWeight: 800, letterSpacing: "-0.02em" }}>Stop reading 500 reviews. Start acting on them.</div>
          <p style={{ opacity: 0.9, maxWidth: 520, margin: "10px auto 22px", fontSize: 15 }}>
            Know exactly what to fix and what's working — without lifting a finger.
          </p>
          <SignUpButton mode="modal">
            <button className="btn btn-white btn-lg">Get started free →</button>
          </SignUpButton>
        </section>

        <footer className="muted center" style={{ fontSize: 12, marginTop: 44 }}>
          reviewiq · serverless AI on AWS · your review data stays private &amp; encrypted
        </footer>
      </main>
    </div>
  );
}

/* ---- Product preview mockup (the hero visual) ---- */
function DashboardMock() {
  const bars = [
    { n: "Headphones", v: 55, c: "#d97706" },
    { n: "Phone Case", v: 42, c: "#dc2626" },
    { n: "USB Cable", v: 74, c: "#16a34a" },
    { n: "Charger", v: 63, c: "#d97706" },
  ];
  return (
    <div className="mock section">
      <div className="mock-bar">
        <span className="dot" style={{ background: "#ff5f57" }} />
        <span className="dot" style={{ background: "#febc2e" }} />
        <span className="dot" style={{ background: "#28c840" }} />
        <span style={{ marginLeft: 8, fontSize: 11, color: "#9ca3af", background: "#fff", border: "1px solid var(--border)", borderRadius: 6, padding: "2px 12px" }}>
          reviewiq · Dashboard
        </span>
      </div>
      <div style={{ padding: 16, background: "#fbfbfd" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8, marginBottom: 12 }}>
          <MiniKpi label="Sentiment" value="54" color="#d97706" />
          <MiniKpi label="Reviews" value="128" />
          <MiniKpi label="Confidence" value="91%" />
        </div>
        <div style={{ background: "#fff", border: "1px solid var(--border)", borderRadius: 10, padding: 12, marginBottom: 10 }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: "var(--muted)", letterSpacing: "0.04em", marginBottom: 10 }}>PRODUCT SENTIMENT</div>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 12, height: 78 }}>
            {bars.map((b, i) => (
              <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", height: "100%", justifyContent: "flex-end" }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: "#374151", marginBottom: 3 }}>{b.v}</div>
                <div style={{ width: "100%", height: `${b.v}%`, background: b.c, borderRadius: "4px 4px 0 0" }} />
                <div style={{ fontSize: 9, color: "var(--muted)", marginTop: 5, maxWidth: "100%", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{b.n}</div>
              </div>
            ))}
          </div>
        </div>
        <div style={{ background: "#fff", border: "1px solid var(--border)", borderRadius: 10, padding: "11px 12px", display: "flex", alignItems: "center", gap: 8, fontSize: 12.5 }}>
          <span style={{ background: "#fee2e2", color: "#b91c1c", fontWeight: 700, fontSize: 10, padding: "2px 8px", borderRadius: 999 }}>HIGH</span>
          <b>Battery life</b>
          <span style={{ color: "var(--muted)" }}>— 43 mentions, trending ↑</span>
        </div>
      </div>
    </div>
  );
}

function MiniKpi({ label, value, color }) {
  return (
    <div style={{ background: "#fff", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 10px" }}>
      <div style={{ fontSize: 9, fontWeight: 700, color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>{label}</div>
      <div style={{ fontSize: 21, fontWeight: 800, color: color || "var(--ink)", marginTop: 2, lineHeight: 1 }}>{value}</div>
    </div>
  );
}
