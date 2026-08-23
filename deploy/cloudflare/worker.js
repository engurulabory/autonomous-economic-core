// Legacy compatibility entrypoint.
// Canonical production deployment uses runtime-v1_1.js, which wraps edge-runtime.js.
// Keep this file valid for older tooling and CI without duplicating runtime logic.
export { default } from "./edge-runtime.js";
