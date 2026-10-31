import { createHash } from "node:crypto";
import { z } from "zod";

export const enabled = () => process.env.CORELAB_V2 === "1";
export const BACKUP_LIMIT = 128 * 1024 * 1024;
export const WRITE_LIMIT = 16 * 1024;
export class V2Error extends Error {
  constructor(
    public code: string,
    message: string,
    public status = 400,
  ) {
    super(message);
  }
}
export const id = z.string().regex(/^[A-Za-z0-9][A-Za-z0-9._@-]{0,119}$/);
export const time = z.iso.datetime();
export const purpose = z.enum(["practice", "placement", "verify", "review"]);
export const level = z.number().int().min(0).max(3);
export type Purpose = z.infer<typeof purpose>;
export type Dimension = "C" | "M";

// JSON.parse discards duplicate keys. Scan object scopes before parsing instead.
export function strictJSON(text: string): unknown {
  let i = 0;
  const ws = () => {
    while (/\s/.test(text[i] ?? "") && i < text.length) i++;
  };
  function string(): string {
    const start = i++;
    while (i < text.length) {
      if (text[i] === "\\") {
        i += 2;
        continue;
      }
      if (text[i++] === '"') return JSON.parse(text.slice(start, i));
    }
    throw new V2Error("invalid_json", "Unterminated JSON string");
  }
  function value(depth: number): void {
    if (depth > 48)
      throw new V2Error("invalid_json", "JSON nesting limit exceeded");
    ws();
    if (text[i] === "{") {
      i++;
      ws();
      const keys = new Set<string>();
      if (text[i] === "}") {
        i++;
        return;
      }
      while (i < text.length) {
        ws();
        if (text[i] !== '"') throw new Error("Expected object key");
        const key = string();
        if (keys.has(key))
          throw new V2Error("duplicate_key", "Duplicate JSON key");
        keys.add(key);
        ws();
        if (text[i++] !== ":") throw new Error("Expected colon");
        value(depth + 1);
        ws();
        if (text[i] === "}") {
          i++;
          return;
        }
        if (text[i++] !== ",") throw new Error("Expected comma");
      }
    } else if (text[i] === "[") {
      i++;
      ws();
      if (text[i] === "]") {
        i++;
        return;
      }
      while (i < text.length) {
        value(depth + 1);
        ws();
        if (text[i] === "]") {
          i++;
          return;
        }
        if (text[i++] !== ",") throw new Error("Expected comma");
      }
    } else if (text[i] === '"') {
      string();
      return;
    } else {
      const start = i;
      while (i < text.length && !/[\s,\]}]/.test(text[i])) i++;
      if (i === start) throw new Error("Expected value");
      JSON.parse(text.slice(start, i));
      return;
    }
    throw new Error("Incomplete JSON value");
  }
  value(0);
  ws();
  if (i !== text.length) throw new Error("Trailing JSON input");
  const result: unknown = JSON.parse(text);
  canonical(result); // Also reject nonfinite numbers and lone surrogates.
  return result;
}

function validString(s: string) {
  for (let i = 0; i < s.length; i++) {
    const c = s.charCodeAt(i);
    if (c >= 0xd800 && c <= 0xdbff) {
      const next = s.charCodeAt(++i);
      if (!(next >= 0xdc00 && next <= 0xdfff))
        throw new Error("Invalid Unicode");
    } else if (c >= 0xdc00 && c <= 0xdfff) throw new Error("Invalid Unicode");
  }
}
// RFC 8785: ECMAScript primitive serialization and UTF-16 property ordering.
export function canonical(v: unknown): string {
  if (v === null || typeof v === "boolean") return JSON.stringify(v);
  if (typeof v === "number") {
    if (!Number.isFinite(v)) throw new Error("Nonfinite JSON number");
    return JSON.stringify(v);
  }
  if (typeof v === "string") {
    validString(v);
    return JSON.stringify(v);
  }
  if (Array.isArray(v)) return "[" + v.map(canonical).join(",") + "]";
  if (
    v &&
    typeof v === "object" &&
    Object.getPrototypeOf(v) === Object.prototype
  )
    return (
      "{" +
      Object.keys(v)
        .sort()
        .map((k) => {
          validString(k);
          return (
            JSON.stringify(k) +
            ":" +
            canonical((v as Record<string, unknown>)[k])
          );
        })
        .join(",") +
      "}"
    );
  throw new Error("Unsupported JSON value");
}
export const hash = (v: string) => createHash("sha256").update(v).digest("hex");
export const digest = (v: unknown) => hash(canonical(v));
export const bytes = (v: unknown) => Buffer.byteLength(canonical(v), "utf8");
export const fingerprint = (structure: string, inputs: unknown) =>
  hash("corelab-fingerprint/1\n" + canonical({ structure, inputs }));

export function numberAnswer(s: string): {
  n: string;
  d: string;
  value: number;
} {
  s = s.trim();
  let n: bigint, d: bigint;
  if (/^[+-]?\d{1,9}\/[1-9]\d{0,8}$/.test(s)) {
    const parts = s.split("/");
    n = BigInt(parts[0]);
    d = BigInt(parts[1]);
  } else if (/^[+-]?\d{1,12}(\.\d{1,12})?$/.test(s)) {
    const sign = s.startsWith("-") ? -1n : 1n;
    const [whole, decimals = ""] = s.replace(/^[+-]/, "").split(".");
    d = 10n ** BigInt(decimals.length);
    n = sign * BigInt(whole + decimals);
  } else
    throw new V2Error(
      "answer_format",
      "Use a decimal or a fraction such as 2/3",
    );
  function gcd(a: bigint, b: bigint): bigint {
    return b === 0n ? a : gcd(b, a % b);
  }
  const g = gcd(n < 0n ? -n : n, d);
  n /= g;
  d /= g;
  return { n: String(n), d: String(d), value: Number(n) / Number(d) };
}
export async function readJSON(request: Request, limit = WRITE_LIMIT) {
  if (!request.headers.get("content-type")?.includes("application/json"))
    throw new V2Error("content_type", "Expected application/json");
  const reader = request.body?.getReader();
  if (!reader) throw new V2Error("empty_body", "Expected a JSON body");
  const chunks: Uint8Array[] = [];
  let length = 0;
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      length += value.byteLength;
      if (length > limit) {
        await reader.cancel();
        throw new V2Error(
          "body_limit",
          "Request exceeds the supported byte limit",
          413,
        );
      }
      chunks.push(value);
    }
    const data = new Uint8Array(length);
    let offset = 0;
    for (const chunk of chunks) {
      data.set(chunk, offset);
      offset += chunk.length;
    }
    return strictJSON(new TextDecoder("utf-8", { fatal: true }).decode(data));
  } finally {
    reader.releaseLock();
  }
}
