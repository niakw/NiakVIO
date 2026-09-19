# Hub46 — mechanism / blocker inventory — 2026-09-11

This report distinguishes a provider that currently returns zero streams from a provider whose site mechanism is genuinely not demonstrated by current repository evidence.

- Targets: **46/46**.
- Enabled in canonical manifest: **46/46**.
- Repository-evidence opaque candidates: **6**.
- `repoOpaque=true` is a research queue, not a declaration that the provider is dead.

## Opaque candidates from repository evidence

- **voiranime** — mechanism `known-site-no-executable-route`; reasons: no_api_recipe, no_provider_lego; hub relation: `match`; blocker: `network-or-antibot-timeout`.
- **4khdhub** — mechanism `known-site-no-executable-route`; reasons: no_api_recipe, no_provider_lego; hub relation: `match`; blocker: `network-or-antibot-timeout`.
- **uhdmovies** — mechanism `known-site-no-executable-route`; reasons: no_api_recipe, no_provider_lego; hub relation: `match`; blocker: `network-or-antibot-timeout`.
- **moviesdrive** — mechanism `known-site-no-executable-route`; reasons: no_api_recipe, no_provider_lego; hub relation: `match`; blocker: `network-or-antibot-timeout`.
- **cinefreak** — mechanism `known-site-no-executable-route`; reasons: no_api_recipe, no_provider_lego, registry_only_hub; hub relation: `registry-only`; blocker: `network-or-antibot-timeout`.
- **coflix** — mechanism `known-site-no-executable-route`; reasons: no_api_recipe, no_provider_lego; hub relation: `match`; blocker: `network-or-antibot-timeout`.

## All 46

| Provider | Mechanism | Repo opaque | Lab blocker | Route state | Hub relation |
|---|---|---:|---|---|---|
| animesama-co | structured-search-value-plan | no | network-or-antibot-timeout | repair | match |
| vostfree | api-route | no | network-or-antibot-timeout | repair | registry-only |
| papadustream | external-identity-plan | no | cross-runtime-divergence | repair | match |
| mugiwarastream | structured-search-value-plan | no | network-or-antibot-timeout | repair | match |
| anime-sama | provider-lego | no | network-or-antibot-timeout | repair | match |
| voiranime | known-site-no-executable-route | yes | network-or-antibot-timeout | repair | match |
| movix | provider-lego | no | network-or-antibot-timeout | off | match |
| videasy | provider-lego | no | cross-runtime-divergence | on | match |
| animepahe | search-detail-extraction | no | network-or-antibot-timeout | repair | registry-only |
| 4khdhub | known-site-no-executable-route | yes | network-or-antibot-timeout | repair | match |
| playimdb | typed-resolver-api | no | cross-runtime-divergence | on | registry-only |
| desiflix | provider-lego | no | network-or-antibot-timeout | repair | match |
| allanime | api-route | no | network-or-antibot-timeout | repair | match |
| anikototv | provider-lego | no | network-or-antibot-timeout | repair | match |
| animesalt | html-detail-scraper | no | network-or-antibot-timeout | repair | match |
| hdghartv | search-detail-extraction | no | network-or-antibot-timeout | repair | match |
| netmirror | typed-resolver-api | no | network-or-antibot-timeout | off | match |
| vidfast | iframe-player | no | network-or-antibot-timeout | repair | registry-only |
| vidlink | api-route | no | network-or-antibot-timeout | repair | registry-only |
| hindmoviez | structured-search-value-plan | no | network-or-antibot-timeout | repair | match |
| uhdmovies | known-site-no-executable-route | yes | network-or-antibot-timeout | repair | match |
| vidsrc | player-or-source-route | no | network-or-antibot-timeout | repair | registry-only |
| vixsrc | api-route | no | network-or-antibot-timeout | off | registry-only |
| movies4u | structured-search-plan | no | network-or-antibot-timeout | repair | match |
| cineby | provider-lego | no | network-or-antibot-timeout | repair | match |
| vidrock | provider-lego | no | network-or-antibot-timeout | repair | registry-only |
| vegamovies | api-recipe | no | network-or-antibot-timeout | repair | match |
| anizone | provider-lego | no | network-or-antibot-timeout | repair | match |
| moviebox | player-or-source-route | no | network-or-antibot-timeout | off | match |
| animetsu | search-detail-extraction | no | network-or-antibot-timeout | repair | match |
| moviesdrive | known-site-no-executable-route | yes | network-or-antibot-timeout | repair | match |
| zinkmovies | direct-media-site | no | network-or-antibot-timeout | repair | registry-only |
| anidb | provider-lego | no | network-or-antibot-timeout | repair | match |
| movieshunt | structured-search-plan | no | network-or-antibot-timeout | on | match |
| wookafr | search-detail-extraction | no | network-or-antibot-timeout | repair | match |
| allwish | player-or-source-route | no | content-identity | on | match |
| cinefreak | known-site-no-executable-route | yes | network-or-antibot-timeout | repair | registry-only |
| frenchstream | api-recipe | no | stream-transport-403 | repair | match |
| nakios | player-or-source-route | no | network-or-antibot-timeout | repair | match |
| purstream | search-detail-extraction | no | network-or-antibot-timeout | repair | match |
| toflix | api-recipe | no | network-or-antibot-timeout | repair | match |
| coflix | known-site-no-executable-route | yes | network-or-antibot-timeout | repair | match |
| flemmix | api-route | no | network-or-antibot-timeout | repair | match |
| kehflix | api-route | no | network-or-antibot-timeout | repair | match |
| 1shows | api-recipe | no | network-or-antibot-timeout | repair | match |
| moonflix | direct-media-site | no | network-or-antibot-timeout | repair | match |

## Counts

### Mechanisms

- `api-recipe`: 4
- `api-route`: 6
- `direct-media-site`: 2
- `external-identity-plan`: 1
- `html-detail-scraper`: 1
- `iframe-player`: 1
- `known-site-no-executable-route`: 6
- `player-or-source-route`: 4
- `provider-lego`: 9
- `search-detail-extraction`: 5
- `structured-search-plan`: 2
- `structured-search-value-plan`: 3
- `typed-resolver-api`: 2

### Current evidence blockers

- `content-identity`: 1
- `cross-runtime-divergence`: 3
- `network-or-antibot-timeout`: 41
- `stream-transport-403`: 1

## Interpretation

- `route-or-extraction-no-stream` does **not** mean opaque: routes/strategy may be understood but currently fail to yield a stream.
- `cross-runtime-divergence` means at least one native runtime proved the provider while another failed; prioritize common runtime/bridge analysis before provider-specific rewrites.
- `repoOpaque=true` means current structured DATA does not establish a credible execution mechanism; those providers should be investigated manually/web-side and returned to the user by name if still unresolved.
