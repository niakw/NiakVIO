<div align="center">
  <img src="assets/branding/nuvio-providers-logo.png" alt="Logo NiakVIO" width="300">

  <h1>NiakVIO</h1>
  <p><strong>Le moteur communautaire qui agrège, teste, répare et maintient les providers Nuvio.</strong></p>
  <p>VO · VF · VOSTFR &nbsp;•&nbsp; Mobile · Desktop · TV</p>

[![Node](https://img.shields.io/badge/Node.js-%E2%89%A524-339933?style=for-the-badge&logo=node.js&logoColor=white)](package.json)
[![Licence](https://img.shields.io/badge/licence-GPL--3.0-blue?style=for-the-badge)](LICENSE)
[![Nuvio](https://img.shields.io/badge/Nuvio-Mobile%20%7C%20Desktop%20%7C%20TV-7c3aed?style=for-the-badge)](#compatibilit%C3%A9-nuvio)

</div>

---

## Ajouter NiakVIO à Nuvio

### Manifest général — recommandé

Tous les providers publiés : VF, VOSTFR, VO et autres langues.

```text
https://raw.githubusercontent.com/niakw/Niakvio/refs/heads/main/manifest.json
```

### Manifest francophone

Projection centrée sur les providers proposant du français ou du sous-titrage français.

```text
https://raw.githubusercontent.com/niakw/Niakvio/refs/heads/main/vf/manifest.json
```

Dans Nuvio, copiez l'URL du manifest souhaité dans la gestion des plugins/providers puis actualisez le repository lorsque nécessaire.

**Les URL restent stables.** NiakVIO peut faire évoluer derrière elles les bundles, versions, domaines, règles runtime, preuves et états d'activation.

> NiakVIO ne stocke ni n'héberge de vidéo. Le projet maintient des manifests, des métadonnées, des règles de compatibilité et des bundles de providers consommés côté client.

---

## Écosystème et sources

### Clients Nuvio officiels

- [Nuvio Mobile — `NuvioMedia/NuvioMobile`](https://github.com/NuvioMedia/NuvioMobile)
- [Nuvio Desktop — `NuvioMedia/NuvioDesktop`](https://github.com/NuvioMedia/NuvioDesktop)
- [NuvioTV — `NuvioMedia/NuvioTV`](https://github.com/NuvioMedia/NuvioTV)

### Repositories providers suivis

NiakVIO agrège et compare plusieurs upstreams au lieu de dépendre d'une seule copie d'un provider :

- [Gowaru — `Gowaru/gowaru-nuvio-providers`](https://github.com/Gowaru/gowaru-nuvio-providers)
- [Yoru — `yoruix/nuvio-providers`](https://github.com/yoruix/nuvio-providers)
- [All-in-One Nuvio — `NuvioPlugin/All-in-One-Nuvio`](https://github.com/NuvioPlugin/All-in-One-Nuvio)

La provenance et les licences tierces sont suivies dans [`PROVENANCE.json`](PROVENANCE.json) et [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

---

## Pourquoi NiakVIO ?

Un provider peut fonctionner aujourd'hui puis casser demain à cause d'un domaine déplacé, d'une API modifiée, d'un lecteur remplacé, d'un token devenu obsolète ou d'une différence entre Mobile, Desktop et TV.

NiakVIO ajoute une couche de maintenance entre les repositories providers et Nuvio :

- **un point d'installation unique** plutôt qu'une collection de manifests à gérer séparément ;
- **plusieurs variantes comparées** avant de modifier du code ;
- **réparation automatique bornée** lorsque la meilleure variante connue ne fonctionne plus ;
- **contrôle réel du média**, pas seulement de l'URL retournée ;
- **vérification de l'œuvre, de la saison et de l'épisode** pour éviter les faux positifs ;
- **attention particulière au français** sans inventer VF/VOSTFR à partir d'un simple nom de domaine ;
- **preuves séparées Mobile, Desktop et TV** ;
- **dernier état sain conservé** lorsqu'une nouvelle observation est seulement inconclusive ;
- **publication atomique et fail-closed** pour empêcher une génération partielle de remplacer silencieusement un état sain.

L'objectif n'est donc pas d'afficher le plus grand nombre possible de providers. L'objectif est de publier **le plus de providers réellement utiles possible, avec suffisamment de preuves pour savoir pourquoi ils fonctionnent — ou pourquoi ils ne fonctionnent plus.**

---

## Ce que NiakVIO maintient automatiquement

### Providers et variantes

Pour une même famille, NiakVIO peut disposer de plusieurs bundles issus des upstreams, d'un dernier état publié et d'un LKG. La sélection d'un sibling sain est tentée avant une réparation structurelle.

### Domaines et routes

Le moteur distingue notamment :

- hub d'information ;
- domaine terminal ;
- redirection ;
- API ;
- peer observé ;
- domaine historique encore cohérent ;
- route appartenant à un autre provider.

Une migration de domaine n'est pas promue simplement parce qu'un serveur répond en HTTP.

### Extraction média

Lorsque cela est nécessaire, la récupération peut suivre la chaîne réelle :

```text
provider
  → recherche / catalogue / API
  → fiche exacte de l'œuvre
  → saison / épisode
  → iframe / lecteur
  → JavaScript / XHR / JSON
  → playlist / média final
```

Les budgets de pages, embeds, hosts, fetches, taille de réponse et temps empêchent cette exploration de devenir une navigation sans limite.

### Lecture réelle

Une URL n'est pas considérée comme valide uniquement parce qu'elle se termine par `.m3u8` ou `.mp4`. Les contrôles peuvent confirmer ou rejeter :

- playlist HLS réelle (`#EXTM3U`) ;
- DASH/MPD ;
- signatures de conteneurs ;
- HTML ou JSON déguisé en média ;
- publicité, preview ou asset parasite ;
- redirection incohérente ;
- premier segment ou contenu inaccessible ;
- contexte `Referer` / `Origin` / headers nécessaire à la lecture.

### Identité du contenu

Un flux jouable correspondant à la mauvaise œuvre est un **échec**, pas un succès.

Les preuves peuvent combiner titre, alias, année, type, saison, épisode, metadata catalogue/player, nom du média et durée attendue/mesurée.

### Langues

VF/VOSTFR n'est jamais déduite d'un seul indice. Selon les informations disponibles, NiakVIO combine metadata provider, domaine, catalogue, player, pistes audio, sous-titres et observations de lecture.

---

## Compatibilité Nuvio

Les commits clients acceptés sont épinglés dans [`sources.json`](sources.json) et les validations natives utilisent les repositories officiels à ces révisions exactes.

| Client | Repository | Preuve native retenue |
|---|---|---|
| Nuvio Mobile | [`NuvioMedia/NuvioMobile`](https://github.com/NuvioMedia/NuvioMobile) | chemin Android officiel et stack de lecture du client |
| Nuvio Desktop | [`NuvioMedia/NuvioDesktop`](https://github.com/NuvioMedia/NuvioDesktop) | bridges/lecteurs natifs **macOS et Windows** ; le stub Linux n'est pas une preuve lecteur |
| NuvioTV | [`NuvioMedia/NuvioTV`](https://github.com/NuvioMedia/NuvioTV) | Android TV officiel avec Media3/ExoPlayer |

Le contrat logique ARCHI 2 est commun, mais **une preuve Desktop ne vaut jamais automatiquement preuve Mobile ou TV**.

Les labs natifs parcourent les lignes du manifest compatibles avec la plateforme, **y compris les providers `enabled:false`**, et lisent **chaque stream retourné** sur des routes représentatives film, série et anime. Les routes incompatibles sont comptabilisées comme skips explicites ; les probes `tv/anime` non déclarés restent des preuves de capacité et ne déclenchent pas de réparation provider sur un simple échec.

Les profils Nuvio, snapshots AVD, caches providers et caches Gradle sont conservés lorsque c'est sûr afin d'éviter de reconstruire inutilement l'environnement. Les retests ciblés par device restent disponibles manuellement.

---

# Architecture technique

## ARCHI 2 : une seule source de vérité

NiakVIO repose sur **Provider Engine V2 / ARCHI 2**.

[`provider_catalog.json`](provider_catalog.json) est le registre canonique de publication. `manifest.json` et `vf/manifest.json` sont des projections déterministes du même catalogue et non deux bases concurrentes.

```text
3 upstreams + état publié/LKG
              │
              ▼
      Discovery multi-variantes
              │
              ▼
      hubs / DNS / domaines
              │
              ▼
      provider_catalog.json
              │
              ▼
 ProviderSpec + Resolver Core V2
              │
              ▼
        Evidence Matrix
              │
              ▼
        Repair Brain v4
              │
              ▼
 média + identité + langue + contexte
              │
        ┌─────┼─────┐
        ▼     ▼     ▼
     Mobile Desktop TV
        └─────┼─────┘
              ▼
      publication fail-closed
        ┌─────┴─────┐
        ▼           ▼
 manifest.json   vf/manifest.json
```

La description complète se trouve dans [`ARCHITECTURE.md`](ARCHITECTURE.md) et l'implémentation du moteur dans [`engine_v2/README.md`](engine_v2/README.md).

### Frontière de compatibilité

Certaines primitives historiques de `scripts/` sont encore utilisées lorsqu'elles assurent une fonction qui n'a pas encore d'équivalent V2 : LKG, adaptation de routes, probes spécialisés, génération de bundle, etc.

Elles restent **derrière ARCHI 2** : aucun second manifest, orchestrateur ou système d'activation concurrent ne doit devenir une deuxième source de vérité.

---

## Quick et Deep

Le pipeline principal est [`.github/workflows/sync.yml`](.github/workflows/sync.yml).

### Quick — maintenance courante

Quick peut notamment :

- rafraîchir hubs et domaines ;
- découvrir les variantes upstream ;
- comparer les siblings ;
- conserver le bundle publié/LKG ;
- lancer une réparation bornée sur les familles non résolues ;
- publier une amélioration lorsqu'elle est effectivement prouvée.

Il évite d'attendre un Deep pour une simple migration de domaine ou une réparation déjà comprise.

### Deep — reconstruction et preuve large

Deep est réservé aux opérations plus coûteuses :

- nouvelles variantes et connaissances provider ;
- corpus plus large ;
- intégration d'un nouveau provider ;
- changement structurel du moteur ;
- reconstruction ou recherche de route plus profonde ;
- validation stricte d'identité, de qualité et de transport.

Un changement courant ne force donc pas automatiquement une reconstruction profonde de tout le système.

---

## Repair Brain et apprentissage

Le Repair Brain ne considère pas `no_streams` comme une cause. Il cherche à classer l'étape fautive : DNS, accès, recherche, fiche, épisode, player, extraction média, contexte playback, transport, identité ou contrat Nuvio.

Sa boucle de travail est :

```text
diagnostic
   ↓
hypothèse de réparation
   ↓
mutation en sandbox
   ↓
retest lecteur officiel
   ↓
acceptation ou mémoire d'échec
```

Une stratégie échouée peut être mémorisée pour éviter de répéter mécaniquement le même repair. Une stratégie réussie n'est réutilisable automatiquement qu'après les preuves prévues par la politique du moteur.

Le **Brain Learning Lab** est séparé de la publication : il travaille en sandbox, produit une mémoire sanitizée et n'a pas le droit de publier directement un provider ou un manifest. La mémoire de réparation lecteur conserve les résultats des retests officiels et les IDs de runs déjà importés afin d'éviter le double apprentissage d'une même preuve. L'import automatique est limité aux runs lecteurs issus de `main` ; une preuve de PR ne modifie pas silencieusement la mémoire persistante.

Un audit historique 5.20.63 sert de bootstrap de départ afin de confronter les nouvelles observations à un état antérieur riche. Les apprentissages futurs doivent ensuite être portés par les preuves du moteur, les corpus natifs et la mémoire d'expérience du Brain — pas par une liste humaine de providers à forcer.

---

## LKG et quarantaine

Une mise à jour upstream vide ou cassée ne doit pas écraser un provider publié sain.

NiakVIO peut conserver :

- snapshots LKG upstream ;
- bundle publié comme sibling ;
- état d'activation précédemment prouvé ;
- routes et domaines historiquement cohérents ;
- provenance et catégories validées.

Un signal inconclusif peut conserver le dernier état sain. La quarantaine est destinée aux contradictions fortes de sécurité ou d'identité, pas à un simple zéro résultat isolé.

---

## Corpus natif et couverture

Films, séries et anime sont des dimensions de test distinctes. La cible de largeur du projet est **10 providers jouables par œuvre, dont au moins 3 VF** lorsque le catalogue permet réellement de les obtenir.

Cette cible n'autorise aucun faux positif : mauvaise œuvre, mauvais épisode, durée incohérente ou média non lisible ne comptent pas.

Le dispositif comprend :

- un lab **NuvioTV Android TV** officiel sur des routes film/TV/anime, tous providers compatibles — actifs ou inactifs — et tous les streams retournés ;
- un lab **Nuvio Mobile Android** officiel avec le même contrat de traversal et de lecture ;
- un lab **Nuvio Desktop natif macOS/Windows**, Linux étant explicitement exclu comme preuve lecteur ;
- une preuve repository → provider → HTTP → stream → lecteur, plus des phases frontend capturées ;
- des retests ciblés par device disponibles **manuellement** sans relancer toute la matrice ;
- un sandbox Brain v4 qui peut matérialiser jusqu'à 24 mutations provider génériques justifiées, puis rejoue Sinners sur NuvioTV avec tous les providers et tous les streams avant comparaison ;
- une mémoire lecteur fail-closed : preuve incomplète = pas d'apprentissage et pas de plan de réparation.

---

## Publication, versions et intégrité

La publication est atomique et fail-closed. La transaction peut inclure :

- `provider_catalog.json` ;
- bundles providers ;
- `manifest.json` ;
- `vf/manifest.json` ;
- provenance ;
- états domaine/LKG ;
- versions ;
- `FILE-HASHES.json` ;
- `SHA256SUMS.json` ;
- `PATCH-SHA256SUMS.txt`.

Une génération incohérente ne remplace pas silencieusement le dernier état publié.

### Invalidation des caches Nuvio

Lorsqu'une transaction change réellement une donnée visible côté client :

- le patch provider peut être augmenté ;
- une réactivation peut faire tourner l'ID client case-only pour éviter un ancien état local désactivé ;
- la projection VF est resynchronisée depuis le catalogue ;
- la release globale est propagée aux manifests et métadonnées associées ;
- un rerun sans changement reste idempotent.

---

## Workflows principaux

| Workflow | Rôle |
|---|---|
| `sync.yml` | discovery → repair → validation → publication Quick/Deep |
| `canonical-media-types.yml` | contrats media, evidence native, cache et mémoire Brain |
| `github-actions-gate.yml` | sécurité et invariants des workflows |
| `native-android-route-reader.yml` | preuve native exhaustive NuvioTV + Mobile et retest Brain v4 |
| `native-desktop-reader-acceptance.yml` | preuve lecteur officielle Desktop macOS/Windows |
| `native-corpus-device-targeted.yml` | retests device à la demande uniquement |
| `native-reader-learning-sync.yml` | import idempotent des résultats lecteur validés de `main` |
| `brain-learning-lab.yml` | expérimentation et mémoire du Repair Brain en sandbox |
| `availability.yml` | disponibilité des providers publiés |
| `domain-refresh.yml` | observation des domaines |
| `engine-regression-offline.yml` | non-régressions moteur hors réseau |
| `provider-rebuild-offline.yml` | reconstruction hors réseau |
| `provider-catalogue-breadth-lab.yml` | largeur de catalogue |
| `provider-status-export.yml` | snapshot diagnostic |

Les anciens labs à refs clientes mutables, les preuves Desktop Linux, les workflows provider-spécifiques et les orchestrateurs superseded ne font pas partie de l'architecture cible.

---

## Structure du repository

```text
Niakvio/
├── provider_catalog.json            # source canonique de publication
├── manifest.json                    # projection générale
├── vf/manifest.json                 # projection francophone
├── engine_v2/                       # Provider Engine V2 / ARCHI 2
│   ├── src/                         # contrats, resolver, repair, evidence
│   ├── scripts/                     # ingestion, observation, apprentissage
│   ├── config/                      # politiques et adapters
│   └── tests/                       # invariants V2
├── providers/                       # bundles publiés hashés
├── scripts/                         # primitives runtime/compatibilité nécessaires
├── automation/                      # upstreams, LKG et états durables
├── tests/                           # non-régressions publication/compatibilité
├── .github/workflows/               # production, labs et preuves natives
├── PROVENANCE.json
├── FILE-HASHES.json
├── SHA256SUMS.json
└── PATCH-SHA256SUMS.txt
```

---

## Tests locaux

Prérequis : Node.js 24+ et Python 3.

```bash
npm install
npm test
node engine_v2/tests/provider-catalog.test.mjs
```

Diagnostics :

```bash
npm run diagnostics
```

Les tests locaux ne remplacent pas la validation native lorsqu'un changement touche le playback ou le contrat d'un client Nuvio.

---

## Politique de branches

- `main` : état stable et publiable ;
- `brain-learning/proposals` : mémoire sanitizée persistante du Brain ;
- `lab/desktop-mobile-real` et `lab/tv-real` : labs permanents, à ne pas nettoyer automatiquement ;
- les branches temporaires `fix/*`, `ci/*`, `proof/*`, `tmp/*`, `chore/*` et `refactor/*` doivent disparaître après intégration ou abandon vérifié.

Une branche n'est jamais supprimée avant comparaison avec `main`. Du contenu unique utile doit être intégré ou explicitement abandonné.

---

## Sécurité, responsabilité et indépendance

Le moteur applique des budgets de workers, des protections réseau/SSRF, des contrôles d'identité, une publication fail-closed et une sanitisation des artefacts CI. Les secrets, tokens, cookies, headers sensibles et URL signées ne doivent pas être persistés dans la mémoire d'apprentissage publique.

NiakVIO est un projet communautaire indépendant, non affilié aux développeurs de Nuvio ni aux services tiers référencés. Le projet ne contrôle pas la disponibilité, le contenu, les droits ou les pratiques de sites tiers. L'utilisation doit respecter la législation applicable et les conditions des services concernés.

Voir [`DISCLAIMER.md`](DISCLAIMER.md), [`LICENSE`](LICENSE), [`NOTICE`](NOTICE), [`SECURITY.md`](SECURITY.md), [`CONTRIBUTING.md`](CONTRIBUTING.md) et [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).