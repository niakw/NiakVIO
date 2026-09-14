## 2026-09-14 — Main-only 5.21.46 publication, Hub46 atomicity, security/audit/minimizer continuation

### Repository / branch authority
- `main` is the only active write/publication target. The merged repair branch `fix/labs-5.21.44-20260912` was deleted by repository hygiene and must not be recreated for this continuation.
- Historical provider archive remains `provider-old/`; exactly 46 current provider slugs remain executable/materialized in `providers/` + `provider-bases/`, 50 historical provider slugs remain archive-only.
- PR #114 was merged to main through merge commit `3e144d66b402e15af962f6adde767736c00bed2f`; all continuation after merge is main-only.

### Release / manifests / Domain Refresh
- The old apparent 5.21.43 state was real only for Hub46 projections: root/language manifests had advanced while `manifest-hub46.json` / `native-hub46/manifest.json` lagged. Release finalization was repaired so root, language projections, Hub46 projection and pinned native Hub46 transport synchronize together.
- Domain Refresh was rebuilt as an atomic two-local-commit / one-push transaction: first local provider-generation commit creates the SHA that owns new content-addressed bundles; `native-hub46/manifest.json` is then pinned to that provider SHA; hashes/integrity are regenerated; only the final commit is pushed to main.
- Domain Refresh now preserves current filename stage and current-46 scope, leaves historical rows immutable, runs current-only sanitation/guarding, and is fail-closed on unexpected scope or history changes.
- A real domain refresh changed 11 current providers and legitimately bumped release `5.21.44 -> 5.21.45`. Later durable provider fixes for AnimeSama.co/VoirAnime changed provider bytes and legitimately bumped `5.21.45 -> 5.21.46`.
- Final accepted published release at this checkpoint is **5.21.46**. The finalizer has repeatedly proved fixed point afterward: `patched=0`, `release_changed=false`, provider bumps `0` on no-op runs.
- Final Domain Refresh after 5.21.46 is strict no-op: `applied=0`, `registry=0`, `bundles=0`, metadata `changed=0`, `FIELD_DOMAIN_TRANSACTION_CHANGED false`, `FIELD_DOMAIN_REFRESH_IDEMPOTENT true`; observation-only DNS/GlobalPing limits never mutate authority.

### Release finalizer architecture
- `.github/workflows/release-finalize.yml` is the permanent exact-SHA accepted-release finalizer and now supports atomic provider-generation + pinned-Hub46 finalization before one push.
- Release integrity, Hub46 projection, native pin, language projections and release hashes are mandatory. Finalizer must not bump a release/provider when bytes did not change.
- `manifest-hub46.json` is a current projection; `native-hub46/manifest.json` is an immutable transport projection pinned to the local provider-generation commit SHA that actually contains referenced bundles.

### Current runtime/security fixes already durable
- Core provider timeout remains **25 s**.
- Latest-request A->B->C stale-generation suppression remains mandatory even when native fetch ignores AbortSignal.
- 403/404/410 terminal media remains fail-closed while valid sibling streams may survive.
- AnimeSama.co and VoirAnime published HTML parsing was repaired at the owned Provider-block source using deterministic scanners; published HTML-security gate reached **0 forbidden regex findings across 46/46** before 5.21.46 finalization.
- Purstream current authoritative site is `https://purstream.mx`; its API authority remains under `api.purstream.ad`. Stale tests expecting only `purstream.ad` were corrected without weakening DATA authority.
- Workflow/Media stale assertions left from the old 96-provider execution catalogue were reconciled to the current 46 executable providers without touching the 50-provider historical archive.

### Final exact-SHA validation status before new minimizer/security cleanup
- Candidate SHA used for the in-progress final validation was `4811cfa9bc5a4fa343bd59ecda17e79b83d091b8`, release 5.21.46.
- `CORE - Verify & Publish` Quick: green on that SHA, including published-byte gates after fixed-point replay was aligned to the actual publication pipeline (`blocks -> security hardening -> published bytes`).
- Core gates green on the same SHA: Non-Regression, Stream Metadata, Media Type & Playback, Provider Overrides. Separate Workflow Gate was also repaired/green after replacing stale current-catalogue fixtures/assertions.
- `SEC - CodeQL` run `34828935079`: all 12 analysis/scope jobs and final `CodeQL · javascript-typescript` matrix-enforcement job completed success on SHA `4811cfa9...`.
- IMPORTANT: a green CodeQL workflow means analysis executed successfully; it does **not** mean zero Code Scanning alerts. User reports GitHub UI still shows about **1386 Code Scanning alerts**, so security cleanup is NOT complete.
- Native final validation was still running when this checkpoint was requested: Desktop macOS+Windows built successfully and were executing movie/tv/anime routes; Mobile Android entered live routes after green prebuild/KVM; TV Android was still prebuilding; iOS had resolved official NuvioMobile and was queued for macOS runner. Do not call five Labs complete until all five platform jobs are terminal.

