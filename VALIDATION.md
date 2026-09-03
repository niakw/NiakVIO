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

## Validation native et corpus borné par type

Le corpus canonique est versionné dans [`.github/triggers/nuvio-client-lab.json`](.github/triggers/nuvio-client-lab.json). La liste peut contenir plusieurs œuvres de diagnostic, mais la preuve native standard en sélectionne **une seule par type déclaré et par provider** : au maximum 1 film + 1 série + 1 anime.

La preuve native est répartie entre plusieurs workflows complémentaires :

- [`native-mobile-android-reader.yml`](.github/workflows/native-mobile-android-reader.yml) : NuvioTV/Android TV **et** Nuvio Mobile Android, avec jobs/runtimes isolés et preuves distinctes par client ;
- [`native-mobile-ios-reader.yml`](.github/workflows/native-mobile-ios-reader.yml) : Nuvio Mobile iOS, workflow autonome sur simulateur iOS avec runtime plugin et lecteur iOS officiels ;
- [`native-desktop-reader-acceptance.yml`](.github/workflows/native-desktop-reader-acceptance.yml) : lecteurs officiels Desktop macOS et Windows ;
- [`native-corpus-device-targeted.yml`](.github/workflows/native-corpus-device-targeted.yml) : retest manuel borné d'un device, d'un provider ou du corpus natif ciblé.

Les preuves sont **indépendantes par client et par device** : la surface canonique est exactement TV Android, Mobile Android, Mobile iOS, Desktop macOS et Desktop Windows. Une réussite sur une cible ne vaut jamais automatiquement réussite sur une autre. Les Labs peuvent inclure des providers `enabled:false` afin de diagnostiquer ou revalider un provider sans le réactiver implicitement. Les workflows natifs lourds s'exécutent sur `main` ou manuellement, pas sur chaque PR : ils enrichissent la preuve sans bloquer la publication normale.

La politique du corpus conserve une cible de couverture de **10 providers dont 3 VF**, mais cette cible n'est pas un seuil automatique de publication (`blocking:false`, `enforce_policy:false`). En revanche, une contradiction d'identité, de saison, d'épisode ou de média final reste un signal bloquant pour la preuve concernée et ne doit jamais être transformée en succès de couverture.

Chaque exécution provider est bornée individuellement. Un timeout natif n'est pas rejoué en boucle dans le même Lab : il devient une preuve exploitable par Learning ; Deep reste observationnel et ne répare pas. Les artifacts natifs temporaires des workflows actuels sont conservés **8 jours** et les preuves persistées restent sanitizées : pas d'URL de lecture complète, de token, de cookie ou de valeur d'en-tête sensible.

## Cycle Provider v3

Le code provider évolue par ProviderBase v3, DATA et Lego versionnés. La reconstruction complète est manuelle, limitée à une branche non-main et doit prouver 96/96 providers + reverse rebuild byte-identical.

`sync.yml` est l'unique routine CORE Quick/Deep : Quick/Deep vérifient et observent, sans repair ni reconstruction provider. Le Learning travaille en sandbox et ne publie pas directement. `domain-refresh.yml` peut uniquement rematérialiser un CONFIG `official_site` validé.

Les bundles providers restent adressés par contenu ; les projections et hashes sont régénérés puis `scripts/validate_release_integrity.py` ferme la transaction.

## Limites

Une IP de CI peut être bloquée alors qu'une connexion résidentielle fonctionne, et un échantillon ne peut pas prouver tous les titres, langues ou appareils. Une couverture faible reste donc distincte d'une incompatibilité concluante. Une validation technique ne détermine pas non plus le statut juridique d'une source tierce.
