<!-- NIAKVIO_MEMORY_CHECKPOINT:2026-09-07-main-rollback-v37-incident-v6 -->
## 2026-09-07 — CRITICAL recovery checkpoint: V6 repair progress, broken 5.21.37, rollback to 5.21.35, Anime-Sama wrong-content incident, mandatory publication invariants

This checkpoint supersedes older release-state statements where they conflict. It must be read before any future provider/runtime/publication work.

### Current production/main safety state

- Catalogue remains **96 providers**. Never shrink the catalogue to improve metrics.
- `main` was urgently restored to the **exact 5.21.35 published tree** after 5.21.37 caused a severe production regression where *Children of Men* exposed only Anime-Sama streams and launched unrelated ~2h58 content.
- Broken 5.21.37 was preserved before rollback as **`backup/main-5.21.37-broken-20260907`**. Never merge/restore that branch wholesale.
- The rollback was done by a normal non-force commit because branch protection blocked force-push. Production rollback must preserve history.
- A minimal Anime-Sama identity hotfix was proven on top of the restored 5.21.35 tree. PR **#100** is the safety patch candidate; it must not import V29 or other 5.21.37 reconstruction changes.
- Candidate validation run for the 5.21.35 Anime-Sama hotfix: **`34157621920`**. It proves: *Children of Men* => Anime-Sama `raw=0`, `playable=0`; no requests descend to the known wrong path; **95 other providers remain unchanged**.
- Verified candidate commit before clean publication work: **`5c145102...`**; generated Anime-Sama bundle **`anime-sama-fe222ff3b14216b2.js`**. Re-read exact current PR/main SHAs before any future merge because subsequent doc/bot commits may advance refs.
- Restored durable MEMORY writer commit on main: **`400a065c5832a19005a989e498bc6fa0360b915c`**.

### Exact Anime-Sama / Children of Men incident — root cause proven, not hypothetical

The bad media path was reproduced on both exact 5.21.35 and broken 5.21.37 using *Children of Men* identity (TMDB `9693`, IMDb `tt0206634`, expected runtime ~109 min).

Observed wrong path on the broken/provider runtime:
1. expected Anime-Sama slug `les-fils-de-l-homme` => 404;
2. provider-specific Anime-Sama fallback search runs;
3. its custom `searchSlugs()` logic takes early `/catalogue/<slug>` results without proving title identity;
4. observed unrelated catalogue slugs included **`lag`** then **`les-mikails`**;
5. runtime descends to an embed at **`ansembed.net`**;
6. embed resolves an HLS at **`vmcld.space`**;
7. media is technically readable but measured around **10,691.8 seconds (~2h58)** and unrelated to *Children of Men*;
8. downstream presentation stamped requested-work metadata such as *Les Fils de l'homme*, 2006 and expected duration ~109 min onto the wrong source, making the player-facing row look legitimate.

Critical conclusion:
- **The Roblox/unrelated ~2h58 stream was NOT created by V29.** It was reproducible on 5.21.35 too.
- 5.21.37 made the incident dramatically visible because many other providers disappeared, leaving the pre-existing Anime-Sama false positive almost alone.
- Wrong-content detection in Labs/probes correctly recognized **`strong_title_mismatch` / `identity_contradiction`**, but that diagnostic was not a mandatory runtime rejection boundary before provider-specific detail/player resolution.

### Why existing route/DATA/integrity checks did not stop Anime-Sama

Do not ever describe this incident as “Anime-Sama somehow bypassed a working global gate”. The architecture allowed a path that never invoked the gate.

- Route/DATA checks proved that observed routes and structured provider DATA were real/coherent. They did **not** prove that every search result selected by provider-specific code matched the requested work.
- Anime-Sama had a **provider-specific Lego/runtime path** with its own `searchSlugs()` behavior.
- That path extracted early catalogue slugs and continued toward detail/player without requiring a positive title-identity decision from shared Core.
- Structural integrity tests verified markers, Core presence, CONFIG shape, hashing/materialization, syntax and similar invariants, but did not prove **control-flow domination**: that every provider-specific path must pass the identity boundary before player/source resolution.
- Labs could detect wrong content after the source was already returned, which is too late for runtime safety.

Permanent invariant from this incident:
> **No provider-specific Lego, generic crawler, API recipe, Source Plan or fallback may reach detail/player/source resolution unless the work identity required by that plan has been positively established. Presence of identity code in the bundle is insufficient; execution must be dominated by the identity decision.**

