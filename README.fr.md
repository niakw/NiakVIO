<div align="center">
  <img src="assets/branding/niakvio-logo.svg" alt="NiakVIO" width="560">

  <p><a href="README.md">English</a> · <strong>Français</strong></p>
  <h3>Une seule couche providers maintenue pour Nuvio.</h3>
  <p>
    <kbd>Hub-46</kbd>
    <kbd>VO / VF</kbd>
    <kbd>TV · Mobile · Desktop</kbd>
    <kbd>Provider v3</kbd>
  </p>
  <p>Connaissance provider structurée, publication cache-safe et validation native sur les clients Nuvio officiels.</p>
</div>

<p align="center">
  <a href="#-installer-niakvio"><strong>Installer</strong></a> ·
  <a href="#-configuration-nuvio-recommandée"><strong>Setup</strong></a> ·
  <a href="#-comment-fonctionne-niakvio"><strong>Fonctionnement</strong></a> ·
  <a href="#-compatibilité-native"><strong>Labs natifs</strong></a> ·
  <a href="#-références-upstream--crédits"><strong>Upstreams</strong></a> ·
  <a href="#-sécurité-responsabilité--indépendance"><strong>Sécurité</strong></a>
</p>

---

## ⚡ Installer NiakVIO

> [!TIP]
> Pour la plupart des utilisateurs, commencez par le **manifest général**. Les autres projections utilisent la même couche providers maintenue avec une présentation plus ciblée.

### Recommandé — manifest général

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/manifest.json
```

<details>
<summary><strong>Autres projections</strong> — orientées français et/ou sans providers anime</summary>

<br>

**Manifest orienté français**

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/vf/manifest.json
```

**Manifest général sans providers orientés anime**

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/no-anime/manifest.json
```

**Manifest français sans providers orientés anime**

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/vf-no-anime/manifest.json
```

</details>

**Guide manifest :** [`docs/fr/how-to-add-manifest.md`](docs/fr/how-to-add-manifest.md)

### Feed StreamBadge

```text
https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/stream-badges-fusion-v2.json
```

**Guide StreamBadge :** [`docs/fr/how-to-add-stream-badges.md`](docs/fr/how-to-add-stream-badges.md)

> [!NOTE]
> NiakVIO n’héberge aucune vidéo. Le projet maintient les métadonnées providers, la connaissance protocolaire structurée, les règles de compatibilité, les manifests et les bundles providers exécutés côté client.

> [!IMPORTANT]
> Les œuvres citées dans le code, les CI ou la documentation sont des **fixtures de test déterministes**, pas un catalogue. Voir [`TESTING_NOTICE.md`](TESTING_NOTICE.md) et [`DISCLAIMER.md`](DISCLAIMER.md).

---

## ✨ Pourquoi NiakVIO ?

NiakVIO est conçu pour la partie qui devient difficile avec le temps : **garder une grosse couche providers compréhensible quand les domaines, protocoles, clients et comportements de lecture évoluent**.

| | Ce qui reste explicite |
| --- | --- |
| **🔌 Catalogue** | **46 Provider Objects Hub** restent visibles ; un état désactivé ou non résolu n’est pas effacé pour améliorer artificiellement un taux de réussite. |
| **🌍 Projections** | Les manifests général, francophone et sans anime viennent d’une seule couche maintenue. |
| **🧠 Connaissance** | Routes, sémantique des requêtes, identité média, domaines officiels et provenance vivent hors des bundles opaques publiés. |
| **🧩 Réparation** | Les défauts communs peuvent être traités au niveau Provider/Core/famille ; les changements incertains passent par des propositions Learning reviewables. |
| **🧪 Preuves natives** | TV Android, Mobile Android, Mobile iOS, macOS et Windows sont cinq frontières de compatibilité indépendantes. |
| **📦 Publication** | Versions providers, manifests, bundles adressés par contenu et métadonnées d’intégrité restent synchronisés. |
| **🛡️ Validation** | Zéro flux, mauvais média, média malformé et panne upstream d’un client restent des états distincts au lieu d’être maquillés en succès. |

<div align="center">
  <img src="assets/branding/how-it-works.png" alt="Fonctionnement de NiakVIO" width="820">
</div>

<details>
<summary><strong>NiakVIO vs un manifest provider brut</strong></summary>

<br>

Un provider ou manifest autonome peut très bien convenir. NiakVIO prend surtout son sens quand l’objectif devient un **gros catalogue providers mouvant qui doit rester maintenable sur plusieurs clients Nuvio**.

