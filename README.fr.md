<div align="center">
  <img src="assets/branding/niakvio-logo.svg" alt="NiakVIO" width="560">

  <p><a href="README.md">English</a> · <strong>Français</strong></p>
  <p><strong>Le moteur communautaire qui agrège, teste, répare et maintient les providers Nuvio.</strong></p>
  <p>VO · VF &nbsp;•&nbsp; Mobile · Desktop · TV</p>

[![Node](https://img.shields.io/badge/Node.js-%E2%89%A524-339933?style=for-the-badge&logo=node.js&logoColor=white)](package.json)
[![Licence](https://img.shields.io/badge/licence-GPL--3.0-blue?style=for-the-badge)](LICENSE)
[![Nuvio](https://img.shields.io/badge/Nuvio-Mobile%20%7C%20Desktop%20%7C%20TV-7c3aed?style=for-the-badge)](#compatibilit%C3%A9-nuvio)

</div>

---

## Ajouter NiakVIO à Nuvio

### Manifest général — recommandé ([Comment l’ajouter ?](docs/fr/how-to-add-manifest.md))

Tous les providers publiés : VF, VO et autres langues explicitement déclarées par les providers ou les flux.

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/manifest.json
```

### Manifest francophone ([Comment l’ajouter ?](docs/fr/how-to-add-manifest.md))

Projection centrée sur les providers proposant du français lorsque cette langue est explicitement déclarée par le provider ou le flux.

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/vf/manifest.json
```

### Manifest VO sans anime ([Comment l’ajouter ?](docs/fr/how-to-add-manifest.md))

Copie du manifest général en retirant les providers qui **déclarent uniquement le type `anime`** ou dont l'**id / nom contient `anim`** (insensible à la casse). Un provider mixte film/série/anime reste présent sauf si son identité indique clairement qu'il est orienté anime.

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/no-anime/manifest.json
```

### Manifest VF sans anime ([Comment l’ajouter ?](docs/fr/how-to-add-manifest.md))

Copie du manifest francophone avec le même filtre déterministe : type `anime` seul, ou `anim` présent dans l'id / nom du provider.

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/vf-no-anime/manifest.json
```

### Badges StreamBadge — recommandé ([Comment les ajouter ?](docs/fr/how-to-add-stream-badges.md))

Pour un réglage unique au niveau du compte Nuvio, utilisez le feed **Fusion v2**. Il emploie les variantes 96×40 avec chip sombre conçues pour rester lisibles sur fonds sombres comme clairs.

**Fusion v2 — recommandé**

```text
https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/stream-badges-fusion-v2.json
```

> NuvioTV conserve localement les règles d'un feed déjà importé. Si l'ancien `stream-badges-fusion.json` avait déjà été ajouté, supprimez cet import puis ajoutez **Fusion v2** : l'URL versionnée force un import frais des règles corrigées.

Feeds spécifiques si le client peut sélectionner le thème :

**Fond sombre / gris**

```text
https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/stream-badges-dark.json
```

**Fond clair / blanc**

```text
https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/stream-badges-light.json
```

Catalogue complet et mapping Core/Brain/UI : [`badge_catalog_v2_complete.json`](assets/badge_catalog_v2_complete.json) · [`mapping_core_brain_ui_v2_complete.json`](assets/mapping_core_brain_ui_v2_complete.json) · [documentation badges/assets](assets/README.md).

Dans Nuvio, copiez l'URL du manifest souhaité dans la gestion des plugins/providers, puis ajoutez le feed badges dans les réglages StreamBadge lorsque cette fonction est disponible. **Le feed StreamBadge est indépendant du manifest providers.**

**Les URL restent stables.** NiakVIO peut faire évoluer derrière elles les bundles, versions, domaines, règles runtime, preuves et états d'activation.

> NiakVIO ne stocke ni n'héberge de vidéo. Le projet maintient des manifests, des métadonnées, des règles de compatibilité et des bundles de providers consommés côté client.

> [!IMPORTANT]
> **Références d'œuvres = fixtures de test.** Les titres, années, saisons ou épisodes visibles dans ce README, le code, les logs CI et les artefacts servent uniquement d'**identifiants déterministes de test** pour vérifier le matching, la compatibilité et les régressions de type « mauvais média ». Leur présence ne constitue ni un catalogue, ni une mise à disposition, ni une recommandation, ni une déclaration sur les droits/licences d'un service tiers. NiakVIO ne doit pas publier de média, extrait, sous-titre, clé de déchiffrement, jeton d'accès ou URL complète de lecture. **Les exceptions et limitations au droit d'auteur varient selon les pays : NiakVIO ne présume d'aucune exception locale et n'accorde aucun droit d'accès ou d'utilisation.** Voir [`TESTING_NOTICE.md`](TESTING_NOTICE.md) et [`DISCLAIMER.md`](DISCLAIMER.md).

---

## Écosystème et sources

### Clients Nuvio officiels

- [Nuvio Mobile — `NuvioMedia/NuvioMobile`](https://github.com/NuvioMedia/NuvioMobile)
- [Nuvio Desktop — `NuvioMedia/NuvioDesktop`](https://github.com/NuvioMedia/NuvioDesktop)
- [NuvioTV — `NuvioMedia/NuvioTV`](https://github.com/NuvioMedia/NuvioTV)

### Repositories providers suivis

NiakVIO consulte plusieurs upstreams au lieu de dépendre d'une seule source ; les doublons canoniques sont éliminés avant Health/Repair :

- [Gowaru — `Gowaru/gowaru-nuvio-providers`](https://github.com/Gowaru/gowaru-nuvio-providers)
- [Yoru — `yoruix/nuvio-providers`](https://github.com/yoruix/nuvio-providers)
- [All-in-One Nuvio — `NuvioPlugin/All-in-One-Nuvio`](https://github.com/NuvioPlugin/All-in-One-Nuvio)

La provenance et les licences tierces sont suivies dans [`PROVENANCE.json`](PROVENANCE.json) et [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

---

## Pourquoi NiakVIO ?

Un provider peut fonctionner aujourd'hui puis casser demain à cause d'un domaine déplacé, d'une API modifiée, d'un lecteur remplacé, d'un token devenu obsolète ou d'une différence entre Mobile, Desktop et TV.

NiakVIO ajoute une couche de maintenance entre les repositories providers et Nuvio :

- **un point d'installation unique** plutôt qu'une collection de manifests à gérer séparément ;
- **plusieurs upstreams observés**, puis une seule entrée canonique déterministe retenue avant Health/Repair ;
- **réparation automatique bornée** lorsque la meilleure variante connue ne fonctionne plus ;
- **contrôle réel du média**, pas seulement de l'URL retournée ;
- **vérification de l'œuvre, de la saison et de l'épisode** pour éviter les faux positifs ;
- **attention particulière au français** sans inventer VF à partir d'un simple nom de domaine ;
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

La langue d'un flux n'est jamais déduite d'un seul indice. NiakVIO conserve en priorité les indications explicitement fournies par le provider ou le flux et peut les croiser avec les métadonnées disponibles. **Les sous-titres ne sont ni inférés ni garantis par NiakVIO** : seule une indication explicitement exposée par un provider ou dans la description/métadonnée d'un flux peut être affichée.

---

## Compatibilité Nuvio

Les commits clients audités sont suivis dans [`automation/nuvio-client-upstreams.json`](automation/nuvio-client-upstreams.json) et [`sources.json`](sources.json). Les Labs résolvent le **HEAD officiel courant** de chaque branche client suivie, vérifient le drift de contrat, puis utilisent ce SHA exact comme baseline en lecture seule.

| Client | Repository | Preuve native retenue |
|---|---|---|
| Nuvio Mobile Android | [`NuvioMedia/NuvioMobile`](https://github.com/NuvioMedia/NuvioMobile) | chemin Android officiel et stack de lecture du client |
| Nuvio Mobile iOS | [`NuvioMedia/NuvioMobile`](https://github.com/NuvioMedia/NuvioMobile) | runtime plugin iOS Full + simulateur iOS + bridge lecteur MPV officiel |
| Nuvio Desktop | [`NuvioMedia/NuvioDesktop`](https://github.com/NuvioMedia/NuvioDesktop) | bridges/lecteurs natifs **macOS et Windows** ; le stub Linux n'est pas une preuve lecteur |
| NuvioTV | [`NuvioMedia/NuvioTV`](https://github.com/NuvioMedia/NuvioTV) | Android TV officiel avec Media3/ExoPlayer |

Le contrat logique ARCHI 2 est commun, mais **une preuve Desktop ne vaut jamais automatiquement preuve Mobile ou TV**.

Les labs natifs parcourent les providers compatibles avec la plateforme, **y compris les providers `enabled:false`**. La couverture standard est désormais **1/1/1 par provider selon les types déclarés** : le Lab retient le **premier type déclaré** applicable à chaque catégorie et exécute au maximum une œuvre film, une œuvre série et une œuvre anime, chacune choisie dans la liste centrale de fixtures. Un provider n'est jamais rejoué sur une seconde œuvre du même type dans le Lab standard. Les routes non déclarées ne sont plus ajoutées comme probes automatiques ; leur découverte appartient au Learning/Deep ciblé. Ces Labs produisent des preuves health/lecteur mais ne bloquent pas le fonctionnement ni la publication normale.

Les snapshots AVD TV/Mobile Android restent réutilisables lorsqu'ils évitent une reconstruction coûteuse. Le **cache Gradle est désactivé sur les Labs natifs** pour préserver le quota de cache GitHub Actions, et leurs artifacts temporaires sont conservés **1 jour**. Les retests ciblés par device restent disponibles manuellement.

---

<!-- NIAKVIO_PROVIDER_RESULTS_START -->
## Providers actifs & résultats natifs vérifiés

<div align="center">

![PROVIDERS ACTIFS](https://img.shields.io/badge/PROVIDERS_ACTIFS-63-16a34a?style=for-the-badge)
![NATIFS VERIFIES](https://img.shields.io/badge/NATIFS_VERIFIES-14-2563eb?style=for-the-badge)
![PREUVES LECTEUR](https://img.shields.io/badge/PREUVES_LECTEUR-32-7c3aed?style=for-the-badge)
![DERNIERE PREUVE](https://img.shields.io/badge/DERNIERE_PREUVE-2026--08--23-334155?style=for-the-badge)

</div>

> **Ici, NiakVIO n'affiche que des succès natifs réellement conservés.** Une preuve signifie que le lecteur officiel Nuvio a atteint un état sain pour le **provider + fixture de test + device exacts**. L'absence de preuve n'est jamais maquillée en succès — et n'est pas non plus présentée comme un échec.

> **Cadre des œuvres citées :** les titres/épisodes du tableau sont des **fixtures de test**, pas un catalogue ni une offre de contenu. Les résultats décrivent uniquement une observation technique sanitizée. Voir [`TESTING_NOTICE.md`](TESTING_NOTICE.md) et [`DISCLAIMER.md`](DISCLAIMER.md).

**14 providers** disposent actuellement d'au moins une preuve lecteur native conservée, sur **4 cas de lecture distincts** et **1 plateforme native** déjà représentée. L'inventaire complet reste synchronisé automatiquement sur `manifest.json`.

### 📡 Couverture des lecteurs officiels

Cette vue distingue **support du lecteur** et **preuve positive conservée** : les cinq cibles natives sont suivies en permanence, même lorsqu'aucune preuve saine n'a encore été retenue pour l'une d'elles.

| Lecteur officiel | Preuves positives conservées | Providers avec preuve | Dernière preuve | État |
|---|---:|---:|---:|---|
| 📺 **TV** | **32** | **14** | `2026-08-23` | ✅ Couvert par une preuve native |
| 🤖 **Mobile Android** | **0** | **0** | `—` | 🟡 Suivi actif · aucune preuve positive conservée |
| 🍎 **Mobile iOS** | **0** | **0** | `—` | 🟡 Suivi actif · aucune preuve positive conservée |
| 🖥️ **Desktop macOS** | **0** | **0** | `—` | 🟡 Suivi actif · aucune preuve positive conservée |
| 🪟 **Desktop Windows** | **0** | **0** | `—` | 🟡 Suivi actif · aucune preuve positive conservée |

### ✅ Lectures natives confirmées

| Provider | Fixtures de test réellement validées | Lecteurs officiels confirmés | Preuves | Dernière validation |
|---|---|---|---:|---:|
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/cineby.webp" width="42" alt="">&nbsp; **Cineby** | 📺 Breaking Bad S01E01 · Série<br>🎌 Jujutsu Kaisen S01E01 · Anime<br>🎬 Sinners 2025 · Film<br>🎬 Sinners · Film | 📺 **TV** ✅ | **4** | `2026-08-23` |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/videasy.webp" width="42" alt="">&nbsp; **VidEasy** | 📺 Breaking Bad S01E01 · Série<br>🎌 Jujutsu Kaisen S01E01 · Anime<br>🎬 Sinners 2025 · Film<br>🎬 Sinners · Film | 📺 **TV** ✅ | **4** | `2026-08-23` |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/castle.webp" width="42" alt="">&nbsp; **Castle** | 📺 Breaking Bad S01E01 · Série<br>🎌 Jujutsu Kaisen S01E01 · Anime<br>🎬 Sinners 2025 · Film | 📺 **TV** ✅ | **3** | `2026-08-23` |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/hindmoviez.webp" width="42" alt="">&nbsp; **HindMoviez** | 📺 Breaking Bad S01E01 · Série<br>🎌 Jujutsu Kaisen S01E01 · Anime<br>🎬 Sinners 2025 · Film | 📺 **TV** ✅ | **3** | `2026-08-23` |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/playimdb.webp" width="42" alt="">&nbsp; **PlayIMDb** | 📺 Breaking Bad S01E01 · Série<br>🎌 Jujutsu Kaisen S01E01 · Anime<br>🎬 Sinners 2025 · Film | 📺 **TV** ✅ | **3** | `2026-08-23` |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/purstream.webp" width="42" alt="">&nbsp; **Purstream** | 📺 Breaking Bad S01E01 · Série<br>🎌 Jujutsu Kaisen S01E01 · Anime<br>🎬 Sinners 2025 · Film | 📺 **TV** ✅ | **3** | `2026-08-23` |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/vegamovies.webp" width="42" alt="">&nbsp; **VegaMovies** | 📺 Breaking Bad S01E01 · Série<br>🎌 Jujutsu Kaisen S01E01 · Anime<br>🎬 Sinners 2025 · Film | 📺 **TV** ✅ | **3** | `2026-08-23` |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/animezey.webp" width="42" alt="">&nbsp; **AnimeZeY** | 📺 Breaking Bad S01E01 · Série<br>🎌 Jujutsu Kaisen S01E01 · Anime | 📺 **TV** ✅ | **2** | `2026-08-23` |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/hdghartv.webp" width="42" alt="">&nbsp; **HDGharTV** | 📺 Breaking Bad S01E01 · Série<br>🎬 Sinners 2025 · Film | 📺 **TV** ✅ | **2** | `2026-08-23` |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/anikototv.webp" width="42" alt="">&nbsp; **AnikotoTV** | 🎌 Jujutsu Kaisen S01E01 · Anime | 📺 **TV** ✅ | **1** | `2026-08-22` |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/anime-sama.webp" width="42" alt="">&nbsp; **Anime-Sama** | 🎌 Jujutsu Kaisen S01E01 · Anime | 📺 **TV** ✅ | **1** | `2026-08-23` |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/animesama-co.webp" width="42" alt="">&nbsp; **AnimeSama.co (DLE Mirror)** | 🎌 Jujutsu Kaisen S01E01 · Anime | 📺 **TV** ✅ | **1** | `2026-08-22` |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/hianime.webp" width="42" alt="">&nbsp; **HiAnime** | 🎌 Jujutsu Kaisen S01E01 · Anime | 📺 **TV** ✅ | **1** | `2026-08-22` |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/streamzo.webp" width="42" alt="">&nbsp; **StreamZo** | 🎬 Sinners 2025 · Film | 📺 **TV** ✅ | **1** | `2026-08-23` |

<details>
<summary><strong>🟢 Voir les 63 providers actifs</strong> — inventaire complet synchronisé au manifest</summary>

La liste ci-dessous décrit **l'état de publication**, pas une supposition sur la lecture. Les providers déjà prouvés natifs sont signalés ; les autres restent simplement actifs dans le manifest jusqu'à ce qu'une preuve positive soit conservée.

| Provider | Types publiés | État de confiance public |
|---|---|---|
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/anikototv.webp" width="42" alt="">&nbsp; **AnikotoTV** | 🎌 Anime · 🎬 Film · 📺 Série | ✅ **Preuve native conservée** · 1 validation lecteur |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/anime-sama.webp" width="42" alt="">&nbsp; **Anime-Sama** | 🎬 Film · 🎌 Anime · 📺 Série | ✅ **Preuve native conservée** · 1 validation lecteur |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/animesama-co.webp" width="42" alt="">&nbsp; **AnimeSama.co (DLE Mirror)** | 🎬 Film · 🎌 Anime · 📺 Série | ✅ **Preuve native conservée** · 1 validation lecteur |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/animezey.webp" width="42" alt="">&nbsp; **AnimeZeY** | 🎬 Film · 📺 Série | ✅ **Preuve native conservée** · 2 validations lecteur |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/castle.webp" width="42" alt="">&nbsp; **Castle** | 🎬 Film · 📺 Série | ✅ **Preuve native conservée** · 3 validations lecteur |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/cineby.webp" width="42" alt="">&nbsp; **Cineby** | 🎬 Film · 📺 Série | ✅ **Preuve native conservée** · 4 validations lecteur |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/hdghartv.webp" width="42" alt="">&nbsp; **HDGharTV** | 🎬 Film · 📺 Série | ✅ **Preuve native conservée** · 2 validations lecteur |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/hianime.webp" width="42" alt="">&nbsp; **HiAnime** | 🎌 Anime · 📺 Série | ✅ **Preuve native conservée** · 1 validation lecteur |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/hindmoviez.webp" width="42" alt="">&nbsp; **HindMoviez** | 🎬 Film · 📺 Série | ✅ **Preuve native conservée** · 3 validations lecteur |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/playimdb.webp" width="42" alt="">&nbsp; **PlayIMDb** | 🎬 Film · 📺 Série | ✅ **Preuve native conservée** · 3 validations lecteur |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/purstream.webp" width="42" alt="">&nbsp; **Purstream** | 🎬 Film · 📺 Série | ✅ **Preuve native conservée** · 3 validations lecteur |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/streamzo.webp" width="42" alt="">&nbsp; **StreamZo** | 🎬 Film · 📺 Série · 🎌 Anime | ✅ **Preuve native conservée** · 1 validation lecteur |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/vegamovies.webp" width="42" alt="">&nbsp; **VegaMovies** | 🎬 Film · 📺 Série | ✅ **Preuve native conservée** · 3 validations lecteur |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/videasy.webp" width="42" alt="">&nbsp; **VidEasy** | 🎬 Film · 📺 Série | ✅ **Preuve native conservée** · 4 validations lecteur |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/4khdhub.webp" width="42" alt="">&nbsp; **4KHDHub** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/4khdhubnew.webp" width="42" alt="">&nbsp; **4KHDHub-NEW** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/allmovieland.webp" width="42" alt="">&nbsp; **AllMovieLand** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/anidb.webp" width="42" alt="">&nbsp; **AniDB** | 🎌 Anime · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/animekai.webp" width="42" alt="">&nbsp; **AnimeKai** | 🎌 Anime · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/animepahe.webp" width="42" alt="">&nbsp; **AnimePahe** | 🎌 Anime · 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/animesalt.webp" width="42" alt="">&nbsp; **AnimeSalt** | 🎌 Anime · 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/animesultra.webp" width="42" alt="">&nbsp; **AnimesUltra** | 🎬 Film · 🎌 Anime · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/animetsu.webp" width="42" alt="">&nbsp; **Animetsu** | 🎌 Anime · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/animevostfr.webp" width="42" alt="">&nbsp; **AnimeVOSTFR** | 🎬 Film · 🎌 Anime · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/animoflix.webp" width="42" alt="">&nbsp; **AnimoFlix** | 🎬 Film · 🎌 Anime · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/anizone.webp" width="42" alt="">&nbsp; **AniZone** | 🎌 Anime · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/cinemacity.webp" width="42" alt="">&nbsp; **CinemaCity** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/cinemm.webp" width="42" alt="">&nbsp; **CineMM** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/coflix.webp" width="42" alt="">&nbsp; **Coflix** | 🎬 Film · 📺 Série · 🎌 Anime | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/desiflix.webp" width="42" alt="">&nbsp; **DesiFlix** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/dooflix.webp" width="42" alt="">&nbsp; **DooFlix** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/dulourd.webp" width="42" alt="">&nbsp; **DuLourd** | 🎌 Anime · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/flemmix.webp" width="42" alt="">&nbsp; **Flemmix** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/french-manga.webp" width="42" alt="">&nbsp; **French-Manga** | 🎬 Film · 🎌 Anime · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/goated.webp" width="42" alt="">&nbsp; **Goated** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/hdhub4u.webp" width="42" alt="">&nbsp; **HDHub4u** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/kehflix.webp" width="42" alt="">&nbsp; **Kehflix** | 🎬 Film · 📺 Série · 🎌 Anime | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/kurage.webp" width="42" alt="">&nbsp; **Kurage** | 🎌 Anime · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/movieblast.webp" width="42" alt="">&nbsp; **MovieBlast** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/movies4u.webp" width="42" alt="">&nbsp; **Movies4u** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/moviesdrive.webp" width="42" alt="">&nbsp; **MoviesDrive** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/movieshunt.webp" width="42" alt="">&nbsp; **MoviesHunt** | 🎬 Film | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/moviesmod.webp" width="42" alt="">&nbsp; **MoviesMod** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/mugiwarastream.webp" width="42" alt="">&nbsp; **Mugiwara-no-Streaming** | 🎬 Film · 🎌 Anime · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/nakios.webp" width="42" alt="">&nbsp; **Nakios** | 🎬 Film · 📺 Série · 🎌 Anime | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/neko-sama.webp" width="42" alt="">&nbsp; **Neko-Sama** | 🎌 Anime · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/papadustream.webp" width="42" alt="">&nbsp; **Papadustream** | 🎬 Film · 📺 Série · 🎌 Anime | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/peachify.webp" width="42" alt="">&nbsp; **Peachify** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/persianstremio.webp" width="42" alt="">&nbsp; **PersianStremio** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/sekai.webp" width="42" alt="">&nbsp; **Sekai** | 🎬 Film · 🎌 Anime · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/streamflix.webp" width="42" alt="">&nbsp; **StreamFlix** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/toflix.webp" width="42" alt="">&nbsp; **ToFlix** | 🎬 Film · 📺 Série · 🎌 Anime | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/uhdmovies.webp" width="42" alt="">&nbsp; **UHDMovies** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/vidfast.webp" width="42" alt="">&nbsp; **VidFast** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/vidlink.webp" width="42" alt="">&nbsp; **VidLink** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/vidrock.webp" width="42" alt="">&nbsp; **VidRock** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/voiranime.webp" width="42" alt="">&nbsp; **VoirAnime** | 🎬 Film · 🎌 Anime · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/voiranime-homes.webp" width="42" alt="">&nbsp; **VoirAnime.homes** | 🎌 Anime · 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/voiranime-rip.webp" width="42" alt="">&nbsp; **VoirAnime.rip** | 🎬 Film · 🎌 Anime · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/vostfree.webp" width="42" alt="">&nbsp; **Vostfree** | 🎬 Film · 🎌 Anime · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/wookafr.webp" width="42" alt="">&nbsp; **Wookafr** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/yflix.webp" width="42" alt="">&nbsp; **YFlix** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |
| <img src="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/72x32/zinkmovies.webp" width="42" alt="">&nbsp; **ZinkMovies** | 🎬 Film · 📺 Série | 🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive |

</details>

### Pourquoi ces résultats sont plus stricts qu'une simple liste de providers

| Contrôle | NiakVIO | Manifest/provider brut |
|---|---|---|
| Provider présent dans un manifest | ✅ | ✅ |
| Plusieurs upstreams comparés avant promotion | ✅ | Variable |
| Média final réellement atteint | ✅ | Non garanti |
| Lecteur officiel vérifié par plateforme | ✅ TV / Android / iOS / macOS / Windows | Non garanti |
| Identité œuvre / année / saison / épisode contrôlée | ✅ | Non garanti |
| HLS / DASH / média direct validé au-delà de l'extension URL | ✅ | Non garanti |
| Mauvais média jouable classé comme échec | ✅ | Non garanti |
| Repair Brain puis retest avant promotion | ✅ | Non |
| Dernier état sain + publication fail-closed | ✅ | Non garanti |
| Historique machine des preuves positives | ✅ | Variable |

**Lecture de la vitrine :** `✅` signifie *preuve positive conservée*, jamais simple détection d'URL. Les résultats affichés restent fixes tant qu'une nouvelle preuve native plus récente ne vient pas les compléter ; un run inconclusif ne détruit pas une preuve saine existante.

Source machine : [`automation/provider-device-results.json`](automation/provider-device-results.json) · Inventaire : [`manifest.json`](manifest.json) · Les prochains Deep/Brain/Labs enrichissent automatiquement cette vitrine uniquement avec des preuves positives qualifiées.
<!-- NIAKVIO_PROVIDER_RESULTS_END -->

---

# Architecture technique

## Provider v3 : source exécutable reconstruisible

La vérité **exécutable** n'est plus un vieux Provider JS publié. Un bundle est généré depuis :

```text
ProviderBase v3 propre
  + DATA/CONFIG + connaissance statique durable
  + type/strategy + plan exécutable
  + Lego PROVIDER.*
  + frontière Core unique
  + Lego CORE.*
  + minimizer NiakVIO-safe pré-hash
  = providers/<id>-<hash>.js
```

Les upstreams, hubs et pages publiques servent de connaissance/provenance. Ils ne sont jamais réinjectés comme seed JavaScript canonique.

Les blocs appartenant à NiakVIO utilisent exclusivement `STARTFIX:<ID>`, `FIXDATA:<ID>` et `CLOSEFIX:<ID>`. Le marqueur ProviderBase courant est `NIAKVIO_PROVIDER_BASE_OWNED_V3`.

La reconstruction forcée complète appartient uniquement à `.github/workflows/provider-v3-reconstruct-all.yml` sur une branche non-main. Elle doit produire 96/96 providers, prouver les plans compatibles avec la typologie (`91` exécutables + `5` quarantined à la référence retry 25), passer les gates minimizer/sécurité puis prouver un reverse rebuild byte-identical 96/96.

La référence actuelle avant la rematérialisation finale sécurité/minimizer est **retry 25** : génération `8e354389b41b2498`, reconstruction `bdfb1e9ab2bc5133d1805e520329dfc85d5e7dcb`, CORE Quick vert `28d98a54264f7d24379c62b310a81b2e60dd7b4b`.

Voir [`ARCHITECTURE.md`](ARCHITECTURE.md).

---

## CORE Quick et Deep

Le workflow routine unique est [`.github/workflows/sync.yml`](.github/workflows/sync.yml), affiché **CORE - Verify & Publish**.

### Quick

Quick est un gate rapide sur les bytes Provider v3 exacts :

- tests structurels et contrats Core critiques ;
- audit du portfolio Lego ;
- aucune reconstruction ;
- aucun repair ;
- aucune mutation Provider/DATA/Core ;
- aucun full network health ;
- aucune publication de nouveau code provider.

### Deep

Deep ajoute :

- contrats structurels complets ;
- observation réseau/hubs en lecture seule ;
- health sur les Provider JS publiés exacts ;
- re-projection des manifests ;
- reports et hashes.

Deep **ne répare et ne reconstruit pas** les providers. Sur `main`, ses écritures sont limitées aux rapports, projections et inventaires explicitement autorisés.

---

## Learning et Domain Refresh

Le Learning quotidien (`brain-learning-lab.yml`) est un sandbox indépendant. Il peut observer, classifier, tester des repairs et produire une mémoire sanitizée ou une proposition reviewable ; il n'a aucune voie de publication directe.

`engine_v2/` reste la couche d'evidence/classification/Learning. Ce n'est pas un deuxième orchestrateur de production.

`domain-refresh.yml` est une exception DATA bornée : il peut modifier uniquement un `official_site` validé et rematérialiser le bloc `PROVIDER.<ID>.CONFIG.V1` correspondant. Les bytes hors CONFIG doivent rester identiques.

---

## Cinq Labs natifs

La surface d'acceptation native est exactement :

1. **TV Android** — NuvioTV officiel ;
2. **Mobile Android** — NuvioMobile officiel ;
3. **Mobile iOS** — NuvioMobile officiel ;
4. **Desktop macOS** — NuvioDesktop officiel ;
5. **Desktop Windows** — NuvioDesktop officiel.

Le trigger commun est `.github/triggers/full-native-lab-validation.json`. La matrice finale couvre **96 providers / 214 routes déclarées** (`82 movie + 92 tv + 40 anime`), providers désactivés inclus en audit. Les fixtures représentatives sont Interstellar, Breaking Bad S01E01 et Jujutsu Kaisen S01E01.

Les Labs consomment le SHA NiakVIO exact, contrôlent le drift du HEAD client officiel et observent extraction, identité, transport, session et lecture. Ils ne réparent, reconstruisent ou réécrivent jamais un provider.

Un échec de stream individuel est une preuve stream-level ; il ne désactive pas automatiquement le provider entier.

---

## HLS et intégrité de lecture

Une playlist valide ne garantit pas un segment valide. `CORE.HLS_RUNTIME_INTEGRITY.V1` peut appliquer une preuve premier-segment bornée sur les providers qui en ont besoin :

- playlist / variant ;
- headers `Referer` / `Origin` conservés ;
- premier segment ou init map lu sur quelques Ko ;
- sync MPEG-TS ou signature fMP4 ;
- HTML/JSON à la place d'un segment rejeté ;
- réseau incertain, timeout ou HLS chiffré conservés comme inconclusifs plutôt que rejetés à tort.

Cette capacité Core générique est activable par DATA provider ; elle n'est pas codée en dur pour un site.

---

## Publication et intégrité

`provider_catalog.json` reste le registre canonique de métadonnées/projections. `manifest.json`, `vf/manifest.json`, `no-anime/manifest.json` et `vf-no-anime/manifest.json` sont des projections.

Les Provider JS sont adressés par contenu. Une génération incohérente ne remplace jamais silencieusement une génération validée.

Terser reste interdit. `scripts/provider_v3_minimizer.py` est désormais le minimizer de production pré-hash : il conserve chaque retour ligne, commentaire/marker, littéral et expression, et retire uniquement l'indentation de lignes dont l'état lexical initial est prouvé comme du code JavaScript ordinaire. Preview Node 96/96, idempotence et fixed-point publié sont obligatoires.

---

## Workflows principaux

| Workflow | Rôle |
|---|---|
| `sync.yml` | CORE Quick/Deep read-only côté providers |
| `provider-v3-reconstruct-all.yml` | reconstruction manuelle 96/96 + reverse proof sur branche non-main |
| `brain-learning-lab.yml` | Learning sandbox + propositions reviewables |
| `domain-refresh.yml` | maintenance `official_site` CONFIG-only |
| `add-provider.yml` | onboarding provider structuré |
| `native-mobile-android-reader.yml` | TV Android + Mobile Android |
| `native-mobile-ios-reader.yml` | Mobile iOS |
| `native-desktop-reader-acceptance.yml` | Desktop macOS + Windows |
| `native-corpus-device-targeted.yml` | retest manuel ciblé |
| `native-reader-learning-sync.yml` | import de preuves sanitizées dans Learning |
| `github-actions-gate.yml` | sécurité/invariants Actions |
| `codeql.yml` | analyse CodeQL |
| `external-code-audit.yml` | Sonar / DeepSource / CodeScene |

---

## Structure du repository

```text
NiakVIO/
├── provider-bases/                  # ProviderBase v3 propres
├── providers/                       # bundles client générés/hashés
├── provider_catalog.json            # registre de publication
├── provider-overrides.json          # DATA/options provider
├── provider-v3-materialization.json # état de matérialisation
├── scripts/provider_patches/        # Lego PROVIDER.* / CORE.*
├── engine_v2/                       # evidence / classification / Learning
├── automation/                      # contrats machine-readable
├── tests/                           # non-régressions
├── .github/workflows/               # CORE / Learning / Labs / maintenance
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

- `main` : unique branche de code, état stable et publiable ;
- `brain-learning/proposals` : mémoire sanitizée persistante du Brain, sans code de production ni publication autonome ;
- les Labs TV/Mobile Android/Mobile iOS/Desktop utilisent directement le SHA de `main` et les dépôts clients Nuvio officiels comme baselines en lecture seule ;
- aucune branche `lab/*`, `fix/*`, `ci/*`, `proof/*`, `tmp/*`, `chore/*`, `refactor/*` ou `brain-repair/*` n'est conservée comme branche de travail.

Les réparations, tests et nettoyages sont matérialisés sur `main`. La mémoire Brain séparée reste non publiable et ne peut pas contourner les gates de production.

---

## Sécurité, responsabilité et indépendance

Le moteur applique des budgets de workers, des protections réseau/SSRF, des contrôles d'identité, une publication fail-closed et une sanitisation des artefacts CI. Les secrets, tokens, cookies, headers sensibles et URL signées ne doivent pas être persistés dans la mémoire d'apprentissage publique.

NiakVIO est un projet communautaire indépendant, non affilié aux développeurs de Nuvio ni aux services tiers référencés. Le projet ne contrôle pas la disponibilité, le contenu, les droits ou les pratiques de sites tiers. L'utilisation doit respecter la législation applicable et les conditions des services concernés.

Voir [`TESTING_NOTICE.md`](TESTING_NOTICE.md), [`DISCLAIMER.md`](DISCLAIMER.md), [`LICENSE`](LICENSE), [`NOTICE`](NOTICE), [`SECURITY.md`](SECURITY.md), [`CONTRIBUTING.md`](CONTRIBUTING.md) et [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).### Workflows de maintenance durables

- `weekly-upstream-provider-discovery.yml` — découverte upstream hebdomadaire en lecture seule.
- `purge-actions-history.yml` — purge planifiée de l'historique GitHub Actions selon la rétention.
- `brain-branch-maintenance.yml` — maintenance des branches Learning/proposals durables, sans publication directe des Provider JS.

