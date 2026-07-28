## v5.13.1 — manifests général et VF clairement documentés

La validation `deep` exécute une requête représentative et sonde au maximum un stream. Les types de catalogue sont déduits des métadonnées **fusionnées des trois manifests** : une description telle que « Films, Séries et Animes en VF et VOSTFR » conserve `movie`, `tv` et `anime` au lieu d’être réduite à l’anime.

Trois incohérences globales sont corrigées :

- un deep actuellement sain peut activer immédiatement un nouveau SHA ; l’historique sert seulement de grâce lors d’un futur résultat inconclusif ;
- des sous-titres optionnels annoncés mais non sondables ne désactivent plus un stream principal jouable dont l’audio FR/EN est accepté ;
- les langues réellement observées priment sur la description : un provider annonçant « VF et VOSTFR » mais retournant uniquement du VOSTFR est classé VOSTFR.

Les providers VF, VOSTFR puis francophones sont classés par résolution et score ; les autres langues sont classées d’abord par score de santé/qualité. Les exclusions P2P/torrent restent absolues.

# Nuvio Curated Providers

## Correctifs v5.5

La version du manifest est désormais révisée automatiquement à chaque changement réel du catalogue afin de contourner le cache de NuvioTV. La tolérance aux résultats CI inconclusifs est générique : elle n’est liée à aucun provider précis et exige le même SHA, un score historique au-dessus du seuil et la validation antérieure de toutes les portes de qualité.


## Ajouter un manifest dans Nuvio

Le dépôt publie automatiquement **deux manifests distincts** lors du même workflow `deep`.

### Manifest général — recommandé

Ajoutez cette URL dans la section **Plugins / Providers** de Nuvio :

```text
https://raw.githubusercontent.com/niakw/niakw-nuvio-providers-group-1-0/refs/heads/main/manifest.json
```

Il contient tous les providers validés : **VF, VOSTFR, français non précisé, VO et autres langues**. L’ordre de chargement privilégie la VF, puis la VOSTFR, avant les autres sources.

### Manifest VF uniquement

Pour ne charger que les providers classés en **version française**, utilisez :

```text
https://raw.githubusercontent.com/niakw/niakw-nuvio-providers-group-1-0/refs/heads/main/vf/manifest.json
```

Il est généré automatiquement à partir du manifest général et ne conserve que les providers **activés** dont le classement final est `vf`. Les providers uniquement VOSTFR, les langues étrangères et les providers désactivés en sont exclus.

| Manifest | Contenu |
| --- | --- |
| `/manifest.json` | VF + VOSTFR + français non précisé + VO/autres langues |
| `/vf/manifest.json` | VF uniquement |

Les deux fichiers sont régénérés et publiés ensemble lors de chaque validation `deep`.

Manifest communautaire combinant automatiquement les trois manifests amont. Les contrôles rapides restent informatifs ; seule une validation `deep` peut modifier le manifest. En mode `deep`, chaque variante exécute une seule requête représentative. L’activation exige à la fois un serveur réellement joignable et une curation suffisante issue des métadonnées fusionnées des trois manifests.

> **Description GitHub conseillée**  
> Curated Nuvio provider manifest with automated availability and compatibility checks. No media hosted, indexed or supplied.

## Objet du projet

Ce dépôt automatise uniquement des opérations techniques sur des modules tiers
installables par l’utilisateur :

- découverte des versions publiées dans plusieurs manifests amont ;
- exclusion des providers et flux torrent, magnet et P2P ;
- exécution des modules candidats dans un processus séparé, au sein d’un job sans secret et sans droit d’écriture sur le dépôt ;
- vérification limitée de la disponibilité des points techniques retournés ;
- inspection des manifests HLS/DASH et des métadonnées exposées ;
- comparaison des résolutions, codecs, langues et sous-titres lorsqu’ils sont détectables ;
- contrôle de chaque variante téléchargée avant toute modification du manifest ;
- regroupement des doublons uniquement après ces contrôles ;
- publication des fichiers JavaScript avant le manifest qui les référence ;
- conservation de la version publiée lorsqu’une nouvelle copie ne peut pas être téléchargée.

