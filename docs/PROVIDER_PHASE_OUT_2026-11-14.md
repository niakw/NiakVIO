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


## Phase-out cohort 1 : preuve de publication (2026-11-14)

- **Réussite effective:** workflow [Provider Disabled Lifecycle #43535544778](https://github.com/niakw/NiakVIO/actions/runs/43535544778) **success** ; commit de publication `b3263ad5a0859009e9dec7e61316c750a1dc6558`.
- `manifest.json` **41 visibles / 39 actifs**, dont `yflix` et `ANIMEVOST-FR` désactivés. `vf/manifest.json` **21 visibles / 20 actifs**, `ANIMEVOST-FR` désactivé. Deux entrées visibles restent le temps de la rétention plutôt que de casser l'import.
- Exacts fichiers contrôlés sur GitHub : `provider-disabled/yflix--nuvio--d9a87c04b9e1aa32.js` et `provider-disabled/animevost-fr--nuvio--a47f44cd69693435.js` présents ; originaux `providers/` correspondants absents. `provider_catalog.json` et `provider-v3-materialization.json` indiquent 39 actifs.
- `automation/provider-disabled-lifecycle.json`: `state=disabled-retained`, `disabledAt=2026-11-14`, `purgeAfter=2026-11-21` pour les deux. Archivage physique/removal des manifests seulement après l'échéance et un nouveau run de cycle de vie.
- **Pas de preuve de playback nouvelle:** les autres providers et le ratio 20/20/20 par manifest n'ont pas été requalifiés. Les CI Core/CodeQL générales sur l'état post-lifecycle étaient encore en attente ou sur d'anciens SHA au moment de cette mise à jour. Ne pas appeler « full validated ».


## Cohorte 2 — AllAnime / MalluMV : contrôle supplémentaire du 14 novembre 2026

| Provider | Genre / manifest | Preuve négative croisée | Précaution |
| --- | --- | --- | --- |
| AllAnime | anime / Global seulement | Census #43460048984 : CHAIN REACHED, 4/45 recherches et aucun média terminal ; availability 2026-11-13 : no_streams ; Fast Repair #43536125705 : 4 fixtures, 0 flux, `no_streams` | Sites référencés ; conserver DATA et historique, désactivation provisoire uniquement |
| MalluMV | film / Global seulement | Census #43460048984 : CHAIN REACHED, 1/42 recherches, 0 terminal ; availability 2026-11-13 : no_streams ; Fast Repair #43536125705 : 4 fixtures, 0 flux, `no_streams` | Dépendances réseau à rechercher ; désactivation provisoire uniquement |

- Aucune correspondance d'épisode ni lecture terminale prouvée. La CI Fast Repair a terminé sans accepter de réparation : `selected=13, accepted=0, validated=0`.
- Les décisions sont des *retraits du catalogue actif* et non des jugements sur la réparabilité des sites.
- Utiliser le même cycle de vie générique : `provider-hubs.json` → trigger → `classify_provider_authority.py --apply-safe-disables` → `manage_provider_lifecycle.py --apply`, conservation 7 jours, puis archivage uniquement après nouvelle vérification.
- Les providers historico-FULL et WAF-only restent protégés en attendant un diagnostic Brain / Client approprié.
