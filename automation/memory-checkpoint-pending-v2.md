## 2026-09-12 — retry 9 rebuilt ProviderBase 96/96; stale layering fixture blocked after materialization

- TEMP run **34719219904**, job **103621866958**, completed the full focused regression suite green and then successfully executed the owned ProviderBase materializer.
- Authoritative materializer line: `FIELD_PROVIDER_BASE_V3_STORE providers=96 unique_paths=96 reconstruction_required=0 provider_js_seed=false upstream_js_seed=false runtime_reader=v10 route_sanitizer=v1 html_text_hardening=deterministic-scanner-v1 movie_identity=v21.10 episode_identity=v22.1`.
- This resolves the prior concrete blocker `anime-sama: missing durable ProviderBase`: all 96 clean bases are now generated from NiakVIO-owned common skeleton + DATA with **no published/upstream JS seed**.
- Run 34719219904 stopped immediately after materialization in `tests/provider_base_layering_contract_test.py`, not in generated ProviderBase bytes. The stale synthetic fixture explicitly expected `/* NUVIO_PROVIDER_SECURITY_HARDENING_V1 */` to be accepted inside a clean ProviderBase even though current `DERIVED_BASE_MARKERS` explicitly classifies that security hardening as a derived/publication layer.
- The layering invariant is not weakened. Commit **6e1db8fa3f32fd499b3d118634726fe5f219288d** removes the stale acceptance and strengthens the test: `NUVIO_PROVIDER_SECURITY_HARDENING_V1` is now explicitly required in the forbidden derived-marker set and a contaminated synthetic base must fail.
- No generated 96-base changes from the failed runner were committed because the job stopped before its commit step; the next verifier will rematerialize deterministically.
- All-96 bundle rebuild was not reached yet. `main` remains untouched.
