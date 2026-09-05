<div align="center">
  <img src="assets/branding/niakvio-logo.svg" alt="NiakVIO" width="560">
  <br>
  <img src="assets/branding/nuvio-providers-logo.png" alt="NiakVIO Nuvio Providers" width="360">

  <p><strong>English</strong> · <a href="README.fr.md">Français</a></p>
  <h3>One maintained provider layer for Nuvio.</h3>
  <p><strong>96 Provider Objects · VO / VF · TV / Mobile / Desktop</strong></p>
  <p>Install once. Keep a broad provider catalogue without stacking duplicate addons, while NiakVIO handles structured maintenance, domain changes, validation and cache-safe releases.</p>
</div>

---

## Get NiakVIO

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

Manifest guide: [`docs/how-to-add-manifest.md`](docs/how-to-add-manifest.md)

### StreamBadge feed

```text
https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/stream-badges-fusion-v2.json
```

StreamBadge guide: [`docs/how-to-add-stream-badges.md`](docs/how-to-add-stream-badges.md)

> NiakVIO does not host video. It maintains provider metadata, structured protocol knowledge, compatibility rules, manifests and client-side provider bundles.

> [!IMPORTANT]
> Named works in code, CI or documentation are deterministic **test fixtures**, not a catalogue. See [`TESTING_NOTICE.md`](TESTING_NOTICE.md) and [`DISCLAIMER.md`](DISCLAIMER.md).

---

## Why NiakVIO?

A provider layer is easy when everything is static. The hard part starts when domains rotate, APIs change, player requirements drift, one client behaves differently from another, or a cached provider version refuses to refresh.

NiakVIO is built around that maintenance problem.

- **96 Provider Objects kept in the census** — disabled or unresolved providers are not silently removed just to improve a success rate.
- **VO and VF projections** — one maintained catalogue with dedicated French-focused manifests.
- **Less addon duplication** — NiakVIO is designed to be the provider layer, rather than another provider pack stacked on top of several others.
- **Structured provider knowledge** — routes, request semantics, identity rules and official-domain evidence live outside opaque published bundles.
- **Repairable architecture** — common failures can be fixed at Provider/Core-family level; uncertain changes go through Learning proposals instead of uncontrolled runtime mutation.
- **Native compatibility evidence** — TV Android, Mobile Android, Mobile iOS, macOS and Windows are treated as independent compatibility boundaries.
- **Cache-safe publication** — provider and manifest versions, content-addressed bundles and release integrity are synchronized so Nuvio can actually receive a new generation.
- **Fail-closed validation** — zero streams, wrong-media playback, malformed media or an upstream client failure are kept distinct instead of being converted into fake success.

<div align="center">
  <img src="assets/branding/how-it-works.png" alt="How NiakVIO works" width="820">
</div>

---

## Recommended Nuvio setup

<div align="center">
  <img src="assets/thanks/nuvio-bg.png" alt="Nuvio" width="150">
  <p><strong>Keep the stack small and let each addon do one job well.</strong></p>
</div>

<table>
  <tr>
    <td align="center" width="25%">
      <img src="assets/branding/niakvio-mark.svg" alt="NiakVIO" width="90"><br>
      <strong>Providers</strong><br>
      NiakVIO only
    </td>
    <td align="center" width="25%">
      <img src="assets/thanks/ultramax-bg.png" alt="UltraMax" width="90"><br>
      <strong>Metadata / catalogue</strong><br>
      UltraMax
    </td>
    <td align="center" width="25%">
      <img src="assets/thanks/subsense-bg.png" alt="SubSense" width="90"><br>
      <strong>Subtitles</strong><br>
      SubSense
    </td>
    <td align="center" width="25%">
      <img src="assets/thanks/simkl-bg.png" alt="SIMKL" width="90"><br>
      <strong>Favorites / tracking</strong><br>
      SIMKL
    </td>
  </tr>
</table>

The idea is deliberately simple: **one provider layer, one metadata/catalogue addon, one subtitle addon and one tracking service**. Avoid loading several provider addons that duplicate the same role and make failures, caching and source selection harder to understand.

