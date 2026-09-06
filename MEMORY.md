# NiakVIO — Recovery Memory

Last authoritative rewrite: 2026-09-06.

This file is the durable recovery source of truth when conversation context is lost. Prefer the current repository state over historical chat summaries. Git history remains the source for retry-by-retry details; this file records the architecture, non-negotiable product decisions, current cleanup state, known failure families and release rules that must survive between sessions.

## Current repository topology

- Repository: `niakw/NiakVIO`.
- **Current and only active write target: `main`.**
- Durable Learning proposal branch: `brain-learning/proposals` is a passive proposal store, not an active implementation branch and never a direct publication authority.
- PR #91 was a closed, superseded reverse-sync attempt and must not be merged.
- Historical `chore/secondary-clean-*` / `workbench/*` refs are not active write targets and must not appear in workflow triggers or current instructions.
- All current secondary-clean changes have been fast-forwarded onto `main`.
- Before deleting any historical branch/PR, verify that no code, DATA, docs or generated artifacts needed for the final state exist only there.

## Execution method

- Complete the requested task; do not stop at a plan, diagnosis, first edit or first green test.
- Do not ask for confirmation when the next implementation/test step is already implied.
- Group failures by common root cause and batch corrections before expensive rebuilds.
- Use cheap structural/unit/security gates before expensive 96-provider materialization or native Labs.
- If a tool or test fails, diagnose, retry or use an alternate path and continue.
- Never claim a test or workflow passed if it was not actually executed.
- Before completion, re-check every requested deliverable.

## Current work priority

Primary provider recovery remains the strategic priority when live yield is weak, but the current active task is the requested secondary clean while the large Native Lab pile is already congested. Do not relaunch the full Native Lab pile merely for cleanup.

When provider recovery resumes, order of attention is:
1. recover and validate real executable routes/protocol DATA;
2. recover request semantics: method, body, encoding, headers, response kind and dynamic construction;
3. recover provider identity/media-type requirements;
4. materialize clean ProviderBase + DATA + Provider/Core Lego;
5. run yield and playback verification;
6. publish only after the required validation pile is accepted.

Catalogue target remains **all 96 Provider Objects**, including disabled/off entries for census and recoverability. Never shrink the catalogue to improve a metric.

## Provider v3 architecture

A generated provider is composed from:
1. clean ProviderBase v3;
2. structured provider DATA/static knowledge;
3. provider-owned `PROVIDER.*` Lego;
4. shared `CORE.*` Lego;
5. the conservative NiakVIO minimizer before content hashing.

Hard rules:
- Published/upstream/historical provider JS is knowledge/reference only, never a reconstruction seed.
- ProviderBase stays clean; provider-specific behavior belongs in DATA or owned Lego.
- Managed Lego uses `STARTFIX` / `CLOSEFIX` and `FIXDATA` ownership where required.
- Provider Lego precedes exactly one global Core boundary; Core Lego follows it.
- Reverse reconstruction must be deterministic and byte-verifiable.
- Terser is forbidden.
- Runtime provider JS is a specialized reader, not a crawler or Learning engine.

Conceptual runtime order:
```text
BEGIN PROVIDER
  gate provider selection/capability before network work
  if the provider protocol requires TMDB metadata before its first provider call
    resolve/cache the needed identity first
  endif
  execute the provider DATA/protocol plan
  if useful streams > 0
    run provider/core stream fixes, identity, presentation and sanitization
  endif
END PROVIDER
```

## Canonical media type vs Nuvio transport — critical

Never collapse semantic capability and client transport into one field.

`canonicalSupportedTypes` describes what the provider semantically serves:
- `movie`
- `tv`
- `anime`

`supportedTypes` describes how Nuvio may launch the provider.

An anime-only provider may intentionally expose:
```json
{
  "canonicalSupportedTypes": ["anime"],
  "supportedTypes": ["anime", "tv", "movie"]
}
```

`tv` is transport compatibility for episodic anime and `movie` is transport compatibility for anime films. These aliases do **not** make the provider a generic movie/TV provider. Authoritative identity logic must still reject ordinary non-anime works.

Castle-like generic movie/TV providers must not accept anime merely because anime can use TV-shaped transport elsewhere.

## TMDB / identity contract

Official Nuvio provider input remains conceptually `getStreams(tmdbId, mediaType, season, episode)`.

- Capability/type gate happens before provider network work.
- Non-launch events return `[]` before provider/network work.
- TMDB enrichment is paid only when the declared provider plan needs it.
- Catalogue/title/external-id plans can require preflight identity before the first provider call.
- Direct plans should not pay unnecessary metadata work.
- Identity/cache is scoped safely by work/type/season/episode.
- IMDb/external IDs remain available when provider protocol requires them.
- Zero streams never manufacture success.
- One broken stream never disables a provider globally.

