"use client";

import { SignedIn, SignedOut } from "@clerk/clerk-react";
import Landing from "./Landing";

// Signed-in users get the app; signed-out visitors get the marketing landing page.
export default function AuthGate({ children }) {
  return (
    <>
      <SignedIn>{children}</SignedIn>
      <SignedOut>
        <Landing />
      </SignedOut>
    </>
  );
}