---

## NiakVIO vs a raw provider manifest

A standalone provider or manifest can be perfectly useful. NiakVIO becomes valuable when the objective is a **large, changing provider catalogue that must remain maintainable across multiple Nuvio clients**.

| Capability | Raw provider / standalone manifest | NiakVIO |
|---|---|---|
| Installation | One or several provider manifests | One stable provider layer with general/VF projections |
| Catalogue maintenance | Mostly manual | 96 Provider Objects retained and continuously audited |
| Durable source | Often the published JS itself | ProviderBase v3 + structured DATA + owned Provider/Core Lego |
| Route knowledge | Usually embedded in provider code | Structured route/request/provenance data |
| Domain rotation | Manual/static URL changes | Official-hub discovery + bounded `official_site` refresh |
| Media types | Launch type and semantic capability can be mixed | Canonical capability separated from Nuvio transport compatibility |
| Failure diagnosis | Often zero streams / generic error | Search, detail, episode, runtime, player, media and device evidence |
| Repair | Manual provider rewrite | Family/Core repair + reviewable Learning proposals |
| Client coverage | Often inferred from one runtime | Five independent native Labs |
| Publication | File replacement | Cache-safe provider versions + manifest generation + integrity hashes |
| Security | Source-dependent | Bounded execution, network/resource guards and sanitization contracts |

---

## Built for the official Nuvio clients

NiakVIO treats every official client/device as its own compatibility boundary:

