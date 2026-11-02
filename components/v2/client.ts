export async function v2<T>(
  path: string,
  body?: unknown,
  method = body === undefined ? "GET" : "POST",
): Promise<T> {
  const r = await fetch("/api/v2/" + path, {
    method,
    cache: "no-store",
    ...(body !== undefined
      ? {
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      : {}),
  });
  const data = await r.json();
  if (!r.ok)
    throw new Error(data.error ?? "The local operation could not finish");
  return data as T;
}
// Display-only rounding of a stored numeric oracle; grading and stored grades
// keep the exact authored string.
export function readableAnswer(value: string) {
  if (!/^[+-]?\d+(\.\d+)?(e[+-]?\d+)?$/i.test(value)) return value;
  const n = Number(value);
  if (!Number.isFinite(n)) return value;
  if (Math.abs(n) < 1e-9) return "0";
  return String(Number(n.toPrecision(10)));
}