| Capacité | Provider / manifest brut | NiakVIO |
| --- | --- | --- |
| Installation | Un ou plusieurs manifests | Une couche maintenue avec plusieurs projections |
| Maintenance catalogue | Principalement manuelle | Hub-46 conservé et audité |
| Source durable | Souvent le JS publié lui-même | ProviderBase v3 + DATA structurée + Lego Provider/Core détenus |
| Connaissance routes | Souvent enfouie dans le code | Routes/requêtes/provenance structurées |
| Rotation domaines | Changement manuel/statique | Découverte hub officiel + refresh `official_site` borné |
| Types média | Type de lancement et capacité parfois mélangés | Capacité canonique séparée de la compatibilité transport Nuvio |
| Diagnostic | Souvent zéro flux / erreur générique | Preuves search, detail, episode, runtime, player, media et device |
| Réparation | Réécriture manuelle | Réparation famille/Core + propositions Learning reviewables |
| Couverture clients | Souvent extrapolée depuis un seul runtime | Cinq Labs natifs indépendants |
| Publication | Remplacement de fichier | Versions cache-safe + génération manifests + hashes d’intégrité |

</details>

---

## 🧩 Configuration Nuvio recommandée

<div align="center">
  <a href="https://github.com/NuvioMedia"><img src="assets/thanks/nuvio-bg.png" alt="Nuvio" width="150"></a>
  <p><strong>Gardez une stack simple : un outil par rôle.</strong></p>
</div>

