"use client";

import { SignedIn, SignedOut, SignInButton } from "@clerk/clerk-react";

// Gates the app: signed-in users see the page; signed-out users get a sign-in prompt.
export default function AuthGate({ children }) {
  return (
    <>
      <SignedIn>{children}</SignedIn>
      <SignedOut>
        <main style={{ fontFamily: "system-ui, sans-serif", maxWidth: 480, margin: "80px auto", textAlign: "center", padding: 24 }}>
          <h1 style={{ color: "#c0392b" }}>reviewiq</h1>
          <p style={{ color: "#555", fontSize: 16 }}>AI review intelligence — sign in to view your dashboard.</p>
          <SignInButton mode="modal">
            <button style={{ background: "#c0392b", color: "#fff", border: "none", borderRadius: 6, padding: "12px 24px", fontSize: 15, cursor: "pointer", marginTop: 12 }}>
              Sign in
            </button>
          </SignInButton>
        </main>
      </SignedOut>
    </>
  );
}
