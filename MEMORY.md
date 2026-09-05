# NiakVIO — Recovery Memory

Last authoritative rewrite: 2026-09-05.
This file is the recovery source of truth if ChatGPT/session context is lost. Prefer the current repository state over older chat summaries. Older retry-by-retry history remains available in Git history; this file intentionally prioritizes the current contracts and active blockers.

## Branch safety
- Active development branch: `workbench/provider-v3-performance-playback`.
- DO NOT write to `main` while the workbench is being completed and validated.
- Production/main remains a separate user-facing baseline until final acceptance/merge.
- All current Provider v3/runtime/yield/Lab/minifier/security work belongs on the workbench.

## Non-negotiable execution method
- Do NOT use the loop `one failing test -> one fix -> rebuild -> discover next test`.
- For every candidate SHA, collect ALL visible failing workflows/jobs first.
- Group failures by common root cause.
- Apply one batched correction for the full known set.
- Run cheap/unit/structural gates before another expensive 96/96 reconstruction.
- Manual reconstruction must execute the important cross-workflow contracts before materializing 96 providers, so stale test contracts fail early.
- When a newer reconstruction request supersedes an older one on the same branch, the older run should be cancelled rather than queueing/holding the branch.

## Primary target
- Catalogue target: ALL 96 providers, including disabled/off providers for structural completeness.
- A low yield such as 3/96 or 7/96 is a systemic regression, not an acceptable release state.
- Do not focus only on Kehflix/Castle/StreamZo or any small currently-working subset.
- Objective is the maximum real usable provider count, then native client/playback acceptance.

## Provider v3 architecture
A generated provider is composed from:
1. clean ProviderBase v3;
2. structured provider DATA;
3. provider-owned `PROVIDER.*` Lego;
4. shared `CORE.*` Lego.

Hard rules:
- Historical/upstream/published provider JS is knowledge/reference only, never an executable reconstruction seed.
- Provider envelope markers are mandatory:
  - `/* BEGIN NIAKVIO_PROVIDER */`
  - `/* END NIAKVIO_PROVIDER */`
- Provider Lego must precede exactly one Core boundary.
- Core Lego must follow that boundary.
- Managed Lego uses STARTFIX/CLOSEFIX + FIXDATA ownership.
- Reverse reconstruction must remain deterministic/byte-verifiable.

## Provider taxonomy
Use the existing architecture taxonomy; do not invent a parallel type system:
- `official_domain_hub`
- `api_stream_resolver`
- `html_scraper`
- `mixed_embed_resolver`
- `direct_media`
- `iframe_player`
- `quarantined`

Last structurally validated quarantine set was five providers:
- DVDPLAY
- MOVIEBOX
- NETMIRROR
- TOPCARTOONS
- VIXSRC

Frenchstream is NOT a permanent quarantine. `https://fstream.website/` is its maintenance/discovery hub; the provider itself uses a DLE-style business protocol and may remain activation-deferred until clean runtime proof.

## Canonical media type vs Nuvio transport — CRITICAL
This distinction must never be forgotten again.

### Canonical capability
`canonicalSupportedTypes` describes WHAT the provider catalogue semantically serves:
- `movie`
- `tv`
- `anime`

An anime-only provider can correctly have:
- `canonicalSupportedTypes = ["anime"]`

Do NOT add ordinary `movie` semantic capability merely because the provider can launch an anime film.

### Nuvio launch compatibility
`supportedTypes` is the transport/launch surface consumed by Nuvio.

Anime providers MUST be compatible with:
- `anime`
- `tv` for episodic anime / Nuvio series-shaped requests
- `movie` for anime films present in anime provider catalogues

Therefore this is valid and intentional:
- `canonicalSupportedTypes = ["anime"]`
- `supportedTypes = ["anime", "tv", "movie"]`

`movie` here is transport compatibility, NOT permission to return arbitrary non-anime movies.
Authoritative TMDB/canonical classification must still reject non-anime works for an anime-only provider.

Client aliases:
- `series`, `show`, `other` normalize to TV-shaped input.
- Anime may be discovered from trusted TMDB metadata and then transported to the provider through the real TV/movie namespace.

## TMDB / identity contract
Official Nuvio provider signature remains conceptually:
- `getStreams(tmdbId, mediaType, season, episode)`