### External audits — fresh evidence and required cleanup
- `SEC - External Code Audit` run `34828937432` completed success on SHA `4811cfa9...` with `publish=false` (read-only), artifact `external-code-audit-34828937432`, artifact id `10341474975`, SHA-256 `ae270858724eaf123fb2d9888b9e5a161336a718054bca55640856ffc965e489`.
- Fresh Sonar, DeepSource and CodeScene exports were all produced. This audit must be treated as a release gate, not decoration.
- Preliminary export triage: Sonar exported 10,000 open findings; roughly 9,997 are under generated `providers/` bundles, leaving only a tiny maintained-source remainder. DeepSource exported 256 findings with 0 vulnerability count in its export; many critical secret-like findings are in captured diagnostics/LKG/evidence rather than maintained runtime source. CodeScene export completed with no defect count observed in preliminary summary, but hotspot ranking is polluted by generated/historical bundles.
- Required security model: generated published bundles remain covered by mandatory NiakVIO publication/runtime/security gates (artifact syntax/runtime validation, security hardening, forbidden-pattern gate, fixed-point/reverse reconstruction, hashes/integrity). Static analyzers should primarily scan maintained source (`provider-bases/`, provider/Core block generators, engine/scripts/actions), not repeatedly count the same generated Core inside every `providers/*.js` artifact or archive evidence.
- Do not suppress/close real maintained-source security findings merely to reduce counts. First separate generated/evidence noise from maintained-source findings, then fix the maintained-source findings and rerun fresh external audits.

### CodeQL workflow cleanup now mandatory
- Current `.github/workflows/codeql.yml` exposes 1 scope job + 11 analysis jobs + 1 aggregate job. User explicitly rejects this noisy matrix presentation.
- Current shards duplicate JavaScript scanning across `providers/**` and `provider-bases/**` in four lexical shards each, plus source/actions/python. `provider-old/**` remains excluded and must stay excluded.
- Target: retain Hub46/current-source coverage while reducing visible jobs to a compact set, e.g. Actions, Python, JS Core/source, JS ProviderBase/current maintained provider source, plus one aggregate if needed. Generated `providers/**` should not duplicate maintained-source CodeQL if publication gates continue to audit exact final bytes.
- The 1386 UI alerts must be treated as a real unresolved security-quality issue until current maintained-source alerts are isolated/fixed or precisely classified; do not equate green CodeQL execution with zero findings.

### NiakVIO Provider v3 minimizer — exact authoritative rule
- User clarified repeatedly: **NO Terser and no external/generic JS minifier.** Do not introduce Terser.
- Architecture already declares `scripts/provider_v3_minimizer.py` as the only production minimizer; `automation/provider-v3-architecture.json` explicitly says `terser_allowed=false`, phase `pre-hash-safe-whitespace`, production enabled.
- Current bug: `scripts/reapply_published_overrides.py` still explicitly bypasses the minimizer and preserves post-Core bytes verbatim, contradicting architecture and `provider_v3_minimizer_published_test.py`.
- The minimizer is deliberately NiakVIO-safe: no identifier rename, no expression reorder/fold, no literal/regex rewrite, preserve every line terminator and managed marker cardinality, leave template-bearing files byte-stable, current production transform only removes code-line leading indentation safely.
- Minification applies to final `providers/*.js` publication output using the **NiakVIO minimizer**, and must remain compatible with add/remove/update of owned Provider/Core fix blocks: reconstruct from ProviderBase + structured DATA/static knowledge + owned blocks, apply security hardening, apply NiakVIO minimizer at the declared pre-hash stage, validate syntax/fixed-point, then compute content SHA / content-addressed filename / provider version / manifests / hashes.
- User clarification on ownership: do not introduce a generic tool that rewrites upstream/external source semantics. The runtime artifact is minified only through the conservative NiakVIO-aware transformation contract.
- Required tests before publication: `tests/provider_v3_minimizer_contract_test.py`, `tests/provider_v3_minimizer_preview_test.py`, `tests/provider_v3_minimizer_published_test.py`, reverse rebuild / static audit / published artifact validation / security hardening / release integrity.
- Because enabling the already-declared minimizer may change current provider bytes, the next real publication may legitimately become **5.21.47**. Never force the version; let exact byte drift drive provider/release bumps.

### Immediate continuation after this checkpoint
1. Persist this checkpoint physically into `MEMORY.md` through the durable pending-memory writer and verify the pending sentinel resets.
2. Wire `scripts/provider_v3_minimizer.py` into `reapply_published_overrides.py` at the production pre-hash stage, replacing the contradictory verbatim/no-minifier branch; add/strengthen tests that prove add/remove block reconstruction is reminimized deterministically.
3. Consolidate CodeQL jobs and maintained-source scope without weakening security; keep `provider-old/` excluded and keep exact published-bundle security gates mandatory.
4. Triage fresh Sonar/DeepSource/CodeScene exports into maintained source vs generated/archive/evidence; fix maintained-source blocking findings and configure/report scopes so future audits are actionable rather than dominated by generated bundles.
5. Run finalizer atomically; accept 5.21.47 only if minimization actually changes bytes. Regenerate Hub46/native pin/projections/hashes/integrity.
6. Re-run Domain Refresh to strict no-op on the new final head.
7. Re-run Verify & Publish, four Core gates, Workflow Gate, compact CodeQL, external audits, dependency/security checks, and all five Native Labs on one exact final SHA. Final completion requires terminal green/precisely classified evidence, not just dispatched runs.
