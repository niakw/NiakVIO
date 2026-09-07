<!-- NIAKVIO_MEMORY_CHECKPOINT:2026-09-08-fast-v15-v29-provider-wave -->
## 2026-09-08 — Fast provider-repair loop, V15 status, V29 restoration gate

### Provider repair status and counting
- Catalogue remains 96/96. Zero providers are "never seen": all 96 have been through at least one general census.
- `automation/provider-repair-skip.json` is only the proven-green recognition skip set, not a complete count of working providers. Do not equate `skip=10` with "only 10 providers work".
- Last safe V13.2 portfolio proof had 11 playable / 10 verified providers with no new wrong-content after typed-recipe sanitation; historical local campaigns have shown 30+ positive providers.
- Latest merged route report has 46/96 providers with at least one live-proven route. Of the 86 not formally closed, 38 already have live-proven routes and mainly need reconstruction/stream-finalization; 48 still need fresh route/protocol requalification.
- Current priority recoverable upstream-positive wave: AnimeKai, Movies4u, FrenchStream movie, MugiwaraStream, then the remaining multi-hop positives, then the 48 without usable live proof.
- MugiwaraStream is explicitly recoverable: original/upstream is positive and the latest quick-yield reaches `/api/search` then `/catalogue/.../films`; its loss is after catalogue/detail, not evidence of a dead provider.

### New acceleration policy — mandatory without reducing quality
- Use `provider-repair-fast-targeted.yml` / `run_provider_repair_fast_targeted_v1.py` for iterative repair loops.
- Fast loop: run migrations/contracts + targeted upstream recognition + materialize only touched providers + targeted acceptance. Do NOT rematerialize all 96 for every failed experiment.
- Only after a targeted smoke produces a real positive gain may a common-runtime change pay the full portfolio before/after gate.
- Final acceptance still requires full portfolio preservation (`raw`, `playable`, `verified`, `wrong_content`) and the normal 96 deterministic/global contracts. Acceleration changes cadence, not proof quality.
- Retries remain targeted to observed losses/transient failures rather than rerunning all providers.

### V15 targeted smoke evidence
- Experimental branch: `workbench/route-recognition-v14-search-plan`; publication remains forbidden.
- V15 is provider-agnostic. It adds bounded explicit player attributes (`data-video`, `data-embed`, etc.), rejects arbitrary noisy `data-*` values as URLs, allows the current proven search-response origin locally for detail parsing, adds bounded catalogue article/title-year identity, and allows short third-party `/e/<id>` resolver traversal only after provider identity is established.
- V15 must not encode AnimeKai, Movies4u, FrenchStream, Mugiwara or their hosts/fixtures as runtime rules.
- Fast run `34166932027` proved the acceleration path works and fully reached live recognition/materialization in ~targeted scope instead of a full repair wave.
- Upstream recognition in that run: 4/4 targets proven, 48 total proven routes: AnimeKai 8, FrenchStream 14, Movies4u 16, MugiwaraStream 10.
- Merged report after targeted recognition: 46 providers proven, 319 routes, 23 recipes, 4 historical typed-direct recipes sanitized.
- Only the 4 target providers were rematerialized in the fast loop; 96 CONFIG and deterministic global output/identity/media-type guards still passed.
- V15 targeted result is NOT accepted: `raw=0 playable=0 verified=0`, upstream-positive pairs=5, preserved=0, lost=5 (`animekai:anime`, `frenchstream:movie`, `frenchstream:tv`, `movies4u:movie`, `mugiwarastream:anime`). No full portfolio gate should be run from this failed smoke.
- This failure is useful: routes are real, but the reconstruction/execution model still misses later multi-hop semantics. Diagnose per family from the fast artifact before another common change.

### Known deterministic provider-family gaps
- AnimeKai: reconstruction reaches correct search/watch/episode chain; remaining known gap is final server/player extraction from `data-video`/embed data and crawl semantics. Do not invent AnimeKai-specific route constants.
- Movies4u: live search request is proven and requires structured request context; search returns 200. Original chain selects a matching catalogue article/bookmark before `m4uplay`/resolver. Preserve title+year identity and same/current response origin without weakening movie-year contradiction rejection.
- FrenchStream: V13.2 recovered TV previously. V14/V14.1 regressed it and were rejected. Search/detail evidence may hit 429 on DLE search while secondary API routes return 200; treat this as availability/fallback evidence, not permission to overwrite a previously working TV path.
- MugiwaraStream: upstream-positive multi-hop provider; search/catalogue is live and working, so continue after the catalogue stage rather than classifying it OFF.

### Unique-provider patch debt
- Provider-specific runtime patches such as `anime_sama_runtime_v1.py` can exist when a provider protocol cannot yet be represented by global DATA/plan primitives.
- Do NOT prioritize deleting/consolidating those patches now. First maximize provider recovery.
- After provider recovery stabilizes, audit provider-specific runtime patches and absorb any patch whose behavior is expressible by the generalized Search Request Plan / Source Plan / identity / player primitives.

### Anime-Sama incident lesson retained
- Route/DATA checks being green did not guarantee that every provider-specific Lego path was dominated by the shared identity gate.
- The Roblox false-positive showed that a provider-specific `searchSlugs()` path could reach player resolution without positive title identity.
- Production `main` is currently 5.21.35 plus the narrowly validated Anime-Sama fail-closed hotfix; experimental V6/V14/V15 code must not be published there directly.
- Future integrity must test control-flow dominance/behavior, not merely presence of Core markers/routes/DATA.

### `.37` functional restoration / V29
- Rebuild the functional `.37` from the restored `.35` baseline; do not restore the broken `.37` tree wholesale.
- Presentation fix for `- Inconnue` has preserved portfolio behavior after targeted retry and is considered safe to retain.
- V29 native-abort/session source passes its dedicated synthetic race test, including a host fetch that ignores AbortController.
- Run `34163731580` still did NOT reach final live-yield after V29 because rematerialization failed on a stale shape assertion in `tests/provider_base_store_test.py`: it expects literal `requests < 7` while current bounded crawler uses the newer request budget. This is a test-contract drift, not evidence that V29 runtime failed.
- Update only the stale contract to assert the actual bounded-current behavior, then rerun the same `.35 -> presentation -> V29 -> full live-yield preservation` workflow. Do not authorize release until final live portfolio and Children-of-Men/Anime-Sama negative gate pass.

### Publication safety rules reinforced
- Repairing one provider/family must never silently regress another positive provider.
- Every common Core/ProviderBase change: baseline portfolio before, candidate after, compare raw/playable/verified/wrong-content, targeted retries for losses, fail on persistent loss or new wrong-content.
- A targeted provider improvement is not sufficient for publication.
- A route being live/proven is not equivalent to an end-to-end playable provider.
- Do not classify unresolved providers OFF merely because current reconstruction yields zero.
