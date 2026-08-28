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
- contrats des Labs natifs et du corpus multi-œuvres.

## Validation native et corpus multi-œuvres

Le corpus canonique est versionné dans [`.github/triggers/nuvio-client-lab.json`](.github/triggers/nuvio-client-lab.json). Il contient actuellement **10 fixtures** couvrant films, séries et anime, avec des cas de désambiguïsation d'année, de saison/épisode, de durée et de mauvaise identité média.

La preuve native est répartie entre trois workflows complémentaires :

- [`native-android-route-reader.yml`](.github/workflows/native-android-route-reader.yml) : Nuvio Mobile + NuvioTV/Android TV sur les fixtures représentatives et les régressions TV prioritaires ;
- [`native-desktop-reader-acceptance.yml`](.github/workflows/native-desktop-reader-acceptance.yml) : lecteurs officiels Desktop macOS et Windows ;
- [`native-corpus-device-targeted.yml`](.github/workflows/native-corpus-device-targeted.yml) : retest manuel borné d'un device, d'un provider ou du corpus natif ciblé.

Les preuves sont **indépendantes par client et par device** : une réussite Desktop ne vaut pas automatiquement réussite Mobile ou TV. Les Labs peuvent inclure des providers `enabled:false` afin de diagnostiquer ou revalider un provider sans le réactiver implicitement.

La politique du corpus conserve une cible de couverture de **10 providers dont 3 VF**, mais cette cible n'est pas un seuil automatique de publication (`blocking:false`, `enforce_policy:false`). En revanche, une contradiction d'identité, de saison, d'épisode ou de média final reste un signal bloquant pour la preuve concernée et ne doit jamais être transformée en succès de couverture.

Les timeouts isolés peuvent être retentés de manière bornée. Les artifacts natifs temporaires sont conservés **1 jour** et les preuves persistées restent sanitizées : pas d'URL de lecture complète, de token, de cookie ou de valeur d'en-tête sensible.

## Cycle de réparation et publication

Une réparation n'est conservée que si le bundle exact progresse lors d'une nouvelle exécution bornée. La publication synchronise les versions des manifests et paquets, élague les bundles hachés devenus non référencés, régénère les empreintes, puis exécute `scripts/validate_release_integrity.py`.

`sync.yml` est l'unique orchestrateur de publication complète. Les Labs natifs produisent de la preuve ; ils ne constituent pas une seconde voie de publication.

## Limites

Une IP de CI peut être bloquée alors qu'une connexion résidentielle fonctionne, et un échantillon ne peut pas prouver tous les titres, langues ou appareils. Une couverture faible reste donc distincte d'une incompatibilité concluante. Une validation technique ne détermine pas non plus le statut juridique d'une source tierce.
