# Cohorte 2 — extension sans publication (14 novembre 2026)

Goal: accelerate the user's requirement of around 60 **functioning**, separately selected Global and France providers on existing manifest URLs, with ~20 independently proven movie/TV/anime sources per region. The existing active manifests remain untouched by this lab.

After a first 14-candidate screen yielded three upstream terminal positives (FrenchStream, Movix, TopCartoons), this independently tests **27 new pinned Nuvio modules**: 17 Global and 10 France. Each declared lane receives three rotating current fixtures (twice the coverage of the original pilot for some cases), and only verified terminal MP4/HLS probe results count as positives. Existing sources with confirmed historical no-stream or disabled state are not reactivated.

Source priority:
- From the user's Sept 11 workbook **Global**: Moonflix (#48), XPass (#102), 1Shows (#164), AniDB (#210), Animeworld (#237). **France**: Webflix (#44), WaveAnime (#72).
- Other modules are labeled **Nuvio-upstream-expansion** rather than pretending they have user workbook ranks/scores; these expansions provide additional candidate diversity for films, TV and anime. Their rank and score are `null`.
- Upstream: pinned `NuvioPlugin/All-in-One-Nuvio@3f09a6ff` and `Gowaru/gowaru-nuvio-providers@66494c59`, checked beforehand to contain concrete script content. No mutable upstream branch used for the executable sandbox.

The pipeline is **read-only** and runs on GitHub Actions with official locked Node/Python, existing sandbox worker and terminal HLS/MP4 probe. Only sanitized evidence is uploaded. **No manifest activation and no automatic removal based on these limited probes**. Passing upstream means candidate media observed, not correct title/episode or playable native TV/Mobile/Desktop. A failing runner does not prove the provider is broken; WAF/network differential must be considered.

Only after representative Brain-generated NiakVIO clean Provider v3 materials prove terminal playback and exact content identity should a provider enter Global/France production. France-only manifest projection has an unresolved structural dependency on Global and cannot be circumvented by duplication.
