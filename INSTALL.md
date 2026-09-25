# Installation et maintenance

> [!NOTE]
> Ce document couvre deux usages distincts : **installer NiakVIO dans Nuvio** et **maintenir/publier le repository**.

## ⚡ Utilisateurs Nuvio

> [!TIP]
> Pour la plupart des utilisateurs, utilisez le **manifest général**.

### Manifest recommandé

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/manifest.json
```

<details>
<summary><strong>Autres projections disponibles</strong></summary>

<br>

**Francophone — VF/VOSTFR**

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/vf/manifest.json
```

**Général sans providers orientés anime**

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/no-anime/manifest.json
```

**Francophone sans providers orientés anime**

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/vf-no-anime/manifest.json
```

</details>

Dans un client Nuvio compatible :

1. ouvrez la gestion des plugins/providers ;
2. ajoutez/importez l’URL voulue ;
3. actualisez le repository.

Les URL restent stables. Les versions, bundles, domaines et états d’activation évoluent derrière elles.

---

## 🛠️ Mainteneurs

| Besoin | Outil / version |
| --- | --- |
| Runtime JavaScript | **Node.js 24+** |
| Scripts / tests | **Python 3.12 recommandé** |
| Dépendances | lockfile npm, lifecycle scripts désactivés |

### Installation reproductible

```bash
npm ci --ignore-scripts --no-audit --no-fund
```

### Validation locale minimale

```bash
npm test
node engine_v2/tests/provider-catalog.test.mjs
```

### Diagnostics

```bash
npm run diagnostics
```

---

## 📦 Publication

> [!IMPORTANT]
> Le workflow routine unique est **CORE - Verify & Publish** (`.github/workflows/sync.yml`). Quick et Deep valident ; ils ne doivent pas devenir un deuxième moteur de reconstruction/réparation.

| Mode | Autorité |
| --- | --- |
| **Quick** | gate rapide et déterministe sur les bytes Provider v3 exacts et les contrats Core critiques ; aucun repair, aucune reconstruction, aucune mutation Provider/DATA/Core |
| **Deep** | vérification structurelle complète + observation réseau read-only + re-projection manifests/reports/hashes ; toujours aucun repair ni reconstruction provider |
| **Full reconstruction** | `.github/workflows/provider-v3-reconstruct-all.yml`, sur branche non-main, avec reverse rebuild byte-identical |
| **Learning** | `brain-learning-lab.yml`, sandbox uniquement, propositions reviewables |
| **Domain Refresh** | `domain-refresh.yml`, limité au CONFIG `official_site` validé |

Ne modifiez pas manuellement `manifest.json` et `vf/manifest.json` comme deux sources autonomes. La source publiée canonique de métadonnées/projections est `provider_catalog.json` ; les manifests sont des projections rendues et revalidées dans la transaction autorisée.

Les bundles providers hashés sont immuables et adressés par contenu. Le code durable reste **ProviderBase v3 + DATA/CONFIG + Bloc `PROVIDER.*` / `CORE.*`**.

---

## 🧪 Vérification runtime

> [!IMPORTANT]
> La surface d’acceptation comporte **exactement cinq Labs** indépendants.

| Lab | Workflow |
| --- | --- |
| TV Android + Mobile Android | `.github/workflows/native-mobile-android-reader.yml` |
| Mobile iOS | `.github/workflows/native-mobile-ios-reader.yml` |
| Desktop macOS + Windows | `.github/workflows/native-desktop-reader-acceptance.yml` |
| Diagnostics ciblés | `.github/workflows/native-corpus-device-targeted.yml` |

Le corpus ordinaire est piloté par `.github/triggers/rotating-popular-corpus.json` ; `.github/triggers/nuvio-client-lab.json` conserve les fixtures ciblées/historiques de régression.

Les Labs consomment les bytes NiakVIO exacts et les clients Nuvio officiels sans réparer, reconstruire ou réécrire les providers. Un défaut appartenant au client/OS reste une preuve externe, pas une raison de modifier artificiellement Provider v3.

---

<details>
<summary><strong>Maintenance GitHub Actions</strong></summary>

<br>

`.github/workflows/purge-actions-history.yml` effectue chaque semaine une maintenance automatique : les runs terminés de plus de **7 jours** sont supprimés avec leurs artifacts. Le workflow conserve aussi un mode manuel pour une purge ponctuelle des logs seuls ou des runs complets.

Les artifacts temporaires des Labs natifs sont actuellement conservés **8 jours**. Le cache Gradle reste désactivé lorsque le workflow le prévoit afin de préserver le quota GitHub Actions ; les preuves persistées doivent rester sanitizées.

</details>

## 🧭 Règle de maintenance

Une correction générique appartient au Provider v3/Core approprié.

Les scripts historiques encore présents ne sont que des primitives de compatibilité ou de Learning ; ils ne doivent jamais recréer :

- un second pipeline de publication ;
- un second manifest canonique ;
- une politique d’activation concurrente.

> [!TIP]
> Pour l’architecture complète, voir [`ARCHITECTURE.md`](ARCHITECTURE.md). Pour l’état de validation, voir [`VALIDATION.md`](VALIDATION.md).
