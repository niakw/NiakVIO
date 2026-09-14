<!-- NIAKVIO_MEMORY_PENDING_EMPTY -->

## 2026-09-14 — Native one-shot repair published and post-merge validated

### Published authority (supersedes pre-merge checkpoint status lines)
- The earlier checkpoint section `2026-09-14 — Native Labs one-shot harness hardening from existing evidence` was written while PR #116 was still draft. Its statements that `main` was untouched / PR should remain draft were true only at that intermediate checkpoint and are now superseded by this section.
- PR **#116** `fix(native): harden one-shot Labs from existing evidence` was marked ready and **merged into `main`**.
- Merge commit / published main authority: **`8d9ac77928cd6f392a9c24a3425a6ea8663d26f6`**.
- Published behavior is the same one-shot repair already documented: serialized native provider execution (`chunked(1)`), adaptive Android/TV catalogue rotations without production-player probes, and generation-safe iOS watchdog restart/drain/exact-BEGIN correlation.

### Post-merge validation on published main
- **CORE - Workflow Gate** run **`34866432607`** on merge SHA `8d9ac779...`: **success**. Python syntax, executable multi-device runtime contract, workflow architecture, native provider-loading compatibility and side-effect-free compatibility checks all passed.
- **CORE - Verify & Publish** run **`34866432526`** on merge SHA `8d9ac779...`: **success**. The Quick gate passed; all Deep stages were explicitly **skipped**, so no fresh exhaustive provider observation/publication campaign was run.
- **LEARN - Brain Branch Maintenance** run **`34866432627`** on merge SHA `8d9ac779...`: **success**.
- The previously interrupted PR CodeQL run **`34865005265`** was resumed only for its cancelled `JS ProviderBase` job. Final rerun state: **all CodeQL jobs success** — Actions, Python, JS Core, JS ProviderBase, plus the maintained-source matrix.
- No Native Reader workflow (`NATIVE - Android Reader`, `NATIVE - Mobile iOS Reader`, `NATIVE - Desktop Reader`, etc.) was dispatched for merge SHA `8d9ac779...`. The head-SHA workflow list contains only Workflow Gate, Verify & Publish, and Brain Branch Maintenance. This preserves the user rule: **do not rerun the long five-platform Native Labs for this repair**.

### Final interpretation / anti-regression rule
- The former macOS/Windows missing terminals remain classified as **harness process-crash victims**, not provider regressions: macOS SIGBUS / Windows QuickJS access violation happened with concurrent providers in flight. Do not reopen those provider IDs as regressions solely from those terminated routes.
- TV StreamZo/The100 remains the canonical proof that adaptive provider traversal must not be coupled to inline production-player smoke: provider yield was positive before the player probe killed the fixture.
- iOS late-terminal interleaving remains the canonical reason watchdog restart must stop + drain the previous console generation and correlate terminals strictly after the exact current `PROVIDER_BEGIN`.
- Provider scope for this campaign is **46 Hub46 providers**. The historical-looking `96` represented adaptive fixture/title samples, not 96 executed providers.
- Future long Native Labs should be redesigned/bounded rather than repeated blindly. Existing evidence plus the new static/codegen contracts is the authority for this one-shot repair.
