<div align="center">
  <img src="assets/branding/nuvio-providers-logo.png" alt="Niakvio" width="280">

# Niakvio

**Écosystème communautaire pour Nuvio regroupant des providers VO, VF et VOSTFR, avec compatibilité Nuvio Mobile, Desktop et NuvioTV.**

[![Type](https://img.shields.io/badge/type-Nuvio%20providers-1f6feb?style=for-the-badge)](#installation)
[![Node](https://img.shields.io/badge/Node.js-%E2%89%A524-339933?style=for-the-badge&logo=node.js&logoColor=white)](package.json)
[![Licence](https://img.shields.io/badge/licence-GPL--3.0-blue?style=for-the-badge)](LICENSE)
[![Plateformes](https://img.shields.io/badge/Nuvio-Android%20%7C%20iOS%20%7C%20Desktop%20%7C%20NuvioTV-7c3aed?style=for-the-badge)](#compatibilit%C3%A9-nuvio)

</div>

---

## Manifests Niakvio

### Manifest providers général — recommandé

**VF + VOSTFR + VO + autres langues**

```text
https://raw.githubusercontent.com/niakw/Niakvio/refs/heads/main/manifest.json
```

[Ouvrir le manifest général](https://raw.githubusercontent.com/niakw/Niakvio/refs/heads/main/manifest.json)

### Manifest providers francophone

**Projection dédiée aux providers proposant du contenu français ou sous-titré français.**

```text
https://raw.githubusercontent.com/niakw/Niakvio/refs/heads/main/vf/manifest.json
```

[Ouvrir le manifest francophone](https://raw.githubusercontent.com/niakw/Niakvio/refs/heads/main/vf/manifest.json)

> Les URL des manifests providers restent stables. Les versions, bundles, états d’activation, domaines et règles de compatibilité évoluent derrière ces URL.


---

## Installation

### Providers Nuvio

1. Copiez l’URL du manifest souhaité.
2. Ouvrez le client Nuvio compatible.
3. Accédez à la gestion des plugins/providers.
4. Ajoutez ou importez l’URL.
5. Utilisez ensuite l’actualisation du repository pour récupérer les nouvelles versions.

Lorsqu’un provider est réactivé après une correction, Niakvio peut réviser son identifiant client interne afin d’éviter qu’un ancien état mis en cache conserve artificiellement le provider désactivé.


---

## Compatibilité Nuvio

Niakvio couvre plusieurs familles de runtime Nuvio et ne suppose pas qu’un provider fonctionnant dans l’une fonctionnera automatiquement dans toutes les autres.

### Dépôts clients de référence

La compatibilité n’est pas déduite d’un contrat théorique figé : Niakvio suit les dépôts clients Nuvio et audite les parties susceptibles de modifier l’exécution des providers ou la lecture des streams.

| Client | Dépôt de référence | Plateformes | Branche suivie |
|---|---|---|---|
| Nuvio Mobile | [NuvioMedia/NuvioMobile](https://github.com/NuvioMedia/NuvioMobile) | Android, iOS | `cmp-rewrite` |
| Nuvio Desktop | [NuvioMedia/NuvioDesktop](https://github.com/NuvioMedia/NuvioDesktop) | Windows, macOS, Linux | `Dev` |
| NuvioTV | [NuvioMedia/NuvioTV](https://github.com/NuvioMedia/NuvioTV) | Android TV | `dev` |

Les commits acceptés, chemins sensibles et règles de détection de dérive sont suivis dans [`automation/nuvio-client-upstreams.json`](automation/nuvio-client-upstreams.json). Un changement de contrat ou de sémantique provider peut bloquer la publication jusqu’à réaudit, au lieu d’être accepté silencieusement.

Niakvio ne reprend pas le code de ces clients et reste un projet communautaire indépendant ; ces dépôts servent de **références runtime** pour reproduire au mieux le comportement attendu côté Nuvio.

### Providers JavaScript

| Plateforme | Famille runtime contrôlée | Contrat / filtrage |
|---|---|---|
| Android | Nuvio Mobile / QuickJS | `android` + appel positionnel |
| iOS | Nuvio Mobile / QuickJS | `ios` + appel positionnel |
| Windows | Nuvio Desktop / QuickJS JVM | `desktop`, `jvm`, `windows` |
| macOS | Nuvio Desktop / QuickJS JVM | `desktop`, `jvm`, `macos` |
| Linux | Nuvio Desktop / QuickJS JVM | `desktop`, `jvm`, `linux` |
| Android TV / NuvioTV | Runtime provider NuvioTV | 4 arguments positionnels + `SCRAPER_SETTINGS` global |

Les clients Mobile/Desktop utilisent le contrat provider positionnel :

```text
getStreams(tmdbId, mediaType, season, episode)
```

NuvioTV est également testé sur un appel à quatre arguments positionnels, mais avec son environnement propre, notamment le contexte Android TV et le réglage global `SCRAPER_SETTINGS`. Il dispose donc d’un **probe et d’un garde-fou dédiés**, au lieu d’être artificiellement assimilé au runtime Mobile ou Desktop.

### Compatibilité média NuvioTV

> **Particularité NuvioTV :** le client actuel parse les champs `supportedPlatforms` et `disabledPlatforms`, mais son `PluginManager` ne les applique pas lors de la construction des scrapers actifs. Niakvio ne s’appuie donc pas sur ces champs pour sécuriser NuvioTV : un provider à risque doit résoudre ses lecteurs puis filtrer ses propres sorties pour ne conserver que des payloads média réellement vérifiés.

Le dépôt contient un chemin NuvioTV spécifique qui :

- simule l’environnement Android TV attendu ;
- appelle le provider avec les quatre arguments positionnels ;
- expose `SCRAPER_SETTINGS` et les globals attendus ;
- inspecte les URLs retournées ;
- rejette les assets, démos, pages HTML et faux médias ;
- ne considère comme preuve stricte qu’un véritable HLS `#EXTM3U`, un DASH MPD ou une signature réelle de conteneur vidéo ;
- peut appliquer un wrapper direct-media NuvioTV lorsqu’il améliore strictement le résultat sans régression ;
- conserve une provenance et un rapport de promotion pour les bundles NuvioTV publiés.

Les principaux fichiers de cette famille sont :

| Fichier | Rôle |
|---|---|
| [`automation/nuvio-tv-runtime-contract.json`](automation/nuvio-tv-runtime-contract.json) | Contrat durable NuvioTV |
| [`scripts/nuvio_tv_probe_v2.cjs`](scripts/nuvio_tv_probe_v2.cjs) | Probe runtime et média NuvioTV |
| [`scripts/provider_patches/nuvio_tv_direct_media_v2.py`](scripts/provider_patches/nuvio_tv_direct_media_v2.py) | Adaptation direct-media NuvioTV |
| [`scripts/promote_global_nuvio_tv_candidates.py`](scripts/promote_global_nuvio_tv_candidates.py) | Promotion uniquement après amélioration stricte |
| [`automation/nuvio-tv-global-promotion.json`](automation/nuvio-tv-global-promotion.json) | Dernier rapport de promotion strict enregistré |
| [`scripts/validate_nuvio_tv_runtime_policy.py`](scripts/validate_nuvio_tv_runtime_policy.py) | Validation permanente du contrat et des bundles publiés |


### Politique de compatibilité providers

Un provider n’est **pas** déclaré incompatible simplement parce qu’un titre de test retourne zéro résultat.

La décision distingue :

- **compatible direct** : un média directement lisible a été prouvé ;
- **inconclusif** : aucune preuve positive, mais aucune incompatibilité concluante non plus ; le provider reste disponible ;
- **incompatible concluante** : runtime cassé ou payload retourné de façon répétée mais non lisible comme média ; le provider peut alors être masqué sur la famille concernée.

Cette règle évite deux erreurs opposées : conserver des providers qui apparaissent mais ne peuvent pas être lus, ou désactiver des providers fonctionnels uniquement parce que les œuvres échantillonnées ne sont pas présentes dans leur catalogue.

> Les probes CI reproduisent les contrats runtime et vérifient les payloads réseau. Ils ne prétendent pas remplacer un test manuel sur chaque modèle physique de téléphone, ordinateur ou box Android TV.

### Lab de transport média multi-œuvres

Le workflow [`Nuvio client media transport lab`](.github/workflows/nuvio-client-lab.yml) exécute une matrice reproductible de films, séries et anime, dont une œuvre récente à faible couverture. Chaque provider sélectionné est exécuté avec les contrats NuvioTV, Desktop macOS et Mobile, puis les playlists et premiers segments sont vérifiés jusqu'au média final. Les contradictions de titre, saison, épisode, nom de fichier média ou durée sont rejetées.

Une durée connue est comparée au média réellement mesuré avec une tolérance configurée. Si la durée n’est pas disponible, le résultat reste `identity_unverified` au lieu d’être déclaré faux. De même, `Unknown` / `Inconnue` dans la qualité affichée par Nuvio ne signifie pas que l’identité de l’œuvre est inconnue et ne provoque aucune désactivation à lui seul.

Seuls les providers activés et jouables sur tous les clients demandés entrent dans le décompte. Un timeout isolé est retenté une fois avec un profil réduit, et les rapports JSON/Markdown publiés comme artefacts sont nettoyés des URL complètes, jetons et valeurs d'en-têtes.

La cible de couverture est **10 providers jouables par œuvre, dont au moins 3 VF**. C'est un objectif indicatif, pas un verrou de publication : une œuvre récente ou rare peut légitimement rester sous 10. En revanche, une erreur d'exécution, une identité non vérifiée, un contenu contradictoire, une durée incohérente ou un média non lisible ne compte jamais comme un succès.

Configuration et tests : [`nuvio-client-lab.json`](.github/triggers/nuvio-client-lab.json), [`nuvio_client_lab.cjs`](scripts/nuvio_client_lab.cjs) et [`nuvio_client_lab.test.cjs`](tests/nuvio_client_lab.test.cjs).

---

## À quoi sert Niakvio ?

Niakvio n’est plus un simple agrégateur de fichiers JavaScript. Le projet ajoute une couche de sélection, réparation, validation, compatibilité et publication autour de plusieurs sources communautaires.

Le projet peut notamment :

- collecter plusieurs variantes d’un même provider ;
- éliminer les doublons et variantes obsolètes ;
- exclure les protocoles torrent, magnet, Acestream et autres chemins P2P ;
- résoudre les changements de domaine depuis des hubs, redirections publiques et domaines historiquement validés ;
- retester des **peers historiques** lorsque le domaine courant devient inutilisable, puis promouvoir uniquement un terminal dont l’identité est cohérente ;
- distinguer un hub d’information d’un véritable domaine terminal utilisable ;
- détecter des routes API, recherche ou catalogue devenues obsolètes ;
- poursuivre une récupération générique depuis le provider natif vers le site/API, la recherche catalogue, la fiche, l’iframe/lecteur, les endpoints JS/XHR/JSON puis le média final ;
- capturer les URLs de player/API réellement visitées pendant l’exécution native et les réutiliser comme points de reprise lorsque le résultat initial est vide ou invalide ;
- essayer des origines sœurs cohérentes lorsqu’un service répartit listing et playback entre plusieurs endpoints de la même famille ;
- reconnaître un média même lorsque son URL n’a pas d’extension exploitable, grâce aux redirections, en-têtes, manifests et signatures binaires sondées de façon bornée ;
- rejeter les URLs opaques non vérifiables, faux HLS, previews courtes, pages HTML/JSON et lecteurs parasites, puis continuer la résolution au lieu de les publier comme streams ;
- appliquer des correctifs partagés et versionnés aux bundles et migrer automatiquement les wrappers déjà publiés lorsqu’une implémentation générique évolue ;
- garantir que la réapplication des correctifs converge en une passe et reste idempotente ;
- restaurer un dernier bundle connu comme sain lorsqu’un upstream est incomplet ou corrompu ;
- exécuter les providers dans des workers/probes bornés ;
- tester une matrice multi-œuvres sur les contrats NuvioTV, Desktop macOS et Mobile avec un objectif indicatif de couverture 10/3 ;
- conserver séparément les preuves par catégorie, runtime et génération de bundle ;
- adapter certains providers au runtime NuvioTV lorsqu’une amélioration stricte est démontrée ;
- synchroniser le manifest général avec sa projection francophone ;
- publier uniquement une release dont les versions et empreintes sont cohérentes.

```text
                         Écosystème Niakvio
                                │
                       Sources communautaires
                                │
                 Discovery + sélection des variantes
                                │
            DNS / hubs / redirections / peers historiques
                                │
              Provider natif ── API / recherche catalogue
                                │
                   Fiche ── iframe / lecteur / XHR
                                │
             Validation du média final (URL ou payload)
                                │
                    ┌───────────┴───────────┐
                    │                       │
             Mobile / Desktop           NuvioTV
                  QuickJS            Android TV runtime
                    │                       │
                    └───────────┬───────────┘
                                │
                  Manifest général + projection VF
                                │
                    Versions + hashes + intégrité
```

**Niakvio ne stocke aucune vidéo.** Le projet publie des manifests, métadonnées, correctifs et bundles de providers consommés côté client.

---

## Validation des providers

### 1. DNS et domaine

Avant d’interpréter une erreur comme une panne du provider, Niakvio vérifie le domaine et son rôle.

La récupération peut s’appuyer sur :

- le registre de hubs officiels ;
- les redirections publiques ;
- des pages officielles d’adresses ;
- l’historique de domaines précédemment validés ;
- les anciens terminaux connus, retestés comme **peers historiques** lorsque la route courante échoue ;
- des candidats de récupération strictement bornés.

Les erreurs d’accès structurantes (par exemple `403`, `404`, `408`, `410`, `425`, `429` ou `5xx`) peuvent déclencher un essai sur un peer cohérent. Une nouvelle adresse n’est toutefois jamais promue uniquement parce qu’elle répond en HTTP : son identité, son rôle et sa compatibilité avec le provider doivent rester cohérents. Les règles inverses devenues obsolètes sont supprimées afin d’éviter de réécrire ensuite le nouveau domaine sain vers l’ancien domaine cassé.

### 2. Accès et catégorie

Les catégories sont traitées explicitement :

- `movie` pour les films ;
- `tv` pour les séries ;
- `anime` lorsque le provider expose une logique animation dédiée.

Un provider peut donc fonctionner sur une catégorie et échouer sur une autre. Niakvio évite autant que possible de transformer une réussite représentative sur une catégorie en preuve universelle pour toutes les autres.

### 3. Runtime réel

Les workers reproduisent les signatures d’appel utilisées par les différentes familles Nuvio et limitent :

- le nombre de requêtes ;
- les redirections ;
- le volume des réponses ;
- le nombre d’hôtes distincts ;
- la durée d’exécution.

Mobile/Desktop et NuvioTV disposent de contrats explicitement séparés. Les erreurs structurées permettent de distinguer une panne réseau, une erreur d’invocation, une route disparue, un catalogue vide ou une extraction cassée.

Le moteur de récupération peut également mémoriser les URLs de pages, players et endpoints observées pendant l’appel natif. Si le provider ne produit finalement aucun média valide, ces URLs deviennent des points de reprise bornés. Pour des services répartis sur plusieurs origines sœurs, Niakvio peut rejouer la même route ou le même token sur une origine équivalente détectée dans le bundle, sans coder le nom d’un provider dans le moteur générique.

### 4. Stream réellement lisible

Une URL retournée ne suffit pas.

Niakvio inspecte notamment :

- le statut HTTP et les redirections jusqu’à l’URL finale ;
- le `Content-Type` et, lorsqu’il est utile, le `Content-Disposition` ;
- la présence d’un véritable manifest `#EXTM3U` pour HLS ;
- les manifests DASH ;
- les signatures de conteneurs MP4 / Matroska / WebM / MPEG-TS ;
- des préfixes binaires sondés avec une requête bornée lorsque l’URL et le MIME sont opaques ;
- les pages HTML ou JSON présentées à tort comme un média ;
- les previews anormalement courtes ;
- les hôtes ou routes explicitement bloqués.

**L’extension de l’URL n’est donc pas une condition de lecture.** Une URL telle que `/stream/token/abc` peut être normalisée comme média direct si la réponse réseau le prouve réellement. À l’inverse, une URL opaque qui ne peut pas être vérifiée est rejetée plutôt que rendue aveuglément au client.

### 5. Réparation et comparaison

Une réparation n’est conservée que si elle améliore réellement le comportement observé.

Le pipeline peut :

1. exécuter le bundle d’origine ;
2. identifier une classe de panne ;
3. essayer les stratégies génériques applicables : domaine, endpoint, catalogue, fiche, player, API/XHR ou média ;
4. appliquer un correctif borné lorsqu’une amélioration est démontrée ;
5. retester exactement le bundle modifié ;
6. comparer le résultat avec le parent ;
7. rejeter les réparations neutres, régressives ou purement cosmétiques.

Les wrappers génériques portent une révision d’implémentation lorsqu’elle est nécessaire. Un bundle déjà publié peut ainsi être migré vers une nouvelle logique même si sa configuration n’a pas changé, puis la réapplication suivante doit être un **no-op byte-for-byte**. Cela évite qu’un ancien correctif reste figé indéfiniment ou que les hashes/versions dérivent à chaque passage.

Le promoteur NuvioTV applique la même philosophie : un wrapper TV n’est publié que si le résultat candidat est strictement meilleur et conserve des sorties média strictes.

### 6. Activation et last-known-good

Un historique positif peut aider à préserver un provider lorsque le runner CI rencontre une situation inconclusive, mais il ne doit pas fabriquer une preuve actuelle inexistante.

Les mécanismes de dernier état sain servent principalement à empêcher une panne temporaire de l’upstream ou du runner de détruire inutilement un bundle déjà validé.

---

## Sécurité réseau et sandbox

Les providers sont du code tiers. Niakvio applique donc plusieurs protections avant et pendant les probes :

- blocage des destinations locales, privées et metadata ;
- protection contre certains scénarios de DNS rebinding ;
- validation manuelle des redirections par le garde réseau ;
- quotas de requêtes, taille et hôtes ;
- environnement d’exécution contraint ;
- contrôle des sorties provider ;
- refus des protocoles P2P dans les manifests publiés ;
- tests de non-régression du worker et du garde réseau.

Voir [`SECURITY.md`](SECURITY.md) pour les règles détaillées.

---

## Manifests général et VF

Le manifest VF n’est pas maintenu comme un projet indépendant : il est une **projection contrôlée** du manifest général.

La validation vérifie notamment :

- les identifiants providers ;
- l’état `enabled` ;
- les catégories `supportedTypes` ;
- le bundle réellement référencé ;
- les règles `supportedPlatforms` / `disabledPlatforms` ;
- les chemins `providers/...` et `../providers/...` ;
- l’alignement de version entre les deux manifests.

Les bundles NuvioTV promus font eux aussi partie de cette cohérence : lorsqu’un provider francophone NuvioTV est publié dans le général et projeté dans le VF, les deux manifests doivent référencer le même bundle réel.

---

## Intégrité des releases providers

Une publication Niakvio ne se limite pas à modifier `manifest.json`.

Le pipeline synchronise la version entre :

- [`package.json`](package.json) ;
- [`package-lock.json`](package-lock.json) ;
- [`manifest.json`](manifest.json) ;
- [`vf/manifest.json`](vf/manifest.json) ;
- [`sources.json`](sources.json).

Les fichiers durables de la release sont ensuite inventoriés par SHA-256.

| Ressource | Rôle |
|---|---|
| [`SHA256SUMS.json`](SHA256SUMS.json) | Empreintes des fichiers cœur de la release |
| [`FILE-HASHES.json`](FILE-HASHES.json) | Inventaire étendu des fichiers publiés |
| [`PATCH-SHA256SUMS.txt`](PATCH-SHA256SUMS.txt) | Inventaire déterministe utilisé pour contrôler l’arbre publié |
| [`PROVENANCE.json`](PROVENANCE.json) | Origine et traçabilité des bundles |

Les contrats et scripts NuvioTV font désormais partie du périmètre cœur de l’intégrité de release afin qu’une modification silencieuse de cette compatibilité soit détectée.

---

## Matrices et contrats runtime

### Mobile / Desktop

| Fichier | Description |
|---|---|
| [`automation/platform-runtime-contracts.json`](automation/platform-runtime-contracts.json) | Contrats et tokens Android, iOS, Windows, macOS et Linux |
| [`automation/platform-runtime-matrix.json`](automation/platform-runtime-matrix.json) | Résultats du dernier probe multi-runtime Mobile/Desktop |
| [`automation/platform-runtime-policy.json`](automation/platform-runtime-policy.json) | Décisions de visibilité issues de cette matrice |
| [`automation/nuvio-client-upstreams.json`](automation/nuvio-client-upstreams.json) | Dépôts clients Nuvio suivis, branches/commits acceptés et politique de dérive runtime |

### NuvioTV

| Fichier | Description |
|---|---|
| [`automation/nuvio-tv-runtime-contract.json`](automation/nuvio-tv-runtime-contract.json) | Contrat provider NuvioTV Android TV |
| [`automation/nuvio-tv-global-promotion.json`](automation/nuvio-tv-global-promotion.json) | Preuves historiques strictes et promotions |
| [`scripts/validate_nuvio_tv_runtime_policy.py`](scripts/validate_nuvio_tv_runtime_policy.py) | Garde-fou permanent de compatibilité NuvioTV |

NuvioTV n’est volontairement pas fusionné dans la matrice QuickJS Mobile/Desktop : **il est inclus dans la compatibilité globale du projet via une validation dédiée adaptée à son propre runtime.**

---

## Rapports et fichiers utiles

| Ressource | Description |
|---|---|
| [`manifest.json`](manifest.json) | Manifest général providers Niakvio |
| [`vf/manifest.json`](vf/manifest.json) | Manifest providers francophone |
| [`health-report.json`](health-report.json) | Résultat du dernier contrôle de santé |
| [`availability-report.json`](availability-report.json) | État d’accessibilité observé |
| [`repair-report.json`](repair-report.json) | Réparations testées et décisions associées |
| [`provider-hubs.json`](provider-hubs.json) | Registre des hubs et domaines officiels |
| [`provider-overrides.json`](provider-overrides.json) | Overrides durables de domaine, route, patch et manifest |
| [`automation/nuvio-tv-global-promotion.json`](automation/nuvio-tv-global-promotion.json) | Rapport de compatibilité/promotion NuvioTV |
| [`PROVENANCE.json`](PROVENANCE.json) | Origine des bundles publiés |
| [`SHA256SUMS.json`](SHA256SUMS.json) | Hashes cœur de release |
| [`FILE-HASHES.json`](FILE-HASHES.json) | Hashes étendus de publication |

Les nombres de providers, leur état et la version courante évoluent avec les publications. **Les manifests présents sur `main` constituent la source de vérité de la branche providers.**

---

## Principes de décision

Niakvio suit quelques règles destinées à éviter les faux positifs et les désactivations arbitraires :

1. **Un domaine accessible n’est pas une preuve de fonctionnement.**
2. **L’extension d’une URL n’est ni une preuve de média, ni une condition nécessaire : le payload réseau décide.**
3. **Une URL retournée n’est pas une preuve de média.**
4. **Zéro résultat sur une œuvre n’est pas une preuve d’incompatibilité.**
5. **Une réparation n’est publiée que si elle améliore le runtime observé.**
6. **Une incompatibilité plateforme doit être concluante avant de masquer un provider.**
7. **Les preuves actuelles priment sur les états historiques, qui restent toutefois des candidats de récupération utiles.**
8. **NuvioTV, Mobile et Desktop doivent être validés selon leurs contrats propres et leurs dépôts clients de référence.**
9. **Une publication doit être reproductible, idempotente et intègre jusque sur le `main` final.**

---

## Projets communautaires regroupés

Niakvio ajoute une couche de regroupement, validation et maintenance autour de plusieurs projets amont, notamment :

- [Gowaru — gowaru-nuvio-providers](https://github.com/Gowaru/gowaru-nuvio-providers)
- [yoruix — nuvio-providers](https://github.com/yoruix/nuvio-providers)
- [NuvioPlugin — All-in-One-Nuvio](https://github.com/NuvioPlugin/All-in-One-Nuvio)

Les crédits détaillés sont disponibles dans [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md), [`NOTICE`](NOTICE) et [`UPSTREAMS.md`](UPSTREAMS.md).

### Dépôts Nuvio utilisés comme références runtime

Niakvio vérifie également sa compatibilité contre les implémentations clientes de l’écosystème Nuvio :

- [NuvioMedia/NuvioMobile](https://github.com/NuvioMedia/NuvioMobile) — Android et iOS ;
- [NuvioMedia/NuvioDesktop](https://github.com/NuvioMedia/NuvioDesktop) — Windows, macOS et Linux ;
- [NuvioMedia/NuvioTV](https://github.com/NuvioMedia/NuvioTV) — Android TV.

Ces dépôts ne sont pas des sources de providers pour Niakvio : ils servent à auditer les **contrats d’exécution et de lecture côté client**. Les références exactes acceptées sont versionnées dans [`automation/nuvio-client-upstreams.json`](automation/nuvio-client-upstreams.json).

> Niakvio est un projet communautaire indépendant. Il n’est affilié ni à Nuvio, ni aux mainteneurs des dépôts amont.

---

## Transparence

<div align="center">
  <img src="assets/branding/vibe-coded-badge.png" alt="Vibe Coded — community transparency" width="190">
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/branding/niakw-avatar.png" alt="niakw" width="190">
</div>

Niakvio est développé et maintenu dans une démarche de **vibe coding assisté par IA**, avec tests reproductibles, contrôles automatisés, provenance et historique public des modifications.

Mainteneur : **[niakw](https://github.com/niakw)**

---

## Utilisation responsable

Utilisez uniquement des sources et contenus auxquels vous êtes autorisé à accéder.

Les contrôles automatisés de Niakvio vérifient des éléments techniques. Ils ne déterminent ni le statut juridique d’un contenu, ni l’autorisation de le consulter.

Le projet ne fournit, n’héberge, ne stocke, ne met en cache et ne distribue aucun contenu audiovisuel, compte, abonnement, identifiant ou fichier média.

Documentation complémentaire :

- [`INSTALL.md`](INSTALL.md)
- [`HEALTH-CHECK.md`](HEALTH-CHECK.md)
- [`VALIDATION.md`](VALIDATION.md)
- [`SELECTION.md`](SELECTION.md)
- [`SECURITY.md`](SECURITY.md)
- [`DISCLAIMER.md`](DISCLAIMER.md)
- [`CHANGELOG.md`](CHANGELOG.md)

---

<div align="center">

**Niakvio — Écosystème communautaire pour Nuvio**

Providers • NuvioTV • Réparation • Validation • Compatibilité • Intégrité

</div>
