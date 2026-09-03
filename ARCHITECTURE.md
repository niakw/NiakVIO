# Architecture NiakVIO — Provider v3

> Source de vérité technique du dépôt. Toute modification des règles Provider v3, CORE, Learning, Domain Refresh ou Native Labs doit mettre ce document à jour dans la même transaction.

## 1. Principe

NiakVIO sépare strictement **connaissance**, **code provider durable**, **artefacts publiés**, **validation** et **apprentissage**.

- `provider_catalog.json` est le registre canonique de métadonnées/projections publiées.
- `provider-bases/` contient les ProviderBase v3 propres et durables appartenant à NiakVIO.
- `provider-overrides.json` et les données structurées associées portent la configuration provider et les options Core.
- `scripts/provider_patches/**` contient les Lego `PROVIDER.*` et `CORE.*` versionnés.
- `providers/*.js` est un résultat matérialisé et adressé par contenu. Ce n'est jamais une seed de reconstruction.
- les upstreams et sites tiers sont des sources de connaissance/provenance, jamais une base JS exécutable canonique.

Le marqueur de propriété ProviderBase courant est `NIAKVIO_PROVIDER_BASE_OWNED_V3`.

## 2. Reconstruction déterministe

La seule reconstruction complète des 96 providers est le workflow manuel `.github/workflows/provider-v3-reconstruct-all.yml`.

Entrées canoniques :

1. ProviderBase v3 propre ;
2. DATA/CONFIG structurées ;
3. Lego provider appartenant au provider ;
4. Lego Core partagés ;
5. manifest/provenance/politiques nécessaires à la projection.

Interdictions :

- seed depuis `providers/*.js` ;
- seed depuis un bundle upstream ;
- replay d'un ancien patch source-shape comme vérité canonique ;
- reconstruction automatique dans Quick, Deep ou Native Labs ;
- commit direct de la reconstruction manuelle sur `main`.

Une reconstruction acceptable doit couvrir 96/96 providers et passer `verify_provider_v3_reverse_rebuild.py` avec 96/96 byte-identical.

## 3. Forme canonique d'un Provider JS

```text
/* BEGIN NIAKVIO_PROVIDER */
/* NIAKVIO_PROVIDER_ID:<id> */
/* NIAKVIO_PROVIDER_BASE_OWNED_V3 */
<ProviderBase v3 propre>

/* STARTFIX:PROVIDER.<ID>.CONFIG.V1 */
/* FIXDATA:PROVIDER.<ID>.CONFIG.V1:<payload> */
<DATA provider>
/* CLOSEFIX:PROVIDER.<ID>.CONFIG.V1 */

<autres Lego PROVIDER.* éventuels>

/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */
<Lego CORE.* chacun dans STARTFIX/CLOSEFIX>

/* END NIAKVIO_PROVIDER */
```

Les blocs managés utilisent exclusivement `STARTFIX:<ID>` / `CLOSEFIX:<ID>` et, lorsque nécessaire, `FIXDATA:<ID>`. L'intérieur d'un bloc appartient à ce bloc ; un patch ne peut pas modifier les bytes d'un autre Lego.

Ordre Core de composition : catalogue/alias si nécessaire, media enrichment si nécessaire, runtime media safety, HLS integrity, security boundary, runtime compatibility, stream facts, stream identity, stream presentation, provider branding, terminal sanitizer, puis media-type resolution. L'exécution des wrappers suit naturellement l'ordre inverse de la composition textuelle.

## 4. Contrat runtime

Le Provider JS est un **lecteur spécialisé**, pas un crawler ni un moteur Learning.

- l'événement utile est `launch` ; les autres événements doivent sortir rapidement ;
- l'identité TMDB reste composite : `movie:<id>` ou `tv:<id>` ; anime est un type sémantique, pas un troisième namespace TMDB ;
- `series/show/tv` sont normalisés vers `tv` ;
- la résolution média v26 réconcilie le contexte client et le contexte TMDB avant le travail provider incompatible ;
- un provider incompatible retourne `[]` sans lancer de recherche arbitraire sur son domaine ;
- le provider exécute uniquement des routes/recettes connues et bornées ;
- les traitements de sortie Core n'ont de sens qu'après production de streams ; zéro flux ne devient jamais une raison de fabriquer un résultat ;
- un échec stream-level ne désactive pas à lui seul le provider.

