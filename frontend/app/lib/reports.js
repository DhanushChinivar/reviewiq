import { API_BASE } from "./config";

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export function fetchReports(userId) {
  return fetch(`${API_BASE}/reports?user_id=${encodeURIComponent(userId)}`).then((r) => r.json());
}

/**
 * Kick off an on-demand report and wait for it to finish, tracking JOB STATUS.
 *
 * The trigger returns 202 with a job_id (the analysis runs async, free of API
 * Gateway's 29s limit). We poll GET /reports?job=<id> and react to the job's
 * status: SUCCEEDED → return the fresh report data; FAILED → throw the job's
 * friendly error (so a background failure becomes a real "it failed" message,
 * not a silent hang).
 *
 * Throws: Error with .failed=true (job failed, message is user-friendly),
 *         or "timeout".
 */
export async function generateAndWait(userId, { timeoutMs = 120000, intervalMs = 3000 } = {}) {
  const res = await fetch(`${API_BASE}/reports/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  });
  if (!res.ok && res.status !== 202) {
    throw new Error(`Couldn't start the analysis (${res.status}). Please try again.`);
  }
  const { job_id } = await res.json();

  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    await sleep(intervalMs);
    const data = await fetch(
      `${API_BASE}/reports?user_id=${encodeURIComponent(userId)}&job=${encodeURIComponent(job_id)}`
    ).then((r) => r.json());
    const status = data?.job?.status;
    if (status === "FAILED") {
      const e = new Error(data.job.error || "Analysis failed. Please try again.");
      e.failed = true;
      throw e;
    }
    if (status === "SUCCEEDED") return data; // report is already written; data has it
  }
  throw new Error("timeout");
}
