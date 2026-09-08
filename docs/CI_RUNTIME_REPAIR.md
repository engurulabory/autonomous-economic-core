# CI Runtime Repair Evidence

During PR #6 validation, CI exposed a pre-existing Cloudflare runtime layering defect: `edge-runtime.js` imported `worker.js` while the current `worker.js` re-exported `edge-runtime.js`, creating a circular delegation path. The durable-state gateway implementation from commit `a02c4e4c6892a8d7eaf3eea1b5867caa5d03f2d1` is the last known implementation containing the canonical durable HTTP endpoints and bearer-auth contract.

Repair rule: restore `deploy/cloudflare/worker.js` to that known-good durable gateway blob and align `scripts/verify_cloudflare_bundle.py` with the actual layering: durable endpoints/auth belong to `worker.js`; `edge-runtime.js` extends that base; `runtime-v1_1.js` extends `edge-runtime.js`.

This repair is required before Commercial Closure Pass™ can be merged because a green CI result must represent a non-circular runtime graph rather than a verifier bypass.