Le projet **ne fournit, n’héberge, ne stocke, ne met en cache, n’indexe et ne
distribue aucun contenu audiovisuel**. Il ne fournit pas non plus de compte,
abonnement, identifiant, clé d’accès, fichier média ou catalogue.

## Responsabilité de l’utilisateur

Ce logiciel doit être utilisé uniquement avec des contenus :

- dont l’utilisateur est propriétaire ;
- qu’il a lui-même créés ou mis à disposition ;
- pour lesquels il dispose d’une licence, d’un abonnement ou d’une autorisation valable ;
- ou qui sont librement accessibles dans le respect des lois et conditions applicables.

Les contrôles automatisés sont exclusivement techniques. Ils ne déterminent ni la
propriété d’un contenu, ni son statut juridique, ni l’autorisation de le consulter.
Chaque utilisateur reste seul responsable de ses sources, de ses accès, de ses choix
de visionnage, du respect des droits applicables et des conditions d’utilisation des
services consultés.

Cette section décrit l’usage attendu du logiciel. Elle ne modifie pas la GPL et
n’ajoute aucune restriction supplémentaire à la licence du code.

## Remerciements et projets amont

Ce projet repose sur le travail de trois dépôts amont. Merci à leurs mainteneurs et
contributeurs pour leur développement, leur documentation et leur maintenance :