## Source repositories: references, not runtime dependencies

Historical/provider repositories such as Gowaru, Yoru and All-in-One may be consulted during reverse engineering, but NiakVIO production reconstruction must rely on NiakVIO-owned DATA, observations and contracts.

- Do not require those repositories during ordinary 96/96 reconstruction.
- Do not embed or execute their provider JavaScript.
- Persist learned request/route/identity behavior into NiakVIO DATA.
- Repository/source shape is provenance, not runtime provider taxonomy.

## Route recognition contract

The generalized recognizer must statically and safely understand, where observable:
- literal URLs/routes;
- template strings and concatenations;
- variables passed later to `fetch`;
- dynamic paths/hosts while retaining meaningful provider path DATA;
- GET/POST/PUT/PATCH/DELETE;
- JSON/form bodies and body field names;
- `Referer` / `Origin` requirements;
- JSON vs HTML/text response evidence;
- search/detail/player/source/episode-index roles;
- TMDB/IMDb/title/season/episode identity dependencies;
- movie/tv/anime evidence;
- bounded static decoding of common string tables without executing JS;
- junk-route rejection for assets, helper files, admin/login/oEmbed and HTML attributes.

Fail closed on missing evidence. Do not invent routes merely because a shape looks plausible.

Durable route/protocol ownership is `provider.model.routeData`. Other projections are derived views, not new evidence sources.

## Important recovered provider examples

### Frenchstream
- Maintenance/address hub: `https://fstream.website/`.
- The hub locates/supplements the active provider; it does not replace the actual DLE-style search/detail/player protocol.
- Frenchstream is not a permanent quarantine.

### Kehflix
- Manual recovery proved the title -> player -> `/api/streams/...` chain and became a reference case for generalized route recognition.

### AnimeKai
- Search route: `/browser?keyword={query}`.
- Result/watch and episode paths are dynamically assembled.
- `data-video` is extraction evidence, not an HTTP route.

### AnimeZey
- Search uses worker-hosted `/1:search` behavior with POST JSON and provider-specific request fields/Referer evidence.
- Worker origins are DATA and may rotate; generic recognizer logic must not hardcode the provider.

### Anime-Ultime
- `/VideoPlayer.html` / `/VideoPlayer` are player route evidence; the historic problem was role classification rather than justification for another external dependency.

## Quarantine and provider health

Historically validated quarantine evidence included DVDPLAY, MOVIEBOX, NETMIRROR, TOPCARTOONS and VIXSRC, but quarantine is evidence-based and can change. Do not use it to hide missing reconstruction logic.

- Missing route evidence means unknown, not automatically dead.
- Zero streams from one request do not globally disable a provider.
- Stream-level failures are not provider-level disable evidence.
- Temporary timeout/fetch failure can be inconclusive.

## Runtime / player evidence

A `.m3u8` URL or `#EXTM3U` response is not proof of native playback. Keep distinct:
1. extraction;
2. identity;
3. request context/headers;
4. playlist/variant resolution;
5. media/container integrity;
6. official native player outcome.

HTML/JSON disguised as media or positively malformed transport/container data can be rejected. Temporary fetch failure, unsupported diagnostic byte access or encryption is not automatically a provider-wide failure.

## Five first-class Native Labs

Exactly five platform proofs are first-class:
1. TV Android — official NuvioTV;
2. Mobile Android — official NuvioMobile;
3. Mobile iOS — official NuvioMobile;
4. Desktop macOS — official NuvioDesktop;
5. Desktop Windows — official NuvioDesktop.

Native Labs are observational:
- consume official clients as-is;
- consume exact NiakVIO candidate bytes;
- test-only plumbing is allowed only when behavior-neutral and needed to expose the official path;
- **never patch NuvioTV, NuvioMobile or NuvioDesktop production behavior merely to make a Lab green**;
- upstream compile, dependency, packaging, runtime, player and QuickJS failures remain visible upstream evidence.

Known upstream evidence seen historically includes Windows QuickJS native crashes, Desktop API/test drift and NuvioMobile Android duplicate native-library packaging. These are not NiakVIO provider fixes.

The old Android helper `scripts/harden_nuvio_mobile_device_test.py` was an upstream-masking workaround and is intentionally removed.

## Workflow ownership

### `CORE - Verify & Publish`
`sync.yml` owns routine verification/publication.

- **Quick**: deterministic structural/runtime/unit/security/minimizer checks over candidate bytes.
- **Deep**: broader read-only network/hub/provider observations, diagnostics, projections and integrity evidence.
- Quick and Deep do **not** repair or reconstruct Provider JS.

