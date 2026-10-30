import { it, expect } from "vitest";
import { checkLocalRequest } from "../lib/http";
it("accepts loopback same-origin API traffic", () =>
  expect(() =>
    checkLocalRequest(
      new Request("http://127.0.0.1:3000/api/action", {
        headers: { host: "127.0.0.1:3000", origin: "http://127.0.0.1:3000" },
      }),
    ),
  ).not.toThrow());
it("blocks cross-origin mutations", () =>
  expect(() =>
    checkLocalRequest(
      new Request("http://127.0.0.1:3000/api/action", {
        headers: { host: "127.0.0.1:3000", origin: "https://other.example" },
      }),
    ),
  ).toThrow("Cross-origin"));
it("rejects nonlocal Host headers", () =>
  expect(() =>
    checkLocalRequest(
      new Request("http://other.example/api/state", {
        headers: { host: "other.example" },
      }),
    ),
  ).toThrow("localhost"));

it("uses the validated browser Host when Next reconstructs an internal URL", () =>
  expect(() =>
    checkLocalRequest(
      new Request("http://localhost:3217/api/action", {
        headers: { host: "127.0.0.1:3217", origin: "http://127.0.0.1:3217" },
      }),
    ),
  ).not.toThrow());
