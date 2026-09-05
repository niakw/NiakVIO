# Architecture NiakVIO — Provider v3

> Source de vérité technique du dépôt. Toute évolution Provider v3, CORE, route recognition, Learning, Domain Refresh, Native Labs ou publication doit mettre ce document à jour dans la même transaction.

## 1. Modèle mental

NiakVIO sépare strictement trois rôles :

- **Provider Object = boîte noire structurée** : identité, DATA, routes, stratégie, limites, preuves et provenance ;
- **NiakVIO = cerveau** : reconnaît, compose, vérifie, apprend et publie ;
- **clients Nuvio = appareils de laboratoire** : ils donnent une preuve native d'extraction/transport/lecture, mais ne deviennent jamais une source de vérité inter-device.

NiakVIO ne doit pas réduire artificiellement le catalogue pour obtenir des métriques vertes. Les **96 Provider Objects** restent dans le census, providers désactivés compris. Une absence de route reconnue, un zéro flux ou un échec stream-level ne constitue jamais à lui seul une preuve de mort/quarantaine du provider.

## 2. Sources de vérité Provider v3

- `provider_catalog.json` : registre canonique de métadonnées/projections publiées ;
- `provider-bases/` : ProviderBase v3 propres appartenant à NiakVIO ;
- `provider-overrides.json` : DATA/options provider ;
- `automation/provider-v3-static-knowledge.json` : connaissance structurée durable 96/96 ;
- `scripts/provider_patches/**` : Lego `PROVIDER.*` et `CORE.*` ;
- `providers/*.js` : artefacts client matérialisés et adressés par contenu, **jamais seeds de reconstruction** ;
- upstreams/sites tiers : connaissance/provenance uniquement, jamais JS canonique exécutable.

Le marqueur ProviderBase courant est `NIAKVIO_PROVIDER_BASE_OWNED_V3`.

## 3. DATA de routes canonique

La DATA canonique des routes appartient directement à l'objet unique du provider :

```text
provider.model.routeData
```

Règles :

1. `reconstruct_provider_routes(...)` travaille sur le **Provider Object**, pas sur une seconde structure parallèle ;
2. `provider.model.routes` est uniquement une projection compacte dérivée de `routeData` ;
3. `provider.knowledge.recognizedContract.requests` est uniquement une projection de compatibilité de `routeData` ;
4. chaque route peut conserver `role`, `method`, `bodyFields`, encodage, `Referer`/`Origin`, type de réponse, preuve HTTP, provenance et confiance ;
5. les champs structurés (`searchRoute`, `movieRoute`, `episodeRoute`, `*Path`, `*Endpoint`, etc.) sont reconnus directement ;
6. le source fourni lors de l'onboarding peut être analysé statiquement, y compris variables/concaténations/templates, **sans exécuter le JavaScript provider** ;
7. la reconnaissance est idempotente : `model.routes` et `recognizedContract.requests` ne redeviennent jamais de nouvelles preuves au passage suivant.

Le workflow route-only est `.github/workflows/provider-v3-reconstruct-routes.yml`. Il ne lance ni reconstruction Provider v3 ni JavaScript provider.

### Census route-only vérifié — 5 septembre 2026

Run `33949700926`, source `2fc4279ff1e6b13d1be3614c3d661d8b49d8ca6f`, DATA persistée par `0a2e7c1d8b72d1f0ad8ac45b9de0cdd124053231` :

- **96/96 Provider Objects analysés** ;
- **401 routes** reconstruites ;
- **6 routes avec preuve HTTP** après normalisation/idempotence ;
- **95/96** objets avec `routeData` non vide ;
- `topcartoons` : `routeData=[]`, état de reconnaissance `unknown` ;
- **0 JavaScript provider exécuté** ;
- **0 reconstruction provider exécutée**.

`topcartoons` n'est pas déclaré mort/quarantiné par cette absence. L'état signifie seulement : **aucune route durable identifiable avec les preuves actuelles**.

## 4. Reconstruction déterministe complète

La reconstruction complète des 96 providers appartient uniquement à `.github/workflows/provider-v3-reconstruct-all.yml` sur une branche non-main.

Entrées : ProviderBase v3 + DATA/connaissance statique + type/stratégie/plan + Lego Provider + Lego Core + minimizer NiakVIO-safe + projections/provenance.

Interdictions :

- seed depuis `providers/*.js` ;
- seed depuis un bundle upstream ;
- replay d'un ancien patch source-shape comme vérité canonique ;
- reconstruction automatique dans Quick, Deep ou Native Labs ;
- reconstruction forcée directement sur `main`.

