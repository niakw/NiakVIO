<div align="center">
  <img src="assets/branding/nuvio-providers-logo.png" alt="Niakvio" width="280">

# Niakvio

**Moteur communautaire de collecte, reconstruction, réparation, validation et publication de providers Nuvio, avec preuves séparées Mobile, Desktop et NuvioTV.**

[![Node](https://img.shields.io/badge/Node.js-%E2%89%A524-339933?style=for-the-badge&logo=node.js&logoColor=white)](package.json)
[![Licence](https://img.shields.io/badge/licence-GPL--3.0-blue?style=for-the-badge)](LICENSE)
[![Runtimes](https://img.shields.io/badge/Nuvio-Mobile%20%7C%20Desktop%20%7C%20TV-7c3aed?style=for-the-badge)](#compatibilit%C3%A9-nuvio)

</div>

---

## Installation

### Manifest général — recommandé

VF, VOSTFR, VO et autres langues :

```text
https://raw.githubusercontent.com/niakw/Niakvio/refs/heads/main/manifest.json
```

### Manifest francophone

Projection dédiée aux providers proposant du français ou du sous-titrage français :

```text
https://raw.githubusercontent.com/niakw/Niakvio/refs/heads/main/vf/manifest.json
```

Dans Nuvio :

1. copier l'URL du manifest souhaité ;
2. ouvrir la gestion des plugins/providers ;
3. ajouter/importer l'URL ;
4. actualiser le repository lorsque Niakvio publie une nouvelle version.

Les URL restent stables. Les bundles, versions, hashes, domaines, règles runtime et états d'activation évoluent derrière elles.

Lorsqu'un provider est réactivé après réparation, Niakvio peut réviser son identifiant client interne afin qu'un ancien état mis en cache ne maintienne pas artificiellement une désactivation devenue obsolète.

**Niakvio ne stocke aucune vidéo.** Le dépôt publie des manifests, métadonnées, règles, preuves et bundles de providers consommés côté client.

---

## ARCHI 2 : une seule source de vérité

Niakvio repose désormais sur un seul plan de contrôle : **Provider Engine V2 / ARCHI 2**.

`provider_catalog.json` est le registre canonique des providers publiés. Il porte une définition unique de chaque provider et ses projections. `manifest.json` et `vf/manifest.json` sont des sorties déterministes de ce catalogue, pas deux bases indépendantes.

```text
3 upstreams + dernier état sain
              │
              ▼
      Discovery multi-variantes
              │
              ▼
    hubs / DNS / domaines / LKG
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
       Repair Brain V2
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

La référence complète est [`ARCHITECTURE.md`](ARCHITECTURE.md). L'implémentation du plan de contrôle est documentée dans [`engine_v2/README.md`](engine_v2/README.md).

### Frontière de compatibilité

Certains providers publiés utilisent encore des primitives historiques de `scripts/` pour exécuter ou transformer leur bundle. Elles sont conservées uniquement lorsqu'elles apportent une fonction non encore remplacée — LKG, adaptation de route, génération de bundle, probes spécialisés, etc.

Elles sont **derrière ARCHI 2** : elles ne possèdent ni manifest autonome, ni second orchestrateur, ni politique d'activation concurrente. Une primitive devenue inutile est supprimée après preuve d'équivalence.

---

## Quick et Deep

Un seul workflow orchestre la production : [`.github/workflows/sync.yml`](.github/workflows/sync.yml).

### Quick — maintenance courante

Quick n'est plus un mode « rapport uniquement ». Il peut :

- actualiser hubs et domaines ;
- collecter toutes les variantes upstream ;
- conserver le bundle publié/LKG comme sibling de secours ;
- choisir la variante déjà saine avant de modifier du code ;
- lancer une réparation structurelle bornée sur les familles non résolues ;
- préserver un dernier état sain lorsque le nouveau signal est inconclusif ;
- publier immédiatement une amélioration réellement prouvée.

Il évite donc d'attendre un deep pour chaque changement de domaine ou réparation simple.

### Deep — reconstruction et preuve large

Deep est réservé aux travaux qui justifient un coût supérieur :

- nouvelles connaissances/variantes provider ;
- persistance de profils/recipes ;
- validation de corpus plus large ;
- intégration de nouveaux providers ;
- changements structurels importants ;
- contrôles stricts d'identité et de transport.

Il est planifié séparément et peut être déclenché explicitement avec `.github/triggers/deep-provider-repair`.

---

## Ce que le moteur sait faire

### Discovery et provenance

Niakvio collecte plusieurs variantes d'un même provider depuis les upstreams communautaires, conserve leur provenance, rejette P2P/torrent/magnet/Acestream et compare les siblings avant de réparer.

Les upstreams principaux sont :

- [`Gowaru/gowaru-nuvio-providers`](https://github.com/Gowaru/gowaru-nuvio-providers) ;
- [`yoruix/nuvio-providers`](https://github.com/yoruix/nuvio-providers) ;
- [`NuvioPlugin/All-in-One-Nuvio`](https://github.com/NuvioPlugin/All-in-One-Nuvio).

Les licences/provenances restent suivies dans [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) et [`PROVENANCE.json`](PROVENANCE.json).

### Hubs, DNS et domaines

Un domaine qui répond en HTTP n'est pas automatiquement valide. Le moteur distingue notamment :

- hub d'information ;
- domaine terminal ;
- redirection ;
- peer observé ;
- domaine historique encore cohérent ;
- route contaminée ou appartenant à un autre provider.

Les routes historiquement saines peuvent être retestées lorsqu'une adresse courante casse. Une migration n'est promue qu'après vérification d'identité et de rôle.

### Récupération structurelle

L'upstream JS est un point de départ, pas une autorité. Une récupération bornée peut poursuivre :

```text
provider natif
  → API / recherche / catalogue
  → fiche exacte de l'œuvre
  → iframe / lecteur / embed
  → JavaScript / XHR / JSON
  → playlist / média final
```

Les budgets limitent pages, embeds, hosts, fetches, taille de réponse et temps. Le contexte de lecture (`Referer`, `Origin`, `User-Agent`, cookies nécessaires) reste scoped à la chaîne qui l'a produit.

### Réparation déterministe

Le Repair Brain classe les causes au lieu de traiter `no_streams` comme un diagnostic final : DNS, transport, recherche, détail, épisode, player, extraction média, contexte playback, validation média, identité ou dérive du contrat Nuvio.

Une stratégie n'est conservée que si elle améliore réellement le résultat sans introduire de régression runtime ou de contradiction de contenu.

### LKG avant destruction

Une mise à jour upstream vide/cassée ne doit pas écraser silencieusement un provider publié sain.

Niakvio conserve :

- snapshots LKG des upstreams ;
- bundle publié comme sibling de dernier recours ;
- LKG provider vérifié ;
- provenance et catégories précédemment prouvées.

Un signal inconclusif conserve le LKG. La quarantine est réservée aux preuves fortes de problème de sécurité ou d'identité, pas à un simple zéro résultat.

### Validation média

Une URL ressemblant à une vidéo ne suffit pas. Le système sait confirmer/rejeter notamment :

- HLS réel (`#EXTM3U`) ;
- DASH/MPD ;
- signatures de conteneurs ;
- HTML/JSON déguisé ;
- publicité/assets/démos ;
- previews anormalement courtes ;
- redirections incohérentes ;
- playlist ou premier segment illisible.

### Identité de contenu

Un flux jouable correspondant à la mauvaise œuvre est un **échec bloquant**. Les preuves peuvent croiser :

- titre/alias ;
- année ;
- movie/tv/anime ;
- saison/épisode ;
- métadonnées catalogue/player ;
- nom du média ;
- durée attendue/mesurée.

`Unknown` / `Inconnue` dans un label de qualité Nuvio ne signifie pas que l'identité du contenu est inconnue.

### Langue

VF/VOSTFR n'est jamais inventée à partir d'un indice unique. Le moteur combine, lorsque disponibles, metadata provider, domaine, catalogue, player, pistes audio/sous-titres et observations de lecture.

---

## Compatibilité Nuvio

Les commits clients de référence sont épinglés dans [`automation/nuvio-client-upstreams.json`](automation/nuvio-client-upstreams.json).

| Client | Dépôt officiel | Famille de preuve |
|---|---|---|
| Nuvio Mobile | [`NuvioMedia/NuvioMobile`](https://github.com/NuvioMedia/NuvioMobile) | Android/iOS, contrat Mobile |
| Nuvio Desktop | [`NuvioMedia/NuvioDesktop`](https://github.com/NuvioMedia/NuvioDesktop) | Windows/macOS/Linux, runtime Desktop |
| NuvioTV | [`NuvioMedia/NuvioTV`](https://github.com/NuvioMedia/NuvioTV) | Android TV, environnement TV |

Le contrat interne ARCHI 2 est commun ; les adapters traduisent ce contrat vers chaque client. Une exception spécifique à une plateforme n'est admise que si le runtime l'impose réellement.

Une preuve Desktop ne vaut jamais preuve Mobile ou TV.

[`final-native-client-validation-v2.yml`](.github/workflows/final-native-client-validation-v2.yml) sépare les trois validations. Les Labs permanents permettent aussi de reproduire les comportements réels :

- `lab/desktop-mobile-real` ;
- `lab/tv-real`.

---

## Corpus et cible 10 / 3

Movie, série et anime sont des dimensions de test de premier rang. Breaking Bad S01E01 reste une régression TV obligatoire.

La cible de largeur est **10 providers jouables par œuvre, dont au moins 3 VF**. C'est un objectif de couverture, pas une excuse pour compter des résultats douteux : mauvaise œuvre, mauvaise saison/épisode, durée contradictoire, média illisible ou identité non prouvée ne comptent pas comme succès.

---

## Publication et intégrité

La publication est atomique et fail-closed. La transaction finale comprend :

- `provider_catalog.json` ;
- bundles providers ;
- `manifest.json` ;
- `vf/manifest.json` ;
- provenance ;
- états de domaine/LKG ;
- versions ;
- `FILE-HASHES.json` ;
- `SHA256SUMS.json` ;
- `PATCH-SHA256SUMS.txt`.

Le catalogue est revalidé avant publication, puis les manifests sont régénérés depuis lui. Une génération incohérente ne remplace pas silencieusement le dernier état publié.

---

## Workflows durables

Le dépôt vise un petit nombre de workflows ayant chacun un rôle unique :

| Workflow | Rôle |
|---|---|
| `sync.yml` | **seul pipeline de discovery → repair → publication quick/deep** |
| `provider-engine-v2.yml` | tests/observation du moteur ARCHI 2 |
| `availability.yml` | disponibilité des providers publiés |
| `domain-refresh.yml` | observations de domaines hors publication principale |
| `engine-regression-offline.yml` | régressions moteur hors réseau |
| `provider-rebuild-offline.yml` | reconstruction hors réseau |
| `finalize-safe-generation.yml` | finalisation contrôlée d'une génération |
| `final-native-client-validation-v2.yml` | preuves natives Mobile/Desktop/TV |
| `validate-desktop-runtime-compat.yml` | contrat Desktop |
| `nuvio-client-lab.yml` | matrice multi-œuvres / transport |
| `native-corpus-device-lab.yml` | corpus natif devices |
| `provider-catalogue-breadth-lab.yml` | largeur catalogue |
| `permanent-real-client-labs.yml` | reproductions réelles Desktop/Mobile |
| `permanent-android-real-client.yml` | banc Android isolé |
| `permanent-lab-branch-guard.yml` | protection des Labs |
| `provider-status-export.yml` | snapshot diagnostic après pipeline |

Les workflows `tmp-*`, one-shot, dispatchers de réparation et orchestrateurs superseded ne font pas partie de l'architecture finale.

---

## Structure

```text
Niakvio/
├── provider_catalog.json            # source de vérité publiée
├── manifest.json                    # projection générale
├── vf/manifest.json                 # projection francophone
├── engine_v2/                       # plan de contrôle ARCHI 2
│   ├── src/                         # contrats, resolver, repair, evidence, catalogue
│   ├── scripts/                     # ingestion, observation, génération
│   ├── config/                      # upstreams, adapters, evidence, classes
│   └── tests/                       # invariants V2
├── providers/                       # bundles publiés immuables/hashés
├── scripts/                         # primitives de compatibilité encore nécessaires
├── automation/                      # runtime/upstream/LKG/politiques
├── tests/                           # non-régressions publication/compatibilité
├── .github/workflows/               # production + preuves durables
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

Les tests locaux ne remplacent pas les preuves natives lorsqu'un chemin de playback partagé est modifié.

---

## Politique de branches

- `main` : état stable, publiable et propre ;
- `lab/desktop-mobile-real` et `lab/tv-real` : Labs permanents ;
- branches `fix/*`, `ci/*`, `proof/*`, `tmp/*`, `chore/*`, `refactor/*` : supprimées après intégration ou abandon **vérifié**.

Une branche n'est jamais supprimée avant comparaison avec `main`. Du contenu unique utile doit être intégré ou explicitement abandonné.

---

## Sécurité et responsabilité

Le moteur impose des workers/budgets bornés, des protections réseau/SSRF, des contrôles d'identité, des sorties fail-closed et une sanitisation des artefacts CI. Aucun secret, token, URL signée complète ou header sensible ne doit être publié dans les rapports.

Niakvio est un projet communautaire indépendant, non affilié aux développeurs de Nuvio ni aux services tiers. Le projet ne contrôle pas la disponibilité, le contenu, les droits ni les pratiques des sites tiers. L'utilisation doit respecter la législation applicable et les conditions des services concernés.

Voir [`DISCLAIMER.md`](DISCLAIMER.md), [`LICENSE`](LICENSE), [`NOTICE`](NOTICE), [`CONTRIBUTING.md`](CONTRIBUTING.md) et [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
