"use client";

import Link from "next/link";
import { SignedIn, SignedOut, UserButton, SignInButton } from "@clerk/clerk-react";

const LINKS = [
  ["/", "Dashboard"],
  ["/reports", "Reports"],
  ["/connect", "Connect"],
  ["/settings", "Settings"],
];

export default function Nav() {
  return (
    <header style={{ background: "var(--surface)", borderBottom: "1px solid var(--border)" }}>
      <div
        style={{
          maxWidth: 960,
          margin: "0 auto",
          padding: "0 24px",
          height: 60,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 28 }}>
          <Link href="/" style={{ fontWeight: 800, fontSize: 19, letterSpacing: "-0.02em", color: "var(--brand)", textDecoration: "none" }}>
            reviewiq
          </Link>
          <SignedIn>
            <nav style={{ display: "flex", gap: 22 }}>
              {LINKS.map(([href, label]) => (
                <Link key={href} href={href} style={{ fontSize: 14, fontWeight: 500, color: "var(--muted)", textDecoration: "none" }}>
                  {label}
                </Link>
              ))}
            </nav>
          </SignedIn>
        </div>

        <SignedIn>
          <UserButton afterSignOutUrl="/" />
        </SignedIn>
        <SignedOut>
          <SignInButton mode="modal">
            <button className="btn" style={{ padding: "8px 16px" }}>Sign in</button>
          </SignInButton>
        </SignedOut>
      </div>
    </header>
  );
}