| Providers | Métadonnées & catalogue | Sous-titres | Favoris & suivi |
| :---: | :---: | :---: | :---: |
| <img src="assets/branding/niakvio-mark.svg" alt="NiakVIO" width="52"><br>**NiakVIO** | <img src="assets/thanks/ultramax-bg.png" alt="Ultra MAX" width="52"><br>**Ultra MAX** | <img src="assets/thanks/subsense-bg.png" alt="SubSense" width="52"><br>**SubSense** | <img src="assets/thanks/simkl-bg.png" alt="SIMKL" width="52"><br>**SIMKL** |
| Une seule couche providers. | Découverte et rangées orientées métadonnées. | Addon dédié aux sous-titres. | Historique, favoris et tracking. |
| [Repository](https://github.com/niakw/NiakVIO) · [Manifest](https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/manifest.json) | [Ultra MAX](https://ultramax.vip) · [GitHub](https://github.com/PaRaN01a-hash/UltraMax) | [Configurer](https://subsense.nepiraw.com/configure) · [GitHub](https://github.com/NepiRaw/Stremio-SubSense) | [SIMKL](https://simkl.com) |

> [!TIP]
> **Stack cible simple :** 1 couche providers + 1 addon métadonnées/catalogue + 1 addon sous-titres + 1 service de suivi. Évitez d’empiler plusieurs packs providers qui se disputent le même rôle, sauf si vous les testez volontairement.

---

## 🔄 Comment fonctionne NiakVIO

La surface publique reste simple ; la complexité est repoussée derrière des contrats explicites.

1. **La connaissance provider est normalisée** dans ProviderBase v3, DATA structurée et Lego Provider/Core détenus.
2. **Le runtime est gaté et validé** sans transformer un zéro résultat en faux succès.
3. **Les bytes acceptés sont publiés atomiquement** avec manifests, versions et métadonnées d’intégrité synchronisés.

**Pour aller plus loin :** [`ARCHITECTURE.md`](ARCHITECTURE.md) · [`INSTALL.md`](INSTALL.md) · [`VALIDATION.md`](VALIDATION.md)

<details>
<summary><strong>Provider v3, DATA et contrats runtime</strong></summary>

<br>

Les bundles providers publiés sont reconstruits depuis :

```text
ProviderBase v3
+ DATA/connaissance statique provider structurée
+ Lego PROVIDER.*
+ Lego CORE.*
+ minimizer NiakVIO sécurisé
```

Les fichiers `providers/*.js` publiés sont des artefacts runtime adressés par contenu, **jamais des seeds de reconstruction**. Le JavaScript upstream/historique sert uniquement de connaissance et de provenance.

La source durable des routes est :

```text
provider.model.routeData
```

La reconnaissance conserve, lorsqu’ils sont connus, méthode, encodage/champs du body, `Referer`, `Origin`, type de réponse, placeholders, rôle, provenance et confiance. Une absence de route prouvée signifie **inconnu**, pas automatiquement mort ou quarantiné.

Règles runtime :

- gate capacité/type avant tout réseau provider ;
- enrichissement TMDB uniquement si le plan en a besoin ;
- identité scoped par œuvre/type/saison/épisode ;
- provider incompatible → `[]`, pas de recherche arbitraire ;
- Core ne traite les sorties qu’après présence de flux utiles ;
- zéro flux ne fabrique jamais un succès ;
- mauvais média = échec ;
- un flux cassé ne désactive jamais tout le provider.

</details>

<details>
<summary><strong>Types média — capacité sémantique vs transport Nuvio</strong></summary>

<br>

`canonicalSupportedTypes` décrit ce que le catalogue du provider sert réellement (`movie`, `tv`, `anime`). `supportedTypes` décrit comment Nuvio peut le lancer.

Un provider exclusivement anime peut donc légitimement exposer :

```json
{
  "canonicalSupportedTypes": ["anime"],
  "supportedTypes": ["anime", "tv"]
}
```

`tv` est l’alias de compatibilité de lancement épisodique de l’anime. NiakVIO ne synthétise pas `series` ; `movie` n’est exposé que si le provider déclare réellement une capacité canonique `movie`. Les alias de transport n’élargissent jamais la capacité sémantique.

Voir [`docs/media-type-transport-contract.md`](docs/media-type-transport-contract.md).

</details>

<details>
<summary><strong>CORE, Learning, Domain Refresh et publication</strong></summary>

<br>

- **Quick** — checks déterministes structure/runtime/unit/security/minimizer. Aucune réparation/reconstruction provider.
- **Deep** — observation réseau/hub plus large en lecture seule, health providers, projections, rapports et inventaires d’intégrité. Toujours aucune réparation/reconstruction Provider JS.
- **Learning** — chemin isolé d’évolution/réparation du code ; les changements proposés restent reviewables avant publication.
- **Domain Refresh** — maintenance volontairement limitée au DATA CONFIG `official_site` validé.

La publication est atomique et fail-closed. Tout changement des bytes providers publiés impose une synchronisation provider/manifest/cache/release, mais le bump n’est effectué qu’une fois la pile de validation acceptée.

`release-finalize.yml` finalise une génération acceptée au SHA exact. Une modification documentation, workflow ou harness n’impose **aucun bump provider/cache** tant que les bytes providers publiés restent identiques.

</details>

<details>
<summary><strong>Principaux workflows</strong></summary>

<br>

| Workflow | Responsabilité |
| --- | --- |
| `sync.yml` | **CORE - Verify & Publish** Quick/Deep |
| `release-finalize.yml` | finalisation de release acceptée au SHA exact |
| `provider-v3-reconstruct-routes.yml` | reconnaissance route-only / census `routeData` |
| `provider-v3-reconstruct-all.yml` | reconstruction complète Provider v3 + reverse byte proof |
| `brain-learning-lab.yml` | Learning sandbox + propositions reviewables |
| `domain-refresh.yml` | maintenance CONFIG `official_site` validée |
| `add-provider.yml` | onboarding provider structuré |
| `native-mobile-android-reader.yml` | preuves TV Android + Mobile Android |
| `native-mobile-ios-reader.yml` | preuves Mobile iOS |
| `native-desktop-reader-acceptance.yml` | preuves Desktop macOS + Windows |
| `native-corpus-device-targeted.yml` | diagnostics device/provider ciblés |
| `github-actions-gate.yml` | invariants sécurité workflows/repository |
| `codeql.yml` | CodeQL `security-extended` + audit dépendances production |
| `weekly-upstream-provider-discovery.yml` | découverte upstream read-only |

</details>

---

## 🧪 Compatibilité native

> [!IMPORTANT]
> Une preuve Desktop ne vaut pas preuve Android/iOS/TV. **Chaque client/device officiel est une frontière de compatibilité indépendante.**

| Lab | Client officiel |
| --- | --- |
| **TV Android** | [NuvioTV](https://github.com/NuvioMedia/NuvioTV) |
| **Mobile Android** | [NuvioMobile](https://github.com/NuvioMedia/NuvioMobile) |
| **Mobile iOS** | [NuvioMobile](https://github.com/NuvioMedia/NuvioMobile) |
| **Desktop macOS** | [NuvioDesktop](https://github.com/NuvioMedia/NuvioDesktop) |
| **Desktop Windows** | [NuvioDesktop](https://github.com/NuvioMedia/NuvioDesktop) |

Les Labs consomment les clients officiels tels quels. Une erreur upstream de compilation, dépendance, packaging, runtime, player ou QuickJS reste visible au lieu d’être patchée dans NiakVIO uniquement pour fabriquer une CI verte.

<!-- NIAKVIO_NATIVE_ADAPTIVE_LAB_DOCS_V1 -->
<details>
<summary><strong>Scope d’acceptation native et échantillonnage adaptatif</strong></summary>

<br>

Le catalogue maintenu reste **46 Provider Objects Hub**. L’acceptation native finale utilise le scope physique explicite **Hub-46** défini par `automation/evidence/hub-lab-matrix-46.json` ; les lignes désactivées ou hors scope restent visibles comme dette de maintenance et ne sont pas supprimées artificiellement.

Le corpus Lab ordinaire est adaptatif. `.github/triggers/rotating-popular-corpus.json` possède trois réserves globales récentes — **movie, TV et anime**. Une campagne native démarre avec **1 film + 1 épisode TV + 1 épisode anime**. Un provider/lane n’avance qu’après un résultat propre `0 streams`. Une preuve positive arrête la rotation ; une erreur runtime/load/timeout/transport/player/identité s’arrête et reste visible.

Les fixtures historiques de `.github/triggers/nuvio-client-lab.json` restent disponibles pour les diagnostics de régression ciblés, mais ne sont pas l’autorité d’échantillonnage global ordinaire.

</details>

---

## 📚 Références upstream & crédits

> [!NOTE]
> NiakVIO est indépendant. Les repositories upstream servent de **connaissance, preuve d’implémentation et provenance** — pas d’autorité de reconstruction NiakVIO.

| Projet | Apport utile | Rôle dans NiakVIO |
| --- | --- | --- |
| [<img src="assets/thanks/gowaru-bg.png" alt="Gowaru" width="110">](https://github.com/Gowaru/gowaru-nuvio-providers)<br>**[Gowaru](https://github.com/Gowaru/gowaru-nuvio-providers)** | Implémentations providers françaises et connaissance protocolaire locale. | **Référence / preuve** |
| [<img src="assets/thanks/yoru-bg.png" alt="Yoru" width="110">](https://github.com/yoruix/nuvio-providers)<br>**[Yoru](https://github.com/yoruix/nuvio-providers)** | Implémentations providers et conventions Nuvio utiles pour croiser runtime/interfaces. | **Référence / preuve** |
| [<img src="assets/thanks/deadlyrocket-bg.png" alt="All-in-One Nuvio" width="110">](https://github.com/NuvioPlugin/All-in-One-Nuvio)<br>**[All-in-One Nuvio](https://github.com/NuvioPlugin/All-in-One-Nuvio)** | Matériel international d’agrégation/référence. L’[ancien miroir D3adlyRocket](https://github.com/D3adlyRocket/All-in-One-Nuvio) reste utile pour la provenance historique. | **Référence / preuve + provenance historique** |

<details>
<summary><strong>Ce que signifie “connaissance upstream” ici</strong></summary>

<br>

NiakVIO peut utiliser les projets upstream pour apprendre ou vérifier la structure des endpoints, la sémantique des requêtes, le nommage provider, le comportement historique ou des conventions runtime. Cette connaissance est normalisée dans le modèle DATA / Provider/Core de NiakVIO avant publication.

L’objectif est de préserver **crédit et preuves** sans faire des bundles tiers publiés la source durable de vérité.

Voir [`UPSTREAMS.md`](UPSTREAMS.md).

</details>

---

## 🔐 Sécurité, responsabilité & indépendance

Le JavaScript provider est traité comme une entrée non fiable. NiakVIO utilise workers bornés, contrôles SSRF/réseau, sandboxing, vérifications d’identité, sanitization CI et publication fail-closed.

> [!CAUTION]
> NiakVIO est un projet communautaire indépendant, non affilié à Nuvio ni aux services tiers cités. Rien dans ce repository n’accorde de droits sur des médias/services tiers ni n’autorise le contournement d’une authentification, d’un paywall, d’un chiffrement ou d’un contrôle d’accès.

**Documents projet :** [`SECURITY.md`](SECURITY.md) · [`TESTING_NOTICE.md`](TESTING_NOTICE.md) · [`DISCLAIMER.md`](DISCLAIMER.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) · [`LICENSE`](LICENSE) · [`NOTICE`](NOTICE)
