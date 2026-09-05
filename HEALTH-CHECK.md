# Santé, preuve et décision — ARCHI 2

Ce document décrit les contrôles qui alimentent **Provider Engine V2 / ARCHI 2**. Ils ne forment pas une architecture parallèle : la décision finale reste portée par le catalogue canonique, l'Evidence Matrix, le Repair Brain et l'unique pipeline `sync.yml`.

## Principe

La santé d'un provider n'est jamais réduite à un code HTTP, à un score global ou à `no_streams`.

La chaîne de preuve distingue notamment :

| Famille | Preuves / observations |
|---|---|
| Discovery | manifest lisible, ID canonique, provenance, JS exploitable, SHA-256, exclusion P2P |
| Domaine | hub, terminal, redirect, peer historique, DNS, cohérence d'identité |
| Runtime | chargement, contrat `getStreams`, timeout, mémoire, exception |
| Catalogue | recherche, type movie/tv/anime, titre, saison, épisode |
| Player | detail, iframe/embed, JS/XHR/JSON, contexte Referer/Origin/cookies |
| Média | HLS, DASH, conteneur, playlist/segment, payload réel |
| Identité | titre/alias, année, saison/épisode, fichier média, durée |
| Langue | metadata, catalogue, pistes audio/sous-titres, indices cohérents |
| Compatibilité | TV Android, Mobile Android, Mobile iOS, Desktop macOS et Desktop Windows prouvés séparément |
| Stabilité | preuve courante, LKG, failures répétées, récupération |
| Publication | catalogue, manifests, provenance, versions, hashes, intégrité |

Une validation par corpus reste un échantillonnage : elle ne prétend pas prouver chaque titre, épisode, langue ou appareil.

## Quick

Quick est un **gate de vérification non-mutant côté providers**.

Il valide notamment les bytes Provider v3 exacts, les contrats Core critiques, les cinq Labs déclarés et l'intégrité structurelle. Il ne lance ni discovery de réparation, ni repair, ni reconstruction, ni publication de nouveau code provider.

Une simple migration de domaine n'appartient pas à Quick : elle est gérée par `domain-refresh.yml` dans son périmètre CONFIG-only.

## Deep

Deep ajoute une observation plus large :

- contrats structurels complets ;
- hubs/domaines observés en lecture seule ;
- health réseau des Provider JS publiés exacts ;
- diagnostics ;
- re-projection manifests ;
- hashes et release integrity.

Deep ne répare pas et ne reconstruit pas les providers. Sur `main`, seules les sorties de rapport/projection/hashes explicitement allowlistées peuvent être publiées.

Le repair appartient au Learning sandbox et aux propositions reviewables ; un run Deep n'est jamais un repair déguisé.

## Classification

`no_streams` est un symptôme. Les familles de cause V2 incluent notamment :

- `not_invoked` ;
- `dns_unreachable` ;
- `transport_blocked` ;
- `search_gap` ;
- `identity_mismatch` ;
- `detail_gap` ;
- `episode_gap` ;
- `player_gap` ;
- `media_extraction_gap` ;
- `playback_context_gap` ;
- `media_validation_gap` ;
- `runtime_contract_drift` ;
- `healthy`.

Le Repair Brain sélectionne ensuite une stratégie ciblée et bornée. Une disparition de 404 sans amélioration réelle du résultat ne suffit pas à accepter une réparation.

## Validation média

Une URL n'est pas un stream prouvé.

Le système peut confirmer :

- HLS réel (`#EXTM3U`) ;
- DASH/MPD ;
- signature de conteneur ;
- playlist et/ou premier segment ;
- redirects cohérents ;
- contexte de lecture requis.

Il rejette notamment :

- HTML/JSON déguisé ;
- player non résolu ;
- asset, publicité ou démo ;
- preview anormalement courte ;
- média illisible ;
- payload ou redirect incohérent.

## Identité

Un média lisible correspondant à la mauvaise œuvre est un **échec bloquant**.

Les contrôles peuvent croiser :

- titre/alias ;
- année ;
- movie/tv/anime ;
- saison/épisode ;
- metadata catalogue/player ;
- nom ou chemin du média ;
- durée attendue/mesurée.

Lorsque l'identité ne peut pas être suffisamment prouvée sans contradiction, le résultat reste inconclusif ; il n'est pas transformé artificiellement en succès.

`Unknown` / `Inconnue` dans un label de qualité Nuvio n'est pas une preuve d'identité inconnue et ne provoque jamais un rejet à lui seul.

