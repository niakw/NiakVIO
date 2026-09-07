<!-- NIAKVIO_MEMORY_CHECKPOINT:2026-09-07-correction-v8-chronology -->
## 2026-09-07 — CORRECTION to incident checkpoint: ProviderBase V8 chronology

This correction overrides one statement in the immediately preceding incident checkpoint.

- Earlier working diagnosis said ProviderBase **V8 API-recipe precedence appeared between 5.21.35 and 5.21.36** and could therefore explain the production regression specific to `.37`.
- That chronology is **wrong**.
- Exact verification against accepted **5.21.35 commit `9db07b3aa42ce2535ec1d7c19866beb43586badd`** shows published provider bundle `providers/purstream--nuvio--ec203db0a04b6453.js` already contains marker:
  - `/* NIAKVIO_PROVIDER_BASE_API_RECIPE_FIRST_V8 */`
  - including the `apiRecipe` precedence / `allowGenericFallback` logic.
- Therefore **V8 is not a new `.35 -> .36/.37` delta and must not be cited as the root cause of the sudden `.37` catalogue collapse without additional evidence**.
- V8 can still be architecturally problematic for V6 repair/multi-hop providers and may require redesign, but that is a separate issue from the production regression that appeared today.
- Future diagnosis of the `.37` collapse must compare exact published bytes and live behavior across exact 5.21.35 / 5.21.36 / 5.21.37 trees, especially V29/session/presentation and any DATA/Core rematerialization deltas, rather than inferring causality from source-generator chronology.
- Permanent rule reinforced: **before assigning a regression to a migration/version marker, verify the marker/behavior in the exact previously-good published bytes, not only in source generators or commit messages.**
