# Installation — v5.13.1

1. Remplace les fichiers du dépôt par ceux de cette archive en conservant le dossier `.github`.
2. Commit et pousse sur `main`.
3. Lance **Check all manifests and publish Nuvio providers** en mode `deep`.
4. Le nouveau rapport doit afficher `"schema_version": 63`.

## Résultat attendu

- une seule requête représentative par provider ;
- un résultat sain unique suffit aux gates runtime correspondants et active immédiatement un nouveau SHA ;
- les descriptions et types des trois manifests sont fusionnés avant le choix de la fixture ;
- une description comme `Films, Séries et Animes en VF et VOSTFR` publie `movie`, `tv` et `anime`, même si une variante amont ne déclare que `anime` ;
- les providers VF sont placés en premier, par résolution puis score ;
- les providers VOSTFR arrivent ensuite ; le runtime prime sur une description générale mentionnant à la fois VF et VOSTFR ;
- les autres providers francophones suivent ;
- les providers VO/autres langues sont classés d’abord par score de santé/qualité, puis par résolution ;
- toute réponse HTTP réelle d’un serveur provider compte comme accès serveur, tandis que DNS, connexion, TLS et timeout restent des échecs ;
- un serveur accessible ne suffit pas : le score éditorial agrégé doit atteindre 5 ;
- des sous-titres optionnels injoignables ne bloquent pas un stream principal avec audio accepté ;
- aucun torrent, magnet ou P2P n’est publié.

### Variantes linguistiques

- Manifest général : `/manifest.json`
- VF uniquement : `/vf/manifest.json`
