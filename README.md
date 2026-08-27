<div align="center">
  <img src="assets/branding/nuvio-providers-logo.png" alt="NiakVIO logo" width="300">

  <h1>NiakVIO</h1>
  <p><strong>English</strong> · <a href="README.fr.md">Français</a></p>
  <p><strong>A community engine that aggregates, tests, repairs and maintains Nuvio providers.</strong></p>
  <p>VO · VF &nbsp;•&nbsp; Mobile · Desktop · TV</p>
</div>

---

## Add NiakVIO to Nuvio

### General manifest — recommended ([How to add?](docs/how-to-add-manifest.md))

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/manifest.json
```

### French-focused manifest ([How to add?](docs/how-to-add-manifest.md))

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/vf/manifest.json
```

### StreamBadge feed — recommended ([How to add?](docs/how-to-add-stream-badges.md))

```text
https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/stream-badges-fusion-v2.json
```

Dark and light feeds are also available under `assets/`.

> NiakVIO does not store or host video. It maintains manifests, metadata, compatibility rules and provider bundles consumed client-side.

> [!IMPORTANT]
> **Work references are test fixtures.** Titles, years, seasons and episodes visible in the README, source code, CI logs or artifacts are deterministic **test identifiers** used to verify matching, compatibility and wrong-media regressions. They are not a content catalogue, an offer, an endorsement or a statement about third-party rights/licensing. NiakVIO must not publish media files, clips, subtitle payloads, decryption keys, access tokens or complete playback URLs. **Copyright exceptions and limitations differ by jurisdiction; NiakVIO does not assume that fair use, fair dealing, research/testing or any other exception applies, and grants no right to access or use third-party material.** See [`TESTING_NOTICE.md`](TESTING_NOTICE.md) and [`DISCLAIMER.md`](DISCLAIMER.md).

---

## Why NiakVIO?

Providers can break because of domain moves, API changes, player changes, expired runtime assumptions or client differences.

NiakVIO adds a maintenance layer between upstream provider repositories and Nuvio:

- one installation point;
- multiple upstream variants compared before promotion;
- bounded automated repair;
- final-media validation rather than URL-only checks;
- title/year/season/episode identity validation;
- explicit Mobile, Desktop and TV evidence;
- last-known-good preservation;
- atomic fail-closed publication.

The objective is not to publish the largest possible provider count. It is to publish useful providers with enough evidence to understand why they work or fail.

---

## Official Nuvio clients

- [Nuvio Mobile](https://github.com/NuvioMedia/NuvioMobile)
- [Nuvio Desktop](https://github.com/NuvioMedia/NuvioDesktop)
- [NuvioTV](https://github.com/NuvioMedia/NuvioTV)

NiakVIO audits the current official client HEADs and treats each client as a separate compatibility boundary. Desktop evidence never automatically counts as Mobile or TV evidence.

---

## Provider Engine V2 / ARCHI 2

`provider_catalog.json` is the canonical publication registry. `manifest.json` and `vf/manifest.json` are deterministic projections of the same catalogue.

```text
upstreams + published/LKG
          |
          v
 multi-variant discovery
          |
          v
 hubs / DNS / domains
          |
          v
 provider_catalog.json
          |
          v
 ProviderSpec + Resolver Core V2
          |
          v
 Evidence Matrix
          |
          v
 Repair Brain
          |
          v
 media + identity + language + playback context
      /       |       \
 Mobile   Desktop     TV
      \       |       /
          v
 fail-closed publication
      /             \
manifest.json    vf/manifest.json
```

See [`ARCHITECTURE.md`](ARCHITECTURE.md) and [`engine_v2/README.md`](engine_v2/README.md).

---

## Quick and Deep

The main provider pipeline is [`.github/workflows/sync.yml`](.github/workflows/sync.yml).

**Quick** handles routine maintenance such as hub/domain refresh, sibling comparison and bounded repairs.

**Deep** is reserved for broader reconstruction, new provider knowledge, larger evidence scopes and stronger identity/transport validation.

---

## Native Labs

NiakVIO validates real paths on official Nuvio clients:

- NuvioTV on Android TV;
- Nuvio Mobile on Android;
- Nuvio Desktop on native macOS and Windows.

The Labs distinguish provider extraction problems, runtime errors, player/client incompatibility, transport failures, missing media and wrong-media identity.

Named movies, series and anime in Lab configurations are **test fixtures**, not catalogue entries. Public evidence is intentionally minimized and sanitized. See [`TESTING_NOTICE.md`](TESTING_NOTICE.md).

---

## Repair Brain and Learning

The Brain classifies failures before attempting repair. It can reason about search, catalogue, episode, player, extraction, transport, playback context, identity and client-contract failures.

Learning runs in a sandbox and can preserve successful/failed strategies across runs. Production code is not silently rewritten from learning state; validated automated proposals remain review-gated.

---

## Publication and integrity

Publication is atomic and fail-closed and can include:

- `provider_catalog.json`;
- provider bundles;
- `manifest.json`;
- `vf/manifest.json`;
- provenance;
- domain/LKG state;
- release hashes.

Inconsistent generations must not silently replace a previously healthy published state.

---

## Main workflows

| Workflow | Purpose |
|---|---|
| `sync.yml` | discovery → repair → validation → Quick/Deep publication |
| `native-android-route-reader.yml` | official NuvioTV + Mobile native evidence |
| `native-desktop-reader-acceptance.yml` | official macOS/Windows Desktop evidence |
| `core-media-finalize-main.yml` | Core fixed point and publication integrity |
| `brain-learning-lab.yml` | sandbox Repair Brain learning |
| `github-actions-gate.yml` | workflow/dependency security invariants |
| `codeql.yml` | CodeQL analysis |
| `provider-results-readme-sync.yml` | positive native-evidence README synchronization |
| `external-code-audit.yml` | SonarQube Cloud / DeepSource / CodeScene evidence refresh |

---

## Repository policy

- `main` is the only production code branch;
- Labs use exact `main` SHAs;
- `brain-learning/proposals` stores sanitized learning memory only;
- automated Brain repair proposals require human review/merge;
- official Nuvio repositories are consumed read-only.

---

## International / jurisdiction-specific use

Copyright, related-rights, database, contract and technological-protection rules vary by country. NiakVIO's documentation does not choose or presume a copyright exception for users worldwide.

The repository follows a conservative technical policy: minimize persisted evidence, prefer metadata or lawful public previews/trailers when they can prove the same assertion, do not publish complete playback URLs or protected payloads, and never treat a successful test as proof of authorization.

Nothing in this repository grants a licence, waives third-party rights, authorizes circumvention of authentication, paywalls, access controls, encryption or technological protection measures, or authorizes conduct prohibited by applicable law or binding service terms. Users and contributors are responsible for the rules that apply where they act.

---

## Security, responsibility and independence

Provider JavaScript is treated as untrusted input. NiakVIO applies bounded workers, network/SSRF controls, provider sandbox hardening, identity checks, CI sanitization and fail-closed publication.

NiakVIO is an independent community project and is not affiliated with Nuvio or referenced third-party services. It does not determine the legal status, rights or authorization of third-party content/services. Use must comply with applicable law, third-party rights and relevant service terms.

See [`TESTING_NOTICE.md`](TESTING_NOTICE.md), [`DISCLAIMER.md`](DISCLAIMER.md), [`LICENSE`](LICENSE), [`NOTICE`](NOTICE), [`SECURITY.md`](SECURITY.md), [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