For catalogue search specifically:
- **No positive title match => no candidate.** Type, year, provider ID, HTTP success or playable media can add confidence only after a positive title/identity match; they can never compensate for absent/contradictory title identity.
- An opaque playable URL is not proof of work identity.
- `playable` must never override `wrong_content` / explicit identity contradiction.
- Expected TMDB duration is work metadata, not measured source-media duration. Do not present expected duration as if it were a fact observed from the stream.

### Anime-Sama hotfix contract

The proven minimal 5.21.35 safety fix changes only Anime-Sama identity/search behavior and its generated bundle/projection as needed.

Required behavior:
- search result slug must be allowed only after positive title identity;
- *Children of Men* must produce **zero Anime-Sama streams**;
- no fetch to `lag`, `les-mikails`, `ansembed.net`, `vmcld.space` for this fixture;
- 95/95 non-Anime-Sama provider files remain byte-identical in the minimal production hotfix candidate.

Do not “fix” this by provider-specific hardcoding of *Children of Men*, Roblox domains, known bad slugs or duration alone. The rule is generic identity fail-closed.

### 5.21.35 -> 5.21.36 -> broken 5.21.37: global provider-yield regression

Anime-Sama alone does **not** explain why 5.21.37 showed almost no other providers. Treat the global disappearance as a separate systemic regression.

Important timeline and findings:

1. **ProviderBase V7 family-first existed already in 5.21.35.** Do not blame that change merely because family-first is conceptually risky; it is not the new `.35 -> .36` delta.
2. A dangerous **ProviderBase V8 “API recipe precedence”** change appears between 5.21.35 and 5.21.36. Commit identified: **`6a67049b4075160d38aecaa9d6c7820108da1ea0`**.
3. The V8 behavior effectively does:
   - if `apiRecipe` exists, execute recipe first;
   - if recipe returns streams, return them;
   - if recipe returns 0 and `allowGenericFallback !== true`, **return `[]` immediately**;
   - therefore do not reach Source Plan/generic/historical path that may have worked in 5.21.35.
4. V6 repair evidence later proved that many synthesized `apiRecipe`s were partial, polluted, stale or incapable of expressing multi-hop behavior. Therefore recipe precedence can systematically suppress providers even when their original/upstream path remains functional.
5. Broken 5.21.37 additionally introduced **V29 terminal/session changes** and rematerialized all 96 bundles again. Exact V29 commit found: **`6f74939efa11b2c886e82002c242b923a4f87f6c`**. Do not assume V29 is the sole global regression until `.35/.36/.37` same-run yield comparison proves it.
6. Earlier hypothesis that V29 providers cancel one another through shared `globalThis` was checked against current NuvioTV execution: TV creates a fresh QuickJS execution context per provider invocation, so cross-provider shared-global cancellation does **not** by itself explain TV catalogue collapse. Do not repeat that hypothesis as fact.

### V29 intended fixes — must be recovered without importing broken 5.21.37 wholesale

V29 mixed two legitimate concerns:

A. **Stream presentation cleanup**
- remove placeholder suffixes such as `- Inconnue`, `Unknown`, `N/A`;
- keep meaningful provider/quality/language presentation;
- synchronize final `title`/`name` presentation consistently.

B. **Stale/switch request settlement**
- native/host fetch may ignore `AbortController` and remain pending after provider/work switches;
- intended fix races host fetch against an abort/stale promise so stale work settles quickly and does not pile up;
- this is about stale invocation cleanup and performance, not provider route precedence.

Recovery rule requested by user:
- produce a **functional 5.21.37-equivalent** from restored 5.21.35, reapplying useful `.37` corrections one by one;
- **do not re-import 255 mixed commits or rematerialize 96 providers blindly**;
- **do not import ProviderBase V8 API-recipe precedence** unless redesigned and independently proven to preserve yield;
- preserve 5.21.35 provider behavior/bytes as baseline wherever a Core patch does not require a provider byte change.

Active candidate branch for this work: **`hotfix/5.21.37-functional-v2`**. It is based on restored/safe 5.21.35 + Anime-Sama safety context, not broken `.37` wholesale.