- **TV Android** — [NuvioTV](https://github.com/NuvioMedia/NuvioTV)
- **Mobile Android** — [NuvioMobile](https://github.com/NuvioMedia/NuvioMobile)
- **Mobile iOS** — [NuvioMobile](https://github.com/NuvioMedia/NuvioMobile)
- **Desktop macOS** — [NuvioDesktop](https://github.com/NuvioMedia/NuvioDesktop)
- **Desktop Windows** — [NuvioDesktop](https://github.com/NuvioMedia/NuvioDesktop)

A Desktop result does not automatically count as Android/iOS/TV evidence. Labs consume official clients as-is: an upstream compile, packaging, runtime, player or QuickJS failure remains visible instead of being patched inside NiakVIO merely to obtain a green CI result.

---

## Under the hood

### Provider v3

Provider bundles are reconstructed from:

```text
ProviderBase v3
+ structured provider DATA/static knowledge
+ PROVIDER.* Lego
+ CORE.* Lego
+ NiakVIO-safe minimizer
```

Published `providers/*.js` files are content-addressed runtime artifacts, **never reconstruction seeds**. Historical/upstream JavaScript is knowledge and provenance only.

Canonical ownership uses managed `STARTFIX` / `CLOSEFIX` / `FIXDATA` boundaries and a single global Core boundary. Full reconstruction must finish with a byte-identical reverse rebuild. Terser is forbidden; `scripts/provider_v3_minimizer.py` is deliberately conservative and runs before content hashing.

See [`ARCHITECTURE.md`](ARCHITECTURE.md).

### Route and protocol DATA

The durable source is:

```text
provider.model.routeData
```

Route recognition can preserve method, body encoding/fields, `Referer`, `Origin`, response kind, placeholders, role, provenance and confidence. Static analysis can recover variables, concatenations and templates without treating the published provider bundle as the source of truth.

Missing route evidence means **unknown**, not automatically dead or quarantined.

### Media types: semantic capability vs Nuvio transport

`canonicalSupportedTypes` describes what the provider catalogue actually serves (`movie`, `tv`, `anime`). `supportedTypes` describes how Nuvio may launch it.

An anime-only provider can therefore legitimately expose:

```json
{
  "canonicalSupportedTypes": ["anime"],
  "supportedTypes": ["anime", "tv", "movie"]
}
```

`tv` supports episodic anime transport and `movie` supports anime films. Those aliases do **not** turn an anime-only provider into a generic movie/TV provider; ordinary non-anime content must still be rejected by authoritative identity logic.

### Runtime rules

Provider JS is a specialized reader, not a crawler or Learning engine.

- capability/type gate before provider network work;
- TMDB enrichment only when the provider plan needs it;
- identity scoped by work/type/season/episode;
- incompatible provider returns `[]` instead of arbitrary searching;
- Core output processing runs only after useful streams exist;
- zero streams never manufacture success;
- wrong-media playback is a failure;
- one broken stream never disables the whole provider by itself.

### Reader, transport and playback

A `.m3u8` URL or `#EXTM3U` response does not prove native playback. NiakVIO separates extraction, identity, request context, playlist/variant resolution, media/container integrity and the actual native player outcome.

HTML/JSON disguised as media or positively malformed TS/fMP4 can be rejected. A timeout, temporary fetch failure, encrypted stream or missing byte API is **inconclusive**, not evidence for a fabricated provider-wide failure.

---

## CORE, Learning and Domain Refresh

`CORE - Verify & Publish` is the routine publication workflow.

- **Quick** — deterministic structure/runtime/unit/security/minimizer checks. No provider repair or reconstruction.
- **Deep** — broader read-only network/hub observation, provider health evidence, projections, reports and integrity inventories. Still no Provider JS repair/reconstruction.
- **Learning** — the isolated code-evolution/repair path. Proposed changes remain reviewable before publication authority.
- **Domain Refresh** — deliberately narrow maintenance of validated `official_site` CONFIG data only.

This separation prevents a health check from silently rewriting a provider just because a site is temporarily unavailable.

---

## Publication and integrity

Publication is atomic and fail-closed and can include:

- `provider_catalog.json`;
- content-addressed provider bundles;
- `manifest.json` and VF/no-anime projections;
- provenance/domain state;
- synchronized provider/cache versions;
- release hashes and allowlisted reports.

An inconsistent generation must never silently replace a healthy published state.

---

## Main workflows

| Workflow | Responsibility |
|---|---|
| `sync.yml` | **CORE - Verify & Publish** Quick/Deep; no provider repair/reconstruction |
| `provider-v3-reconstruct-routes.yml` | route-only recognition/canonical `routeData` census |
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
| `brain-branch-maintenance.yml` | durable Learning/proposals branch maintenance |

---

## Thanks & upstream knowledge

NiakVIO is independent, but it benefits from the wider Nuvio provider ecosystem and the work published by other maintainers.

<table>
  <tr>
    <td align="center" width="33%">
      <img src="assets/thanks/gowaru-bg.png" alt="Gowaru" width="150"><br>
      <strong>Gowaru</strong><br>
      Provider implementations and protocol knowledge used as upstream evidence/provenance where applicable.
    </td>
    <td align="center" width="33%">
      <img src="assets/thanks/yoru-bg.png" alt="Yoru" width="150"><br>
      <strong>Yoru</strong><br>
      Provider ecosystem work and implementation ideas that help cross-check behavior and compatibility.
    </td>
    <td align="center" width="33%">
      <img src="assets/thanks/deadlyrocket-bg.png" alt="All-in-One Nuvio / D3adlyRocket" width="150"><br>
      <strong>All-in-One Nuvio / D3adlyRocket</strong><br>
      Historical provider aggregation/mirror material used as one provenance source, never as NiakVIO reconstruction authority.
    </td>
  </tr>
</table>

---

## Security, responsibility and independence

Provider JavaScript is treated as untrusted input. NiakVIO uses bounded workers, SSRF/network controls, sandboxing, identity checks, CI sanitization and fail-closed publication. Generic regex-based HTML stripping is forbidden by the Provider v3 security contract.

NiakVIO is an independent community project and is not affiliated with Nuvio or referenced third-party services. Nothing in this repository grants rights to third-party media/services or authorizes bypassing authentication, paywalls, encryption or access controls.

See [`SECURITY.md`](SECURITY.md), [`TESTING_NOTICE.md`](TESTING_NOTICE.md), [`DISCLAIMER.md`](DISCLAIMER.md), [`LICENSE`](LICENSE), [`NOTICE`](NOTICE), [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
