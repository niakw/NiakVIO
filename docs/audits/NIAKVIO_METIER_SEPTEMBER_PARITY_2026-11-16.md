# NiakVIO — audit de parité métier avec septembre

Date : 2026-11-16  
Référence septembre : `ee746ed5b101849a2babd777fcfb9f2984ff4629`  
Référence de comparaison actuelle : `5a747133a96063ca91dc5ccbbaa5d7d71edbbeac`

> Cet audit mesure la **structure métier et les primitives communes**, pas la disponibilité réseau d'un provider. Une parité de code n'est ni un FULL OK ni une preuve de lecture. La certification finale reste liée aux octets publiés, au reverse rebuild et aux cinq Labs Nuvio.

## Conclusion provisoire

Le socle Provider v3 courant conserve les primitives de la base de septembre et ajoute les mécanismes nécessaires aux améliorations actuelles : projection Global+France, séparation type provider / namespace TMDB, couverture multi-stream, preuve exacte des octets et certification multi-client.

Aucune fonction nommée de `scripts/provider_base_store.py` présente à la référence de septembre n'a disparu dans la version courante.

| Composant | Septembre | Courant | Fonctions septembre absentes |
| --- | ---: | ---: | ---: |
| `provider_base_store.py` | 206 | 219 | **0** |
| `apply_provider_overrides.py` | 35 | 38 | **0** |
| `materialize_provider_v3_all.py` | 18 | 20 | **0** |
| `current_provider_scope.py` | 15 | 29 | **0** |
| `global_media_type_resolution_v1.py` | 53 | 53 | **0** |
| `global_stream_score_v1.py` | 20 | 20 | **0** |

Le ProviderBase ajoute notamment la déduplication par identité de lecture, l'extraction de variantes média/qualité et la séparation explicite `_mediaNamespace` / `_tmdbNamespace`.

## Stream Presentation / langues

`global_stream_presentation_v1.py` passe de 61 à 71 fonctions. Les deux helpers locaux historiques `isVf` / `isVfq` ne sont plus des fonctions autonomes ; leur comportement n'a pas été supprimé.

La version actuelle possède une projection plus structurée :

- détection explicite VF / VFF / VFQ / VOSTFR / VO ;
- `languageCode` avec locales telles que `fr-ca`, `fr-ch`, `pt-br`, `pt-pt`, etc. ;
- `languageRole` pour Original / Dub / Sub ;
- `languageTracks` pour distinguer pistes audio et sous-titres ;
- conservation des sources de sous-titres et de leurs headers ;
- enrichissement à partir des faits réels du player/HLS.

Il s'agit donc d'un remplacement enrichi de la logique de septembre, pas d'une perte de capacité.

## Invariants métier restaurés ou renforcés

- Provider v3 = ProviderBase propre + DATA structurée + Blocs Provider + Blocs Core + minimizer.
- Global et France sont une même autorité d'exécution par union de projections ; les providers France-only restent France-only.
- Le transport natif de validation contient **75 identités actives uniques** au lieu d'un ancien sous-ensemble de neuf.
- `movie|tv|anime` reste l'ABI provider canonique. `series|show|other` sont des alias d'entrée TV ; `tv` peut rester un alias de lancement pour un provider anime sans devenir sa sémantique.
- Le namespace TMDB `movie|tv` sert à l'identité et ne réécrit plus implicitement `anime` côté provider.
- Saison 0 est valide ; `Spartacus S00E01` est une régression obligatoire dans les cinq Labs.
- Le runtime partagé agrège lecteurs/serveurs/sources/langues/qualités avant le plafond final ; contrat courant : 40 identités de lecture, déduplication URL + headers requis.
- Core commun : HLS integrity, security boundary, runtime compatibility, stream facts, identity, media type, presentation, branding, sanitizer, media safety, StreamScore et telemetry sont des responsabilités communes et non des hacks provider.
- Domain Refresh ne possède que l'autorité d'adresse et ses dérivés.
- Quick/Deep vérifient ; ils ne réparent pas silencieusement les providers.
- Une release finale doit passer current-Nuvio ABI, projection/materialisation fixed-point, reverse byte-identical rebuild, intégrité des hashes, puis cinq Labs indépendants sur le SHA final.

## Éléments historiques volontairement non repris comme autorité

Les nombres de campagne `46`, `44` ou `96`, les anciens Hub-46 figés, les anciennes branches workbench et les workflows directs de publication de septembre ne sont pas des invariants métier. Les noms de fichiers historiques peuvent rester pour compatibilité, mais leur cardinalité ne gouverne plus le scope courant.

Les preuves anciennes restent de la provenance et ne sont pas automatiquement transférées à des octets Core/ProviderBase rematérialisés.

## Validation encore requise

La parité structurelle ne sera déclarée certifiée qu'après :

1. reconstruction Provider v3 exacte sans dérive de migration ;
2. projection Global+France rematérialisée et fixed-point ;
3. reverse rebuild byte-identical ;
4. census exact-current-byte et non-régression ;
5. finalizer de release avec HEAD Nuvio actuel et intégrité régénérée ;
6. Android TV, Android, iOS, macOS et Windows Labs sur le SHA final.

Le Brain Repair reste volontairement secondaire jusqu'à cette certification.
