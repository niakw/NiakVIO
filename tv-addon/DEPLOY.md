# Déploiement

## Render

1. Créer un nouveau Blueprint Render depuis ce dépôt.
2. Sélectionner la branche contenant `render.yaml`.
3. Valider le service `niakvio-official-tv`.
4. Attendre que `/manifest.json` réponde en HTTPS.
5. Ajouter cette URL dans Nuvio.

Le port est fourni automatiquement par Render via la variable `PORT`. Le serveur écoute sur `0.0.0.0`.

## Vérifications

```bash
curl -f https://VOTRE-SERVICE/manifest.json
curl -f https://VOTRE-SERVICE/catalog/tv/official-tv-all.json
```

Le manifest doit annoncer les quatre catalogues et les ressources `catalog`, `meta` et `stream`.
