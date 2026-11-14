# Candidate intake — 14 November 2026

This is **NOT** a provider manifest or a parallel installation URL. All customer-facing links remain `manifest.json` (Global) and `vf/manifest.json` (France).

## User-defined target

- Global: approximately **20 verified movie / 20 verified TV / 20 verified anime** providers.
- France: separately **20 verified movie / 20 verified TV / 20 verified anime** providers, without duplicating new French-only IDs into Global.
- Never count a provider as functional because an upstream JS exists, a route responds, or an HTTP URL is returned.

## Actual first intake

Read-only tests of **8 Global + 6 France** candidates from the provided 11 Sep workbook (259 Global rows, 81 France rows), using exact upstream script hashes pinned to 40-hex Git commits, with genre-specific TMDB fixtures.

Global IDs: kisskh (#2), vidsrc (#9), reanime (#71), anizone (#90), topcartoons (#96), vidlink (#99), cineby (#106), cinemacity (#125).

France IDs: frenchstream (#1), movix (#3), french-anime (#28), dulourd (#34), franime (#39), nakios (#41).

The source workbook scores are discovery hints only, **not a 2026-11-14 health proof**.

## Execution / evidence ladder

`PROVIDERS - Global France Intake Terminal Probe`:

1. Validate unique, region-disjoint IDs and allowlisted, immutable upstream Git SHA references.
2. Download JS into an isolated, short-lived runner; static syntax check; invoke via existing sandboxed `provider_worker.cjs` with bounded network budgets.
3. Rotate film / TV / anime fixtures and invoke the existing terminal media/HLS verification from `run_provider_upstream_parity_v3.py`.
4. Persist sanitized counts, classifications and errors; **never include URL, cookie, authentication token, or JS** in evidence.
5. **No provider is activated** as a result of this workflow. Terminal bytes prove only a candidate reached media on the runner; title/episode identity, quality, subtitles, and native playback remain unverified. Providers with nonterminal player URLs are not positives.
6. A successful candidate can then enter NiakVIO's **structured Provider v3 onboarding** and native TV/Mobile/Desktop acceptance. Only an accepted, materialized and read-validated provider can join the relevant production manifest.

Source code is upstream *diagnostic input*, **not** an executable provider bundle accepted by NiakVIO. This avoids the November 14 failure where unqualified foreign bundles were prematurely enabled and violated Provider v3/security/release gates.

## Known blockers

- **France-only architecture is no longer a blocker.** `add_provider.py`, batch staging, lifecycle authority, static/materialization ledgers, release version/cache synchronization and language projections now support first-class `general:false, vf:true` identities without inserting them into Global.
- Bulk onboarding still stages candidates as `disabled/pending` by design. A staged row is non-executable and does **not** imply playable media; promotion still requires terminal media, identity and native/client validation on the materialized Provider v3 bytes.
- Current production deliberately contains only the cohort that survived current-byte functional evidence; lifecycle-disabled and bulk-pending rows remain repair/onboarding knowledge, not quota fillers.
- Historic lifecycle-disabled sources must not be silently reactivated.
- A successful CI workflow, upstream terminal URL or route proof is not a native decoding proof.

### Current production baseline after lifecycle cleanup

- Release: **5.21.144**.
- Global: **45 visible / 13 active**, canonical active lanes **movie 6 / TV 6 / anime 9**.
- France: **34 visible / 10 active**, canonical active lanes **movie 4 / TV 4 / anime 8**.
- Catalogue union: **58 visible**, including **13 first-class France-only** identities.
- The 20/20/20 target remains a target, not a reason to reactivate rows lacking current terminal playback proof.

Goal: prove a representative source per failure/runtime family before broad promotion. Persist useful positive and negative source patterns for Brain/Learning.


## Résultat réel — A/B terminal source du 14 novembre 2026

- [Run #43538083385](https://github.com/niakw/NiakVIO/actions/runs/43538083385) : deux jobs (France et Global) **success**, 14 modules amont testés sur un corpus de 2 fixtures par genre.
- Global : **TopCartoons 1/2 anime** avec média terminal de type `video` sur *Dan Da Dan S01E01* ; les sept autres (KissKH, VidSrc, Reanime, AniZone, VidLink, Cineby, CinemaCity) ont **0 média terminal vérifié** sur ce corpus.
- France : **FrenchStream 2/4** (film *Thor* et série *Mr. Robot S01E01*, tous deux HLS) ; **Movix 3/4** (films *Spider-Man: Homecoming* et *Deadpool*, série *Le Jeu de la dame S01E01*, HLS) ; French-Anime, Dulourd, Franime et Nakios **0 média terminal vérifié**.
- **Important :** les résultats ci-dessus sont du code *amont* exécuté dans un worker GitHub, pas la version Provider v3 publiée, et sans validation d'identité terminale/bonne saison, langue, qualité ni décodage client. **0 provider promu** dans le manifest de production pour ce test. Au total 5 épreuves terminales positives sur 46 épreuves (2 films+2 séries pour 8 mixtes, etc.) — compter comme observations, pas comme cinq nouveaux flux fiables.
- Artefacts : `provider-intake-global-43538083385` et `provider-intake-france-43538083385` (détails HTTP, sans URL de stream). Résumé durable `automation/evidence/provider-intake-terminal-2026-11-14.json`.
- Les scores du fichier `automation/provider-intake-top-global-france.json` sont corrigés selon les nombres exacts du classeur septembre, sans interpréter un score comme une preuve fonctionnelle.
- Le dépôt conserve d'anciens Lego NiakVIO pour FrenchStream (`frenchstream_exact_runtime_v3.py`) et Movix (`movix_runtime_v1.py`) et des bases historiques `provider-old/`. Ils doivent servir de connaissances Brain pour reconstruction, **pas** être réactivés tels quels.


## Authorized open-archive candidate — Internet Archive

The supplied workbook also references **InternetArchiveProvider** in its hub/raw inventory. It is treated as discovery input only: the workbook itself marks the row non-verified.

NiakVIO now has a reusable `open_archive_public_domain` onboarding strategy. It is intentionally narrower than generic Internet Archive access:

- official origin fixed to `https://archive.org`;
- movie lane only;
- search requires `mediatype:movies AND licenseurl:*publicdomain*`;
- the item metadata endpoint must independently expose a `creativecommons.org/publicdomain/` license URL before any media is returned;
- title identity is matched to Core TMDB metadata and release year is bounded;
- only direct video files from the same Archive origin are emitted;
- the staged provider remains disabled until current materialized bytes pass the normal terminal/identity/playback census.

A provider-specific real fixture, **Plan 9 from Outer Space** (TMDB 10513), is used only for this provider. It does not replace the representative movie corpus for other providers.
