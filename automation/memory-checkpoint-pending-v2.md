<!-- NIAKVIO_MEMORY_CHECKPOINT:2026-09-08-route-cap-parallel-sweep-v18 -->

## Checkpoint — 2026-09-08 — 5.21.39, runtime-route cap, V18 and parallel provider sweep

### Exact production state
- `main` HEAD observed at this checkpoint: `9c92f69cb1bd6eaa616583afc05ebde8604177be` (`chore: recompose published providers with current Core`).
- `manifest.json` and `package.json` are both synchronized at **5.21.39**.
- The 5.21.39 transaction recomposed the 96 published provider bundles with the current Core and passed the fixed-point/recomposition path before publication.
- Do not publish any V18 workbench experiment directly to `main`; workbench changes remain test-only until portfolio + Labs validation.

### Critical route-plan rule — user requirement, durable
This rule was discussed before and must not regress again:

**Many observed/proven HTTP routes are evidence; they are NOT all runtime routes.**

For one provider, the canonical executable runtime surface should normally contain **at most three semantic route plans/lanes**:
1. **one common plan** when movie/series/anime use the same protocol;
2. otherwise **two plans**: movie + series/tv;
3. only when anime is genuinely different, **three plans**: movie + series/tv + anime.

Exceptions above three require explicit proof that the provider truly has more independent protocols; they must not be created merely because the recovery trace observed many URLs.

Important implementation distinction:
- `routeData` / recovery evidence may retain many observed request URLs, hops, redirects, player pages and request shapes for provenance/debugging;
- the **runtime DATA must project that evidence into <=3 top-level executable semantic plans** under the normal contract;
- one semantic plan may itself be a structured multi-step recipe such as `search -> detail -> episode/player -> source`; those internal steps do not justify publishing every observed URL as an independent runtime candidate;
- do not dump 10/20/50 observed links into `NIAKVIO_PROVIDER_MODEL.routes` and let the runtime race them;
- choose the strongest proven request chain for each semantic lane, with exact method/body/header/origin knowledge and identity dependency;
- duplicated/fallback observations stay evidence-only unless a failure mode proves a bounded fallback is genuinely required.

The intended invariant is therefore effectively:
`evidence routes = potentially many` -> `canonical runtime plans = 1..3 normally`.

This cap is important for correctness as well as speed: uncontrolled route injection can cause wrong fixture aliases, stale domains, wrong movie/tv/anime paths, competing searches, network amplification and player/runtime instability.

### Identity/type rules still authoritative
- `canonicalSupportedTypes` is semantic capability (`movie`, `tv`, `anime`).
- `supportedTypes` is Nuvio transport compatibility; `series` aliases `tv` only at transport level.
- Anime may travel through TV transport but must remain canonically anime; a generic TV/movie provider must not gain anime capability from that alias.
- Capability/type gate happens before provider network work.
- Movie year remains strong/authoritative identity evidence.
- TV/anime series origin year must not be a hard reject; season/episode is authoritative for episodic selection.
- No cross-fixture identity/alias state may leak between movie/tv/anime tasks. Any broad-run trace where a Jujutsu Kaisen task searches Interstellar aliases (for example `Csillagok Között` / `Tähtedevaheline`) must be treated as invalid shared-context/cache contamination and investigated, even though a narrower targeted JJK trace has also been observed clean. Batch concurrency must preserve per-task TMDB/alias isolation.

### Active V18 workbench state
Active branch: `workbench/route-recognition-v14-search-plan`.

The generic repair chain currently includes:
- V17: SearchPlan positive identity -> canonical detail resolver -> player crawler fallback; preserve current live same-origin detail instead of immediately substituting stale domain data.
- V18 / V18.1 / V18.2 / V18.4: correlated provider-native identity (`id`/`slug` etc.) from proven search response, deterministic best identity row, JSON-text bridge, provider-value plan executed before recipe/search/family.
- V18.5: canonical anime may execute over TV transport only when the Provider Object is canonically anime; generic TV does not gain anime capability.
- V18.6: bounded Dean-Edwards packed-player decoding without `eval`.
- V18.7: generic same-origin opaque player route normalization such as `/embed|e|f|d|file|download/<id>` -> `/v/<id>` where proven by the player family; original path remains bounded fallback.
- V18.8: bounded same-origin hidden `form#F1` POST handoff, then packed-player/source extraction; no provider/host hardcoding.

All V18 changes are experimental/workbench only. `publicationAllowed=false` remains mandatory until the portfolio gate is explicitly satisfied.

