# Security model

Provider JavaScript is untrusted input. Validation therefore runs only in the read-only job, in a separate process with a reduced environment, bounded runtime and memory, blocked process-spawning modules, bounded output, request-count, distinct-host, per-response and cumulative-download limits, and SSRF checks on every redirect.

This is defense in depth, not a claim of perfect OS isolation. A future hardening target is an ephemeral container or microVM with a read-only root filesystem, no Linux capabilities and an egress proxy that pins validated DNS answers.

Deep publication is blocked for configured providers when a reachable origin exhibits a high-confidence obsolete-route signature. Route diagnostics are retained and published as `route-regressions.json`.

Dependency lifecycle scripts are disabled during CI installation. The committed `package-lock.json` pins the resolved dependency graph, and workflows install it with `npm ci --ignore-scripts --no-audit --no-fund` before running repository checks.
