// Explicit local opt-in; inherits the loopback-only launcher and never changes
// the database path. Test runners must supply their own temporary path.
process.env.CORELAB_V2 = "1";
await import("./run-next.mjs");
