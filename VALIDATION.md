# Validation

## Suite locale obligatoire

```bash
npm ci --ignore-scripts --no-audit --no-fund
npm test
```

La suite couvre notamment :

- sécurité réseau, SSRF, limites de mémoire, durée, sorties et téléchargements ;
- syntaxe, chargement, contrat `getStreams` et sémantique de tous les bundles publiés ;
- exclusions P2P/torrent, catégories, langues et projections général/VF ;
- correctifs globaux, récupération catalogue, idempotence et last-known-good ;
- contrats NuvioTV, Desktop et Mobile, ainsi que la dérive des clients officiels ;
- validation média HLS, DASH, MP4, Matroska et MPEG-TS ;
- versions synchronisées, provenance JSON, périmètre et empreintes de release ;
- comportement et configuration du lab de lecture multi-œuvres.

## Lab de lecture multi-œuvres

Le workflow [`Nuvio client media transport lab`](.github/workflows/nuvio-client-lab.yml)
exécute six fixtures : deux films, deux séries et deux anime, avec une œuvre récente
à faible couverture. Il charge les bundles publiés avec les contrats NuvioTV, Desktop
et Mobile, vérifie le média final et refuse les contradictions d'identité, de saison
ou d'épisode.

Un provider ne compte que s'il est activé et jouable sur tous les clients demandés.
L'objectif est de 10 providers dont 3 VF par œuvre. Ce seuil mesure la couverture mais
ne bloque pas une release lorsqu'une œuvre récente ou rare reste sous la cible. Un
timeout isolé est retenté une fois avec un profil réduit. Les artefacts JSON et Markdown
ne conservent ni URL complète, ni jeton, ni valeur d'en-tête sensible.

Cette tolérance porte uniquement sur le nombre de résultats. Une contradiction
d’identité sur un média lisible bloque le job, y compris si le manifest marque déjà
le provider désactivé, jusqu’à publication d’un bundle inerte cache-safe.

## Cycle de réparation et publication

Une réparation n'est conservée que si le bundle exact progresse lors d'une nouvelle
exécution bornée. La publication synchronise les versions des manifests et paquets,
élague les bundles hachés devenus non référencés, régénère les empreintes, puis exécute
`scripts/validate_release_integrity.py`. Le lab distant vérifie également l'intégrité
du dépôt avant de lancer sa matrice.

## Limites

Une IP de CI peut être bloquée alors qu'une connexion résidentielle fonctionne, et un
échantillon ne peut pas prouver tous les titres, langues ou appareils. Une couverture
faible reste donc distincte d'une incompatibilité concluante. Une validation technique
ne détermine pas non plus le statut juridique d'une source tierce.
