# Retention des census sharded numérotés — 7 novembre 2026

Le commit historique `a9ae80a9ac29d00ef9f608165962366f7d330182` contient toutes les données initiales. Le nettoyage ne réécrit ni n'efface l'historique Git : il retire uniquement les snapshots numérotés excédentaires de l'arbre `main` courant pour alléger les checkouts et la CI.

| Catégorie | Avant | Après sur main |
| --- | ---: | ---: |
| Snapshots numérotés | 1407 | 141 |
| Octets des snapshots numérotés | 636194842 | 71264347 |
| Octets archivés dans l'historique (sortis du tree HEAD) | 0 | 564930495 |

**Index de récupération :** `automation/provider-census-sharded-archive-index.json` contient chaque chemin retiré, le SHA exact du blob et le commit historique. Commande : `git show a9ae80a9ac29d00ef9f608165962366f7d330182:automation/provider-census-sharded-<run-id>.json` (récupérer l'ancien commit si le clone est shallow). GitHub conserve les blobs par l'historique de `main`.

Règle de sélection : 64 runs les plus récents, quatre premiers, un sentinelle tous les 30 runs, 30 plus volumineux et toutes les références explicites trouvées dans les consommateurs métier. Les fichiers `latest`, les preuves consolidées, manifests, données de domaine, mémoire Brain, rapports et artifacts CI sont **intouchés**. Les workflows continuent à publier un snapshot horodaté par run et un artifact ; cette opération ne modifie pas la collecte future.

Le test `tests/provider_census_sharded_archive_retention_test.py` garantit l'intégrité de l'index et de la sélection de HEAD. Les blobs historiques demeurent des données diagnostiques ; leur existence ne prouve pas que les flux sont lisibles, que la bonne saison est sélectionnée, ni que le Brain a réparé un provider. Tout nouveau lecteur métier d'un run historique doit lire son SHA exact, jamais substituer `latest` silencieusement.