### Pilot-provider state
Four providers were used for deep generic-family debugging before the wider sweep:
- **AnimeKai**: upstream and reconstructed runtime can produce streams; pilot is green.
- **Movies4u**: upstream and reconstructed runtime can produce streams; pilot is green.
- **FrenchStream**: upstream remains positive for movie/TV; reconstructed runtime still loses those positive pairs. Search/series protocol reaches real episode/player data and Multiup/player family; remaining issue is player/source resolution plus ensuring stale hub/domain substitutions never override a proven live origin.
- **Mugiwara**: upstream remains positive for anime. V18 fixed search -> provider slug -> `/catalogue/{id}/episodes/saison1`; the runtime reaches real player pages but still yields zero. Continue at the generic player/identity-isolation layer, not with provider-specific hardcoding.

### Parallel execution mode — speed without lowering proof quality
User explicitly requested that provider work stop proceeding one provider / one retry at a time.

New execution policy:
- process providers **in parallel batches grouped by failure family**;
- current practical ceiling: **24 providers active at once**, implemented as 6 jobs x 4 providers, to avoid turning upstream rate limiting into false negatives;
- each provider still gets the same proof-first recovery, materialization, identity/media-type contracts and `require upstream-positive preserved` acceptance logic;
- expensive per-provider trace/fingerprint diagnostics are only run on residual red providers after a batch, not on every green;
- when a 4-provider slot completes, immediately recycle the slot into four new providers;
- prefer one systemic fix that recovers a family of providers, then rerun the affected batch, rather than N provider-specific patches.

### Catalogue/sweep count at this checkpoint
- Catalogue target remains **96 Provider Objects**, including disabled/off objects for census/recoverability.
- Existing skip list contains **10 previously proven functional/corrected providers**: Allwish, Anime-Sama, Castle, HindMoviez, Kehflix, Neko-Sama, PlayIMDb, StreamZo, Videasy and WookaFR. They may be skipped by targeted repair yield but still remain subject to global non-network regression gates.
- 4 deep pilots: AnimeKai, Movies4u, FrenchStream, Mugiwara.
- Before the parallel sweep, **82 providers remained to be deep-processed** beyond the 10 proven-green + 4 pilots.
- First two parallel waves admitted 24 of those 82, then the first completed 4-provider slot was immediately recycled into 4 more; therefore **28 unique providers had entered the new parallel sweep at the time of this checkpoint**, leaving roughly **54 not yet started** from the original 82 (subject to jobs completing while this checkpoint is appended).

### First parallel-wave concrete result already known
Completed `anime-core` batch:
- AniDB: no proven live route in this passage.
- AnikotoTV: no proven live route in this passage.
- HiAnime: timed out repeatedly and ended with no proven route in this passage.
- AnimeSama-CO: 4 routes were proven upstream, but reconstructed runtime produced 0 and lost the upstream-positive `anime` pair.
- Shared V16-V18 contract tests stayed green; this is a runtime/yield failure, not a migration-contract failure.

That slot was recycled immediately into:
- AnimeSalt
- AnimeVOSTFR
- Animoflix
- AnimesUltra

Other parallel groups launched include VF catalogue/core, 4K/download, API/direct and API/resolver families. Continue consuming finished groups and recycling slots instead of serial waiting.

### Branch hygiene
The repository was reduced from 19 branches to 6 useful branches. Current intended set:
- `main`
- `brain-learning/proposals`
- `workbench/route-recognition-v14-search-plan`
- three Dependabot branches corresponding to the open dependency PRs

Old `tmp`, release 5.21.37, diagnostic and superseded workbench/hotfix branches were verified before deletion. After merge/close of the three Dependabot PRs, their branches should disappear. After V18 is integrated or abandoned with all useful content preserved, delete the workbench too.

### What remains after provider recovery
Do not stop after targeted yield improvement. Completion still requires:
1. enforce the <=3 canonical runtime-plan rule across recovery/materialization and add a contract test so evidence-route count can never explode the executable DATA;
2. complete the parallel sweep of the remaining catalogue and repair residual failure families;
3. full 96-provider portfolio run with upstream-positive preservation, wrong-content/identity guards and no regression of the 10 proven greens;
4. Quick + Deep on one exact candidate SHA;
5. all five Native Labs on the same candidate: TV Android, Mobile Android, Mobile iOS, Desktop macOS, Desktop Windows;
6. player/container validation remains stream-scoped; never disable a provider because one stream fails;
7. security/minimizer/docs/architecture consistency and branch/workflow cleanup;
8. promote only validated workbench changes atomically to `main` with correct release/version synchronization;
9. append another final MEMORY checkpoint with exact SHAs, final provider counts and five-Lab outcomes.

### Execution discipline
- Do not optimize metrics by shrinking the 96-provider catalogue.
- Do not invent routes.
- Do not equate an observed HTTP URL with an executable route plan.
- Do not let hubs/old domain substitutions override a live proof origin.
- Do not hardcode provider/host names into generic Core fixes unless the behavior is truly provider-specific DATA.
- Treat concurrent batches as independent tasks with isolated TMDB/media context and bounded network budgets.
- Preserve quality while increasing concurrency; if rate limiting makes evidence inconclusive, lower concurrency for that family rather than recording a false dead provider.
