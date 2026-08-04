<div align="center">
  <img src="assets/branding/nuvio-providers-logo.png" alt="Niakvio" width="280">

# Niakvio

**Plugin communautaire pour Nuvio regroupant des providers VO, VF et VOSTFR dans des manifests unifiés, testés et maintenus automatiquement.**

[![Type](https://img.shields.io/badge/type-plugin%20Nuvio-1f6feb?style=for-the-badge)](#installation)
[![Node](https://img.shields.io/badge/Node.js-%E2%89%A524-339933?style=for-the-badge&logo=node.js&logoColor=white)](package.json)
[![Licence](https://img.shields.io/badge/licence-GPL--3.0-blue?style=for-the-badge)](LICENSE)
[![Deep check](https://github.com/niakw/Niakvio/actions/workflows/sync.yml/badge.svg)](https://github.com/niakw/Niakvio/actions/workflows/sync.yml)

</div>

---

## Manifests Niakvio

### Manifest général — recommandé

**VF + VOSTFR + VO + autres langues**

```text
https://raw.githubusercontent.com/niakw/Niakvio/refs/heads/main/manifest.json
```

[Ouvrir le manifest général](https://raw.githubusercontent.com/niakw/Niakvio/refs/heads/main/manifest.json)

### Manifest francophone

**Sélection dédiée aux providers proposant du contenu en français ou sous-titré français.**

```text
https://raw.githubusercontent.com/niakw/Niakvio/refs/heads/main/vf/manifest.json
```

[Ouvrir le manifest francophone](https://raw.githubusercontent.com/niakw/Niakvio/refs/heads/main/vf/manifest.json)

> Dans Nuvio, ajoutez l’une de ces URL dans la section **Plugins / Providers**.

---

## Installation

1. Copiez l’URL du manifest souhaité.
2. Ouvrez **Nuvio**.
3. Accédez à **Plugins / Providers**.
4. Ajoutez ou importez l’URL.
5. Validez, puis rechargez la liste des providers.

> **Le changement n’apparaît pas ?** Nuvio peut conserver une ancienne version en cache. Actualisez le plugin ou supprimez-le avant de l’ajouter de nouveau.

---

## À quoi sert Niakvio ?

Niakvio rassemble plusieurs projets communautaires de providers Nuvio dans une couche unique de sélection, de contrôle et de maintenance.

Le projet :

- regroupe les variantes disponibles d’un même provider ;
- élimine les doublons ;
- exclut les protocoles torrent, magnet et P2P ;
- recherche les domaines officiels lorsqu’une adresse devient indisponible ;
- applique des corrections techniques contrôlées ;
- teste les providers dans un environnement isolé ;
- vérifie les résultats retournés et leur qualité ;
- publie des manifests général et francophone prêts à être utilisés dans Nuvio.

```text
Sources communautaires
        ↓
Collecte des variantes
        ↓
DNS et domaines officiels
        ↓
Tests d’accès et de fonctionnement
        ↓
Validation des streams et de leur qualité
        ↓
Sélection des meilleures variantes
        ↓
Publication des manifests Niakvio
```

**Niakvio ne stocke aucune vidéo.** Le projet organise uniquement des providers tiers exécutés par le client Nuvio.

---

## Validation des providers

La publication suit une chaîne de validation progressive :

### 1. Domaine et DNS

Le domaine utilisé par le provider est vérifié. Lorsqu’il ne répond plus, Niakvio peut rechercher une adresse de remplacement à partir :

- des hubs officiels enregistrés ;
- des redirections du site ;
- des annonces publiques associées au provider ;
- de l’historique des domaines précédemment validés.

Une nouvelle adresse n’est appliquée qu’après vérification.

### 2. Accès spécifique

Le provider est exécuté selon ses catégories déclarées :

- `movie` pour les films ;
- `tv` pour les séries ;
- `anime` pour les séries et films d’animation pris en charge.

Les étapes de recherche, catalogue, fiche, API, lecteur et extraction sont contrôlées séparément afin de distinguer une panne réseau d’une méthode devenue obsolète.

### 3. Streams et qualité

Un provider ne doit pas être considéré comme valide uniquement parce que son domaine répond ou qu’il retourne une URL.

La validation cherche notamment à écarter :

- les pages HTML présentées comme des vidéos ;
- les manifests HLS malformés ;
- les lecteurs bloqués ou inaccessibles ;
- les liens publicitaires ou parasites ;
- les réponses vides ;
- les routes API obsolètes ;
- les résultats incompatibles avec la catégorie demandée.

Les providers qui ne disposent pas de preuve fonctionnelle suffisante restent présents avec `enabled: false`. Ils peuvent être réactivés lors d’une validation ultérieure réussie.

---

## Manifests et fichiers publiés

| Ressource | Description |
|---|---|
| [`manifest.json`](manifest.json) | Manifest général Niakvio |
| [`vf/manifest.json`](vf/manifest.json) | Manifest francophone |
| [`health-report.json`](health-report.json) | Résultat du dernier contrôle de santé |
| [`availability-report.json`](availability-report.json) | État d’accessibilité des providers |
| [`repair-report.json`](repair-report.json) | Rapport des réparations testées |
| [`provider-hubs.json`](provider-hubs.json) | Registre des hubs et domaines officiels |
| [`PROVENANCE.json`](PROVENANCE.json) | Origine et traçabilité des bundles publiés |
| [`FILE-HASHES.json`](FILE-HASHES.json) | Empreintes des fichiers de publication |

Les nombres de providers, leur état et la version courante évoluent automatiquement. Les manifests publiés constituent la source de vérité.

---

## Projets communautaires regroupés

Niakvio ajoute une couche de regroupement, de validation et de maintenance autour de plusieurs projets amont, notamment :

- [Gowaru — gowaru-nuvio-providers](https://github.com/Gowaru/gowaru-nuvio-providers)
- [yoruix — nuvio-providers](https://github.com/yoruix/nuvio-providers)
- [NuvioPlugin — All-in-One-Nuvio](https://github.com/NuvioPlugin/All-in-One-Nuvio)

Les crédits détaillés sont disponibles dans [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md), [`NOTICE`](NOTICE) et [`UPSTREAMS.md`](UPSTREAMS.md).

> Niakvio est un projet communautaire indépendant. Il n’est affilié ni à Nuvio, ni aux mainteneurs des dépôts amont.

---

## Transparence

<div align="center">
  <img src="assets/branding/vibe-coded-badge.png" alt="Vibe Coded — community transparency" width="190">
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/branding/niakw-avatar.png" alt="niakw" width="190">
</div>

Niakvio est développé et maintenu dans une démarche de **vibe coding assisté par IA**, avec tests reproductibles, contrôles automatisés et historique public des modifications.

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

**Niakvio — Providers communautaires pour Nuvio**

Communautaire • Automatisé • Transparent

</div>
