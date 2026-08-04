# Niakvio TV officielle

Addon compatible avec le protocole Nuvio/Stremio pour afficher des chaînes gratuites depuis leurs services officiels.

## Catalogues

- `official-tv-all` — toutes les chaînes autorisées
- `official-tv-information` — information
- `official-tv-culture` — culture
- `official-tv-generaliste` — généralistes

Chaque catalogue accepte la propriété `search`.

## Sécurité et sélection

`blacklist.config.json` contrôle les identifiants, noms et domaines interdits. La politique par défaut refuse également toute chaîne non vérifiée ou dépourvue de page officielle.

Le filtrage est appliqué aux réponses `catalog`, `meta` et `stream`. Une chaîne retirée du catalogue ne peut donc pas être appelée directement par son identifiant.

## Développement local

```bash
npm install
npm test
npm start
```

Le manifest local est alors disponible sur :

```text
http://127.0.0.1:7000/manifest.json
```

## Installation dans Nuvio

Nuvio doit recevoir une URL publique HTTPS terminant par `/manifest.json`. Le fichier `render.yaml` et le `Dockerfile` permettent de déployer le service sur Render.

Après déploiement, ajouter dans Nuvio :

```text
https://VOTRE-SERVICE/manifest.json
```

## Limite actuelle

Lorsqu'un éditeur ne fournit pas de flux direct officiellement réutilisable, l'addon expose son lecteur officiel via `externalUrl`. Aucun flux provenant de `fstv.rest` ou de `fstream.org` n'est relayé.