Files already staged on that branch for the new safe method include:
- `scripts/apply_v29_functional_hotfix.py` — intended to apply only V29 presentation + native abort race, while explicitly refusing V8/provider route/DATA reconstruction;
- `scripts/compare_quick_yield_preservation.py` — baseline-to-candidate provider preservation gate. Continue strengthening it to cover `raw`, `playable`, `verified`, and new wrong-content regressions.

### Mandatory before/after yield preservation gate — publication rule

This rule exists because `.37` structural tests were green while production behavior collapsed.

For any shared Core/ProviderBase/Lego change affecting published Provider JS:
1. run a live-yield **baseline** on the exact currently accepted tree;
2. apply only the candidate change;
3. run the same fixtures/providers in the **same workflow/environment**;
4. compare provider sets at minimum for:
   - raw/non-empty provider output;
   - playable provider output;
   - verified provider output;
   - wrong-content / identity-contradiction set;
5. rerun only candidate losses with adaptive retries to eliminate transient 429/timeout/reset noise;
6. **any baseline-positive provider still lost after targeted retry blocks publication** unless the loss is an explicit, documented wrong-content/security correction;
7. **any new wrong-content provider blocks publication**;
8. structural 96/96, hash, CONFIG, parse, unit/security tests remain necessary but are no longer sufficient.

Use existing `scripts/audit_provider_quick_yield.py` for portfolio-yield evidence. Do not publish a common runtime change based only on “96 bundles materialized”, marker presence or unit tests.

### V6 provider-repair progress as of incident

The repair branch work remains relevant but must stay separated from urgent production recovery.

Initial protected green/skip set was 9:
- `allwish`
- `anime-sama`
- `castle`
- `hindmoviez`
- `kehflix`
- `neko-sama`
- `streamzo`
- `videasy`
- `wookafr`

After real targeted repair, **PlayIMDb became the first V6 red -> green**, so protected skip became **10/96**. This does not mean only 10 historical providers work; it means only 10 had been promoted into the current V6 “proven green, do not re-probe” contract.

PlayIMDb acceptance:
- run **`34147372929`**;
- reconstructed result `raw=1`, `playable=1`, `verified=1`;
- both upstream-positive movie+TV lanes preserved `2/2`, `lost=0`;
- global 96-provider structural/runtime regression suite remained green.

V6 retry4 before later family fixes:
- targeted unresolved: 87; protected skip: 9 at that moment;
- 39/87 providers had live proven routes;
- 238 proven routes;
- 21 upstream-positive provider/type pairs observed;
- reconstructed portfolio for the 87 was still initially `raw=0/playable=0/verified=0`, proving that route recognition alone was not enough and the proof->runtime bridge was broken.

Key V6 common root causes already discovered/fixed or under active repair:
- false causal attribution: old recovery stamped final task stream count onto every request, making early metadata/search helpers look terminal;
- metadata helpers such as `arm.haglund.dev` / `v3-cinemeta.strem.io` must be evidence/identity only, never executable provider recipes;
- generic `directRoute` must not override valid typed movie/episode routes;
- absolute typed resolver recipes must not require an unrelated search/base gate;
- stream JSON containers such as `stream_urls` / `streamUrls` require bounded parser support;
- temp worker `MODULE_NOT_FOUND` was an environment resolution issue, not provider death: source providers copied into temp dirs could not resolve project-declared modules. After correction, 16/16 affected providers started without that error; do not classify those providers dead from old logs;
- AnimeZey exposed POST body proof/replay limitations. V9/V9.1 added fail-closed reusable text-body abstraction: bounded printable body, no secret/token patterns, must abstract fixture identity into placeholders; opaque static text remains non-reusable;
- NetMirror old quarantine/catalogue model was stale relative to fresh typed TV resolver evidence. V8 repair work changed it from zero provider fetch / lost upstream lane to `raw` output with upstream lane preserved, though stream-level playability remained unresolved due source HTTP behavior;
- Source Plan V10 corrected live search-domain authority, runtime domain replacements, fail-open from partial recipe toward Source Plan, season-aware catalogue scoring and obvious navigation noise;
- FrenchStream TV reached `playable=1/verified=1` under this work, but provider was not promoted because movie remained lost;
- PapaDuStream original contract confirmed as `TMDB -> IMDb -> /series/{imdbId} -> parse series page -> select S/E HLS`, with Origin/Referer. Never freeze fixture IMDb/HLS routes in DATA;
- multi-hop families (AnimeKai, Movies4u, MoviesHunt, Mugiwara, FrenchStream, PapaDuStream, VoirAnime family, French-Manga, Cineby) require structured dataflow/source plans, not flattened single-route recipes.

