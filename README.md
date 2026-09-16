<div align="center">
  <img src="assets/branding/niakvio-logo.svg" alt="NiakVIO" width="560">

  <p><strong>English</strong> · <a href="README.fr.md">Français</a></p>
  <h3>One maintained provider layer for Nuvio.</h3>
  <p>
    <kbd>Hub-46</kbd>
    <kbd>VO / VF</kbd>
    <kbd>TV · Mobile · Desktop</kbd>
    <kbd>Provider v3</kbd>
  </p>
  <p>Structured provider knowledge, cache-safe publication and native validation across the official Nuvio clients.</p>
</div>

<p align="center">
  <a href="#-install-niakvio"><strong>Install</strong></a> ·
  <a href="#-recommended-nuvio-setup"><strong>Setup</strong></a> ·
  <a href="#-how-niakvio-works"><strong>How it works</strong></a> ·
  <a href="#-native-compatibility"><strong>Native Labs</strong></a> ·
  <a href="#-upstream-references--credits"><strong>Upstreams</strong></a> ·
  <a href="#-security-responsibility--independence"><strong>Security</strong></a>
</p>

---

## ⚡ Install NiakVIO

> [!TIP]
> For most users, start with the **general manifest**. The other projections use the same maintained provider layer with a narrower presentation.

### Recommended — general manifest

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/manifest.json
```

<details>
<summary><strong>Other manifest projections</strong> — French-focused and/or without anime-oriented providers</summary>

<br>

**French-focused manifest**

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/vf/manifest.json
```

**General manifest without anime-oriented providers**

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/no-anime/manifest.json
```

**French-focused manifest without anime-oriented providers**

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/vf-no-anime/manifest.json
```

</details>

**Manifest guide:** [`docs/how-to-add-manifest.md`](docs/how-to-add-manifest.md)

### StreamBadge feed

```text
https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/stream-badges-fusion-v2.json
```

**StreamBadge guide:** [`docs/how-to-add-stream-badges.md`](docs/how-to-add-stream-badges.md)

> [!NOTE]
> NiakVIO does not host video. It maintains provider metadata, structured protocol knowledge, compatibility rules, manifests and client-side provider bundles.

> [!IMPORTANT]
> Named works in code, CI or documentation are deterministic **test fixtures**, not a catalogue. See [`TESTING_NOTICE.md`](TESTING_NOTICE.md) and [`DISCLAIMER.md`](DISCLAIMER.md).

---

## ✨ Why NiakVIO?

NiakVIO is built for the part that becomes difficult over time: **keeping a large provider layer understandable when domains, protocols, clients and player behavior change**.

| | What stays explicit |
| --- | --- |
| **🔌 Catalogue** | **46 Hub Provider Objects** remain visible; unresolved or disabled state is not silently erased to improve a success rate. |
| **🌍 Projections** | General, French-focused and no-anime manifests come from one maintained provider layer. |
| **🧠 Knowledge** | Routes, request semantics, identity rules, official-domain evidence and provenance live outside opaque published bundles. |
| **🧩 Repair model** | Common failures can be handled at Provider/Core-family level; uncertain changes go through reviewable Learning proposals. |
| **🧪 Native evidence** | TV Android, Mobile Android, Mobile iOS, macOS and Windows are five independent compatibility boundaries. |
| **📦 Publication** | Provider versions, manifests, content-addressed bundles and integrity metadata stay synchronized. |
| **🛡️ Validation** | Zero streams, wrong-media playback, malformed media and upstream client failures remain distinct states instead of fake success. |

<div align="center">
  <img src="assets/branding/how-it-works-en.svg" alt="How NiakVIO works" width="820">
</div>

<details>
<summary><strong>NiakVIO vs a raw provider manifest</strong></summary>

<br>

A standalone provider or manifest can be perfectly useful. NiakVIO becomes valuable when the goal is a **large, changing provider catalogue that must remain maintainable across multiple Nuvio clients**.

