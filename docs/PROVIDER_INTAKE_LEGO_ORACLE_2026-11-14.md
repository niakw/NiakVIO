# Brain diagnostic oracle: source-positive → reusable NiakVIO Lego

The first read-only upstream intake, run 43538083385, observed terminal media for **Movix** and **FrenchStream** in France; user wants functioning providers without duplicating region entries. Their sources were historically implemented inside NiakVIO and have retained `provider-old/` bases and provider patch Legos.

This is a deliberately **temporary, non-publishing** A/B oracle. For each positive movie/series fixture from the intake, it compiles a minimal adapter around NiakVIO's *existing local managed Lego*, and executes both that local hypothesis and the immutable upstream under `provider_worker.cjs` and the existing terminal HLS/media probe. Pinned source scripts remain untrusted worker inputs.

Two families:
- `frenchstream` : DLE catalogue → season/episode/player → HLS, local `scripts/provider_patches/frenchstream_exact_runtime_v3.py`.
- `movix` : TMDB API cache → provider video groups → HLS/embed, local `scripts/provider_patches/movix_runtime_v1.py`.

If upstream returns terminal media and local Lego does not, this is a **Brain reconstruction/knowledge/route strategy gap** to solve before promoting a provider. If local does return terminal media, it is **not** a verified Provider v3 publication: clean v3 base, Core identity/season/quality, native client acceptance and region-only projection remain mandatory. No manifest, provider, or override is modified by this job; temporary JS is discarded after it runs. The result contains no URL, token, header value, user data or compiled code.

This is not a license to reintroduce a disabled source (e.g. Videasy) or directly execute foreign JS as a production provider. Following a confirmed positive local oracle, the Brain must generate and persist a V3 candidate from the structured route knowledge, materialize and validate it end-to-end before production activation.
