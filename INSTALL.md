# Installation et maintenance

## Utilisateurs Nuvio

Choisissez le manifest adapté :

- général — VF, VOSTFR, VO et autres langues : `https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/manifest.json` ;
- francophone — VF/VOSTFR : `https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/vf/manifest.json` ;
- général sans providers orientés anime : `https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/no-anime/manifest.json` ;
- francophone sans providers orientés anime : `https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/vf-no-anime/manifest.json`.

Dans un client Nuvio compatible :

1. ouvrir la gestion des plugins/providers ;
2. ajouter/importer l'URL voulue ;
3. actualiser le repository.

Les URL restent stables. Les versions, bundles, domaines et états d'activation évoluent derrière elles.

## Mainteneurs

Prérequis : Node.js 24+ et Python 3.12 recommandé.

Installation reproductible :

```bash
npm ci --ignore-scripts --no-audit --no-fund
```

Validation locale minimale :

```bash
npm test
node engine_v2/tests/provider-catalog.test.mjs
```

Diagnostics :

```bash
npm run diagnostics
```

## Publication

Le workflow routine unique est **CORE - Verify & Publish** (`.github/workflows/sync.yml`).

Il expose deux profondeurs de vérification :

- `quick` : gate rapide et déterministe sur les bytes Provider v3 exacts et les contrats Core critiques ; aucun repair, aucune reconstruction, aucune mutation Provider/DATA/Core ;
- `deep` : vérification structurelle complète + observation réseau read-only + re-projection des manifests/reports/hashes ; toujours aucun repair ni reconstruction provider.

La reconstruction forcée 96/96 appartient uniquement à `.github/workflows/provider-v3-reconstruct-all.yml` sur une branche non-main et doit prouver un reverse rebuild byte-identical.

Le Learning (`brain-learning-lab.yml`) est le seul monde d'expérimentation de repair ; il travaille en sandbox et ne publie pas directement. `domain-refresh.yml` est séparément limité au CONFIG `official_site` validé.

Ne modifiez pas manuellement `manifest.json` et `vf/manifest.json` comme deux sources autonomes. La source publiée canonique de métadonnées/projections est `provider_catalog.json` ; les manifests sont des projections rendues et revalidées dans la transaction autorisée.

Les bundles providers hashés sont immuables et adressés par contenu. Le code durable reste ProviderBase v3 + DATA/CONFIG + Lego `PROVIDER.*` / `CORE.*`.

## Vérification runtime

Une modification du chemin de playback partagé doit être suivie des preuves natives appropriées :

- NuvioTV / Android TV + Nuvio Mobile Android : `.github/workflows/native-mobile-android-reader.yml` ;
- Nuvio Mobile iOS : `.github/workflows/native-mobile-ios-reader.yml` ;
- Nuvio Desktop macOS/Windows : `.github/workflows/native-desktop-reader-acceptance.yml` ;
- corpus natif ciblé : `.github/workflows/native-corpus-device-targeted.yml`.

Le corpus de référence est versionné dans `.github/triggers/nuvio-client-lab.json` et couvre Interstellar, Breaking Bad S01E01 et Jujutsu Kaisen S01E01. La surface d'acceptation est exactement cinq Labs : TV Android, Mobile Android, Mobile iOS, Desktop macOS et Desktop Windows. Les Labs consomment les bytes NiakVIO exacts et les clients Nuvio officiels sans réparer, reconstruire ou réécrire les providers.

## Maintenance GitHub Actions

`.github/workflows/purge-actions-history.yml` effectue chaque semaine une maintenance automatique : les runs terminés de plus de **7 jours** sont supprimés avec leurs artifacts. Le workflow conserve aussi un mode manuel pour une purge ponctuelle des logs seuls ou des runs complets.

Les artifacts temporaires des Labs natifs sont actuellement conservés **8 jours**. Le cache Gradle reste désactivé lorsque le workflow le prévoit afin de préserver le quota GitHub Actions ; les preuves persistées doivent rester sanitizées.

## Règle de maintenance

Une correction générique appartient au Provider v3/Core approprié. Les scripts historiques encore présents ne sont que des primitives de compatibilité ou de Learning ; ils ne doivent jamais recréer un second pipeline de publication, un second manifest canonique ou une politique d'activation concurrente.