| Capability | Raw provider / standalone manifest | NiakVIO |
| --- | --- | --- |
| Installation | One or several provider manifests | One maintained layer with several projections |
| Catalogue maintenance | Mostly manual | Hub-46 retained and audited |
| Durable source | Often the published JS itself | ProviderBase v3 + structured DATA + owned Provider/Core Lego |
| Route knowledge | Usually embedded in provider code | Structured route/request/provenance data |
| Domain rotation | Manual/static URL changes | Official-hub discovery + bounded `official_site` refresh |
| Media types | Launch type and semantic capability may be mixed | Canonical capability separated from Nuvio transport compatibility |
| Failure diagnosis | Often zero streams / generic error | Search, detail, episode, runtime, player, media and device evidence |
| Repair | Manual provider rewrite | Family/Core repair + reviewable Learning proposals |
| Client coverage | Often inferred from one runtime | Five independent native Labs |
| Publication | File replacement | Cache-safe versions + manifest generation + integrity hashes |

</details>

---

## 🧩 Recommended Nuvio setup

<div align="center">
  <a href="https://github.com/NuvioMedia"><img src="assets/thanks/nuvio-bg.png" alt="Nuvio" width="150"></a>
  <p><strong>Keep the stack small: one tool per role.</strong></p>
</div>

