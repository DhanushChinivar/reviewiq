import { API_BASE } from "./config";

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// All API calls now send the Clerk session token; the backend derives user_id
// from it (never from the URL/body), so a caller can only touch their own data.
async function authFetch(path, getToken, init = {}) {
  const token = await getToken();
  return fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { ...(init.headers || {}), Authorization: `Bearer ${token}` },
  });
}

export function fetchReports(getToken) {
  return authFetch("/reports", getToken).then((r) => r.json());
}

/**
 * Kick off an on-demand report and wait for it to finish, tracking JOB STATUS.
 * `getToken` is Clerk's useAuth().getToken (called per request for a fresh token).
 *
 * Throws: Error with .failed=true (job failed, message is user-friendly),
 *         or "timeout".
 */
export async function generateAndWait(getToken, { email, timeoutMs = 120000, intervalMs = 3000 } = {}) {
  const res = await authFetch("/reports/generate", getToken, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }), // user_id from the token; email captured for report delivery
  });
  if (!res.ok && res.status !== 202) {
    throw new Error(`Couldn't start the analysis (${res.status}). Please try again.`);
  }
  const { job_id } = await res.json();

  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    await sleep(intervalMs);
    const data = await authFetch(`/reports?job=${encodeURIComponent(job_id)}`, getToken).then((r) => r.json());
    const status = data?.job?.status;
    if (status === "FAILED") {
      const e = new Error(data.job.error || "Analysis failed. Please try again.");
      e.failed = true;
      throw e;
    }
    if (status === "SUCCEEDED") return data;
  }
  throw new Error("timeout");
}