Une reconstruction acceptable doit couvrir 96/96, passer les contrats de type/plan, sécurité/minimizer et terminer `scripts/verify_provider_v3_reverse_rebuild.py` en byte-identical.

## 5. Forme canonique d'un Provider JS

```text
/* BEGIN NIAKVIO_PROVIDER */
/* NIAKVIO_PROVIDER_ID:<id> */
/* NIAKVIO_PROVIDER_BASE_OWNED_V3 */
<ProviderBase v3>

/* STARTFIX:PROVIDER.<ID>.CONFIG.V1 */
/* FIXDATA:PROVIDER.<ID>.CONFIG.V1:<payload> */
<DATA provider>
/* CLOSEFIX:PROVIDER.<ID>.CONFIG.V1 */

<Lego PROVIDER.* éventuels>
/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */
<Lego CORE.* dans STARTFIX/CLOSEFIX>
/* END NIAKVIO_PROVIDER */
```

Les marqueurs canoniques sont `STARTFIX:<ID>` / `CLOSEFIX:<ID>` et, lorsque nécessaire, `FIXDATA:<ID>`. Un Lego ne peut pas modifier les bytes d'un autre Lego.

## 6. Contrat runtime

Le Provider JS est un lecteur spécialisé, pas un crawler ni un moteur Learning.

- événement utile : `launch` ; les autres sortent rapidement ;
- gate capacité/type avant réseau ;
- identité TMDB composite : `movie:<id>` ou `tv:<id>` ; anime reste un type sémantique et utilise le namespace série/TMDB `tv` lorsque nécessaire ;
- `series/show/tv` se normalisent vers `tv` ;
- anime et série sont traités sans mélange heuristique parasite ;
- un provider incompatible retourne `[]` sans recherche arbitraire ;
- TMDB n'est appelé que lorsque la stratégie en a réellement besoin ;
- traitements Core de sortie seulement après production de flux ;
- zéro flux n'autorise jamais la fabrication d'un résultat ;
- une erreur stream-level ne désactive jamais à elle seule le provider.

Le Core Media Type courant reste `tmdb-data-contract-launch-gate-v26-authoritative-context-reconcile`.

## 7. Reader, transport et HLS

Une URL `.m3u8` ou `#EXTM3U` ne prouve pas la lisibilité native.

`CORE.HLS_RUNTIME_INTEGRITY.V1` peut effectuer une validation bornée : playlist, variant, contexte `Referer`/`Origin`, premier segment/init map, sync MPEG-TS ou signature fMP4. HTML/JSON servi à la place d'un média est un rejet positif. Timeout, erreur réseau, chiffrement HLS ou absence d'API bytes côté TV restent **inconclusifs**, jamais faux rejets.

Les Labs doivent séparer : extraction provider, identité, transport, conteneur, contexte de lecture et erreur du player officiel.

## 8. CORE — Verify & Publish

Le workflow routine unique est `.github/workflows/sync.yml`, affiché **CORE - Verify & Publish**.

### Quick

Quick est déterministe, rapide et non-mutant côté provider : contrats structurels, audit bytes exacts, contrats de couverture Labs/minimizer/sécurité. Pas de repair, pas de reconstruction, pas de full network health.

### Deep

Deep ajoute observation réseau/hubs en lecture seule, health des bytes publiés exacts, reprojection manifests, rapports et inventaires. Il ne répare ni ne reconstruit les providers.

**Quick/Deep ne réparent ni ne reconstruisent les providers.**

## 9. Learning et Domain Refresh

Learning (`brain-learning-lab.yml`) est sandbox-only : observation, classification, essais bornés, mémoire sanitizée et propositions reviewables. Aucune publication directe de Provider JS/manifest.

Domain Refresh (`domain-refresh.yml`) est une exception DATA bornée : mise à jour `official_site` validée uniquement, sans changement API/route/Core/Provider structurel ; bytes identiques hors CONFIG concerné.

## 10. Cinq Native Labs

Surface d'acceptation exacte :

1. `TVAndroid` — NuvioTV ;
2. `MobileAndroid` — NuvioMobile ;
3. `MobileIOS` — NuvioMobile ;
4. `DesktopMACOS` — NuvioDesktop ;
5. `DesktopWindows` — NuvioDesktop.

Trigger commun : `.github/triggers/full-native-lab-validation.json`.

