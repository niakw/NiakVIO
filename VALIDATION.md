# Validation

## Suite locale

```bash
npm ci --ignore-scripts --no-audit --no-fund
npm test
node engine_v2/tests/provider-catalog.test.mjs
```

Les tests couvrent notamment :

- sécurité réseau/SSRF, limites mémoire/temps/sorties ;
- syntaxe et contrat `getStreams` des bundles publiés ;
- P2P/torrent interdits ;
- projections de manifests et langues ;
- Provider v3, reverse reconstruction et minimizer ;
- type canonique vs transport Nuvio ;
- identité movie/tv/anime, saison/épisode ;
- HLS/DASH/MP4/Matroska/MPEG-TS ;
- provenance, versions, hashes et release integrity ;
- contrats des cinq Native Labs.

## Matrice native

La surface d’acceptation est exactement :

1. TV Android — NuvioTV ;
2. Mobile Android — NuvioMobile ;
3. Mobile iOS — NuvioMobile ;
4. Desktop macOS — NuvioDesktop ;
5. Desktop Windows — NuvioDesktop.

Workflows :

- `.github/workflows/native-mobile-android-reader.yml` ;
- `.github/workflows/native-mobile-ios-reader.yml` ;
- `.github/workflows/native-desktop-reader-acceptance.yml` ;
- `.github/workflows/native-corpus-device-targeted.yml` pour les diagnostics ciblés.

<!-- NIAKVIO_NATIVE_ADAPTIVE_LAB_DOCS_V1 -->
Le corpus global ordinaire est défini par `.github/triggers/rotating-popular-corpus.json` : exactement trois réserves `movie`, `tv`, `anime`, actuellement 32 œuvres chacune, de 2010 à l’année civile précédente. `.github/triggers/nuvio-client-lab.json` conserve les fixtures de régression ciblées/historiques. Le trigger de validation complète reste `.github/triggers/full-native-lab-validation.json`.

### Couverture dérivée, jamais figée

Le catalogue reste **96 providers**. La campagne d’acceptation native finale utilise actuellement le scope physique **Hub-46** dérivé de `automation/evidence/hub-lab-matrix-46.json` et transporté par `native-hub46/manifest.json`. Les 50 autres lignes ne disparaissent pas du catalogue : elles restent séparées du dénominateur physique du Lab. Le nombre de routes est calculé depuis le scope courant et ses `supportedTypes` ; il ne doit pas être recopié comme constante historique.

La distinction est obligatoire :

- `canonicalSupportedTypes` = capacité sémantique réelle ;
- `supportedTypes` = surface de lancement Nuvio.

Un provider canonique anime-only peut donc avoir `supportedTypes = [anime, tv, series]`. Les voies `anime`, `tv` et `series` restent des lancements compatibles sans élargir la capacité canonique ; `movie` n’est exposé que s’il est canonique.

`tests/native_five_lab_coverage_test.py` doit calculer et vérifier dynamiquement cette relation à chaque changement de manifest.

### Couverture ≠ résultat lecteur

La couverture vérifie que toutes les routes déclarées ont bien été exécutées/terminées. Le verdict lecteur reste séparé :

```text
non-empty / zero / error / timeout / player
```

Un workflow vert ne signifie donc jamais « les 96 providers ont renvoyé des streams ».

Un mauvais média, mauvais épisode, mauvaise identité ou contradiction de type reste un échec de preuve même si une URL est techniquement lisible.

### Les Labs n’adaptent pas les repos Nuvio

Les Labs doivent utiliser le comportement officiel observé. Ils peuvent ajouter du plumbing de test strictement nécessaire pour atteindre/exposer le chemin officiel, mais ils ne doivent pas patcher NuvioTV, NuvioMobile ou NuvioDesktop pour contourner :

- une erreur de compilation ;
- une dépendance/packaging cassé ;
- un crash runtime/QuickJS ;
- un bug player ;
- une restriction réseau/OS ;
- un test upstream cassé.

Un tel défaut reste une preuve externe rouge. Le rendre vert artificiellement détruirait précisément l’information que le Lab doit fournir.

Chaque provider est borné individuellement ; un timeout devient une observation, pas une boucle infinie de retry.

### Rotation adaptative des œuvres

Une exécution native commence par une seule œuvre de chaque réserve globale : **1 movie + 1 TV + 1 anime**. Le reste des 32 œuvres/lane est une réserve, pas un batch. Seul un provider/lane qui a terminé normalement avec `0 streams` avance vers une autre œuvre de la même lane. Dès qu’un flux positif est prouvé, ce provider/lane sort de la rotation. Une erreur technique, un timeout, un échec de chargement/player/transport ou une contradiction d’identité ne déclenche jamais une rotation destinée à cacher l’erreur.

