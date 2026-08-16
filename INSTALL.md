# Installation et maintenance

## Utilisateurs Nuvio

Choisissez l'un des deux manifests stables :

- général — VF, VOSTFR, VO et autres langues : `https://raw.githubusercontent.com/niakw/Niakvio/refs/heads/main/manifest.json` ;
- francophone — VF/VOSTFR : `https://raw.githubusercontent.com/niakw/Niakvio/refs/heads/main/vf/manifest.json`.

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

Il n'existe qu'un orchestrateur de production : **`Niakvio provider pipeline`** (`.github/workflows/sync.yml`).

Il expose deux profondeurs :

- `quick` : maintenance courante, repair-first, capable de publier une amélioration prouvée sans attendre Deep ;
- `deep` : reconstruction et preuve large pour changements structurels, nouvelles intégrations et apprentissage/persistance des recipes.

Ne modifiez pas manuellement `manifest.json` et `vf/manifest.json` comme deux sources autonomes. La source publiée canonique est `provider_catalog.json` ; les manifests sont des projections rendues et revalidées depuis ce catalogue dans la transaction de publication.

Le pipeline régénère également les versions, projections de langue, provenance, LKG et empreintes (`FILE-HASHES.json`, `SHA256SUMS.json`, `PATCH-SHA256SUMS.txt`) avant un commit atomique.

## Vérification runtime

Une modification du chemin de playback partagé doit être suivie des preuves natives appropriées :

- Nuvio Mobile ;
- Nuvio Desktop ;
- NuvioTV / Android TV.

Le workflow `final-native-client-validation-v2.yml` conserve ces preuves séparées. Le Lab multi-œuvres (`nuvio-client-lab.yml`) mesure films, séries et anime ; la cible 10 providers jouables dont 3 VF est un objectif de largeur, tandis que les contradictions d'identité ou médias illisibles restent des échecs.

## Règle de maintenance

Une correction générique appartient à ARCHI 2. Les scripts historiques encore présents ne sont que des primitives de compatibilité derrière le plan de contrôle V2 ; ils ne doivent pas recréer un second pipeline, un second manifest canonique ou une politique d'activation concurrente.