Core owns TMDB metadata resolution/cache and normalized identity context.
Important gates:
- Non-launch provider events must return `[]` before provider/network work.
- Zero-output providers should not pay unnecessary TMDB work unless their declared DATA plan needs metadata BEFORE execution.
- Catalogue/title/external-id plans may require TMDB preflight.
- Ordinary direct plans can run first and only pay canonical verification after positive output.
- TMDB metadata cache must be request-safe and must not leak media context between works.
- External IDs such as IMDb must be retained/exposed when a provider protocol needs them.

## JSON stream-API family clarification
Some providers expose a JSON `streams[]`-style API. This is a SOURCE API contract, not a change of target client.
Nuvio remains the target runtime/client.
Do not describe the work as "moving to Stremio"; the task is adapting those source JSON responses into Nuvio stream objects.

DesiFlix/Persian-style live observation showed 200 responses with zero output when the provider identity was wrong/fell back to raw TMDB.
Commit `0691e922` added a runtime path that can obtain external IMDb identity from Core TMDB metadata before calling those source APIs.
This still requires validation on a reconstructed generation/yield; do not mark it solved merely because code exists.

## Source-plan/runtime recovery
The important systemic losses found during Provider v3 reconstruction were not only dead domains:
- business protocols were flattened into generic scraping;
- generic crawler ordering could waste budget on feeds/comments instead of download intermediates;
- some JSON APIs were treated as generic media URLs;
- some corrupted/templated routes survived into executable DATA;
- source-family classification could select the wrong handler.

Known family examples:
- Frenchstream: DLE POST/search -> news id -> movie/season/episode business endpoints -> players.
- MoviesHunt/HindMoviez/MoviesMod/UHDMovies/4KHDHub family: search/detail -> Abhilinks/HubCloud/VCloud/Driveseed-style intermediates -> final host.
- JSON stream-API family: source response objects need conversion to Nuvio stream rows after correct identity resolution.

Fix families/shared Core where possible; do not hand-patch 89 providers when one lost protocol explains many reds.

## Last authoritative live yield checkpoint
Fast-yield run `33927727936` tested the reconstructed v5 generation and still measured only 7/96 unique providers with playable output.
Across 188 provider/fixture executions the observed buckets were approximately:
- 116 HTTP errors;
- 36 network reached but zero result;
- 22 network/runtime exceptions;
- 11 positive execution rows representing 7 unique playable providers.

Conclusion:
- v5 crawler/parser improvements alone did NOT solve the systemic regression.
- 7/96 remains unacceptable.
- A new yield must be run only against the next verified reconstructed SHA; do not compare new code against the old 7/96 artifact and call it fixed.

## Current 2026-09-05 batch checkpoint
Parent workbench SHA before the current contract batch:
- `847e3ab6c0ee49b6b9e24b5c0c76269f1a76c5eb`
- message: `test: run batched Provider v3 runtime v6 rebuild`

Visible NiakVIO CI failures on that SHA were collected BEFORE another reconstruction:
1. `CORE - Media Type & Playback Gate`
   - `tests/canonical_media_types_test.py`
   - false/stale assertion said ANIDB anime-only must NOT expose `movie` transport.
   - Correct rule: canonical anime-only, but tv+movie transport compatible.
2. `CORE - Workflow Gate`
   - `tests/provider_stream_scope_architecture_test.py`
   - stale source-shape assertion expected an old local `var ns=...` implementation detail.
   - Correct invariant is semantic anime + namespace-preserving tv/movie provider transport.
3. `CORE - Verify & Publish`
   - `tests/native_five_lab_coverage_test.py`
   - stale hard-coded route counts `movie=82 / tv=92 / anime=40` mixed canonical capability with expanded transport compatibility.
   - Test must distinguish canonical route counts from transport route counts instead of freezing old transport totals.
4. GitHub Advanced Security failure on the same period was external infrastructure:
   - its Copilot/code-scanning agent requested `gpt-5.3-codex`;
   - GitHub API returned `400 The requested model is not supported`.
   - Do not classify that as a NiakVIO code defect.

The current correction batch must therefore:
- fix the three stale contracts together;
- add an explicit runtime regression proving anime movie -> canonical `anime`, provider transport `movie`;
- keep existing runtime anime movie support intact;
- move those contract tests into reconstruction preflight;
- make reconstruction concurrency branch-scoped with `cancel-in-progress: true`;
- then run CI once before triggering the next 96/96 rebuild.

## Native Labs
Final acceptance surface is exactly five first-class client/platform Labs:
1. TVAndroid — official NuvioTV
2. MobileAndroid — official NuvioMobile
3. MobileIOS — official NuvioMobile
4. DesktopMACOS — official NuvioDesktop
5. DesktopWindows — official NuvioDesktop

