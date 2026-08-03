# Sources amont et sauvegardes

Le dépôt consolide trois sources communautaires principales.

## Gowaru

- Dépôt : `https://github.com/Gowaru/gowaru-nuvio-providers`
- Manifest : `https://raw.githubusercontent.com/Gowaru/gowaru-nuvio-providers/refs/heads/main/manifest.json`
- Apport principal : providers VF, VOSTFR et anime francophone.

## All-in-One-Nuvio

- Dépôt canonique : `https://github.com/NuvioPlugin/All-in-One-Nuvio`
- Manifest principal : `https://raw.githubusercontent.com/NuvioPlugin/All-in-One-Nuvio/refs/heads/main/manifest.json`
- Ancien miroir accepté : `https://raw.githubusercontent.com/D3adlyRocket/All-in-One-Nuvio/refs/heads/main/manifest.json`
- Apport principal : providers internationaux et correctifs récents.

## Yoru

- Dépôt : `https://github.com/yoruix/nuvio-providers`
- Manifest : `https://raw.githubusercontent.com/yoruix/nuvio-providers/refs/heads/main/manifest.json`
- Apport principal : providers exclusifs et variantes complémentaires.

## Stratégie de repli

Pour chacune des trois sources, le workflow profond conserve les **deux dernières générations complètes** du manifest et de ses fichiers providers dans `upstream-lkg/`.

L’ordre de récupération est le suivant :

1. manifest et provider actuels du dépôt amont ;
2. dernière sauvegarde amont valide ;
3. sauvegarde amont précédente ;
4. provider fonctionnel déjà publié dans ce dépôt.

Un manifest vide, dupliqué, fortement tronqué ou dont trop de fichiers sont invalides n’écrase jamais une sauvegarde saine. Les snapshots ne sont finalisés qu’après la réussite du cycle profond. Les providers déjà publiés restent le dernier repli fonctionnel, même lorsqu’aucune nouvelle sauvegarde amont ne peut être créée.

## Règles

1. Ne jamais activer deux copies du même provider.
2. Ne jamais remplacer un provider publié par une variante qui régresse.
3. Exclure les providers et protocoles P2P.
4. Conserver les anciennes variantes sous forme de sauvegardes bornées, pas indéfiniment.
5. Publier les fichiers providers avant le manifest qui les référence.
