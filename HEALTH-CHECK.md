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
| Compatibilité | Mobile, Desktop et TV prouvés séparément |
| Stabilité | preuve courante, LKG, failures répétées, récupération |
| Publication | catalogue, manifests, provenance, versions, hashes, intégrité |

Une validation par corpus reste un échantillonnage : elle ne prétend pas prouver chaque titre, épisode, langue ou appareil.

## Quick

Quick est une **maintenance réparatrice et publiable**.

Il :

1. actualise hubs/domaines ;
2. redécouvre les variantes upstream ;
3. conserve les versions publiées/LKG comme siblings de secours ;
4. préfère un sibling déjà sain ;
5. répare de façon bornée les familles encore non résolues ;
6. valide les résultats ;
7. conserve le LKG si la nouvelle observation reste inconclusive ;
8. peut publier immédiatement une amélioration prouvée.

Quick ne crée donc pas un simple rapport passif et n'attend pas systématiquement un Deep.

Un provider totalement nouveau n'est pas activé aveuglément par Quick.

## Deep

Deep est la reconstruction/validation large. Il est utilisé notamment pour :

- nouveaux providers ;
- nouvelles variantes ou structures ;
- persistance/apprentissage de recipes ;
- corpus et profondeur de probe supérieurs ;
- modifications importantes du moteur ;
- preuve stricte d'identité et de playback.

Deep n'est pas exécuté à chaque mise à jour. Il dispose d'une cadence séparée et du trigger explicite `.github/triggers/deep-provider-repair`.

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
