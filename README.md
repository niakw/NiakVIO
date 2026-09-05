<div align="center">
  <img src="assets/branding/niakvio-logo.svg" alt="NiakVIO" width="560">
  <br>
  <img src="assets/branding/nuvio-providers-logo.png" alt="NiakVIO Nuvio Providers" width="360">

  <p><strong>English</strong> · <a href="README.fr.md">Français</a></p>
  <p><strong>Community engine for aggregating, recognizing, testing, repairing and maintaining Nuvio providers.</strong></p>
  <p>96 Provider Objects · VO / VF · Mobile / Desktop / TV</p>
</div>

---

## Install

### General manifest — recommended

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/manifest.json
```

### French-focused manifest

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/vf/manifest.json
```

### General manifest without anime-oriented providers

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/no-anime/manifest.json
```

### French-focused manifest without anime-oriented providers

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/vf-no-anime/manifest.json
```

See [`docs/how-to-add-manifest.md`](docs/how-to-add-manifest.md).

### StreamBadge feed

```text
https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/stream-badges-fusion-v2.json
```

See [`docs/how-to-add-stream-badges.md`](docs/how-to-add-stream-badges.md).

> NiakVIO does not store or host video. It maintains provider metadata, structured knowledge, compatibility rules, manifests and client-side provider bundles.

> [!IMPORTANT]
> Named works in code, CI or documentation are deterministic **test fixtures**, not a content catalogue or a statement about third-party rights/licensing. See [`TESTING_NOTICE.md`](TESTING_NOTICE.md) and [`DISCLAIMER.md`](DISCLAIMER.md).

---

## What NiakVIO is

A provider can fail because a domain moved, an API changed, a player changed, a transport/container became malformed, an identity mapping is wrong, or one Nuvio client behaves differently from another.

NiakVIO adds a deterministic maintenance and validation layer between provider knowledge and official Nuvio clients. Its goal is **not to make the dashboard green by shrinking the catalogue**: all **96 Provider Objects** stay in the census, including disabled or unresolved providers, and missing evidence is kept distinct from proof of failure.

The mental model is deliberately simple:

- **Provider Object = black box** containing identity, DATA, routes, strategy, limits, evidence and provenance;
- **NiakVIO = brain** that recognizes, composes, validates, learns and publishes;
- **Nuvio clients = laboratory devices** that provide platform-specific extraction/transport/playback evidence.

<div align="center">
  <img src="assets/branding/how-it-works.png" alt="How NiakVIO works" width="780">
</div>

---

## Provider v3: canonical architecture

Provider v3 is reconstructed from **ProviderBase v3 + structured DATA/static knowledge + owned Provider/Core Lego + the NiakVIO-safe minimizer**.

Published `providers/*.js` files are content-addressed runtime artifacts. They are **never reconstruction seeds**. Upstream JavaScript is knowledge/provenance input only and is not executed as canonical source.

Canonical envelope:

```text
BEGIN NIAKVIO_PROVIDER
  ProviderBase v3
  PROVIDER.<ID>.CONFIG.V1  (STARTFIX / FIXDATA / CLOSEFIX)
  optional PROVIDER.* Lego
  NUVIO_GLOBAL_CORE_START_BOUNDARY_V1
  CORE.* Lego             (STARTFIX / CLOSEFIX)
END NIAKVIO_PROVIDER
```

Full 96/96 reconstruction belongs only to `.github/workflows/provider-v3-reconstruct-all.yml` on a non-main workbench branch and must finish with a byte-identical reverse rebuild.

Terser is forbidden. `scripts/provider_v3_minimizer.py` is a conservative pre-hash transformation that preserves line terminators, managed markers, literals and expressions.

See [`ARCHITECTURE.md`](ARCHITECTURE.md).

---

## Canonical route DATA

Route recognition now works directly on the unique Provider Object.

- canonical source: **`provider.model.routeData`**;
- `provider.model.routes`: compact projection derived from `routeData`;
- `provider.knowledge.recognizedContract.requests`: compatibility projection derived from `routeData`;
- structured fields such as `searchRoute`, `movieRoute`, `episodeRoute`, `*Path` and `*Endpoint` are scanned directly;
- onboarding source can be statically analyzed for variables, concatenations and templates **without executing provider JavaScript**;
- the process is idempotent: projections never become fresh evidence on a second pass.

The dedicated route-only workflow is `.github/workflows/provider-v3-reconstruct-routes.yml`.

### Latest verified route-only census

Run **`33949700926`** on 5 September 2026:

| Metric | Result |
|---|---:|
| Provider Objects analyzed | **96 / 96** |
| Reconstructed durable routes | **401** |
| HTTP-proven routes after idempotent normalization | **6** |
| Providers with non-empty `routeData` | **95 / 96** |
| Provider JavaScript executed | **0** |
| Full provider reconstruction invoked | **0** |

`topcartoons` is the single object with `routeData=[]`. That means **no durable route is currently identifiable from the available evidence**. It is not, by itself, evidence that the provider is dead or quarantined, and NiakVIO does not invent a route to turn the census green.

---

## Runtime contract

Provider JS is a specialized reader, not a crawler or a Learning engine.

- capability/media-type gate happens before provider network work;
- TMDB identity is canonicalized as `movie:<id>` or `tv:<id>`; anime is a semantic type, not a third TMDB namespace;
- incompatible providers return `[]` instead of performing arbitrary searches;
- TMDB enrichment is used only when the provider strategy requires it;
- Core output processing only matters after streams exist;
- zero streams never manufactures a result;
- a stream-level failure never automatically disables the whole provider;
- wrong-media success is worse than a clean zero-result.

