// Shared frontend config.
// user_id is now derived from the signed-in Clerk user (useUser().user.id),
// NOT hardcoded — so each user sees their own data.
export const API_BASE = "https://m25yqjhn7e.execute-api.us-east-1.amazonaws.com/Prod";

// Clerk publishable key (public by design — safe in client code).
export const CLERK_PUBLISHABLE_KEY = "pk_test_cG9saXNoZWQtcmFjZXItMTkuY2xlcmsuYWNjb3VudHMuZGV2JA";
