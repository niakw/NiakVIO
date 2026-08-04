# Contributing to Nuvio Providers

Thank you for your interest in improving this repository.

This project aggregates, tests, repairs, and publishes Nuvio providers while trying to keep the manifests stable, secure, and usable. Contributions are welcome, but every change must preserve the reliability of the published manifests.

## Before contributing

Please make sure that:

- your change is related to a provider, manifest, test, workflow, documentation, or repository tooling;
- you have tested the affected provider locally;
- you do not include credentials, private tokens, cookies, personal data, or copyrighted media files;
- you do not weaken existing security checks;
- you do not activate a provider without a reproducible runtime proof.

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

- use the hub as the primary source of truth;
- validate the resolved domain;
- reject unrelated redirects and known parasite domains;
- keep a safe fallback only when necessary;
- avoid replacing a working domain with an unverified candidate.

A domain resolving correctly does not prove that the provider works. The complete stream extraction path must still be tested.

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

## Manifest changes

Do not edit a manifest version or provider version without a corresponding functional change.

When a provider bundle changes:

- update the provider version;
- update every manifest that references it;
- verify that every referenced bundle exists;
- remove obsolete bundles only when they are no longer referenced;
- regenerate integrity and checksum files when required by the repository;
- keep the general and VF manifests synchronized where appropriate.

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

- preserve the existing repository structure;
- keep provider logic isolated when possible;
- reuse shared helpers instead of duplicating logic;
- add timeouts and clear error handling;
- avoid unbounded recursion, loops, or crawling;
- avoid excessive network requests;
- never log secrets or full private cookies;
- keep runtime behavior deterministic;
- return an empty result instead of a misleading or unsafe stream;
- document non-obvious parsing or fallback logic.

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

For the VF manifest:

- prefer confirmed VF streams;
- keep VOSTFR distinct from VF;
- do not guess the language only from the provider name;
- use domain or homepage language only as a fallback signal;
- preserve unknown language when no reliable evidence exists.

Incorrect language labels are worse than missing labels.

## Legal notice

This repository does not host video files.

Contributors are responsible for complying with applicable laws, platform rules, and repository policies. Do not submit copyrighted media, private access credentials, or mechanisms intended to bypass paid access controls.

## Code of conduct

Be respectful and constructive.

Technical disagreements should focus on reproducible behavior, logs, tests, and code. Harassment, insults, spam, or intentionally misleading reports are not accepted.

## Need help?

Open an issue with the `question` or `provider-help` label and include the smallest reproducible example possible.