Le Core Media Type courant est `tmdb-data-contract-launch-gate-v26-authoritative-context-reconcile`.

## 5. HLS et playback

Une URL `.m3u8` ou un `#EXTM3U` ne suffit pas à prouver qu'un stream sera lisible.

`CORE.HLS_RUNTIME_INTEGRITY.V1` sait valider/recover de manière bornée les playlists. Pour les providers ayant une preuve de segments malformés sur client natif, le même Core peut activer une preuve **premier segment** :

- fetch playlist borné ;
- résolution du premier variant si master ;
- conservation des `Referer`/`Origin` du stream ;
- lecture bornée du premier segment ou init map ;
- TS : recherche de bytes de synchronisation MPEG-TS ;
- fMP4 : signature de box `ftyp/styp/moof/moov` ;
- HTML/JSON servi à la place d'un segment : rejet positif ;
- chiffrement HLS ou erreur réseau/timeout : état inconclusif, pas faux rejet.

Cette preuve est une capacité Core générique et peut être activée par DATA provider ; elle n'est pas un patch spécifique codé en dur.

## 6. CORE — Quick et Deep

Le workflow routine unique est `.github/workflows/sync.yml`, nom affiché `CORE - Verify & Publish`.

### Quick

Quick est un gate **rapide, déterministe et non-mutant côté providers** :

- tests structurels/contrats critiques ;
- audit des bytes Provider v3 exacts ;
- pas de reconstruction ;
- pas de repair ;
- pas de mutation DATA/Core ;
- pas de publication de nouveau code provider ;
- pas de full network health.

### Deep

Deep est une **validation/observation plus large**, toujours sans mutation du code provider :

- tous les contrats structurels ;
- observation réseau/hubs en lecture seule ;
- health des providers publiés exacts ;
- re-projection des manifests dérivés ;
- génération reports/hashes ;
- publication sur `main` limitée aux rapports, projections et inventaires autorisés.

Deep ne répare pas et ne reconstruit pas les providers.

## 7. Learning

`.github/workflows/brain-learning-lab.yml` est le propriétaire des expérimentations de repair/apprentissage.

- sandbox uniquement ;
- catalogue complet, providers désactivés inclus ;
- mémoire sanitizée persistante ;
- propositions de code reviewables ;
- aucune publication directe de Provider JS ou manifest ;
- aucune permission de détendre les invariants de sécurité/identité.

`engine_v2/` est donc un sous-système d'observation, classification, evidence et Learning. Ce n'est pas une seconde boucle de publication ni un repair caché de Quick/Deep.

## 8. Domain Refresh

`domain-refresh.yml` est une exception explicitement bornée de maintenance DATA : il peut mettre à jour uniquement `official_site` validé et rematérialiser le CONFIG provider correspondant.

Le contrat impose :

- aucun patch Core/Provider structurel ;
- aucun changement API/route ;
- bytes identiques hors bloc `PROVIDER.<ID>.CONFIG.V1` ;
- nouveau filename adressé par contenu ;
- hashes/integrity régénérés.

## 9. Cinq Native Labs

La surface d'acceptation native est exactement :

1. `TVAndroid` — NuvioTV officiel ;
2. `MobileAndroid` — NuvioMobile officiel ;
3. `MobileIOS` — NuvioMobile officiel ;
4. `DesktopMACOS` — NuvioDesktop officiel ;
5. `DesktopWindows` — NuvioDesktop officiel.

Le trigger commun est `.github/triggers/full-native-lab-validation.json`.

Les Labs :

- consomment le SHA NiakVIO exact ;
- résolvent le HEAD client officiel puis contrôlent son drift ;
- testent Interstellar, Breaking Bad S01E01 et Jujutsu Kaisen S01E01 ;
- observent extraction, playback, identité, session et transport ;
- ne réparent, ne reconstruisent et ne réécrivent jamais Provider v3 ;
- conservent uniquement des preuves sanitizées.

