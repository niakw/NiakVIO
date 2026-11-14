# Provider phase-out cohort 1 — 2026-11-14

Owner: NiakVIO provider lifecycle. **Production URLs remain unchanged.**

## Scope and evidence

| Provider | Scope | Playback evidence | Recent availability | Action |
| --- | --- | --- | --- | --- |
| yflix | Global only | No historical terminal playback; census 43460048984, movie 1 searched + 43 retained misses; TV 1 searched + 42 retained misses; 0 verified lanes | no_streams at 2026-11-13 23:50 UTC | Candidate disabled (retain 7 days); archive if still negative |
| animevost-fr | Global + France projection | No historical terminal playback; census 43460048984, anime 1 searched + 46 retained misses; 0 verified lanes | no_streams at 2026-11-13 23:50 UTC | Candidate disabled (retain 7 days); archive if still negative |

The census SHA `875427198f48c6755954260787252b1ba229105e` **is not current main**. The availability report is an additional Node-side observation, not direct TV/Mobile/Desktop playback proof. This supports *provisional withdrawal* for user experience; it is not proof that the provider source is irreparable or permanently down.

## Execution

The durable `provider-hubs.json` manual-off signal triggers the existing `scripts/classify_provider_authority.py --apply-safe-disables` and `scripts/manage_provider_lifecycle.py --apply` pipeline via `.github/triggers/provider-disabled-lifecycle`. The pipeline owns atomic movement `providers/` → `provider-disabled/` and updates Global, VF, their no-anime projections, `provider_catalog.json`, lifecycle state, static knowledge and materialization counts. After 7 days the same pipeline archives `provider-old/` and removes the entries from the manifests. Archived source/history and Brain experiments remain available.

**Do not directly delete or set `enabled=false` in `manifest.json` without moving the associated executable bytes**: active folder and manifest are a single contract.

## Proof gate before status 'removed'

Read workflow job and log + commit SHA; independently inspect current main `manifest.json`, `vf/manifest.json`, `provider-disabled/`, lifecycle state and CI. Once the lifecycle job succeeds, report the exact counts. If it fails, the cohort is only **staged**, never **disabled**. No gain in number of functional providers is claimed.

Do not phase out FULL/PARTIAL providers on old evidence alone; do not phase out WAF/transport-blocked cases without client/harness differential diagnosis. Continue cohort-based replacement targeting ~20 movie, 20 TV, 20 anime for each manifest with terminal validated streams. Preserve all failures in Brain experience, not as per-provider hacks.
