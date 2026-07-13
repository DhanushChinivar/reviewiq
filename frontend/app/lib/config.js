// Shared frontend config. Later (Phase 6): move API_BASE to an env var and
// derive USER_ID from the signed-in Clerk user instead of hardcoding it.
export const API_BASE = "https://m25yqjhn7e.execute-api.us-east-1.amazonaws.com/Prod";
export const USER_ID = "u123";

// Clerk publishable key (public by design — safe in client code).
export const CLERK_PUBLISHABLE_KEY = "pk_test_cG9saXNoZWQtcmFjZXItMTkuY2xlcmsuYWNjb3VudHMuZGV2JA";