---

## Reader, transport and playback

A `.m3u8` URL or `#EXTM3U` response does not prove native playback.

NiakVIO separates:

- provider extraction;
- title/year/season/episode identity;
- request context (`Referer`, `Origin`, headers);
- playlist/variant resolution;
- first-segment/container integrity when evidence requires it;
- native client/player outcome.

HTML/JSON disguised as media or positively malformed TS/fMP4 can be rejected. A timeout, temporary fetch failure, encrypted stream or missing byte API is **inconclusive**, not a reason to fabricate a provider-wide failure.

---

## CORE — Verify & Publish

`.github/workflows/sync.yml` is the routine **CORE - Verify & Publish** workflow.

**Quick** is fast and deterministic: structure/contracts, exact Provider v3 bytes, minimizer/security/Lab invariants. No provider repair, reconstruction or full network health.

**Deep** adds read-only network/hub observation, exact published-provider health, manifest reprojection, reports and integrity inventories. Deep still does **not** repair or reconstruct Provider JS.

Provider code evolution belongs to the independent Learning sandbox and reviewable proposals. Domain Refresh is separately constrained to validated `official_site` CONFIG DATA.

---

## Five native Labs

NiakVIO treats each official client/device as a separate compatibility boundary:

- **TV Android** — NuvioTV;
- **Mobile Android** — NuvioMobile;
- **Mobile iOS** — NuvioMobile;
- **Desktop macOS** — NuvioDesktop;
- **Desktop Windows** — NuvioDesktop.

The canonical matrix covers **96 providers / 214 declared routes**: `82 movie + 92 tv + 40 anime`. Disabled providers remain audited. A Desktop result never automatically counts as Mobile or TV evidence.

Labs are observational: they consume exact Provider JS bytes and can diagnose extraction, runtime, player, transport, missing-media and wrong-media failures, but they do not mutate Provider v3 to force a green result.

Official clients:

- [Nuvio Mobile](https://github.com/NuvioMedia/NuvioMobile)
- [Nuvio Desktop](https://github.com/NuvioMedia/NuvioDesktop)
- [NuvioTV](https://github.com/NuvioMedia/NuvioTV)

---

## Historical snapshots are not current provider truth

`provider-v3-materialization.json` and `automation/provider-v3-architecture.json.reference_reconstruction` retain frozen reconstruction snapshots needed for reverse-rebuild compatibility and auditability.

Older counts such as **91 executable plans + 5 quarantined plans** describe that historical materialization snapshot. They must not be reused as the current route-recognition, availability or quarantine truth. Current route recognition comes from `automation/provider-v3-static-knowledge.json` and `route_recognition.latest_verified_census`.

A quarantine needs an explicit, evidence-backed functional reason. `routeData=[]`, a timeout, a zero-stream result or one broken stream is not sufficient by itself.

---

## Publication and integrity

Publication is atomic and fail-closed and can include:

- `provider_catalog.json`;
- content-addressed provider bundles;
- `manifest.json` and its VF/no-anime projections;
- provenance/domain/LKG state;
- release hashes and allowlisted reports.

An inconsistent generation must never silently replace a healthy published state.

---

## Main workflows

| Workflow | Responsibility |
|---|---|
| `sync.yml` | **CORE - Verify & Publish** Quick/Deep; no provider repair/reconstruction |
| `provider-v3-reconstruct-routes.yml` | route-only recognition/canonical `routeData` census over all 96 objects |
| `provider-v3-reconstruct-all.yml` | manual full Provider v3 reconstruction + reverse byte proof |
| `brain-learning-lab.yml` | sandbox observation/repair learning + reviewable proposals |
| `domain-refresh.yml` | validated `official_site` CONFIG-only maintenance |
| `add-provider.yml` | structured provider onboarding |
| `native-mobile-android-reader.yml` | TV Android + Mobile Android evidence |
| `native-mobile-ios-reader.yml` | Mobile iOS evidence |
| `native-desktop-reader-acceptance.yml` | Desktop macOS + Windows evidence |
| `native-corpus-device-targeted.yml` | targeted device/provider diagnostics |
| `github-actions-gate.yml` | workflow/dependency security invariants |
| `codeql.yml` | CodeQL analysis |
| `weekly-upstream-provider-discovery.yml` | read-only upstream discovery |
| `purge-actions-history.yml` | old Actions-run cleanup |

---

## Repository policy

- `main` is production;
- structural Provider v3 work is validated on a workbench branch first;
- current route-recognition workbench: `workbench/provider-v3-recognition-routes-data`;
- Learning/proposal branches never become publication authority;
- official Nuvio repositories are consumed read-only;
- platform evidence remains platform-specific.

---

## Security, responsibility and independence

Provider JavaScript is treated as untrusted input. NiakVIO uses bounded workers, SSRF/network controls, sandboxing, identity checks, CI sanitization and fail-closed publication. Generic regex-based HTML stripping is forbidden by the Provider v3 security contract.

NiakVIO is an independent community project and is not affiliated with Nuvio or referenced third-party services. Nothing in this repository grants rights to third-party media/services or authorizes bypassing authentication, paywalls, encryption or access controls.

See [`SECURITY.md`](SECURITY.md), [`TESTING_NOTICE.md`](TESTING_NOTICE.md), [`DISCLAIMER.md`](DISCLAIMER.md), [`LICENSE`](LICENSE), [`NOTICE`](NOTICE), [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