Le contrat couvre l'intégralité du catalogue : **96 providers / 214 routes déclarées** (`82 movie + 92 tv + 40 anime`). Les Labs sont observationnels : ils consomment les bytes NiakVIO exacts et ne réparent/reconstruisent jamais pour obtenir un vert artificiel.

## 11. Minimizer NiakVIO

Terser est interdit. `scripts/provider_v3_minimizer.py` est conservateur et pré-hash : suppression de l'indentation uniquement lorsque l'état lexical initial est du JavaScript ordinaire. Il conserve retours ligne/ASI, identifiants, expressions, littéraux, regexp, templates sensibles, enveloppes BEGIN/END, `STARTFIX/CLOSEFIX/FIXDATA` et frontière Core.

Gates :

- `tests/provider_v3_minimizer_contract_test.py` ;
- `tests/provider_v3_minimizer_preview_test.py` ;
- `tests/provider_v3_minimizer_published_test.py` ;
- `scripts/verify_provider_v3_reverse_rebuild.py`.

## 12. Snapshots historiques ≠ vérité opérationnelle courante

`automation/provider-v3-architecture.json.reference_reconstruction` conserve volontairement un snapshot de matérialisation historique pour la preuve reverse. Ses anciens comptes de plans/quarantaines ne doivent **jamais** être réinterprétés comme la vérité actuelle de reconnaissance ou de disponibilité.

En particulier, l'ancien snapshot `retry25` (`91` plans exécutables + `5` quarantines) reste une référence de matérialisation figée. L'état courant des routes se lit exclusivement dans `route_recognition.latest_verified_census` et `automation/provider-v3-static-knowledge.json`.

Une quarantaine nécessite une **raison fonctionnelle explicite et prouvée**. `routeData=[]` ne constitue pas cette preuve.

## 13. Branches et publication

- `main` = production ;
- chantier courant de reconnaissance : `workbench/provider-v3-recognition-routes-data` ;
- reconstruction complète manuelle : branche non-main uniquement ;
- Labs sur SHA exact ; aucune preuve d'un device ne vaut preuve d'un autre ;
- branches Learning/proposals séparées du contrôle de publication.

## 14. Invariants non négociables

1. Pas de seed JS publiée/upstream pour reconstruire Provider v3.
2. ProviderBase v3 + DATA + Lego suffisent à recréer les bundles.
3. `provider.model.routeData` est la source canonique des routes.
4. `model.routes` et `knowledge.recognizedContract.requests` sont des projections, pas des preuves sources.
5. La reconnaissance route-only n'exécute ni JS provider ni reconstruction complète.
6. Une reconnaissance vide n'est ni une quarantaine ni une preuve de mort.
7. Quick/Deep ne réparent ni ne reconstruisent les providers.
8. Learning n'a pas de voie de publication directe.
9. Domain Refresh ne modifie que le CONFIG autorisé.
10. Les marqueurs canoniques sont STARTFIX/CLOSEFIX et le Core boundary est unique.
11. Un mauvais média jouable est plus grave qu'un zéro résultat.
12. Une erreur stream-level ne devient pas automatiquement une désactivation provider.
13. Les cinq clients/devices sont des dimensions de preuve distinctes.
14. Main ne reçoit pas une reconstruction forcée directe.
15. Le stripping HTML par regexp générique est interdit.
16. Terser reste interdit ; le minimizer ne transforme que ce que son contrat lexical autorise.
17. Toute documentation qui contredit ces invariants est obsolète et doit faire échouer le contrat de documentation.

## Fichiers de référence

- `automation/provider-v3-architecture.json` — contrat machine-readable ;
- `automation/provider-v3-static-knowledge.json` — Provider Objects + route DATA ;
- `provider-v3-materialization.json` — snapshot de matérialisation ;
- `PROVENANCE.json` — provenance/hashes ;
- `provider-overrides.json` — DATA/options ;
- `scripts/provider_route_reconstructor.py` — reconnaissance/reconstruction route-only ;
- `scripts/materialize_provider_v3_all.py` — reconstruction complète ;
- `scripts/verify_provider_v3_reverse_rebuild.py` — preuve reverse ;
- `scripts/provider_v3_minimizer.py` — minimizer safe ;
- `tests/provider_route_reconstructor_test.py` — routeData/idempotence/census ;
- `tests/provider_v3_documentation_contract_test.py` — drift docs/ownership ;
- `tests/native_five_lab_coverage_test.py` — cinq Labs ;
- `tests/native_lab_observational_purity_test.py` — pureté observationnelle.
