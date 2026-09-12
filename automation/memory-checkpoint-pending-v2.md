## 2026-09-12 — common identity guards integrated into durable ProviderBase generation

- Added provider-agnostic `scripts/upgrade_provider_episode_identity_guard_v22_1.py` plus executable `tests/provider_episode_identity_guard_v22_1_test.py`.
- V22.1 extends common episode identity evidence to query-string forms such as `?season=2&episode=10` / reversed ordering, rejects detail URLs that explicitly identify another episode, and fail-closes generic player fallback when a same-origin episode table proves the requested episode is absent. No provider ids, fixture titles or site hosts are hard-coded.
- Added executable `tests/provider_movie_catalogue_identity_v21_10_test.py` for the existing common V21.10 movie-title equivalence guard. It explicitly permits exact title/alias plus presentation-only noise (correct year, quality, language) and rejects semantic collisions such as documentary titles containing the requested movie name.
- `scripts/materialize_provider_base_v3_store.py` now runs both V21.10 movie identity and V22.1 episode identity upgrades before importing/materializing the common ProviderBase store. Provenance store metadata records `movie_catalogue_identity_guard=v21.10` and `episode_identity_guard=v22.1`.
- This makes the StreamZo wrong-documentary and Mugiwara wrong-episode fixes durable common ProviderBase behavior rather than workflow-only patches or provider-specific exceptions.
- Main remains untouched; all writes stay on `fix/labs-5.21.44-20260912`.
- Next: wire the temporary branch verifier to regenerate the 96 ProviderBase store before 96 bundle recomposition, add no-`setTimeout`/dead-provider isolation contracts, then execute the full branch rebuild and gates.
