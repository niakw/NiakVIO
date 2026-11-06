# NiakVIO maintenance and cleanup audit — 2026-11-06

## Current verified state

- `main` is the only production branch; three refs existed before this cleanup: `main`, `brain-learning/proposals`, `fix/4khdhub-exact-css-class-20261101`.
- PR #252 is closed unmerged with failed media verification run [41702179015](https://github.com/niakw/NiakVIO/actions/runs/41702179015). Its diff and original SHA `a4cc1f5c1afd60fe64548fd8e5bf61d5c712af85` remain archived in GitHub and MEMORY.
- `brain-learning/proposals` is preserved because it is the active review/proposal lane.
- Projection Reconcile run [42303162753](https://github.com/niakw/NiakVIO/actions/runs/42303162753) succeeded; manifest v5.21.137 references 41 provider bundles. This does **not** prove every stream is correct or playable.
- Current census 42305322765 still reports 21 FULL / 17 repairQueue among 46 lifecycle entries (41 enabled).
- GitHub CodeQL main scan 42305731795 succeeded after host assertion hardening; the exact-SHA Security Final Gate must separately verify open High/Critical alerts.
- Community Discussions announcement [#273](https://github.com/niakw/NiakVIO/discussions/273) was successfully posted, and contributor docs were linked.

## Removed inert workflows

These legacy self-triggered workflows had no recurring dispatch/schedule and no live branch or working trigger. Their code remains in Git history:

- `.github/workflows/temp-anime-sama-config-rematerialize.yml`: only targeted deleted branch `tmp/provider-max-repair-proof-20260919`.
- `.github/workflows/temp-repair28-observable-resume.yml`: push on its own filename only.
- `.github/workflows/temp-resume-repair28-post-apply.yml`: push on its own filename only.

Active essential diagnostics **kept**: `temp-current-bytes-full-provider-census.yml`, `temp-targeted-regression-recovery.yml`, `temp-niakgpt-live-hydration.yml`. The emergency release finalizer is also kept pending separate review.

## Evidence and code retained deliberately

- `provider-old/` is the historical provider archive, not runnable current publication.
- `automation/provider-census-sharded-*.json` and `provider-waf-browser-session-*.json` are ongoing Brain evidence; bulk deletion would destroy experiment history and make diagnostics less reproducible.
- The large workflow inventory requires an explicit consumer/trigger audit; blindly removing `temp-`/old scripts would regress Labs, replay and publication.
- No direct provider patch is considered a repair. Core S00 v17 is published, but input runtimes and verified alternate-catalogue mini-series crosswalk still require evidence and remediation.

## To verify completion

The one-shot stale PR cleanup Action must show the exact deleted ref, then GET `/branches` must show only `main` and `brain-learning/proposals`. CodeQL and SEC - Final Gate must both be green on exact current bytes. Provider playback remains a separate status.
