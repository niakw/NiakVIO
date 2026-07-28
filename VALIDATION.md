# Validation — v5.16.0

Verified locally on 2026-07-28:

- complete repository regression suite passes;
- provider child process blocks process-spawning and VM-related modules;
- worker stdout/stderr, memory and runtime are bounded;
- request count, distinct network hosts, per-response bytes and cumulative downloaded bytes are bounded;
- SSRF guard blocks private, link-local, benchmark, documentation, metadata and IPv4-mapped IPv6 destinations;
- route regression diagnostics are retained in the CI artifact and copied to `route-regressions.json` during publication;
- Frenchstream and StreamZo are strict route providers: a reachable origin followed by a high-confidence obsolete-route signature blocks deep publication;
- domain and route overrides are verified in both staged and final published files;
- `frenchstream.food`, `streamzo.fr` and `api.movix.show` remain the required corrected domains.

Known limitation: no `package-lock.json` could be generated in this offline validation environment. Direct dependencies remain exactly pinned and lifecycle scripts are disabled; generating and committing a trusted lockfile remains the next supply-chain task.
