# Contrôles de santé, de compatibilité et de lecture

## Matrice des critères

Le système ne réduit pas la santé d'un provider à un simple code HTTP. Les contrôles
sont répartis en plusieurs familles :

| Famille | Exemples contrôlés |
|---|---|
| Intégrité de découverte | manifest lisible, ID unique, chemin sûr, fichier JavaScript non vide, empreinte SHA-256 |
| Politique | exclusion par ID, métadonnées, code et sortie pour torrent, magnet, P2P et debrid |
| Exécution | chargement CommonJS/ESM, présence de `getStreams`, délai, mémoire, erreur d'exécution |
| Correspondance technique | type film/série/anime, saison et épisode transmis, nombre de réponses |
| Disponibilité réseau | DNS, connexion refusée, délai, HTTP 4xx/5xx, redirections, anti-robot, débit limité |
| Cohérence de charge utile | HLS, DASH, MP4, Matroska, MPEG-TS, sous-titre, HTML ou réponse vide inattendue |
| Lecture HLS/DASH | playlist principale, meilleure variante, premier segment, MPD |
| Identité d’œuvre | titre/alias, saison, épisode, nom de fichier média et cohérence de durée |
| Qualité | résolution annoncée et vérifiée, débit maximal, codecs, HDR/Dolby Vision |
| Langues | pistes audio et sous-titres exposés, vérification limitée d'une piste de sous-titres |
| Performance | latence du provider et des points sondés |
| Stabilité | succès/échecs consécutifs, durée minimale de panne, dernière version fonctionnelle connue |
| Publication | fichiers nommés par empreinte, publication des fichiers avant le manifest, conservation des anciennes versions |
| Provenance | dépôt, auteur/projet, ID amont, licence, nom d'origine et SHA-256 |
| Confidentialité | aucune URL complète dans les rapports, aucun secret transmis au code tiers |

Cette matrice reste une validation par échantillonnage : elle ne peut pas prouver que
tous les titres, épisodes, langues ou appareils fonctionneront.

## Cinq niveaux indépendants

### 1. Disponibilité générale — toutes les quatre heures

Cible tous les providers actuellement publiés. Le contrôle utilise un titre tournant,
un seul endpoint et un petit échantillon d'octets. Son objectif est de détecter les
pannes, pas de mesurer la qualité d'image.

Les pannes franches comprennent les erreurs DNS, connexions refusées, délais dépassés,
erreurs serveur et erreurs d'exécution. Les HTTP 403/429, pages anti-robot et recherches
sans résultat sont suivis séparément et ne comptent pas comme panne franche.

### 2. Relance ciblée — chaque heure en cas de panne

Les providers dont le dernier état est `unavailable` ou `failed`, ainsi que ceux dont
un hôte individuel reste en panne, sont retestés. Jusqu'à trois endpoints sont sondés
pour voir si un hôte a récupéré ou si le provider l'a remplacé. Les providers sains,
bloqués par une IP de datacenter ou simplement sans résultat ne sont pas relancés chaque
heure.

Politique par défaut :

- au moins six échecs francs ;
- panne observée pendant au moins huit heures ;
- puis désactivation automatique ;
- deux succès consécutifs après une désactivation automatique : réactivation ;
- une désactivation manuelle est toujours préservée.

La double condition **nombre + durée** évite qu'une série rapide d'échecs transitoires
ne désactive immédiatement un provider.

### 3. Validation rapide — cinq jours chaque semaine

Télécharge chaque candidat de chaque manifest amont, hors P2P/torrent. Elle exécute un
titre tournant et vérifie la cohérence de base, mais reste strictement **report-only** :
elle ne réécrit, ne promeut et ne désactive aucun provider.

### 4. Audit approfondi — mardi et vendredi

Utilise jusqu'à trois titres et quatre endpoints par candidat. Il peut inspecter :

- playlist principale HLS ;
- meilleure variante HLS ;
- premier segment média ;
- manifest DASH ;
- signatures directes MP4, Matroska et MPEG-TS ;
- hauteur annoncée et vérifiée ;
- débit, codecs et indicateurs HDR ;
- langues audio et sous-titres ;
- accessibilité d'une piste de sous-titres ;
- latence et catégorie de panne.
- durée mesurée du média comparée à la durée attendue lorsqu’elle est connue ;
- contradictions explicites entre l’œuvre demandée et le titre, l’épisode ou le nom du fichier média retourné.

### 5. Lab de lecture multi-œuvres — à chaque changement pertinent

Le lab exécute une matrice de films, séries et anime, dont une œuvre récente à faible
couverture, avec les contrats NuvioTV, Desktop et Mobile. Il vérifie le média final,
les playlists et les premiers segments, puis rejette les contradictions de titre,
saison, épisode, nom de fichier média ou durée. Un timeout isolé peut être retenté
une fois avec un profil réduit. La qualité UI `Unknown` / `Inconnue` reste indépendante
de l’identité de l’œuvre et n’est jamais un motif de rejet à elle seule.