- **Gowaru**, pour  
  [gowaru-nuvio-providers](https://github.com/Gowaru/gowaru-nuvio-providers) ;
- **yoruix**, pour  
  [nuvio-providers](https://github.com/yoruix/nuvio-providers) ;
- **=[D3adly]=, D3adlyRocket, NuvioPlugin et les développeurs crédités par leur
  projet**, pour  
  [All-in-One-Nuvio](https://github.com/NuvioPlugin/All-in-One-Nuvio).

Le README d’All-in-One-Nuvio déclare le projet sous GNU GPL v3. Cette déclaration
publique constitue la base sur laquelle ses fichiers sont utilisés ici. Elle ne vaut
pas affirmation de notre part quant à la titularité détaillée de chaque contribution
agrégée dans ce dépôt.

**Si l’un de ces dépôts répond déjà parfaitement à vos besoins, utilisez-le
directement.** Vous recevrez ainsi les correctifs de son mainteneur sans couche
intermédiaire, et vous soutiendrez plus directement son travail.

Ce dépôt n’a pas vocation à remplacer, concurrencer ou s’attribuer le travail des
projets amont. Il ajoute uniquement une couche optionnelle de curation, de comparaison,
de repli et de contrôle automatisé.

Les auteurs amont :

- ne sont pas responsables de ce dépôt ;
- ne sont pas supposés l’approuver ;
- ne sont pas liés à ses choix de sélection ;
- ne sont pas responsables de l’usage effectué par ses utilisateurs.

Les attributions détaillées figurent dans
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Contrôles automatisés

### Test réseau léger

Chaque variante exécute une seule requête représentative. Les appels vers TMDB et
GitHub sont considérés comme de l’infrastructure et ne prouvent pas la disponibilité
du provider. Un serveur propre au provider est déclaré accessible dès qu’une réponse
HTTP réelle est reçue, y compris 401, 403, 404, 429 ou 5xx. Une erreur DNS, TLS,
connexion refusée ou timeout reste un échec.

Lorsqu’un flux est réellement retourné, un seul flux au maximum est sondé afin de
conserver les informations disponibles sur sa résolution, son format, sa langue et sa
lisibilité sans transformer le workflow en benchmark exhaustif.

### Curation par les trois manifests

Les doublons sont regroupés par identifiant. Le système fusionne les descriptions,
langues, formats, types pris en charge et signaux de qualité déclarés par Gowaru,
All-in-One-Nuvio et yoruix avant de choisir une variante.

Le score éditorial tient notamment compte :

- des résolutions explicites 720p, 1080p, 1440p, 2160p, HD, FHD, UHD ou 4K ;
- des mentions de qualité multiple, de liens directs, de rapidité ou de plusieurs serveurs ;
- de la richesse ou de l’actualité du catalogue lorsqu’elle est annoncée ;
- de la présence du français ou de l’anglais ;
- des mentions VF, VOSTFR, doublé, sous-titré ou multilingue ;
- de formats directs reconnus comme MP4, MKV, HLS/M3U8 ou DASH ;
- de la présence du même provider dans plusieurs manifests.

Un simple serveur HTTP accessible ne suffit donc pas. Sans flux mesurable, le provider
doit avoir une description exploitable, une langue FR/EN, un format reconnu et un
score éditorial agrégé d’au moins **5**.

### Ordre de chargement dans le manifest

Les providers activés sont ordonnés pour favoriser les résultats francophones dès le
début du chargement :

1. providers dont le runtime retourne de la **VF**, sinon déclarant explicitement de la VF ;
2. providers dont le runtime retourne uniquement de la **VOSTFR**, sinon déclarant explicitement du VOSTFR ;
3. providers déclarant le français sans mode audio/sous-titre suffisamment précis ;
4. providers VO et autres langues.

Dans chaque groupe, l’ordre privilégie d’abord la meilleure résolution mesurée ou
déclarée, puis le score de santé, puis le score de curation issu des trois manifests.
Le manifest contrôle l’ordre des providers ; l’application Nuvio peut encore appliquer
son propre tri visuel aux streams après leur réception.

### Protection des mises à jour

La publication échoue si l’un des trois manifests n’a pas pu être chargé ou si une
variante n’a pas été contrôlée. Les fichiers JavaScript sont publiés sous un nom
contenant leur SHA-256 avant la publication du manifest qui les référence. Les checks
`quick` restent report-only ; seuls les checks `deep` publient.

## Exclusion des torrents et du P2P

Le système exclut explicitement :

- les providers identifiés comme torrent, magnet ou P2P ;
- les protocoles `magnet:`, `torrent:`, `acestream:` et `sop:` ;
- les objets contenant des marqueurs comme `infoHash`, `magnet` ou `torrent` ;
- les anciennes entrées correspondantes déjà présentes dans le manifest.

## Combinaison des trois manifests

À chaque synchronisation, le workflow utilise l’intégralité des manifests de Gowaru,
All-in-One-Nuvio et yoruix. Il n’existe plus de liste statique de 38 providers.

Le rapport `health-report.json` indique à chaque exécution :

- le nombre de variantes contrôlées ;
- le nombre de providers uniques découverts ;
- le nombre de providers publiés ;
- le nombre de providers activés et désactivés ;
- la variante amont retenue pour chaque identifiant dupliqué.


## Les dix conditions obligatoires d’activation

1. **Politique sûre** : aucun torrent, magnet, P2P, Acestream, Sopcast ou champ assimilé.
2. **Accès fonctionnel** : au moins un flux réellement vérifié, ou une réponse HTTP provenant d’un serveur propre au provider.
3. **Score** : score d’au moins **70/100**.
4. **Couverture** : une fixture représentative saine dans un type déclaré ; sinon description de manifest exploitable.
5. **Volume** : au moins un stream jouable lorsqu’un stream est retourné ; sinon preuve d’accès au serveur du provider.
6. **Hôte** : au moins un hôte média joignable lorsqu’un stream est retourné ; sinon preuve d’accès au serveur.
7. **Lecture** : au moins une charge utile vérifiée lorsqu’un stream est retourné ; sinon preuve d’accès au serveur sans prétendre avoir vérifié la lecture.
8. **Qualité éditoriale ou mesurée** : au moins 720p lorsqu’elle est mesurée, ou score de curation des trois manifests au moins égal à **5**.
9. **Langues** : français ou anglais détecté dans le flux ou déclaré dans les métadonnées fusionnées.
10. **Stabilité** : latence acceptable et une validation `deep` réussie pour le SHA courant ; pour le contrôle léger, réponse HTTP effective du serveur provider.

Les entrées non conformes restent publiées avec `enabled: false`. Les exclusions P2P
restent absolues et ne peuvent être contournées par l’historique ou une preuve externe.

### Publication

- `quick` : rapport uniquement ;
- `deep` : découverte complète, une requête représentative par variante, curation et publication ;
- changement du fichier JavaScript : nouveau nom SHA-256 et nouvelle révision du manifest si le contenu publié change.

## Rapports

Selon la configuration du dépôt, les fichiers suivants peuvent être générés :

- `health-report.json` ;
- `health-history.json` ;
- `availability-report.json` ;
- `availability-history.json` ;
- `PROVENANCE.json`.

Les rapports ne doivent pas publier les URL complètes retournées par les providers.

## Indépendance

Ce dépôt n’est pas un produit officiel de Nuvio et n’est affilié ni à Nuvio, ni aux
projets amont, ni aux services éventuellement consultés par les modules tiers.

Les noms, marques et logos appartiennent à leurs titulaires respectifs. Leur mention
sert uniquement à identifier les projets logiciels ou compatibilités concernés.

## Licence

Le code original d’automatisation et la documentation de ce dépôt sont distribués sous
**GNU General Public License version 3 uniquement (`GPL-3.0-only`)**.

Les fichiers tiers conservent leurs droits d’auteur, mentions et conditions amont.
Leur inclusion dans ce dépôt n’élargit pas les droits accordés par leurs auteurs.

Il n’est pas possible de placer l’ensemble du dépôt dans le domaine public ou sous
CC0, puisque nous ne détenons pas l’intégralité des droits sur les fichiers tiers.

Consultez :

- [`LICENSE`](LICENSE) ;
- [`NOTICE`](NOTICE) ;
- [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) ;
- [`DISCLAIMER.md`](DISCLAIMER.md).

## Absence de garantie

Le projet est fourni en l’état, sans garantie de disponibilité, d’exactitude, de
compatibilité, de qualité, de légalité d’une source tierce ou d’adéquation à un usage
particulier.

Un test réussi à un instant donné ne garantit pas qu’un service restera accessible ni
qu’il fonctionnera depuis le réseau ou l’appareil de l’utilisateur.

## Manifests linguistiques générés

À chaque publication du manifest général, deux variantes sont régénérées automatiquement à partir du classement linguistique réellement observé pendant le deep :

- `vf/manifest.json` : tous les providers déclarés ou observés comme **VF**, en conservant leur état `enabled` réel ;

Le manifest général reste `manifest.json`. Les fichiers JavaScript demeurent dans `providers/`; les manifests imbriqués utilisent donc des chemins relatifs `../providers/...`.

## Diagnostics, overrides and bounded runtime repair

`provider-overrides.json` is the source of truth for durable literal/domain replacements and reusable structural patch profiles. Behavioural profiles are **not** blindly applied during discovery. A deep build first executes the downloaded JavaScript, classifies generic failure signatures from sanitized network evidence, applies every structurally compatible strategy, executes the exact generated JavaScript again, and retains it only when the before/after result strictly improves without a runtime error.

The repair engine and its loop contain no provider IDs or domains. Domain changes remain simple per-provider data overrides because the destination itself is provider-specific; search, metadata-context and parser recovery are capability-driven. The bounded loop stops after a configured maximum number of rounds, preserves the parent artifact on every failed or neutral attempt, and writes `repair-report.json` with accepted and rejected transformations.

Staged candidates record `upstream_sha256`, the final `sha256`, and `local_patches`, so an upstream refresh cannot silently erase or duplicate a correction. Deep CI also generates `diagnostics-report.json`, `diagnostics-report.html` and `route-regressions.json` without publishing sensitive final stream URLs.

Run the local regression suite with:

```bash
npm test
```

### Validation de bout en bout des overrides

Après le téléchargement des manifests upstream, `scripts/validate_override_pipeline.py` contrôle les fichiers JavaScript exacts placés dans `staging/` avant leur verrouillage et leur exécution. Le workflow échoue si une ancienne valeur configurée subsiste, si le hash du fichier ne correspond plus à `candidates.json`, ou si un patch enregistré n’est pas présent dans le fichier réellement promu. Les hashes upstream et patché ainsi que les remplacements appliqués sont ensuite conservés dans `PROVENANCE.json`.

## Security hardening

Provider code is treated as untrusted. Validation applies process/module restrictions, bounded worker output, memory and time limits, request and host budgets, per-response and cumulative byte budgets, and SSRF destination filtering. Route regressions are handled per candidate: a failed repair cannot mutate or replace the parent JavaScript, and unrelated providers are never blocked by another provider's route failure. See `SECURITY.md` for the exact guarantees and remaining limitations.
