import { API_BASE } from "./config";

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export function fetchReports(userId) {
  return fetch(`${API_BASE}/reports?user_id=${encodeURIComponent(userId)}`).then((r) => r.json());
}

async function latestCreatedAt(userId) {
  try {
    const d = await fetchReports(userId);
    return d?.history?.[0]?.created_at || null;
  } catch {
    return null;
  }
}

/**
 * Kick off an on-demand report and wait for it to appear.
 *
 * The API returns 202 immediately (the analysis runs in the background, free of
 * API Gateway's 29s limit), so we poll GET /reports until a report with a NEWER
 * created_at than before shows up. Returns the fresh reports payload.
 *
 * Throws: Error with .code === 404 (no reviews), "timeout", or a status message.
 */
export async function generateAndWait(userId, { timeoutMs = 120000, intervalMs = 3000 } = {}) {
  const before = await latestCreatedAt(userId);

  const res = await fetch(`${API_BASE}/reports/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  });
  if (res.status === 404) {
    const e = new Error("no_reviews");
    e.code = 404;
    throw e;
  }
  if (!res.ok && res.status !== 202) {
    throw new Error(`Generation failed (${res.status})`);
  }

  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    await sleep(intervalMs);
    const data = await fetchReports(userId);
    const newest = data?.history?.[0]?.created_at || null;
    if (newest && newest !== before) return data; // fresh report landed
  }
  throw new Error("timeout");
}
