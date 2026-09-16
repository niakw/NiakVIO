# Sources amont et provenance

> [!NOTE]
> NiakVIO observe plusieurs sources communautaires pour la **connaissance, la comparaison et la provenance**. Leur JavaScript n’est **jamais une seed JavaScript exécutable** pour reconstruire Provider v3.

## 🌐 Sources principales

| Projet | Dépôt | Apport historique | Rôle |
| --- | --- | --- | --- |
| **Gowaru** | [Gowaru/gowaru-nuvio-providers](https://github.com/Gowaru/gowaru-nuvio-providers) | Providers VF, VOSTFR et anime francophone. | Référence / preuve |
| **All-in-One-Nuvio** | [NuvioPlugin/All-in-One-Nuvio](https://github.com/NuvioPlugin/All-in-One-Nuvio) | Providers internationaux et correctifs récents. | Référence / preuve |
| **D3adlyRocket mirror** | [D3adlyRocket/All-in-One-Nuvio](https://github.com/D3adlyRocket/All-in-One-Nuvio) | Ancien miroir utile comme provenance historique. | Provenance historique |
| **Yoru** | [yoruix/nuvio-providers](https://github.com/yoruix/nuvio-providers) | Providers exclusifs et variantes complémentaires. | Référence / preuve |

<details>
<summary><strong>Manifests upstream</strong></summary>

<br>

**Gowaru**

```text
https://raw.githubusercontent.com/Gowaru/gowaru-nuvio-providers/refs/heads/main/manifest.json
```

**All-in-One-Nuvio**

```text
https://raw.githubusercontent.com/NuvioPlugin/All-in-One-Nuvio/refs/heads/main/manifest.json
```

**Ancien miroir D3adlyRocket**

```text
https://raw.githubusercontent.com/D3adlyRocket/All-in-One-Nuvio/refs/heads/main/manifest.json
```

**Yoru**

```text
https://raw.githubusercontent.com/yoruix/nuvio-providers/refs/heads/main/manifest.json
```

</details>

---

## 🔎 Contrat d’observation

`.github/workflows/weekly-upstream-provider-discovery.yml` observe les sources en lecture seule :

1. résout les hubs/manifests accessibles ;
2. stage temporairement les entrées non-P2P pour comparaison ;
3. signale les providers absents du catalogue NiakVIO ;
4. publie uniquement des artifacts/rapports de découverte ;
5. vérifie par `git diff --exit-code` qu’aucun catalogue, manifest, override ou Provider JS n’a été muté.

> [!IMPORTANT]
> Les répertoires `upstream-lkg/manifests/` et `upstream-lkg/providers/` conservent des snapshots historiques/provenance. Ils ne sont **pas** rafraîchis par CORE Deep aujourd’hui et ne constituent ni ProviderBase v3, ni une seed de reconstruction.

---

## 🧩 Relation avec Provider v3

La reconstruction exécutable part exclusivement de :

```text
ProviderBase v3
+ DATA/CONFIG structurées
+ Lego PROVIDER.*
+ Lego CORE.*
```

Une observation upstream peut inspirer Learning ou une modification reviewable de DATA/Lego, mais son JavaScript n’est jamais copié comme base canonique.

### Ce que NiakVIO peut apprendre d’un upstream

- structure d’endpoint et routes ;
- méthode HTTP, headers, body et forme de réponse ;
- nommage provider et provenance ;
- comportements historiques ;
- conventions runtime ou compatibilité utiles à croiser.

Cette connaissance est normalisée dans le modèle NiakVIO avant toute publication.

---

## 🛡️ Règles

1. Ne jamais activer deux copies du même provider.
2. Ne jamais remplacer une génération publiée par une variante non prouvée.
3. Exclure les protocoles/providers P2P du flux d’onboarding standard.
4. Conserver les snapshots upstream comme provenance bornée, pas comme code de production.
5. Un snapshot LKG ou upstream ne contourne jamais les contrats d’identité, sécurité, HLS ou reverse reconstruction.
6. Les Provider JS publiés sont générés depuis Provider v3 et adressés par contenu avant toute projection qui les référence.

> [!TIP]
> Pour une vue plus synthétique et visuelle des crédits upstream, voir la section **Upstream references & credits** du [`README.md`](README.md) ou sa version [`README.fr.md`](README.fr.md).
