import { expect, it } from "vitest";
import {
  canonical,
  strictJSON,
  numberAnswer,
  fingerprint,
  readJSON,
} from "../../lib/v2/contracts";

it("canonicalizes ECMAScript primitives and sorted UTF-16 keys", () => {
  expect(canonical({ z: -0, a: [1e30, 4.5, 2e-3] })).toBe(
    '{"a":[1e+30,4.5,0.002],"z":0}',
  );
  expect(canonical({ "\u20ac": 1, "\r": 2, "1": 3 })).toBe(
    '{"\\r":2,"1":3,"€":1}',
  );
  expect(() => canonical(NaN)).toThrow();
  expect(() => canonical("\ud800")).toThrow();
  expect(() => canonical({ x: undefined })).toThrow();
  expect(() => canonical(new Array(2))).toThrow("Sparse");
});
it("rejects duplicate decoded keys, malformed JSON, overflow and deep nesting", () => {
  for (const s of [
    '{"a":1,"\\u0061":2}',
    '{"x":NaN}',
    "[1,]",
    '{"a":1,}',
    "1e999",
    '{"x":"\\ud800"}',
    "[".repeat(50) + "0" + "]".repeat(50),
  ])
    expect(() => strictJSON(s)).toThrow();
  expect(strictJSON('{"a":{"x":1},"b":{"x":2}}')).toEqual({
    a: { x: 1 },
    b: { x: 2 },
  });
});
it("normalizes fractions and decimals without eval", () => {
  expect(numberAnswer("2/4")).toEqual(numberAnswer("0.50"));
  expect(numberAnswer("-0").n).toBe("0");
  expect(numberAnswer("−1.5")).toEqual(numberAnswer("-1.5"));
  expect(numberAnswer("−3/4")).toEqual(numberAnswer("-0.75"));
  for (const s of [
    "1/0",
    "1e3",
    "true",
    "1,5",
    "Math.PI",
    "9".repeat(1000),
    "−−1",
    "1−2",
  ])
    expect(() => numberAnswer(s)).toThrow();
  expect(fingerprint("task@1", { x: "1" })).toBe(
    fingerprint("task@1", { x: "1" }),
  );
});
it("counts streamed UTF-8 bytes without Content-Length", async () => {
  const request = new Request("http://localhost", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: '{"x":"éé"}',
  });
  await expect(readJSON(request, 10)).rejects.toThrow("byte limit");
});
