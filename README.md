<div align="center">
  <img src="assets/branding/nuvio-providers-logo.png" alt="Niakvio" width="280">

# Niakvio

**Moteur communautaire de collecte, réparation, validation et publication de providers Nuvio, validé sur Nuvio Mobile, Nuvio Desktop et NuvioTV.**

[![Node](https://img.shields.io/badge/Node.js-%E2%89%A524-339933?style=for-the-badge&logo=node.js&logoColor=white)](package.json)
[![Licence](https://img.shields.io/badge/licence-GPL--3.0-blue?style=for-the-badge)](LICENSE)
[![Runtimes](https://img.shields.io/badge/Nuvio-Mobile%20%7C%20Desktop%20%7C%20TV-7c3aed?style=for-the-badge)](#validation-native)

</div>

---

## Manifests

**Général — recommandé**

```text
https://raw.githubusercontent.com/niakw/Niakvio/refs/heads/main/manifest.json
```

**Francophone — VF / VOSTFR**

```text
https://raw.githubusercontent.com/niakw/Niakvio/refs/heads/main/vf/manifest.json
```

Les URL restent stables. Les bundles, versions, hashes, domaines, règles de compatibilité et états d'activation évoluent derrière ces manifests.

**Niakvio ne stocke aucune vidéo.** Le dépôt publie des manifests, métadonnées, règles de validation, correctifs et bundles de providers consommés côté client.

---

## Architecture après refonte

Niakvio n'est plus une collection de providers corrigés au cas par cas. Le cœur du projet est un **moteur partagé**. Les Labs détectent les défaillances réelles ; les corrections génériques sont ensuite intégrées au moteur commun, testées contre les providers et enfin vérifiées sur les runtimes clients.

La référence détaillée de cette architecture et du moteur provider-agnostic est documentée dans [`ARCHITECTURE.md`](ARCHITECTURE.md).

```text
Sources / upstreams
       │
       ▼
Discovery + sélection
       │
       ▼
DNS / hubs / domaines / LKG
       │
       ▼
┌─────────────────────────────┐
│     MOTEUR PARTAGÉ NIAKVIO  │
│                             │
│ Repair API/site             │
│ Recovery catalogue/player   │
│ Capture iframe/XHR/JSON     │
│ Normalisation streams       │
│ Langue / headers / metadata │
│ Validation média + identité │
└──────────────┬──────────────┘
               │
       ┌───────┼────────┐
       ▼       ▼        ▼
    Mobile  Desktop  NuvioTV
    QuickJS  JVM/QJS Android TV
       └───────┼────────┘
               ▼
      Gates de publication
               │
      ┌────────┴────────┐
      ▼                 ▼
manifest.json      vf/manifest.json
```

### Principe directeur

Une correction propre à une plateforme n'existe que si son contrat runtime l'impose réellement. Dès qu'un défaut appartient à une famille commune — domaine, API, recherche, iframe, HLS, metadata, identité, durée, headers, redirection ou payload — la correction doit améliorer **le moteur partagé** plutôt que créer une rustine Desktop, Mobile ou TV.

Les plateformes servent ensuite de preuves indépendantes de non-régression.

---

## Pipeline

### 1. Discovery et provenance

Plusieurs variantes d'un provider peuvent être collectées. Niakvio conserve leur provenance, choisit la meilleure base exploitable et empêche les variantes obsolètes ou non référencées de s'accumuler indéfiniment.

### 2. Domaine et disponibilité

Le moteur distingue un domaine terminal d'un hub, d'une redirection ou d'une ancienne adresse. Les peers historiques connus comme sains peuvent être retestés lorsqu'une route courante casse. Une adresse n'est jamais promue uniquement parce qu'elle répond en HTTP : identité et rôle doivent rester cohérents avec le provider.

### 3. Réparation et récupération génériques

Lorsque le provider natif ne suffit plus, la récupération peut poursuivre de façon bornée :

```text
provider natif
  → route API / recherche catalogue
  → fiche de l'œuvre
  → iframe / lecteur
  → JS / XHR / JSON
  → manifest / média final
```

Les correctifs partagés sont versionnés et doivent être idempotents : les réappliquer ne doit pas empiler des wrappers ou modifier sans fin le même bundle.

### 4. Validation média

Une URL ressemblant à un média ne suffit pas. Le moteur sait notamment confirmer ou rejeter :

- HLS réel (`#EXTM3U`) ;
- DASH MPD ;
- conteneurs vidéo reconnus ;
- pages HTML/JSON déguisées ;
- assets et démos ;
- previews anormalement courtes ;
- redirections ou payloads incohérents.

### 5. Validation d'identité

Un flux lisible correspondant à la mauvaise œuvre est **dangereux**, pas réussi. La validation peut croiser titre, alias, année, saison/épisode, metadata du média et durée attendue/mesurée.

`Unknown` / `Inconnue` dans la qualité affichée par Nuvio ne signifie pas que l'identité est inconnue et ne doit jamais suffire à rejeter un flux valide.

### 6. Langue

VF/VOSTFR n'est pas déduite d'un seul indice. Le moteur peut combiner metadata provider, domaine, catalogue, player, pistes audio/sous-titres et preuves observées. La projection francophone reste synchronisée avec le manifest général.

### 7. Publication

La publication est fail-closed : manifests, bundles, versions, provenance et empreintes doivent rester cohérents. Une génération invalide ne doit pas écraser silencieusement un dernier état connu comme sain.

---

## Validation native

Les dépôts clients officiels de référence et leurs commits épinglés sont suivis via [`automation/nuvio-client-upstreams.json`](automation/nuvio-client-upstreams.json).

| Client | Dépôt officiel | Validation |
|---|---|---|
| Nuvio Mobile | [`NuvioMedia/NuvioMobile`](https://github.com/NuvioMedia/NuvioMobile) | runtime officiel sur AVD téléphone |
| Nuvio Desktop | [`NuvioMedia/NuvioDesktop`](https://github.com/NuvioMedia/NuvioDesktop) | runtime/tests Desktop officiels |
| NuvioTV | [`NuvioMedia/NuvioTV`](https://github.com/NuvioMedia/NuvioTV) | runtime officiel sur AVD Android TV |

[`final-native-client-validation-v2.yml`](.github/workflows/final-native-client-validation-v2.yml) sépare volontairement les trois preuves. Une réussite Desktop ne vaut pas preuve TV et un émulateur téléphone ne sert pas de faux substitut Android TV.

Pour le sentinel StreamZo, la validation permanente exige un résultat réel, `count > 0`, un flux `type=hls` et une résolution média effective. StreamZo est ici un provider sentinel de régression, pas une technologie constitutive de Niakvio.

---

## Sources upstream des providers

Niakvio agrège, compare, répare et republie des providers issus de plusieurs projets communautaires. Les trois dépôts amont principaux utilisés pour constituer les listes de providers restent explicitement référencés :

- [`Gowaru/gowaru-nuvio-providers`](https://github.com/Gowaru/gowaru-nuvio-providers) — providers notamment francophones ;
- [`yoruix/nuvio-providers`](https://github.com/yoruix/nuvio-providers) — providers, structure source et documentation développeur ;
- [`NuvioPlugin/All-in-One-Nuvio`](https://github.com/NuvioPlugin/All-in-One-Nuvio) — collection internationale de providers.

Les auteurs, licences et responsabilités des projets amont restent détaillés dans [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). La provenance effective de chaque bundle publié est suivie dans [`PROVENANCE.json`](PROVENANCE.json).

---

## Labs permanents

Les Labs sont **conservés volontairement**. Ils sont des bancs de reproduction, pas des branches jetables :

- `lab/desktop-mobile-real`
- `lab/tv-real`

Les workflows permanents de Labs couvrent les clients réels, la matrice multi-œuvres, le corpus natif et la largeur de catalogue. [`permanent-lab-branch-guard.yml`](.github/workflows/permanent-lab-branch-guard.yml) protège cette organisation.

### Cible 10 / 3

Pour chaque œuvre, l'objectif est **10 providers jouables dont au moins 3 VF**. C'est une cible, pas un verrou : une œuvre récente ou rare peut rester sous 10.

La souplesse concerne uniquement la quantité. Ne comptent jamais comme succès : mauvaise œuvre, mauvais épisode, durée contradictoire, média illisible, faux HLS ou identité clairement incohérente.

---

## Workflows durables

`main` doit conserver un nombre réduit de workflows ayant chacun un rôle explicite :

| Workflow | Rôle |
|---|---|
| `sync.yml` | validation globale et publication |
| `availability.yml` | disponibilité des providers publiés |
| `domain-refresh.yml` | actualisation contrôlée des domaines |
| `engine-regression-offline.yml` | régressions du moteur hors réseau |
| `provider-rebuild-offline.yml` | reconstruction provider hors réseau |
| `finalize-safe-generation.yml` | finalisation d'une génération validée |
| `final-native-client-validation-v2.yml` | preuve native Desktop / Mobile / TV |
| `validate-desktop-runtime-compat.yml` | compatibilité Desktop |
| `nuvio-client-lab.yml` | matrice multi-œuvres / transport |
| `native-corpus-device-lab.yml` | corpus natif sur devices |
| `provider-catalogue-breadth-lab.yml` | largeur de catalogue |
| `permanent-real-client-labs.yml` | reproductions clients réels |
| `permanent-android-real-client.yml` | banc Android isolé |
| `permanent-lab-branch-guard.yml` | protection des Labs |

Les workflows `tmp-*`, `one-shot-*` et wrappers superseded doivent disparaître après leur migration.

---

## Structure du dépôt

```text
Niakvio/
├── manifest.json
├── vf/manifest.json
├── providers/                    # bundles publiés/référencés
├── scripts/                      # moteur, repair, probes, publication
│   └── provider_patches/         # correctifs partagés/versionnés
├── automation/                   # politiques, provenance, upstreams
├── tests/                        # non-régressions
├── .github/
│   ├── workflows/                # CI durable + Labs permanents
│   └── triggers/                 # déclencheurs contrôlés
├── FILE-HASHES.json
├── SHA256SUMS.json
├── PATCH-SHA256SUMS.txt
└── PROVENANCE.json
```

---

## Tests locaux

Prérequis : Node.js 24+ et Python 3.

```bash
npm install
npm test
```

Diagnostics :

```bash
npm run diagnostics
```

Le `pretest` reconstruit les profils runtime et vérifie les corpus critiques. Le `posttest` revalide l'intégrité de release. Les tests locaux ne remplacent pas les preuves natives Desktop, Mobile et TV lorsqu'un chemin média est modifié.

---

## Politique de branches

- **`main`** : état stable, publiable et propre.
- **`lab/*`** : environnements expérimentaux permanents ; ils ne sont pas supprimés lors des nettoyages ordinaires.
- **`fix/*`, `ci/*`, `proof/*`, `tmp/*`, `chore/*`** : branches de travail supprimables après intégration ou abandon vérifié.

Avant toute suppression d'une branche de travail, son avance par rapport à `main` doit être contrôlée. Une branche avec du contenu unique n'est jamais supprimée uniquement parce qu'elle est ancienne.

---

## Sécurité, indépendance et responsabilité

Le moteur applique des limites d'exécution, des workers bornés, des contrôles SSRF et une validation fail-closed des sorties. Aucun secret, token, URL signée complète ou header sensible ne doit être publié dans les artefacts CI.

Niakvio est un projet communautaire indépendant, non affilié aux développeurs de Nuvio ni aux services tiers. Le projet ne contrôle pas la disponibilité, le contenu, les droits ou les pratiques des sites tiers. L'utilisation doit respecter la législation applicable et les conditions des services concernés.

Voir [`DISCLAIMER.md`](DISCLAIMER.md), [`LICENSE`](LICENSE), [`NOTICE`](NOTICE), [`CONTRIBUTING.md`](CONTRIBUTING.md) et [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

---

## Boucle de maintenance

Quand un Lab révèle un bug :

1. reproduire et conserver une preuve minimale ;
2. identifier la famille de cause ;
3. corriger le moteur partagé si la cause est générique ;
4. ajouter un test de non-régression ;
5. rejouer les runtimes concernés — Desktop, Mobile et TV pour un chemin média partagé ;
6. publier seulement après cohérence des manifests, bundles, hashes et provenance ;
7. supprimer les branches/workflows temporaires devenus inutiles — **jamais les Labs permanents**.

Cette boucle est la référence de maintenance de Niakvio.
