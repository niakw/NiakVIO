## 2026-09-12 — fix/labs-5.21.44-20260912 manual TV/Desktop regression checkpoint

- Work is intentionally isolated on branch `fix/labs-5.21.44-20260912`; **do not touch or merge `main`** until the branch is fully rebuilt, tested and reviewed.
- User explicitly requires every important diagnosis/correction/run state to be persisted into `MEMORY.md` so nothing is lost between chats. `.github/workflows/memory-checkpoint.yml` now accepts `fix/**` branches in addition to main/workbench.

### User manual TV regression corpus — authoritative UX evidence
- Interstellar: Purstream 720p (historically >=1080p), Castle 2 streams English+Hindi, Papadustream 480p, DesiFlix 4K+720p, **StreamZo returned a wrong documentary-like stream labelled `- Inconnue`**, VidRock returned one 720p stream that was actually HTTP 403 plus one valid 1080p stream, HindMoviez returned four 480p streams that did not appear playable. Reported quality labels were often lower/wrong versus visual quality.
- House of the Dragon S1E2: Purstream 720p, PersianStreamio 7 streams (6x1080p + 1x720p) apparently OK, Castle Indian-language streams apparently OK, DesiFlix streams apparently OK, VidRock 1080p + nominal 720p whose actual quality looked higher, HindMoviez four 480p streams apparently non-playable.
- Ragna Crimson S1E4: Anime-Sama returned one working 720p plus one `- Inconnue` stream that did not work; Mugiwara-no-Streaming returned one working 720p.
- Mushoku Tensei S3E11: no providers/streams loaded.
- HellMode S2E10: Anime-Sama one 1080p apparently OK; **Mugiwara-no-Streaming returned eight 1080p streams for the wrong episode** and labelled them VF although they appeared VOSTFR.
- Cross-title navigation still showed stale provider loading accumulating from one work to the next. Silent/dead providers appeared to disappear only after >1 minute, despite the intended shorter provider budget. Stream titles were no longer uniformly formatted; preserve detailed language/dialect information while restoring uniform branding/presentation.

### Existing branch fixes already proven by targeted runner
- Canonical provider execution timeout is being restored to **25 s** instead of the accidentally reintroduced 60 s budget.
- A→B→C navigation cancellation test passes even when native fetch ignores `AbortSignal`: older generations settle without re-injecting stale results.
- Stream safety is fail-closed for a VidRock-like 403 stream; a 403 URL must not be surfaced while another valid route may still survive.
- Verified HLS quality outranks declared quality: e.g. nominal 480p with a master proving 1080p is promoted to 1080p.
- Stream title/presentation normalization keeps detailed language labels (Hindi/Tamil/Telugu/etc.).
- Generic movie catalogue identity V21.10 is being strengthened so a result whose title merely contains the requested film name (e.g. a documentary containing `Interstellar`) cannot be accepted as the target film.

### Current rebuild blocker and correct recovery path
- The first real 96-provider rebuild failed specifically with `anime-sama: missing durable ProviderBase`.
- Do **not** reverse-reconstruct ProviderBase v3 from published/upstream provider JS. The repo already has the correct path: `scripts/materialize_provider_base_v3_store.py` rebuilds all 96 ProviderBase files from the NiakVIO-owned common skeleton + structured DATA, then `scripts/materialize_provider_v3_all.py` rebuilds all 96 bundles.
- `provider-bases/anime-sama--base--613e0ca190ebffec.js` exists in repository history/current indexed code, confirming this is store/provenance materialization debt rather than absence of a clean authoring source.

### Desktop/macOS evidence from user file `nuvio-tests-complets(1).log`
- This is not a provider-JS loading failure; prior evidence already showed no provider load errors and many extraction/runtime failures.
- **StreamZo native failure:** `getStreams error: 'setTimeout' is not defined` at request/metadata/recover path. Frenchstream shows the same runtime class. Provider execution-budget/cancellation code must work in QuickJS-like runtimes where global `setTimeout` may be absent.
- HindMoviez successfully found the correct Interstellar WordPress post via IMDb and entered the MvLink/HShare chain, but native execution also shows downstream DNS/timeouts; user-visible `480p` rows must be validated for actual playability before surfacing.
- VidRock native log shows real runtime HTTP failures (Interstellar API request HTTP 400; TV path HTTP 404) in addition to player timeouts. A valid sibling stream may survive, but failed/403/404 rows must never be surfaced as playable output.
- Anime-Sama native log shows broad alternate-slug probing for Interstellar; movie/anime capability and identity gates must remain before expensive provider work.

### Remaining work before this branch can be considered fixed
1. Rebuild ProviderBase store 96/96 from owned skeleton+DATA, then rebuild all 96 provider bundles.
2. Add QuickJS/no-`setTimeout` runtime regression and make timeout/cancellation budget implementation safe there.
3. Add generic episodic identity guard that rejects Mugiwara wrong-episode results, without provider-specific hard-coding.
4. Complete generic movie catalogue V21.10 guard and revalidate StreamZo wrong-media/documentary case.
5. Add/verify provider isolation test: dead/403/429/network-stalled provider must not postpone a healthy provider; each provider owns its own 25 s budget and fail-fast state.
6. Recheck HindMoviez/Anime-Sama failed rows through stream playability safety, quality recovery, title/language presentation, A→B→C stale suppression.
7. Re-run targeted contracts, full 96 rebuild/gates, then Mac + TV evidence on the exact branch candidate; remove temporary workflow only after durable evidence is stored.
8. Keep `main` untouched throughout this branch work.
