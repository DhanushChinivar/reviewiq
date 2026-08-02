// Format a report key for display. New reports use a full ISO timestamp
// (date + time); older ones may be date-only ("2026-08-02"). Show time only
// when the value actually has one.
export function fmtDate(s) {
  if (!s) return "";
  const d = new Date(s);
  if (isNaN(d.getTime())) return s;
  const hasTime = /T\d\d/.test(s);
  const opts = hasTime
    ? { year: "numeric", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }
    : { year: "numeric", month: "short", day: "numeric" };
  return d.toLocaleString(undefined, opts);
}