### Learning
`brain-learning-lab.yml` is the isolated code-evolution/repair sandbox. Learning can produce reviewable proposals; it is not uncontrolled direct production mutation.

### Domain Refresh
`domain-refresh.yml` is deliberately narrow:
- validates official provider hubs/domains;
- updates only validated `official_site` CONFIG data;
- must not repair APIs/routes/Core/provider code;
- must not require unrelated staged candidate registries such as `staging/candidates.json` merely to refresh official domains.

The historical `missing staged candidate registry` failure was workflow coupling and must not be reintroduced.

### Full reconstruction / route recognition
- Full reconstruction/materialization owns ProviderBase + DATA + Lego generation and reverse byte proof.
- Route-only recognition/census updates route/protocol DATA/projections only; it does not rebuild Provider JS by implication.

## Version / cache / release rule — critical

**Do not bump provider/manifest/cache/release versions during cleanup or before the validation pile is accepted.**

Decision contract:
- route-only recognition/census with no published Provider JS byte change -> **no bump**;
- docs/tests/workflow-only cleanup with no published provider-byte change -> **no bump**;
- full reconstruction/materialization that changes published provider bytes -> a bump is required, but **deferred until the validation pile is accepted**;
- an applied Learning repair that changes published provider bytes -> same cache-safe bump rule;
- repeated identical materialization -> idempotent, no repeated bump;
- final accepted publication -> bump affected provider versions plus synchronized manifest/global cache/release metadata atomically, regenerate hashes/integrity and validate projections.

A temporary one-shot full-cache-bump workflow appeared on `main` before the pile was accepted on 2026-09-06. It was removed immediately by commit `c89d4e993da2f8c9b6038360b1d452a586a4a460`. Never restore that premature behavior.

## Minimizer contract

`scripts/provider_v3_minimizer.py` is the only production minimizer policy.

- Production enabled.
- Terser forbidden.
- Conservative, marker/comment-aware transforms only.
- Preserve `BEGIN/END`, `STARTFIX/CLOSEFIX`, `FIXDATA` and the Core boundary.
- No arbitrary replacements, identifier renaming, semantic reordering or risky folding.
- Template-literal providers may remain byte-stable when safe minimization cannot be proven.
- Final proof requires fixed-point/idempotence, Node parse where applicable, exact portfolio coverage and reverse reconstruction/native parity gates.

## Security contract

Security completion is measured on the exact final candidate bytes, not only on source scripts.

- Keep deterministic HTML/sanitization scanners; do not reintroduce unsafe catastrophic regex patterns.
- Do not disable CodeQL/security rules to obtain green CI.
- Keep bounded execution/network/resource/redirect/SSRF guards.
- Run dependency/high-severity audit where applicable.
- Review CodeQL on the exact final candidate SHA.
- Distinguish GitHub infrastructure/model/action failures from actual NiakVIO findings.

The historical cluster of ~25 CodeQL findings around shared unsafe HTML-filter regex behavior must remain fixed on final generated/published bytes.

## Documentation / repository hygiene

Current secondary-clean expectations:
- EN/FR README parity and visual assets under `assets/branding` / `assets/thanks`;
- recommended Nuvio stack: NiakVIO providers, UltraMax metadata/catalogue, SubSense subtitles, SIMKL tracking;
- architecture docs describe contracts, not stale frozen route counts;
- `ARCHITECTURE.docx` must be regenerated when normative `ARCHITECTURE.md` materially changes;
- `automation/PLATFORM-RUNTIME-CONTRACTS.md` must stay consistent with five-Lab/type semantics;
- PR template requires root cause, exact-SHA evidence, security, native/upstream responsibility and version/cache decision;
- remove stale deleted-workbench triggers and one-shot/retry/temp helpers after confirming no useful artifact exists only there;
- release hashes/integrity are regenerated only when final content is settled.

## Final publication completion order

When the provider pile is ready for release:
1. settle provider DATA/Core/runtime fixes;
2. materialize exact Provider v3 bytes;
3. conservative minimizer + fixed-point + parse/reverse proof;
4. structural/runtime/security gates;
5. provider/network/yield evidence;
6. five Native Labs, preserving upstream failures as external evidence rather than masking them;
7. accept the validation pile;
8. **then** perform synchronized provider + manifest/cache/release version bump if published bytes changed;
9. regenerate/validate release hashes, projections and integrity metadata;
10. final docs/changelog/release integrity review;
11. merge/publish;
12. delete superseded work branches only after verifying nothing required remains unique.

## Completion principle

A green structural workflow is not proof that 96 providers produce streams, and a native client failure is not automatically a provider failure. Keep each layer explicit, preserve evidence, fix common NiakVIO root causes where NiakVIO owns them, and never manufacture success by deleting providers or patching official Nuvio clients.
