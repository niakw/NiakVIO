# Contributing to Nuvio Providers

Thank you for your interest in improving this repository.

This project aggregates, tests, repairs, and publishes Nuvio providers while trying to keep the manifests stable, secure, and usable. Contributions are welcome, but every change must preserve the reliability of the published manifests.

## Before contributing

Please make sure that:

- your change is related to a provider, catalog, manifest projection, test, workflow, documentation, or repository tooling;
- you have tested the affected provider locally;
- you do not include credentials, private tokens, cookies, personal data, or copyrighted media files;
- you do not weaken existing security checks;
- you do not activate a provider without a reproducible runtime proof;
- you do not create a second provider publication pipeline or a second source of truth outside ARCHI 2.

## Types of contributions

You can contribute by:

- fixing a broken provider;
- updating a provider domain;
- adding or improving official hub resolution;
- improving movie, series, anime, language, or quality detection;
- fixing stream extraction;
- rejecting invalid, fake, blocked, or non-video URLs;
- improving tests, diagnostics, documentation, or workflows;
- reporting a provider that no longer works.

## Reporting a broken provider

Open an issue and include as much useful information as possible:

- provider name;
- manifest used: general or VF;
- media type: movie, series, or anime;
- title tested;
- year, season, and episode when relevant;
- expected language;
- result observed in Nuvio;
- error message or log;
- date and approximate time of the test;
- platform used.

Do not publish private cookies, authentication tokens, or personal information.

A useful report should distinguish between:

- provider missing from the manifest;
- provider visible but returning no stream;
- search page failure;
- title page failure;
- episode selection failure;
- embed or player extraction failure;
- final stream blocked, invalid, silent, too short, or unavailable.

## Provider requirements

A provider should only be considered functional when it can complete the full runtime chain:

```text
search
→ matching title
→ movie page or episode page
→ player or embed
→ final playable MP4 or M3U8 stream
```

A successful HTTP response is not enough.

The final result must not be:

- an HTML page;
- a JavaScript file;
- a font;
- an image;
- a tracking URL;
- a WordPress endpoint;
- a Cloudflare beacon;
- a fake or troll playlist;
- an unresolved embed;
- a blocked or expired URL.

When relevant, the provider must correctly handle:

- movie;
- TV series;
- anime;
- season and episode selection;
- VF, VOSTFR, and VO labels;
- quality information;
- required headers such as `Referer`, `Origin`, or `User-Agent`;
- domain changes through an official hub or trusted resolver.

## Domain and hub updates

Do not hardcode a new domain without checking whether the provider has an official or trusted hub.

When a hub exists:

- use the hub as the primary discovery signal;
- validate the resolved domain;
- reject unrelated redirects and known parasite domains;
- keep a safe fallback only when necessary;
- avoid replacing a working domain with an unverified candidate.

A domain resolving correctly does not prove that the provider works. The complete stream extraction path must still be tested.

`domain-refresh.yml` is observation-only. Validated domain migrations are applied and published only by the canonical `sync.yml` transaction.

## Local testing

Run the relevant local tests before opening a pull request.

At minimum, test:

- one recent or popular movie;
- one second movie with a different title structure;
- one series episode when the provider supports TV;
- one anime episode when the provider supports anime;
- the final returned stream URL.

For VF-related changes, use representative fixtures such as:

```text
Interstellar
Les Gardiens de la Galaxie : Volume 3
Arcane S01E01
```

The returned URLs must be checked as real playable media, not only as reachable URLs.

Run the repository test suite:

```bash
npm test
node engine_v2/tests/provider-catalog.test.mjs
```

Run any targeted provider or pipeline test added by the repository when relevant.

Do not publish or activate a provider solely because mocked fixtures pass.

## Tests required for provider changes

A provider correction should include or update tests covering the bug being fixed.

Tests should verify, when applicable:

- correct title matching;
- correct media type;
- correct season and episode;
- correct domain or API route;
- correct player extraction;
- rejection of false-positive resources;
- final playable MP4 or M3U8;
- language and quality metadata;
- preservation of another provider with a similar name;
- rollback or LKG behavior when runtime validation is inconclusive.

Regression tests are strongly encouraged.

## Catalog, manifests and versions

`provider_catalog.json` is the canonical published provider registry. `manifest.json` and `vf/manifest.json` are projections, not independent sources of truth.

Do **not** manually maintain a provider change by independently editing both manifests or by inventing a cache-bump sequence. The publication pipeline owns finalization.

When a provider transaction is accepted, `sync.yml` automatically:

- imports the promoted candidate into the canonical catalog;
- renders the general and VF projections;
- bumps the provider patch when its client-visible row changed;
- rotates the case-only client ID for a genuine `disabled → enabled` recovery when needed to escape Nuvio's persisted local state;
- bumps the global release when the client-visible generation changed;
- synchronizes the release across the manifests, `package.json`, `package-lock.json` and `sources.json`;
- regenerates release hashes and validates integrity;
- remains idempotent when a rerun contains no client-visible change.

A contribution may update provider logic or canonical metadata, but it must not bypass this version/cache finalizer or add a competing bump helper.

Do not manually activate a provider that failed real runtime validation.

## Pull requests

Keep pull requests focused.

A pull request should include:

- a clear title;
- the provider or component affected;
- the root cause;
- the files changed;
- the tests performed;
- the result of those tests;
- any known limitation.

Example:

```text
Fix StreamZo TV episode extraction

- Adds season and episode selection
- Rejects Cloudflare beacon URLs
- Resolves supported embeds to final HLS
- Adds Arcane S01E01 regression coverage
- npm test passes
```

Avoid mixing unrelated provider repairs in the same pull request unless the change is a shared infrastructure fix.

## Coding guidelines

Please:

- preserve the ARCHI 2 control-plane invariants;
- keep provider logic isolated when possible;
- reuse shared helpers instead of duplicating logic;
- add timeouts and clear error handling;
- avoid unbounded recursion, loops, or crawling;
- avoid excessive network requests;
- never log secrets or full private cookies;
- keep runtime behavior deterministic;
- return an empty result instead of a misleading or unsafe stream;
- document non-obvious parsing or fallback logic;
- keep historical scripts as compatibility primitives only while they provide a function not yet replaced by V2.

## Security

Do not contribute code that:

- executes downloaded remote code;
- bypasses repository network guards;
- disables domain validation;
- exposes credentials or cookies;
- writes outside expected repository paths;
- silently uploads data;
- weakens sandboxing or worker restrictions;
- accepts arbitrary protocols or unsafe URLs.

Suspicious or unsafe contributions may be rejected even if they appear functional.

## Provider availability

Streaming websites, APIs, players, and domains can change without notice.

A provider may stop working because of:

- a domain rotation;
- a redesigned search page;
- an API route change;
- anti-bot protection;
- an expired player token;
- a blocked host;
- a removed title;
- an unsupported embed;
- an upstream outage.

Please avoid describing a provider as permanently fixed unless it has passed current runtime tests.

## Language and labels

For the VF projection:

- prefer confirmed VF streams;
- keep VOSTFR distinct from VF;
- do not guess the language only from the provider name;
- use domain or homepage language only as a fallback signal;
- preserve unknown language when no reliable evidence exists.
