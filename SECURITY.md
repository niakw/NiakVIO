# Security model

Provider JavaScript is untrusted input. Validation therefore runs only in the read-only job, in a separate process with a reduced environment, bounded runtime and memory, blocked process-spawning modules, bounded output, request-count, distinct-host, per-response and cumulative-download limits, and SSRF checks on every redirect.

This is defense in depth, not a claim of perfect OS isolation. A future hardening target is an ephemeral container or microVM with a read-only root filesystem, no Linux capabilities and an egress proxy that pins validated DNS answers.

Deep publication is blocked for configured providers when a reachable origin exhibits a high-confidence obsolete-route signature. Route diagnostics are retained and published as `route-regressions.json`.

Dependency lifecycle scripts are disabled during CI installation. The committed `package-lock.json` pins the resolved dependency graph, and workflows install it with `npm ci --ignore-scripts --no-audit --no-fund` before running repository checks.

## Repository and runtime hardening

GitHub Actions use explicit least-privilege permissions and immutable full-length action SHAs. A repository policy test rejects `pull_request_target`, `write-all`, mutable external Action refs, and unpinned Docker action images. `CODEOWNERS` routes all changes — especially workflows, publication state, scripts and security controls — to the repository owner for review.

The provider worker is a defense-in-depth compatibility sandbox: it receives a reduced environment, blocks process spawning plus direct filesystem/network-capable Node modules, filters `process.getBuiltinModule` and legacy `process.binding` access, rejects static dangerous imports, and is launched by health checks under Node's Permission Model with read-only access limited to the worker scripts, dependencies and staged provider inputs. Provider network access must go through the guarded `fetch` surface so SSRF, redirect, host-count and response-size limits remain effective. This still does not claim perfect hostile-code isolation; OS/container isolation remains the stronger long-term boundary.

The dependency gate installs the committed lockfile with lifecycle scripts disabled, checks high-severity advisories for the non-optional production tree, and runs the deterministic repository suite. The legacy `cheerio-without-node-native` package remains intentionally pinned because published upstream bundles still import it; replacing it requires provider compatibility evidence rather than a blind dependency substitution.

For a potentially sensitive vulnerability, avoid publishing exploit details in a normal public issue. Prefer GitHub private vulnerability reporting when available for the repository, or contact the repository owner privately.
