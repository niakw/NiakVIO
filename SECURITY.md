# Security model

> [!CAUTION]
> Provider JavaScript is **untrusted input**. NiakVIO uses defense in depth; it does not claim perfect hostile-code isolation.

## 🛡️ Security at a glance

| Boundary | Current control |
| --- | --- |
| **Execution** | Separate worker process, reduced environment, bounded runtime/memory/output |
| **Network** | Guarded `fetch`, SSRF checks on every redirect, request/host/response/download limits |
| **Node capabilities** | Process spawning and direct filesystem/network-capable modules blocked; sensitive builtin access filtered |
| **Dependencies** | `npm ci --ignore-scripts --no-audit --no-fund`, committed lockfile, High/Critical production audit |
| **GitHub Actions** | Least-privilege permissions, immutable action SHAs, policy gates against dangerous workflow patterns |
| **Publication** | Fail-closed validation, identity/media checks, deterministic Provider v3 regeneration |
| **Evidence** | Sanitized artifacts and route/security diagnostics kept separate from trust decisions |

> [!NOTE]
> A future hardening target is stronger OS-level isolation: an ephemeral container or microVM with a read-only root filesystem, no Linux capabilities and an egress proxy that pins validated DNS answers.

---

## 🔒 Provider execution sandbox

Validation runs only in the read-only job, in a separate process with:

- reduced environment;
- bounded runtime and memory;
- blocked process-spawning modules;
- bounded output;
- request-count and distinct-host limits;
- per-response and cumulative-download limits;
- SSRF checks on every redirect.

The provider worker is a defense-in-depth compatibility sandbox. It blocks process spawning plus direct filesystem/network-capable Node modules, filters `process.getBuiltinModule` and legacy `process.binding` access, rejects static dangerous imports, and is launched by health checks under Node's Permission Model with read-only access limited to the worker scripts, dependencies and staged provider inputs.

Provider network access must go through the guarded `fetch` surface so SSRF, redirect, host-count and response-size limits remain effective.

This still does not claim perfect hostile-code isolation; OS/container isolation remains the stronger long-term boundary.

---

## 🌐 Route and publication gates

Deep publication is blocked for configured providers when a reachable origin exhibits a high-confidence obsolete-route signature.

Route diagnostics are retained and published as:

```text
route-regressions.json
```

Published provider code is not treated as trusted source. Generated or provenance-preserving snapshots under `providers/` and `upstream-lkg/providers/` remain untrusted inputs.

They are regenerated deterministically from **ProviderBase v3 + structured DATA + owned Lego** through the manual non-main reconstruction workflow rather than hand-edited or seeded from published/upstream JS.

> [!IMPORTANT]
> A static-analysis dismissal for vendored/generated snapshot code does **not** make that provider trusted. Sandboxing, network guards, identity checks and media validation remain the runtime boundary.

---

## ⚙️ Repository & GitHub Actions hardening

GitHub Actions use explicit least-privilege permissions and immutable full-length action SHAs.

Repository policy rejects:

- `pull_request_target`;
- `write-all`;
- mutable external Action refs;
- unpinned Docker action images.

`CODEOWNERS` routes all changes — especially workflows, publication state, scripts and security controls — to the repository owner for review.

Dependency lifecycle scripts are disabled during CI installation. The committed `package-lock.json` pins the resolved dependency graph.

```bash
npm ci --ignore-scripts --no-audit --no-fund
```

The dependency gate also checks High-severity advisories for the non-optional production tree and runs the deterministic repository suite.

Published upstream bundles that still import `cheerio-without-node-native` are kept compatible through an npm alias to the audited `cheerio@1.2.0` implementation; the obsolete `0.20.2` dependency tree is no longer installed.

---

## 🔍 CodeQL policy

CodeQL findings in repository-owned workflows, `scripts/`, `engine_v2/` and tests are treated as NiakVIO findings and must be resolved or explicitly justified.

Files under `providers/` and `upstream-lkg/providers/` are generated or provenance-preserving snapshots of untrusted provider code. Findings limited to those trees may be dismissed as vendored/generated-code findings **only after verifying that no repository-owned path is involved**.

That dismissal does not weaken runtime controls.

---

## 🚨 Reporting a vulnerability

For a potentially sensitive vulnerability:

> [!IMPORTANT]
> Do **not** publish exploit details in a normal public issue.

Prefer GitHub private vulnerability reporting when available for the repository, or contact the repository owner privately.

Related documents: [`DISCLAIMER.md`](DISCLAIMER.md) · [`TESTING_NOTICE.md`](TESTING_NOTICE.md) · [`ARCHITECTURE.md`](ARCHITECTURE.md)