| Providers | Metadata & catalogue | Subtitles | Favorites & tracking |
| :---: | :---: | :---: | :---: |
| <img src="assets/branding/niakvio-mark.svg" alt="NiakVIO" width="52"><br>**NiakVIO** | <img src="assets/thanks/ultramax-bg.png" alt="Ultra MAX" width="52"><br>**Ultra MAX** | <img src="assets/thanks/subsense-bg.png" alt="SubSense" width="52"><br>**SubSense** | <img src="assets/thanks/simkl-bg.png" alt="SIMKL" width="52"><br>**SIMKL** |
| One provider layer. | Discovery and metadata-oriented rows. | Dedicated subtitle addon. | History, favorites and tracking. |
| [Repository](https://github.com/niakw/NiakVIO) · [Manifest](https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/manifest.json) | [Ultra MAX](https://ultramax.vip) · [GitHub](https://github.com/PaRaN01a-hash/UltraMax) | [Configure](https://subsense.nepiraw.com/configure) · [GitHub](https://github.com/NepiRaw/Stremio-SubSense) | [SIMKL](https://simkl.com) |

> [!TIP]
> **Simple target stack:** 1 provider layer + 1 metadata/catalogue addon + 1 subtitle addon + 1 tracking service. Avoid stacking several provider packs that compete for the same role unless you are deliberately testing them.

---

## 🔄 How NiakVIO works

The public surface stays simple; most of the complexity lives behind explicit contracts.

1. **Provider knowledge is normalized** into ProviderBase v3, structured DATA and owned Provider/Core Lego.
2. **Runtime behavior is gated and validated** without turning a zero result into fabricated success.
3. **Accepted bytes are published atomically** with synchronized manifests, versions and integrity metadata.

**Deep dive:** [`ARCHITECTURE.md`](ARCHITECTURE.md) · [`INSTALL.md`](INSTALL.md) · [`VALIDATION.md`](VALIDATION.md)

<details>
<summary><strong>Provider v3, DATA and runtime contracts</strong></summary>

<br>

Published provider bundles are reconstructed from:

```text
ProviderBase v3
+ structured provider DATA/static knowledge
+ PROVIDER.* Lego
+ CORE.* Lego
+ NiakVIO-safe minimizer
```

`providers/*.js` files are content-addressed runtime artifacts, **never reconstruction seeds**. Historical/upstream JavaScript is knowledge and provenance only.

The durable route source is:

```text
provider.model.routeData
```

Recognition preserves, when known, method, body encoding and fields, `Referer`, `Origin`, response kind, placeholders, role, provenance and confidence. Missing route evidence means **unknown**, not automatically dead or quarantined.

Runtime rules include:

- capability/type gate before provider network work;
- TMDB enrichment only when the provider plan needs it;
- identity scoped by work/type/season/episode;
- incompatible provider returns `[]` instead of arbitrary searching;
- Core output processing only after useful streams exist;
- zero streams never manufacture success;
- wrong-media playback is a failure;
- one broken stream never disables the whole provider by itself.

</details>

<details>
<summary><strong>Media types — semantic capability vs Nuvio transport</strong></summary>

<br>

`canonicalSupportedTypes` describes what the provider catalogue actually serves (`movie`, `tv`, `anime`). `supportedTypes` describes how Nuvio may launch it.

An anime-only provider can legitimately expose:

```json
{
  "canonicalSupportedTypes": ["anime"],
  "supportedTypes": ["anime", "tv"]
}
```

`tv` is the episodic launch-compatibility alias for anime. NiakVIO does not synthesize `series`; `movie` appears only when the provider declares canonical movie capability. Transport aliases never widen semantic capability.

See [`docs/media-type-transport-contract.md`](docs/media-type-transport-contract.md).

</details>

<details>
<summary><strong>CORE, Learning, Domain Refresh and publication</strong></summary>

<br>

- **Quick** — deterministic structure/runtime/unit/security/minimizer checks. No provider repair or reconstruction.
- **Deep** — broader read-only network/hub observation, provider-health evidence, projections, reports and integrity inventories. Still no Provider JS repair/reconstruction.
- **Learning** — isolated code-evolution/repair path; proposed changes remain reviewable before publication authority.
- **Domain Refresh** — deliberately narrow maintenance of validated `official_site` CONFIG data only.

Publication is atomic and fail-closed. Published provider-byte changes require synchronized provider/manifest/cache/release metadata, but the bump happens only after the validation pile is accepted.

`release-finalize.yml` finalizes an accepted generation at the exact accepted SHA. Documentation, workflow or harness-only changes do **not** require a provider/cache bump while published provider bytes remain unchanged.

</details>

<details>
<summary><strong>Main workflows</strong></summary>

<br>

| Workflow | Responsibility |
| --- | --- |
| `sync.yml` | **CORE - Verify & Publish** Quick/Deep |
| `release-finalize.yml` | exact-SHA accepted-release finalization |
| `provider-v3-reconstruct-routes.yml` | route-only recognition / canonical `routeData` census |
| `provider-v3-reconstruct-all.yml` | full Provider v3 reconstruction + reverse byte proof |
| `brain-learning-lab.yml` | sandbox Learning + reviewable proposals |
| `domain-refresh.yml` | validated `official_site` CONFIG-only maintenance |
| `add-provider.yml` | structured provider onboarding |
| `native-mobile-android-reader.yml` | TV Android + Mobile Android evidence |
| `native-mobile-ios-reader.yml` | Mobile iOS evidence |
| `native-desktop-reader-acceptance.yml` | Desktop macOS + Windows evidence |
| `native-corpus-device-targeted.yml` | targeted device/provider diagnostics |
| `github-actions-gate.yml` | workflow/repository security invariants |
| `codeql.yml` | local CodeQL `security-extended` + production dependency audit |
| `weekly-upstream-provider-discovery.yml` | read-only upstream discovery |

</details>

---

## 🧪 Native compatibility

> [!IMPORTANT]
> A Desktop result is not Android/iOS/TV evidence. **Each official client/device is a separate compatibility boundary.**

| Lab | Official client |
| --- | --- |
| **TV Android** | [NuvioTV](https://github.com/NuvioMedia/NuvioTV) |
| **Mobile Android** | [NuvioMobile](https://github.com/NuvioMedia/NuvioMobile) |
| **Mobile iOS** | [NuvioMobile](https://github.com/NuvioMedia/NuvioMobile) |
| **Desktop macOS** | [NuvioDesktop](https://github.com/NuvioMedia/NuvioDesktop) |
| **Desktop Windows** | [NuvioDesktop](https://github.com/NuvioMedia/NuvioDesktop) |

Labs consume the official clients as-is. An upstream compile, dependency, packaging, runtime, player or QuickJS failure stays visible instead of being patched inside NiakVIO merely to manufacture green CI.

<!-- NIAKVIO_NATIVE_ADAPTIVE_LAB_DOCS_V1 -->
<details>
<summary><strong>Native acceptance scope and adaptive sampling</strong></summary>

<br>

The maintained catalogue remains **46 Hub Provider Objects**. Final native acceptance uses the explicit physical **Hub-46** scope from `automation/evidence/hub-lab-matrix-46.json`; disabled or out-of-scope catalogue rows remain visible maintenance debt and are not silently deleted.

The ordinary Lab corpus is adaptive. `.github/triggers/rotating-popular-corpus.json` owns three recent global reserves — **movie, TV and anime**. A native campaign starts with **1 movie + 1 TV episode + 1 anime episode**. A provider/lane advances only after a clean `0 streams` result. Positive proof stops rotation; runtime/load/timeout/transport/player/identity failures stop and remain visible instead of being rotated away.

Historical fixtures in `.github/triggers/nuvio-client-lab.json` remain available for targeted regression diagnostics, but they are not the ordinary global sampling authority.

</details>

---

## 📚 Upstream references & credits

> [!NOTE]
> NiakVIO is independent. Upstream repositories are used as **knowledge, implementation evidence and provenance** — not as NiakVIO reconstruction authorities.

| Project | Useful contribution | Role in NiakVIO |
| --- | --- | --- |
| [<img src="assets/thanks/gowaru-bg.png" alt="Gowaru" width="110">](https://github.com/Gowaru/gowaru-nuvio-providers)<br>**[Gowaru](https://github.com/Gowaru/gowaru-nuvio-providers)** | French Nuvio provider implementations and provider-local protocol knowledge. | **Reference / evidence** |
| [<img src="assets/thanks/yoru-bg.png" alt="Yoru" width="110">](https://github.com/yoruix/nuvio-providers)<br>**[Yoru](https://github.com/yoruix/nuvio-providers)** | Provider implementations and reusable Nuvio conventions for runtime/interface cross-checking. | **Reference / evidence** |
| [<img src="assets/thanks/deadlyrocket-bg.png" alt="All-in-One Nuvio" width="110">](https://github.com/NuvioPlugin/All-in-One-Nuvio)<br>**[All-in-One Nuvio](https://github.com/NuvioPlugin/All-in-One-Nuvio)** | International aggregation/reference material. The [D3adlyRocket mirror](https://github.com/D3adlyRocket/All-in-One-Nuvio) remains useful for historical provenance. | **Reference / evidence + historical provenance** |

<details>
<summary><strong>What “upstream knowledge” means here</strong></summary>

<br>

NiakVIO may use upstream projects to learn or verify endpoint structure, request semantics, provider naming, historical behavior and runtime conventions. That knowledge is normalized into NiakVIO's own structured DATA / Provider/Core model before publication.

The goal is to preserve **credit and evidence** without making third-party published bundles the durable source of truth.

See [`UPSTREAMS.md`](UPSTREAMS.md).

</details>

---

## 🔐 Security, responsibility & independence

Provider JavaScript is treated as untrusted input. NiakVIO uses bounded workers, SSRF/network controls, sandboxing, identity checks, CI sanitization and fail-closed publication.

> [!CAUTION]
> NiakVIO is an independent community project and is not affiliated with Nuvio or referenced third-party services. Nothing in this repository grants rights to third-party media/services or authorizes bypassing authentication, paywalls, encryption or access controls.

**Project docs:** [`SECURITY.md`](SECURITY.md) · [`TESTING_NOTICE.md`](TESTING_NOTICE.md) · [`DISCLAIMER.md`](DISCLAIMER.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) · [`LICENSE`](LICENSE) · [`NOTICE`](NOTICE)