Les retests ciblés peuvent relancer un device sans invalider les autres. Desktop dispose d'un trigger ciblé macOS/Windows ; iOS dispose d'un trigger ciblé et d'un watchdog de session reprenable afin qu'un provider QuickJS non-cancellable ne bloque pas le corpus complet.

## 10. Minification

La minification de production est désactivée. Terser ne fait pas partie du pipeline Provider v3.

Tout futur minimizer doit être NiakVIO-aware et prouver qu'il conserve :

- enveloppe BEGIN/END ;
- `STARTFIX/CLOSEFIX/FIXDATA` ;
- frontière Core ;
- remplacement déterministe d'un Lego ;
- équivalence fonctionnelle et reverse reconstruction.

## 11. Branches et publication

- `main` reste la branche de production ;
- les chantiers structurants Provider v3 se valident sur `workbench/provider-v3-performance-playback` ;
- la reconstruction manuelle peut committer uniquement sur une branche non-main sélectionnée ;
- les cinq Labs peuvent tourner sur `main` ou sur le workbench lorsqu'un trigger explicite est poussé ;
- aucun résultat Lab ne doit être présenté comme preuve d'un autre device.

## 12. État de référence du chantier Provider v3

Le 3 septembre 2026, **retry 21** est la reconstruction de référence après le clean d'architecture et le durcissement HLS :

- 96/96 ProviderBase v3 propres ;
- 96/96 providers matérialisés ;
- génération `9ddd9f969838d444` ;
- reverse rebuild 96/96 byte-identical, vérifié une première fois après matérialisation puis à nouveau dans les post-gates ;
- portfolio Lego publié 96/96 vert ;
- audit statique Provider v3 vert ;
- Media Type Core v26 vert ;
- Stream Presentation V18 / identity / runtime media safety / playback integrity / sanitizer verts ;
- release hashes et release integrity verts ;
- commit de reconstruction `8e3f40c318d923e83b1dc49320fc1e4b68efe2cd`.

Retry 19 reste le premier jalon ayant prouvé la reconstruction complète sans seed JS publiée/upstream. Retry 21 confirme la même propriété après les changements Core/DATA ultérieurs, notamment le contrôle HLS premier segment.

Le CORE Quick doit ensuite être exécuté sur **ces mêmes bytes reconstruits** via un commit provider-byte-neutral avant l'acceptation finale des cinq Labs.

## 13. Fichiers de référence

- `automation/provider-v3-architecture.json` — contrat machine-readable ;
- `provider-v3-materialization.json` — état de matérialisation ;
- `PROVENANCE.json` — provenance et hashes de base ;
- `provider-overrides.json` — DATA/options provider ;
- `scripts/provider_patch_blocks.py` — propriété transactionnelle des Lego ;
- `scripts/provider_base_store.py` — ProviderBase v3 ;
- `scripts/materialize_provider_v3_all.py` — reconstruction complète ;
- `scripts/verify_provider_v3_reverse_rebuild.py` — preuve reverse ;
- `tests/provider_v3_workflow_ownership_test.py` — ownership des workflows ;
- `tests/native_five_lab_coverage_test.py` — cinq Labs exacts ;
- `tests/native_lab_observational_purity_test.py` — Labs observationnels ;
- `tests/provider_brick_portfolio_audit_test.py` — audit des Lego publiés.

## 14. Invariants non négociables

1. Pas de seed JS publiée/upstream pour reconstruire Provider v3.
2. ProviderBase v3 + DATA + Lego sont suffisants pour recréer les 96 bundles.
3. Quick/Deep ne réparent ni ne reconstruisent les providers.
4. Learning n'a pas de voie de publication directe.
5. Domain Refresh ne modifie que le CONFIG de domaine autorisé.
6. Les marqueurs canoniques sont STARTFIX/CLOSEFIX.
7. Le Core boundary est unique.
8. Un mauvais média jouable est plus grave qu'un zéro résultat.
9. Une erreur de stream ne devient pas automatiquement une désactivation provider.
10. Les cinq clients/devices sont des dimensions de preuve distinctes.
11. Main ne reçoit pas une reconstruction forcée directe.
12. Toute doc qui contredit ces invariants est considérée comme obsolète et doit faire échouer le contrat de documentation.