La cible de **10 providers jouables dont 3 VF par œuvre** est un objectif de couverture
indicatif. Elle ne bloque pas une publication lorsque le catalogue d'une œuvre récente
ou rare ne permet pas de l'atteindre. Les erreurs runtime, contenus contradictoires et
médias non lisibles ne sont toutefois jamais comptés comme succès. Les rapports JSON
et Markdown sont nettoyés avant leur publication comme artefacts CI.


## Boucle générique de réparation pendant le deep

Le deep n'applique plus préventivement une réécriture à tous les bundles. Il suit une
boucle bornée et vérifiable :

1. exécution du candidat après les seuls remplacements durables ;
2. classification d'un schéma d'échec à partir des observations réseau nettoyées ;
3. sélection des profils structurels compatibles, sans condition sur l'ID du provider ;
4. création d'un nouveau fichier JavaScript et validation syntaxe/chargement ;
5. nouvelle exécution deep du fichier exact ;
6. comparaison stricte avant/après ;
7. conservation du nouveau fichier uniquement si le résultat progresse réellement.

Une simple disparition de routes 404 sans amélioration du statut, du score, de l'accès
au serveur ou des streams ne suffit pas. Les erreurs runtime, résultats identiques et
régressions sont rejetés ; le fichier parent reste la source publiée. Plusieurs profils
peuvent s'enchaîner sur des rounds successifs, avec une limite globale configurée dans
`provider-overrides.json`. Le détail est écrit dans `repair-report.json`.

## Signification des statuts

- `healthy` : au moins un endpoint cohérent a été atteint ;
- `blocked` : blocage probable de l'IP GitHub, contrôle anti-robot ou HTTP 403/429 ;
- `degraded` : le module retourne des endpoints, mais aucun n'a pu être entièrement confirmé ;
- `no_streams` : aucun résultat pour l'échantillon tournant ;
- `unavailable` : panne réseau ou endpoint répétée ;
- `failed` : erreur de chargement ou d'exécution du module ;
- `excluded` : provider ou sortie P2P/torrent interdite par la politique du dépôt.

## Champs de qualité

- `reported_max_height` : résolution écrite par le provider ;
- `verified_max_height` : résolution lue dans une playlist HLS ou un manifest DASH ;
- `max_bandwidth` : débit maximal déclaré ;
- `codecs` : identifiants de codecs exposés ;
- `hdr_formats` : indicateurs HDR/Dolby Vision exposés ;
- `audio_languages` et `subtitle_languages` : codes de langues détectés.

Un endpoint MP4/MKV peut être accessible sans exposer assez de métadonnées pour vérifier
sa résolution exacte. L'absence de `verified_max_height` n'est donc pas automatiquement
un échec.

## Publication atomique et provenance

1. Les candidats sont copiés sous `staging/`.
2. Un job en lecture seule les teste.
3. Les versions acceptées sont copiées vers des noms fondés sur leur SHA-256.
4. Les fichiers, rapports et `PROVENANCE.json` sont publiés en premier.
5. `manifest.json` est remplacé dans un second commit.

Si une phase échoue, l'ancien manifest public demeure utilisable. Une fois la promotion
terminée, les bundles hachés qui ne sont plus référencés par les manifests, le
last-known-good ou la provenance sont élagués. Ils restent récupérables dans l'historique
Git.

## Exclusion torrent/P2P

L'exclusion est appliquée à quatre endroits :

1. ID et métadonnées du manifest ;
2. marqueurs forts dans le code téléchargé ;
3. protocoles et champs des objets retournés ;
4. validation finale du manifest, y compris suppression des anciennes entrées héritées.

## Limites connues

- Une IP GitHub peut être bloquée alors qu'une connexion résidentielle fonctionne.
- Node.js n'est pas identique à tous les moteurs Nuvio et appareils TV.
- Un échantillon limité ne prouve pas que chaque titre ou épisode fonctionne.
- Une validation technique ne détermine pas le statut juridique d'une source tierce.
- Les métadonnées de qualité peuvent être absentes ou inexactes.
- L'analyse ne télécharge pas un média complet et ne vérifie pas visuellement son contenu.
- Un succès à un instant donné ne garantit pas la disponibilité future.

## Global provider-request diagnostics

The worker records requests made by provider code itself. It does not probe selected provider homepages separately and does not assign provider-specific blocking rules.

When a provider depends on TMDb only to obtain title metadata, a failed or rejected TMDb lookup can be replaced with a synthetic response derived from the active fixture. This fallback is restricted to the matching TMDb media type and identifier, is marked with `synthetic_fixture_fallback: true`, and exists only to let the provider continue to its real search/content routes. It does not create or validate a stream.
