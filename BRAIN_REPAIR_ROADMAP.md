# NiakVIO — Brain Repair Roadmap and Decision Register

> **Actualisation audit du 7 novembre 2026** — [Analyse métier / sécurité / qualité](docs/NIAKVIO_BRAIN_METIER_SECURITE_QUALITE_AUDIT_2026-11-07.md). Pannes du validateur de durée/catégorie, remontée des identités et du parcours lecteur corrigées au niveau Brain ; aucune preuve de réparation vidéo encore validée. État de la sécurité : **377 alertes CodeQL High NiakVIO** lors du tri par manifeste (376 snapshots non référencés, une alerte de test #2531 corrigée dans `d5325feb` et à revalider en analyse), **0 alerte CodeQL Brain-LLM** après correction `b3031d36`, inventaire [42364586403](https://github.com/niakw/NiakVIO-Brain-LLM/actions/runs/42364586403). Dependabot/secret scanning restent **non vérifiés** via les droits disponibles. `0/17` repairs; ne pas considérer un status CodeQL « non-référencé » comme un effacement de risque client ancien.

## Synthèse de décision — français (7 novembre 2026)

**Statut constaté : 0 réparation de provider démontrée de bout en bout par le Brain ; 17 en file de réparation.** La présence de 21 statuts FULL est historique : 0/21 avait été retesté dans le census de référence. Le vrai critère de succès est un correctif produit par le modèle, appliqué aux octets exécutés, aboutissant à une vidéo réellement décodée et à l'identité TMDB/saison/épisode correcte, sans régression.

| Priorité | Décision ou action | Critère pour avancer |
| --- | --- | --- |
| P0 — Brain | Fiabiliser les retours négatifs, les métadonnées de lecteurs explorés et les critères de décodage | CI ciblée verte **et** nouveau run de réparation sur le SHA exact, avec artefacts |
| P0 — Première preuve | Obtenir une réparation causale, pas une modification de regex sans effet | ≥1 nouveau média décodé/identifié par le Brain, octets et relecture prouvés |
| P0 — Collecte | Distinguer les 16 lecteurs annoncés de 4KHDHub et l'unique lecteur réellement exploré | Trace des lecteurs visités/ignorés et cause de non-exploration, sans présumer une qualité 4K lisible |
| P1 — Générateur | Comparer Qwen 3B à un modèle de code plus puissant **sur les mêmes preuves et tests** | Plus de correctifs réellement valides, coût/temps/confidentialité bornés |
| P1 — Cohorte | Valider un exemple par famille, puis répartir les 17 providers | Les cas WAF, réseau, replay historique et erreur de provider restent distincts |
| P1 — Sécurité/épisodes | Maintenir CodeQL, TMDB, épisodes S00, mini-séries et saison incorrecte | Vérifications au SHA actuel et lecture terminale, pas une URL ou un job vert |

**Dernier progrès d'infrastructure :** le retour d'expérience conserve maintenant l'exploration réelle des lecteurs, et le validateur reconnaît l'amélioration « lien déjà retourné mais non décodé → média désormais décodé ». Les deux changements doivent rester soumis aux tests réels avant toute promotion de provider. Les décisions, preuves et limites détaillées figurent plus bas dans ce document.

> **Baseline: 2026-11-07, Europe/Paris.** This is an evidence-led execution roadmap, not a claim that broken providers are repaired. All acceptance decisions must reference the **actual tested source SHA and immutable run/artifact**. Do not confuse historical/carry-forward FULL status with freshly decoded playable content.
>
> **Source checkpoint:** NiakVIO `06eaea585f637e080c2956ac22737e79926b200b` · Brain-LLM `6284be0eecadb04d9fc242917af268ef73e53a75` (Brain CI successful; hosted replay pending). Current protected working branch: `main` in both repositories; no repair candidate has publication authority.

## 1. Decision dashboard

| Indicator | Last evidenced value | Interpretation / limitations |
| --- | ---: | --- |
| Verified repairs performed end-to-end by Brain | **0** | The only admissible success is generated → applied → materialized → executed → media decoded and identity-verified → regression-safe → persisted. |
| Active repair queue | **17** | From `automation/provider-census-status.json`; includes two replay-only historical candidates. Do not extrapolate to all 800 future hubs. |
| Current census inventory | **46** | 21 FULL, 3 PARTIAL, 2 CANDIDATE, 10 ROUTE, 2 CHAIN, 1 NO PROOF, 2 REGRESSION, 5 DISABLED. |
| Fresh full proof in last authoritative census | **0/21 FULL; 0/3 PARTIAL** | All FULL/PARTIAL positive classifications were **carried**, not replayed in that census. Run `42321364499`; see `PROVIDER_CENSUS_STATUS.md`. |
| Best demonstrated mutation | **Generated + applied + differing executed bundle bytes** | Hosted run `42358985990`, 4KHDHub; nevertheless **0 accepted, 0 decoded**. |
| Reader exploration gap in that proof | **16 announced candidate players, 1 explored** | Announced 1080p/2160p is not a verified playable variant. Baseline and candidate both returned 0 streams. |
| Film/series/anime fixture mismatch in Brain sandbox | **Correction landed, CI gates passed** | NiakVIO `f751cc7` + `09b9c10`; Core gate `42358986168`, non-regression `42358986032` succeeded on `09b9c10`. End-to-end Brain still failed. |
| Learning after an executed but ineffective decoded patch | **Brain unit CI SUCCESS; hosted replay pending** | Brain-LLM `057d8d0` / `1f7096b` recognizes `decoded_repair_no_new_fixture_control` and preserves real player-fanout gains before rotating source locality. Do not count as repaired until tested. |
| Security release gate | **Unverified/blocked** | `42359913056` displayed SUCCESS but log said `FIELD_CODEQL_STALE_2531_DEFERRED` due to source drift. A green retirement workflow is **not** confirmation #2531 is closed. |
| ~800-provider/hub ambition | **Not qualified** | No evidence of autonomous repair portability at that scale. No mass import/promotion before family-level proofs. |

Useful evidence: [Hosted 4KHDHub run](https://github.com/niakw/NiakVIO/actions/runs/42358985990) · [Brain evidence report](automation/hosted-repair-evidence/42358985990.json) · [Evaluation](automation/hosted-repair-evidence/42358985990-evaluation.json) · [Current census](automation/provider-census-status.json) · [Architecture](BRAIN_REPAIR_ARCHITECTURE.md).

## 2. Milestones and exit criteria

Status key: **DONE** = correct scoped implementation with exact test evidence; **IN PROGRESS** = change published but incomplete validation; **BLOCKED** = prerequisite or observed failure; **OPEN** = not yet evidenced; **GATED** = intentionally withheld until prerequisite succeeds.

| ID / priority | Milestone | Status 2026-11-07 | Observable exit criterion | Blocker / decision |
| --- | --- | --- | --- | --- |
| R0 · P0 | Reconstruct current state and prevent false success | DONE (inventory), continuous | Record branch, SHA, model SHA, run, artifact, fresh/carry status, actual decoded and accepted count for each conclusion. | Census positive carry-forward is not live media. |
| R1 · P0 | Correct category-specific strict fixtures and durations | DONE for code+Core tests; runtime still insufficient | Existing film/TV/anime contracts chosen by manifest; accurate duration and TMDB; same immutable fixtures before/after; no wrong-episode promotion. | Current strict evaluation has 0 decoded proof. |
| R2 · P0 | Learning-feedback parity for executed decoded failures | IN PROGRESS | Brain CI on `1f7096b` green, regression proves rotation only with unchanged player/variant coverage; next hosted run uses this exact Brain pin. | Existing NiakVIO hosted workflow used older Brain `0f559e4`. |
| R3 · P0 | Recover **one** causal Brain-generated repair | BLOCKED | A provider selected from real queue has new verified decoded playable media, correct title/TMDB/season/episode/duration, no lost previous fixture; final code bytes and SHA proven. | Qwen3B proposals mostly no-op/deletion or non-improving regex edits; 4KHDHub 16 players/1 explored. |
| R4 · P0 | Observe complete multi-reader/quality fanout | OPEN | Evidence for every discovered candidate's visited/skipped reason, terminal host, quality, audio and subtitles; improve exploration with bounded budgets and no unproven 4K badge. | Announced candidates are not crawled or playable candidates. Diagnose harness/runtime/network separately. |
| R5 · P0 | Recover historical CANDIDATE program exactly | BLOCKED | Recover precise historical program and bundle SHA; compile and replay on current source; validated current media. | `animesama-co` and `animevostfr` remat from current DATA is **not** historical Brain patch replay; run `42351582449`: 0 playable/0 verified. |
| R6 · P1 | Stronger generator A/B benchmark (without changing validator) | OPEN | Compare Qwen local vs interchangeable stronger hosted/GPU model on same source SHA, immutable fixtures, permitted scopes, token/time/budget; record edit causality, compiled/applied ratio, new decoded proof and spend. | Hosted/model secrets, cost ceiling and allowed sanitized context must be configured and verified. More parameters alone are not proof. |
| R7 · P1 | Family representative qualification | GATED on R3 | ≥1 independent Brain-produced, executed and decoded-positive repair for each *relevant observed failure family*, with regression suite. | Must not infer a family fix from same-name providers or manually injected fixes. |
| R8 · P1 | 17-provider bounded repair sweep | GATED on R7 | All eligible rows classified into repaired/blocked/external/needs-generation with per-provider evidence and no silent retry loop. Update census only on verified proofs. | WAF, replay-only, harness and network cases cannot be masqueraded as JS repair failures. |
| R9 · P1 | Protect TMDB, TV S00, miniseries and special-event identity | OPEN (live proof) | Cross-client end-to-end proof for film, ordinary episode, miniseries, cross-catalog special/S00 and wrong-season negative controls: **selected content = decoded terminal content**. | Prior Core heuristics do not identify opaque media. Explicit Spartacus S00/S201 ambiguity remains an acceptance test, not a claimed fix. |
| R10 · P1 | Release/security and projection | BLOCKED / separate | Actual CodeQL alert inventory and final gate verified on exact current HEAD; source→published bytes/manifest hashes reconciled; TV/Mobile/Desktop proof where available. | #2531 retirement success was deferred; published output is not implied by a repo commit. |
| R11 · P2 | Learn from validated solutions and expand toward hubs | GATED | Retain failure signature, executed candidate, negative outcomes and verified reusable function/Lego/pattern; prove one unseen hub/provider per family before scale. | 800-hub ambition unbenchmarked; no fresh verified family repair yet. |

**Recommended priority now:** R2 (exact-SHA CI) → R3/R4 together (one causal repair plus full reader coverage evidence) → R6 if the same evidence shows generator limitations → R7 → R8. Continue R9 and R10 as independent guards; never weaken identity, security or terminal decode criteria to make the scoreboard green.

## 3. Full current 17-provider queue

Source: committed `automation/provider-census-status.json` on checkpoint NiakVIO `3b07e1f`. Status/diagnostic labels are *not* current decoded playback proof.

| Provider | Census state | Dominant recorded symptom | Required lane / caution |
| --- | --- | --- | --- |
| `4khdhub` | ROUTE PROVEN | provider_network_zero_result ×2 | Brain synthesis; last attempted DOM token change yielded no streams; inspect player enumeration and source parsing. |
| `allanime` | CHAIN REACHED | provider_network_zero_result | Brain synthesis; HTTP 200 can still hide GraphQL errors/null results; prior Qwen no-op. |
| `allwish` | NO PROOF | provider_waf_challenge ×2 | Evidence/authority investigation first; do not synthesize provider JS on a WAF-only diagnosis. |
| `animekai` | REGRESSION PROVIDER | provider_network_exception | Brain synthesis only if proven code-causal, otherwise network/transport classification. |
| `animesalt` | ROUTE PROVEN | provider_waf_challenge | Browser/residential/transport differentiation before mutation. |
| `animesama-co` | CANDIDATE OK | provider_network_http_error | **Replay-only** historical candidate program; not a new mutation workflow. |
| `animesultra` | ROUTE PROVEN | timeout | Investigate execution/runtime and upstream latency; strict budgets. |
| `animevost-fr` | ROUTE PROVEN | provider_network_http_error | Classify provider-vs-upstream HTTP cause before coding. |
| `animevostfr` | CANDIDATE OK | provider_network_zero_result | **Replay-only** historical candidate program; not current DATA remat. |
| `flemmix` | ROUTE PROVEN | provider_waf_challenge ×2 | WAF/harness differential before provider mutation. |
| `mallumv` | CHAIN REACHED | provider_network_zero_result | Brain synthesis on real movie fixtures; earlier syntax-only edit failed strict proof. |
| `moviebox` | ROUTE PROVEN | provider_network_exception ×2 | Network exception layer and actual reader traversal. |
| `moviesmod` | ROUTE PROVEN | provider_waf_challenge ×2 | WAF/harness separation first. |
| `uhdmovies` | REGRESSION PROVIDER | provider_network_zero_result | Representative Brain synthesis; repeated Qwen no-op debt retained. |
| `vidfast` | ROUTE PROVEN | provider_network_http_error ×2 | Upstream HTTP, media identity and correct terminal reader. |
| `vostfree` | ROUTE PROVEN | provider_waf_challenge | WAF/harness differential before mutation. |
| `yflix` | ROUTE PROVEN | provider_network_exception ×2 | Separate environment, DNS/TLS and provider logic evidence. |

**Do not reinterpret WAF/network errors as proven provider-code breakage.** Do not hide the two candidate replay rows simply because source synthesis cannot process them. The queue remains 17 until independent, trustworthy criteria justify a status change.

## 4. Explicit failure taxonomy and decision log

| Observed signal | Owner to test first | Decision / next experiment | Never claim |
| --- | --- | --- | --- |
| Model no-op, cosmetic regex tweak, pure deletion | Brain generator, context/RAG, selection, negative-memory | Reject and rotate exhausted source unit; compare same fixture with stronger generator if repeated; persist failure fingerprints. | 'Provider repaired' from a valid JSON edit. |
| No candidate materialized despite generated patch | Brain converter, compiler, selector, apply/remat | Prove exact changed source bytes, bundle SHA and runtime trace; fix infrastructure before touching provider. | 'Executed' from generated diff alone. |
| Category/duration wrong | Brain evaluation/harness | Static + realistic movie/TV/anime strict fixtures on both baseline/candidate. | 'Model failed' from unrelated 24-minute anime check. |
| Zero streams, announced but unexplored readers | Provider traversal, Core/harness/network observation | Enumerate bounded players, actual visited/skipped causes and network progression before selecting edit locality. | 1080p/4K playable from metadata or announcement. |
| Candidate reproduces same 0/0 media result | Brain feedback and generation locality | Archive immutable negative; avoid repeating same unchanged program without genuinely new evidence. | Acceptance or promotion from byte difference. |
| Candidate historical label, patch bytes missing | Brain persistence/replay | Locate original program + full bytes and replay; otherwise mark unrecoverable and reconstruct with Brain under a new track. | Current DATA remat = historical candidate replay. |
| WAF, DNS, TLS, HTTP challenge, browser-only access | External/harness/transport | Diagnose egress and client differential; preserve negative. | Provider JS broken solely due to GitHub CI challenge. |
| Wrong TV season/S00/episode, opaque player | Core identity + provider extraction + client | Decode terminal identity or keep unverified; negative controls for S00/S201 and separate mini-series. | TMDB match from title alone proves correct video. |
| CodeQL job 'success' with drift/deferred diagnostic | Security workflow | Read log marker, alert API state and current HEAD Final Gate, then decide manual policy route. | Alert dismissed without explicit closure evidence. |

## 5. Definition of a verified repair

All boxes must be met for **one** concrete fixture, with no regression on previously passing fixtures:

- [ ] Exact source repository SHA, Brain SHA, manifest/fixture version and model identified; no undisclosed manual override.
- [ ] Failure reproduced, responsible layer and immutable baseline evidence recorded.
- [ ] LLM-generated candidate is a **causally substantive** change; not no-op, pure deletion or ad-hoc fixture cheat.
- [ ] Candidate compiled, applied, materialized, and exact executing bytes/bundle SHA recorded.
- [ ] Same content fixture replayed before/after with media player/server candidate exploration recorded.
- [ ] Terminal stream is **really decoded**; content identity, TMDB ID, season/episode or S00, duration, language, quality and headers checked as applicable.
- [ ] At least one new verified playable control; prior passing controls preserved; other declared lanes remain explicitly unresolved until tested.
- [ ] Negative/positive experiment and reusable family mechanism persisted in Brain Learning/RAG.
- [ ] Security, Core and provider non-regression gates run at the exact tested SHA; current source and published projection reconciled.
- [ ] Only then update status/census, `MEMORY.md`, this roadmap and release artifacts.

## 6. Decisions needed if progress stalls

**D1 — Generator**: After two genuinely distinct, source-backed generation attempts per representative family without a useful executable edit, benchmark stronger generation *on the same verified fixtures* instead of increasing blind retries. Compare success, latency, cost, privacy and regressions. Keep local Qwen for observation/routing if helpful.

**D2 — Transport**: If website/reader works only in browser or residential egress but not Node/client, invest in harness/Core transport reproduction before provider-code mutations.

**D3 — Provenance**: If exact historical candidate patch bytes are unrecoverable, label the replay gap explicitly; start a Brain reconstruction experiment, never transfer the historical 'CANDIDATE OK' badge as current proof.

**D4 — Scale**: Do not dispatch all 17 as 17 separate free-form generations until at least one validated family mechanism exists; benchmark controlled representative family waves first.

**D5 — Media correctness**: A playable URL without verified selected episode, season, duration and actual terminal decode does not close R3 or R9.

## 7. Maintenance and evidence update rules

1. Update this table only after checking `main`, actual HEAD, model pin, authoritative census state, latest hosted artifact, CI logs, security and any concurrent writes.
2. Each update records **tested SHA vs current HEAD**, outcome, relevant run/artifact, what was and was not executed, and unresolved limitations. An in-progress or superseded run never proves the newer HEAD.
3. Back claims with observable artifacts, not GitHub job color alone. A green workflow that emits `DEFERRED`, `SKIPPED`, `publicationAuthority=false`, or zero decoded media remains non-success.
4. Persist meaningful work in `MEMORY.md`; update `BRAIN_REPAIR_ARCHITECTURE.md` on structural pipeline changes.
5. Prefer Brain-owned fixes (observability, prompt/RAG, tooling, compiler/apply/remat, deterministic validator, learning persistence); do **not** manually fix a single provider to mask Brain incapacity.
6. Keep this document as a decision register. Its numbers are a timestamped snapshot, not an automatically refreshed live dashboard. Compare with the cited current JSON and CI before deciding.


### 2026-11-07 — Follow-up: no-gain reader exploration bridge

- Brain-LLM `057d8d0` (feedback extension) and `1f7096b` (regression test): Brain LLM CI [42360619339](https://github.com/niakw/NiakVIO-Brain-LLM/actions/runs/42360619339) **SUCCESS**; current memory-doc `6284be0` CI [42360846097](https://github.com/niakw/NiakVIO-Brain-LLM/actions/runs/42360846097) **SUCCESS**.
- NiakVIO `80e328f` repairs a second, independently proven loss: `run_hosted_brain_repair_loop.verification_feedback` correctly selected an individual executed evaluation row but silently discarded its `variantCoverage`. The Brain could not tell if a candidate had explored 1 or 3 actual reader requests. The shared Bridge now forwards **only four bounded numeric counts** (announced players, announced variants, explored player requests and max playable height). This is diagnostic context, never playable proof.
- `5402f16` tests unchanged vs increased real fanout, plus forbids raw hostnames/URLs in the next Brain request. `06eaea5` makes the hosted proof trigger on this bridge/test and requires the Brain negative-feedback contract before CPU inference. [Hosted run 42361093507](https://github.com/niakw/NiakVIO/actions/runs/42361093507) was queued at this snapshot; do not claim it passed or repaired a provider.
- **Decision remains unchanged:** first strict decoded, identity-correct Brain repair is still absent. Prioritize diagnosing the specific player fanout route rather than increasing blind generations. Later census/hosted results may supersede this static snapshot, only with explicit proven artifacts.


### 2026-11-07 — Décodage réellement nouveau malgré une URL déjà marquée « playable »

- Le comparateur strict `decoded_repair_gate` conditionnait une amélioration à `old.streams_playable == 0`, puis `new decoded controls > 0`. Une URL déjà comptabilisée « playable » mais **sans aucune image décodée** ne pouvait donc jamais être améliorée aux yeux du Brain, même si le correctif décodait effectivement le média attendu.
- Infrastructure Brain corrigée dans [`43f9e361`](https://github.com/niakw/NiakVIO/commit/43f9e3616f4cdb2016f905830498c0286db2b014) : compter une amélioration uniquement si `new_decoded_identity_safe_controls > old_decoded_identity_safe_controls`; préserver les contrôles de non-régression et d'identité. La validation par l'URL seule reste insuffisante.
- Test [`06ea7688`](https://github.com/niakw/NiakVIO/commit/06ea7688b9c1d29f00456d6fdcf911c7e4c06fa7) : même flux « playable » avant/après, décode absent avant et vérifié après. Exiger qu'il soit reconnu comme un gain strict. [Provider non-regression 42361530112](https://github.com/niakw/NiakVIO/actions/runs/42361530112) **SUCCESS** sur ce SHA ; [Core gate 42361530114](https://github.com/niakw/NiakVIO/actions/runs/42361530114) et [Brain hosted 42361530133](https://github.com/niakw/NiakVIO/actions/runs/42361530133) **en attente/en cours** au moment du constat. Aucun succès de réparation provider n'est affirmé.
