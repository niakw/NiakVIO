<!-- NIAKVIO_MEMORY_CHECKPOINT:2026-09-08-route-budget-parallel-sweep-v18 -->

## Checkpoint — 2026-09-08 — route budget + parallel provider sweep

### Current accepted main

- `main` HEAD at this checkpoint: `9c92f69cb1bd6eaa616583afc05ebde8604177be` (`chore: recompose published providers with current Core`).
- Published manifest version: **5.21.39**.
- 96 published providers were recomposed with the current shared Core; the publication transaction reached its fixed-point/Quick validation path before this checkpoint.
- The shared TMDB ownership correction is retained: STREAM_IDENTITY must consume the shared Core TMDB capability/cache when available instead of causing a duplicate TMDB lookup; fallback presentation tests use runtime credentials rather than treating the native fetch bridge as authentication.
- Do not mutate `main` with experimental V17/V18 route work. Route repair remains on the workbench until portfolio + Native Lab proof is complete.

### Repository branches / hygiene

The repository has been reduced from 19 branches to exactly **6**:
- `main`
- `brain-learning/proposals`
- `workbench/route-recognition-v14-search-plan`
- `dependabot/github_actions/actions/cache-6.1.0` (PR #98)
- `dependabot/github_actions/actions/upload-artifact-7.0.1` (PR #99)
- `dependabot/github_actions/gradle/actions/setup-gradle-6.3.0` (PR #97)

All old release/hotfix/tmp/workbench-v6 branches were removed only after proving their durable behavior/code was absorbed or superseded. Keep the three Dependabot branches only until their PRs are merged/closed. Keep the V14 workbench only while the current provider recovery campaign is active.

### CRITICAL route architecture rule — do not regress

**Evidence routes are not runtime routes.** The recovery/census report may observe and persist many request/response URLs, helper endpoints, redirects, player pages or other proof rows. These are evidence/provenance only and MUST NOT be injected wholesale into Provider DATA/runtime traversal.

Outside a genuinely exceptional provider protocol, the canonical executable entry-plan budget is **at most 3 semantic routes per provider**:
1. preferably **1 shared route/plan** when movie + series/anime are handled together;
2. otherwise **2 routes/plans**: `movie` + `tv/series`;
3. at most **3 routes/plans**: `movie` + `tv/series` + `anime`.

`series` is the transport alias of `tv`; it is **not a fourth semantic route**.

A canonical route/plan may itself describe a bounded proven multi-step protocol such as `search -> detail -> player/source`, but the runtime must not receive dozens of flat candidate URLs and crawl them opportunistically. `provider.model.routeData`/recovery reports may retain many observations for learning/debugging, while the projected executable plan must select/normalize only the minimal proven semantic entry route(s). Add an explicit <=3 executable-plan contract/gate so a report with e.g. 14/24/39 proof rows cannot silently become 14/24/39 runtime candidates.

This rule is especially important because current recovery logs can legitimately show large proof counts (for example 71 proof rows across the first 4K batch, including 24 UHDMovies and 39 VegaMovies observations) while only one canonical path may actually be needed to execute a provider. Never interpret proof count as desired runtime route count.

### Provider campaign execution mode — parallel without lowering proof quality

Do not return to `1 provider -> 1 retry` loops except for isolated residual reds. Current mode is **parallel family batches**:
- up to **6 GitHub jobs x 4 providers = 24 providers in flight**;
- each job still runs route recovery live, up to 3 attempts, targeted materialization, Provider CONFIG validation, episodic/media-type/dual-ID contracts, V16-V18 contracts and upstream-positive preservation;
- keep concurrency bounded around 24 so upstream rate limits/anti-bot responses do not create mass false negatives;
- as soon as one 4-provider job finishes, classify its rows and immediately recycle that slot with four new providers;
- expensive per-provider trace/player diagnostics run only for residual upstream-positive losses, not for every provider;
- track unique provider IDs when counting progress because some diagnostic batches intentionally overlap already-known pilots.

The pre-existing skip set contains 10 already-proven providers: `allwish`, `anime-sama`, `castle`, `hindmoviez`, `kehflix`, `neko-sama`, `playimdb`, `streamzo`, `videasy`, `wookafr`. They remain subject to global non-network/wrong-content/player guards even when skipped from targeted network repair.

### V17/V18 workbench state

Current generalized chain on `workbench/route-recognition-v14-search-plan` includes:
- V16 terminal execution authority;
- V17 search-detail bridge (current live origin preserved, canonical detail resolver, bounded player crawl fallback);
- V18 correlated provider-value plan;
- V18.1 scored JSON/provider slug identity;
- V18.2 provider-value plan executes before recipe/search/family;
- V18.4 JSON-text bridge + sanitized runtime trace;
- V18.5 canonical anime may execute through TV transport, but generic TV providers do not gain anime capability;
- V18.6 bounded Dean-Edwards packed-player decoding without eval;
- V18.7 bounded same-origin player route variants such as opaque `/embed|e|f|d|file|download/<id>` to `/v/<id>`;
- V18.8 bounded same-origin `form#F1` POST handoff + repacked source extraction.

All these remain experimental/non-published.

### Pilot results / root causes

#### AnimeKai / Movies4u
- These are the current successful V18 pilot providers and have produced playable results in the targeted workbench campaign.

#### Mugiwara
- Recovery proof: upstream original still produces anime streams (recent runs: 5-6 streams).
- The reconstructed runtime now correctly performs official search, resolves provider slug `jujutsu-kaisen`, and reaches `/catalogue/{id}/episodes/saison1` (`stage=step_response`, providerId=`jujutsu-kaisen`).
- It reaches multiple Smoothpre embed pages HTTP 200 but still returns 0 final streams.
- Do not regress the fixed search/slug/lane path while working on the downstream player resolver.
- A separate broad/concurrent quick-yield trace showed foreign Interstellar aliases such as `Csillagok Között` / `Tähtedevaheline` during a JJK-related run; treat possible fixture/alias context leakage as a systemic harness/runtime risk and verify per-task identity scoping before attributing every zero to the player.

#### FrenchStream
- Official/live recovery evidence remains positive for TV: recent upstream fingerprints returned 2 streams for Breaking Bad and 2 for House of the Dragon through fsvid/vidzy-family final hosts.
- Reconstructed runtime still returns 0 for positive FrenchStream pairs.
- Runtime trace showed `providerValuePlan` movie selected via `/index.php`, while TV currently lane-skips that value plan and must fall through the correct TV/search/episode protocol; do not manufacture a TV value route unless proven.
- Historical hub `https://fstream.website/` remains discovery/maintenance evidence, not a replacement for the actual DLE/search/detail/player protocol.

### Parallel sweep — launched/observed batches

First parallel wave:
- VF core: `purstream`, `flemmix`, `toflix`, `coflix`
- 4K/download: `uhdmovies`, `movieshunt`, `zinkmovies`, `vegamovies`
- API/direct: `4khdhub`, `4khdhubnew`, `persianstremio`, `desiflix`

Second parallel wave:
- VF catalogue: `papadustream`, `voiranime`, `frenchmanga`, `cestpasbien`
- anime core: `anidb`, `anikototv`, `hianime`, `animesama-co`
- API/resolver: `persianstremio`, `animekai`, `movies4u`, `movix`

First recycled anime slot:
- `animesalt`, `animevostfr`, `animoflix`, `animesultra`

Verified completed batch results so far:
- **4K/download batch:** target gate + global guard green; all four had recovery evidence (71 proof rows total), but only `movieshunt` became playable+verified in this run. No upstream-positive pair was lost. This is a canonical example of why dozens of proof rows must not become dozens of runtime routes.
- **API/direct batch:** target gate + global guard green; `desiflix` became playable+verified. `4khdhubnew` and `desiflix` each had one proven route in this passage; `4khdhub` had no proven route; `persianstremio` repeatedly returned HTTP 503 and had no proven route. No upstream-positive pair was lost.
- **Anime-core batch:** `anidb`, `anikototv`, `hianime` had no proven live route in that passage (`hianime` timed out through retries); `animesama-co` had 4 proven routes but its upstream-positive anime pair was lost by the reconstruction, so this batch is red and `animesama-co:anime` is a residual repair case.

### Completion sequence from this checkpoint

1. Add/enforce the **<=3 canonical executable semantic route/plan** projection contract before accepting further recovery DATA.
2. Continue the parallel 4-provider slot-recycling sweep across all remaining unique providers; preserve proof rows separately from executable route plans.
3. Group residual failures by family: no-proven-route/network, proven-route-but-zero, identity/context leak, player/resolver, protocol-specific exception.
4. Apply generic family fixes and rerun only affected batches; no provider/host hardcoding in shared Core unless the behavior is genuinely provider-owned DATA/Lego.
5. Once the 96-provider portfolio reaches the accepted preservation/wrong-content/stream-integrity gates, run the complete five Native Labs on the same candidate SHA: TV Android, Mobile Android, Mobile iOS, Desktop macOS, Desktop Windows.
6. Only after Labs/security/Quick/Deep are accepted, promote validated workbench changes atomically, clean the workbench/Dependabot branches as applicable, and write the final MEMORY checkpoint.

Never shrink the 96-provider catalogue and never hide failures by flooding runtime with recovered URLs.
