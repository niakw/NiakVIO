# NiakVIO Provider Engine V2 — ARCHI 2

`engine_v2/` est le **plan de contrôle canonique** de NiakVIO. Il ne s'agit plus d'une refonte isolée : le catalogue provider, les contrats, les décisions de réparation, les preuves et les projections de manifests sont les invariants de la production.

Les scripts historiques encore appelés depuis `scripts/` sont des **primitives d'exécution de compatibilité** derrière ce plan de contrôle. Ils ne constituent plus une seconde architecture et ne doivent pas recréer leur propre source de vérité, leur propre cadence de publication ou leur propre politique d'activation.

## Source de vérité

`provider_catalog.json` est le registre canonique publié. Il contient une seule définition de chaque provider et ses projections :

- manifest général ;
- projection VF/VOSTFR ;
- ordre de publication ;
- politiques quick/deep et LKG.

`manifest.json` et `vf/manifest.json` sont rendus depuis ce catalogue. Pendant la migration des anciennes primitives de promotion, leur `manifest.next.json` est traité comme **transaction candidate** : il est importé dans le catalogue puis les manifests sont immédiatement régénérés depuis le catalogue avant toute publication.

Ce pont est volontairement borné et testable ; il n'autorise pas deux états de production concurrents.

## Flux de production

```text
3 upstreams + bundles publiés/LKG
          │
          ▼
Discovery multi-variantes
          │
          ▼
Hubs / DNS / domaines / peers historiques
          │
          ▼
provider_catalog.json ───────────────┐
          │                          │
          ▼                          │
ProviderSpec + connaissance          │
          │                          │
          ▼                          │
Resolver Core V2                     │
search → detail → episode → player → media
          │
          ▼
Evidence Matrix
          │
          ▼
Repair Brain V2
          │
          ▼
validation média + identité + langue + contexte
          │
          ▼
Mobile / Desktop / TV adapters
          │
          ▼
transaction validée → catalogue ─────┘
          │
          ├── manifest.json
          └── vf/manifest.json
```

## Quick et Deep

Il n'existe qu'un orchestrateur de production durable : `.github/workflows/sync.yml`.

### Quick

Le quick est une vraie maintenance, pas un rapport passif :

1. résout hubs/domaines ;
2. collecte toutes les variantes ;
3. protège le catalogue publié et ses LKG ;
4. choisit d'abord un sibling déjà sain ;
5. tente une réparation structurelle bornée uniquement pour les familles non résolues ;
6. conserve un LKG lorsqu'une observation reste inconclusive ;
7. peut publier une amélioration prouvée sans attendre un deep.

Un provider nouveau découvert en quick n'est pas activé aveuglément.

### Deep

Le deep reconstruit la connaissance plus largement, autorise davantage de profondeur de preuve et reste l'autorité pour :

- apprentissage/persistance des profils de réparation ;
- validation stricte de l'identité de contenu ;
- corpus plus large ;
- nouvelles intégrations provider ;
- modifications structurelles importantes.

Le deep n'est **pas** relancé automatiquement à chaque petite mise à jour. Les exécutions planifiées et le trigger explicite `.github/triggers/deep-provider-repair` assurent cette séparation.

## Contrat runtime canonique

Le moteur raisonne sur une requête interne unique :

```js
{
  tmdbId,
  mediaType: "movie" | "tv" | "anime",
  title,
  year,
  season,
  episode,
  languages,
  device,
  settings
}
```

Les adapters traduisent ensuite ce contrat vers Mobile, Desktop et NuvioTV. Une divergence spécifique à une plateforme n'est admise que si le client impose réellement un contrat différent.

## Chaîne de récupération

L'upstream JavaScript est une stratégie initiale, pas une autorité finale. Une récupération peut progresser de façon bornée :

```text
provider natif
  → API / recherche / catalogue
  → fiche exacte
  → iframe / player / embed
  → JavaScript / XHR / JSON
  → playlist / média final
```

À chaque étape, l'origine, les redirects, headers, cookies, `Referer`, `Origin` et `User-Agent` nécessaires peuvent être conservés dans un contexte scoped. Les budgets de pages, embeds, hosts, fetches et temps empêchent l'exploration infinie.

## Repair Brain V2

Les familles de panne incluent notamment :

- `not_invoked`
- `dns_unreachable`
- `transport_blocked`
- `search_gap`
- `identity_mismatch`
- `detail_gap`
- `episode_gap`
- `player_gap`
- `media_extraction_gap`
- `playback_context_gap`
- `media_validation_gap`
- `runtime_contract_drift`
- `healthy`

`no_streams` est une observation, jamais une cause racine suffisante.

Le Repair Brain est déterministe : classification → stratégie ciblée → probe → validation → recette versionnée. Une réparation n'est conservée que si elle améliore le résultat sans introduire de contradiction de contenu, de durée ou de runtime.

## Validation

Une URL n'est pas une preuve de stream. Les gates peuvent vérifier :

- HLS réel (`#EXTM3U`) ;
- DASH/MPD ;
- signature de conteneur vidéo ;
- première playlist/segment ;
- rejet HTML/JSON déguisé ;
- previews et médias anormalement courts ;
- titre/alias/année ;
- saison/épisode ;
- durée attendue ou mesurée ;
- langue et pistes lorsque disponibles ;
- provenance et isolation entre providers.

Un média lisible correspondant à la mauvaise œuvre est un échec bloquant. `Unknown`/`Inconnue` dans un label de qualité Nuvio n'est pas une preuve d'identité inconnue.

## LKG, quarantine et activation

Un échec temporaire ou un catalogue vide ne doit pas effacer une preuve saine déjà publiée.

- **LKG** : conserve le dernier bundle prouvé lorsqu'une nouvelle observation est inconclusive.
- **Repairable/disabled** : état normal d'un provider cassé mais non dangereux.
- **Quarantine** : réservée aux preuves fortes de contenu incohérent, provenance suspecte, domaine détourné, sortie dangereuse ou autre violation de sécurité.

La logique est donc **repair before triage**.

## Evidence Matrix

La preuve est suivie par provider × œuvre × type de média × langue × device × version de contrat client. Une réussite sur un film Desktop ne transforme pas automatiquement le provider en réussite globale.

Movie, TV/series et anime sont des dimensions de corpus de premier rang ; Breaking Bad S01E01 reste une fixture TV obligatoire.

## Tests et preuves natives

`provider-engine-v2.yml` couvre les contrats, adapters, validation média, resolver, Repair Brain, recipes, décisions, evidence, ingestion, analyse JS, domaine, ProviderSpecs et catalogue.

Les preuves clients finales restent séparées :

- Nuvio Mobile ;
- Nuvio Desktop ;
- NuvioTV / Android TV.

Une réussite d'un runtime ne vaut jamais preuve pour les deux autres.

## Règles non négociables

1. Un seul catalogue et un seul orchestrateur de production.
2. Les trois upstreams sont des sources de connaissance, jamais des bundles de confiance par défaut.
3. Discovery domaine/hub précède la reconstruction.
4. Réparer avant de désactiver ; quarantiner seulement sur preuve forte.
5. Préférer un sibling sain avant de modifier du code.
6. Toute exploration est bornée.
7. Toute promotion exige une amélioration prouvée.
8. Quick peut réparer/publier sans Deep ; Deep conserve son autorité d'apprentissage large.
9. Les manifests sont des projections du catalogue, pas une seconde source de vérité.
10. Mobile, Desktop et TV restent des preuves indépendantes.