Le gate final doit agréger ces essais successifs par provider/lane : `FULL`, `PARTIAL`, `RESAMPLE` et `ZERO` décrivent des preuves distinctes ; un clean miss de catalogue n’est pas une régression.

## Cycle Provider v3

Le code durable est :

```text
ProviderBase v3 + structured DATA + owned Lego + NiakVIO-safe minimizer
```

Une reconstruction complète :

- couvre les 46 Provider Objects Hub ;
- s’exécute uniquement sur une branche non-main ;
- ne seed jamais depuis les bundles publiés/upstream ;
- valide sécurité/type/plan/minimizer ;
- termine par `scripts/verify_provider_v3_reverse_rebuild.py` byte-identical.

Les anciens comptes `executable/quarantined` appartiennent aux snapshots historiques de reconstruction et ne doivent pas être utilisés comme vérité actuelle.

## CORE Quick / Deep

`.github/workflows/sync.yml` est l’unique routine **CORE - Verify & Publish**.

### Quick

- déterministe ;
- audit des bytes Provider v3 exacts ;
- contrats Core/type/minimizer/sécurité/Labs ;
- aucun repair ;
- aucune reconstruction provider ;
- aucune mutation Provider/DATA/Core.

### Deep

Ajoute :

- observation hubs/domaines read-only ;
- health des bundles publiés exacts ;
- diagnostics ;
- re-projection des manifests ;
- hashes et release integrity.

Deep ne répare et ne reconstruit pas les providers.

## Learning

`brain-learning-lab.yml` peut observer, classifier et essayer des réparations NiakVIO en sandbox. Une proposition Learning doit repasser par les contrats normaux avant publication.

Un échec Nuvio/OS n’est pas une cause Provider v3 et ne doit pas générer de mutation provider.

## Domain Refresh

`domain-refresh.yml` est une transaction d’adresse séparée et bornée, dont l’autorité de publication est `scripts/domain_refresh_transaction_v2.py` :

- les hubs/channels/redirects officiels servent uniquement à résoudre l’instance terminale courante ;
- la nouvelle autorité d’adresse est persistée dans `provider-overrides.json`, `provider-hubs.json` et `provider-domain-history.json` ;
- seules les dérivées de domaine réellement reliées à l’ancien terminal sont réconciliées ; les routes/protocoles métier et API non liées au déplacement de domaine ne sont pas réécrits ;
- pour chaque provider modifié, le bloc `PROVIDER.<ID>.CONFIG.V1` complet est reconstruit depuis la DATA structurée courante ; l’ancien updater partiel `officialSite`-only n’est pas une autorité de publication ;
- le namespace source-qualified du filename provider est conservé et seul le hash de contenu tourne lorsque le CONFIG change ;
- tous les bytes hors CONFIG, y compris ProviderBase et Lego `CORE.*`, doivent rester identiques ;
- DNS/HTTP après résolution est une observation et ne peut pas annuler une adresse annoncée par une source autoritative uniquement parce qu’un runner reçoit 403/anti-bot/timeout ;
- activation 46/50, projections, versions cache-safe, hashes et release integrity restent synchronisés ;
- la transaction est fail-closed sur rollback, cycle de remplacement, terminal template/social et mutation hors CONFIG, puis Quick est relancé après publication.

Contrats principaux : `tests/domain_refresh_workflow_test.py`, `tests/domain_refresh_transaction_guard_test.py`, `tests/provider_v3_workflow_ownership_test.py` et `scripts/validate_domain_refresh_transaction.py`.

## Minimizer

Terser est interdit. `scripts/provider_v3_minimizer.py` conserve les marqueurs, retours ligne nécessaires, identifiants, ordre d’exécution, littéraux, regexp et templates sensibles. Les transformations risquées restent byte-stables.

Tests principaux :

- `tests/provider_v3_minimizer_contract_test.py` ;
- `tests/provider_v3_minimizer_preview_test.py` ;
- `tests/provider_v3_minimizer_published_test.py` ;
- `scripts/verify_provider_v3_reverse_rebuild.py`.

## Sécurité

Le stripping HTML générique par regexp est interdit. `tests/provider_html_filter_security_test.py` vérifie les sources génératrices et les bundles publiés.

CodeQL et les gates sécurité ne doivent pas être « nettoyés » en désactivant les règles : un finding sur code NiakVIO doit être corrigé ou explicitement justifié.

## Limites de preuve

- une IP CI peut être bloquée alors qu’une IP résidentielle fonctionne ;
- un corpus ne représente pas tous les titres/langues ;
- une preuve sur un device n’est pas transférable à un autre ;
- une réussite ponctuelle ne garantit pas la disponibilité future ;
- une validation technique ne détermine pas le statut juridique d’un service tiers.

Ces limites produisent de l’inconclusif, pas de faux succès ni de faux provider-dead.