### Adaptive retry contract

User explicitly requested more per-provider retries where useful.

- Do **not** blindly run every provider N times.
- Retry only transients: timeout, connection reset, temporary DNS, HTTP 408/425/429 and suitable 5xx.
- Stop retrying after valid proof is obtained.
- Do not waste retries on structural failures such as missing module, unsupported plan, deterministic policy rejection or impossible source mapping; repair those at common runtime/sandbox level.
- Three targeted attempts is an acceptable current default for unstable providers; preserve previous positive evidence when current upstream is temporarily 429, but do not declare repaired until acceptance can be re-proven.

### Provider ON/OFF terminology — do not confuse it again

At the latest V6 checkpoint before the production incident:
- 96 total catalogue entries;
- **10 protected/proven V6 green** after PlayIMDb;
- 86 not yet promoted to that protected-green set;
- **0 provider had been proven definitively dead/irrecoverable**.

Important distinction:
- `enabled=false` / temporarily OFF in NiakVIO due insufficient current proof is **not** the same as “provider/site permanently dead”.
- No route proven from one census is unknown/inconclusive, not death.
- A provider may have historical/local success outside the strict V6 protected set. Earlier campaigns observed on the order of 30-40 useful providers in some local matrices; do not rewrite history as “only 10 providers ever worked”.

### Permanent anti-regression rules from 2026-09-07 incident

1. **Never publish a 96-provider common Core/ProviderBase change without same-run before/after live-yield preservation.**
2. **Never use a structural green result as proof of functional provider preservation.**
3. **Never allow provider-specific Lego to bypass mandatory identity decision boundaries.** Tests must prove control-flow behavior, not marker presence.
4. **Catalogue search is fail-closed on title/work identity.** No positive title identity => no detail/player/source.
5. **Playable is not identity.** HTTP 200/206, valid HLS, duration, provider ID, year/type alone cannot convert unrelated media into the requested work.
6. **Explicit wrong-content/identity contradiction is publication/runtime-fatal for that stream.** Never keep it merely as a diagnostic while returning the row.
7. **Expected metadata is not observed stream fact.** Keep requested-work title/year/duration separate from source-measured metadata.
8. **A new API recipe may be preferred only when its evidence/coverage is sufficient.** A zero-result partial recipe must not suppress a previously functional fallback/source plan by default.
9. **Do not rematerialize all 96 merely because a small shared source patch exists** unless generated bytes genuinely require it and yield preservation proves the result. Prefer byte-preserving/minimal targeted publication when possible.
10. **Rollback before extended diagnosis when production is clearly broken.** Preserve broken tree on a backup branch first; restore known-good public behavior, then reproduce off-main.
11. **Never debug production by weakening gates.** Wrong-content and player integrity guards must become stricter when contradicted evidence is observed.
12. **Always store incident/root-cause/checkpoint evidence in `MEMORY.md` before continuing major work.**

### Immediate continuation sequence after this checkpoint

Urgent production/release recovery takes precedence over broad V6 repair until a safe functional `.37` equivalent exists.

1. Confirm this checkpoint was appended to `MEMORY.md` and pending file reset.
2. Keep public main behavior on restored 5.21.35 plus only the independently proven Anime-Sama wrong-content safety hotfix when merged.
3. On `hotfix/5.21.37-functional-v2`, finish the preservation comparator (`raw` + `playable` + `verified` + wrong-content).
4. Run exact same-workflow `.35 baseline -> candidate with presentation cleanup only`; reject any lost provider.
5. Add native-abort/stale-session race separately and rerun the full preservation comparison; if it loses providers, fix/withdraw that part rather than publishing it.
6. Do not import ProviderBase V8 recipe precedence from `.36/.37`; redesign only on V6 repair branch with explicit fallback-preservation tests.
7. Verify *Children of Men* no longer exposes Anime-Sama wrong content in the final production candidate.
8. Verify representative movie/TV/anime yield is not below accepted `.35` baseline; retry only transient losses.
9. Run 96 structural/runtime/integrity/security checks.
10. Run the five Native Labs on one exact accepted candidate SHA.
11. Only then publish/version the functional replacement for broken `.37`.
12. Resume broad V6 repair of the remaining unresolved providers without re-probing protected greens unnecessarily.