## Langue

VF/VOSTFR/VO peut être établie à partir de plusieurs signaux cohérents : metadata provider, domaine, catalogue, player, pistes audio et sous-titres.

Une seule heuristique faible ne doit pas inventer une langue.

## LKG, réparation et quarantine

Les états sont volontairement séparés :

- **healthy/proven** : promotion possible ;
- **repairable/inconclusive** : réparation ou conservation du LKG ;
- **quarantine** : identité contradictoire, provenance suspecte, domaine détourné, sortie dangereuse ou autre preuve forte.

Un zéro résultat isolé n'est pas une raison suffisante pour quarantiner ou supprimer un provider.

La règle est **repair before triage**.

## Evidence Matrix

Une preuve est scoped :

```text
provider × œuvre × type × langue × device × version du contrat client
```

Un provider sain sur un film Desktop peut rester non prouvé sur une série TV ou sur Android TV.

Les preuves Mobile, Desktop et TV sont indépendantes.

## Corpus et largeur

Movie, série et anime sont des dimensions obligatoires. Breaking Bad S01E01 reste une fixture TV de régression.

La cible de largeur est **10 providers jouables par œuvre, dont au moins 3 VF**.

Elle est non bloquante lorsqu'un catalogue ne permet objectivement pas de l'atteindre. En revanche, ne comptent jamais :

- mauvais contenu ;
- mauvais épisode ;
- durée contradictoire ;
- faux HLS ;
- média illisible ;
- preuve runtime attribuée à un autre provider.

## Publication atomique

La production n'utilise plus deux publications concurrentes.

`sync.yml` construit une transaction validée qui comprend :

1. staging + preuves ;
2. promotion candidate ;
3. import dans `provider_catalog.json` ;
4. rendu de `manifest.json` et `vf/manifest.json` ;
5. audit contenu/média ;
6. provenance/LKG/versions ;
7. hashes et intégrité ;
8. **un commit atomique** de la génération acceptée ;
9. vérification du `main` exact publié.

Une étape en échec bloque la nouvelle transaction et laisse le dernier état sain dans l'historique/publication.

## P2P

Torrent, magnet, Acestream et autres chemins P2P interdits sont filtrés à plusieurs niveaux : metadata/ID, code source, protocoles retournés et validation finale.

## Limites

- Une IP GitHub peut être bloquée alors qu'une IP résidentielle fonctionne.
- Un échantillon ne représente pas l'intégralité d'un catalogue.
- Une preuve technique ne détermine pas le statut juridique d'une source tierce.
- Certaines metadata de qualité/langue peuvent être absentes.
- Un succès à un instant donné ne garantit pas la disponibilité future.

Ces limites produisent de l'**inconclusif**, pas des conclusions arbitraires.

### Résultat DNS NiakVIO

Le résultat DNS visible est volontairement limité à trois états :

- `DNS OK` : SFR, Orange et Free ont été testés et aucun blocage n'a été observé.
- `DNS BLOCK` : au moins un des FAI français testés présente un signal de blocage. C'est l'alerte DNS visible, même si un autre FAI reste accessible.
- `DNS API LIMIT REACH` : la limite de l'API de mesure a été atteinte ; ce n'est jamais interprété comme une panne du provider.

S'il n'existe aucun domaine à tester ou si aucune mesure exploitable n'a pu être produite pour une raison autre qu'une limite API, aucun faux `DNS OK` n'est inventé : le résultat visible reste non applicable.

Les preuves détaillées (FAI, résolveur, HTTP, migration, état interne) restent conservées dans le rapport pour le moteur et le debug, mais ne remplacent pas ces trois statuts dans l'affichage NiakVIO. Un `DNS BLOCK` est une alerte uniquement. Le préflight DNS ne bloque jamais l'exécution runtime, même si le domaine semble bloqué chez un FAI ou globalement injoignable : Health/Quick/Deep/Labs continuent afin de conserver la chaîne de diagnostic complète (DNS, domaine, HTTP, runtime, erreurs et flux).


## Learning quotidien

Le contrôle santé de publication et le Learning sont séparés. Le Learning quotidien observe le catalogue complet, y compris les providers désactivés, puis traite une file adaptative persistante via `scripts/run_brain_learning_queue.py` avec un budget global de 60 minutes (5 minutes réservées à la finalisation). Un provider non terminé ou encore problématique est conservé pour un cycle ultérieur ; un résultat Learning ne contourne jamais les gates d'activation/publication.