Labs are observational evidence only:
- no provider reconstruction;
- no repair;
- no mutation of Nuvio clients to manufacture greens;
- preserve reader/player errors.

Do NOT launch the full five Labs while the shared 96-provider runtime/yield is still structurally broken. First get structural gates + reconstruction + fast yield to a credible level; then use Labs for true client/runtime/playback proof.

## Playback / reader integrity
Kehflix previously produced `Cannot find sync byte / parsing_container_malformed` on a real user playback path.
Shared HLS Core now has opt-in bounded first-segment/container proof:
- preserve Referer/Origin;
- validate MPEG-TS sync or fMP4 structure when bytes are readable;
- reject positive HTML/JSON/malformed container evidence;
- network uncertainty/encrypted HLS remain non-blocking;
- stream-level failures must not disable the whole provider.

Final acceptance must inspect actual reader evidence, not only green workflow conclusions.

## Runtime platform contract
Authoritative comparison document:
- `automation/PLATFORM-RUNTIME-CONTRACTS.md`

Key differences that matter:
- all clients execute JS through QuickJS-compatible native runtimes;
- Android/TV and Desktop/iOS fetch bridges differ;
- TV lacks some capabilities exposed elsewhere (historically TextEncoder/TextDecoder and WebAssembly gaps were important);
- transport/header/subtitle/description/name projection differs by client.

Whenever upstream Nuvio client refs change, re-audit the platform contract instead of guessing.

## Minifier
- Terser is forbidden.
- `scripts/provider_v3_minimizer.py` is the NiakVIO-aware conservative minimizer integrated into materialization.
- It must preserve BEGIN/END provider envelope, STARTFIX/CLOSEFIX/FIXDATA, Core boundary and ownership comments.
- It must not rename identifiers, reorder expressions, fold literals or perform unsafe global replacements.
- Providers with risky template-literal state may remain byte-stable.
- Fixed-point + Node parse + reverse reconstruction + native parity are required.

## Security
The earlier 25 CodeQL high alerts were traced to a shared bad HTML-filtering regex shape in generated provider code.
ProviderBase/Core moved to deterministic HTML scanners and published provider bundles must remain gated against reintroduction.
Before final merge:
- final 96/96 generated bytes must pass HTML-filter security tests;
- npm audit/high dependency gate must be clean;
- CodeQL/security must be checked on the final branch/PR SHA;
- distinguish external GitHub security-agent infrastructure failures from actual findings.

## Workflow ownership
Routine workflow:
- `CORE - Verify & Publish` (`.github/workflows/sync.yml`)

Quick:
- static/runtime/unit safety;
- no reconstruction/repair.

Deep:
- broader read-only observation and report/manifest projection;
- still no provider repair/reconstruction.

Manual full reconstruction:
- `.github/workflows/provider-v3-reconstruct-all.yml`
- only path for full 96/96 materialization;
- workbench/non-main only for commits;
- rebuild from ProviderBase + DATA + owned Lego;
- reverse proof + runtime/integrity gates required.

LEARN:
- only automated code-evolution/repair owner;
- proposals/sandbox/PR flow, not silent production mutation.

Domain Refresh:
- only routine narrow DATA-write exception;
- official domain/config scope only;
- never a substitute full repair engine.

## Completion order from this checkpoint
1. Commit the full known contract batch (canonical vs transport tests + runtime anime-movie regression + reconstruction preflight/concurrency + this MEMORY rewrite).
2. Let all cheap/PR gates for that one SHA complete; collect ALL reds before touching code again.
3. If NiakVIO gates are clean, advance the reconstruction trigger once.
4. Reconstruct all 96 from the corrected shared runtime/DATA.
5. Require reverse rebuild + release/runtime integrity green.
6. Run one fast-yield 96/96 census against exactly that reconstructed SHA.
7. If yield is still weak, group all live failures by protocol/family and patch shared runtime/DATA in another batch; do not start five native Labs yet.
8. Once yield is credible, run all five native Labs on exact bytes and inspect reader/playback evidence.
9. Fix any client-specific/runtime/playback gaps, then final security/docs/clean/merge preparation.

## Never infer "done" from these alone
None of the following by itself means NiakVIO is finished:
- 96/96 files generated;
- reverse reconstruction 96/96;
- a green GitHub workflow;
- 3 or 7 providers returning streams;
- a few working providers on one client;
- a structurally valid manifest.

Done means the full requested workbench is coherent, yield is materially restored across the catalogue, the exact final bytes pass structural/security gates, and the five official Nuvio client Labs provide acceptable reader/playback evidence before merge.
