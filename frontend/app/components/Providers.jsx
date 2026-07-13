"use client";

import { ClerkProvider } from "@clerk/clerk-react";
import { CLERK_PUBLISHABLE_KEY } from "../lib/config";

// Client-side Clerk provider. Used instead of @clerk/nextjs because the site is
// a static export (no server middleware).
export default function Providers({ children }) {
  return (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY} afterSignOutUrl="/">
      {children}
    </ClerkProvider>
  );
}
