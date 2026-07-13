"use client";

import Link from "next/link";
import { SignedIn, UserButton } from "@clerk/clerk-react";

const LINKS = [
  ["/", "Dashboard"],
  ["/reports", "Reports"],
  ["/connect", "Connect"],
  ["/settings", "Settings"],
];

export default function Nav() {
  return (
    <nav
      style={{
        background: "#fff",
        borderBottom: "1px solid #eee",
        padding: "12px 24px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <div style={{ display: "flex", gap: 20, alignItems: "center" }}>
        <Link href="/" style={{ color: "#c0392b", fontWeight: "bold", fontSize: 18, textDecoration: "none" }}>
          reviewiq
        </Link>
        {LINKS.map(([href, label]) => (
          <Link key={href} href={href} style={{ color: "#555", fontSize: 14, textDecoration: "none" }}>
            {label}
          </Link>
        ))}
      </div>
      <SignedIn>
        <UserButton afterSignOutUrl="/" />
      </SignedIn>
    </nav>
  );
}
