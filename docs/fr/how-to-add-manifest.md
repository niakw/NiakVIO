# Ajouter un manifest NiakVIO dans Nuvio

[English](../how-to-add-manifest.md) · [Retour au README](../../README.fr.md)

NiakVIO s'installe dans Nuvio comme un **manifest de repository de plugins**.

## Quel manifest utiliser ?

### Manifest général — recommandé

À utiliser par défaut.

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/manifest.json
```

### Manifest francophone

À utiliser si vous souhaitez uniquement la sélection orientée français / sous-titres français.

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/vf/manifest.json
```

> Installer les deux est généralement inutile car ils se recoupent. Pour la majorité des utilisateurs, installez uniquement le **manifest général**.

## Nuvio Mobile et Nuvio Desktop

Chemin actuel dans l'interface Nuvio :

1. Ouvrez **Settings**.
2. Ouvrez **Content & Discovery**.
3. Ouvrez **Plugins**.
4. Dans **ADD REPOSITORY**, collez l'URL du manifest NiakVIO dans **Plugin manifest URL**.
5. Sélectionnez **Install Plugin Repository**.
6. Vérifiez que **Enable plugin providers globally** est activé.
7. Vérifiez que NiakVIO apparaît dans **INSTALLED REPOSITORIES** et que ses providers sont listés.

Si Nuvio affiche **TMDB API key missing**, configurez TMDB dans les réglages Nuvio. Certains providers utilisent les métadonnées TMDB pour assurer le bon matching film / série / épisode.

## NuvioTV

Chemin actuel dans NuvioTV :

1. Ouvrez **Settings**.
2. Ouvrez **Content Discovery**.
3. Ouvrez **Plugins**.
4. Sélectionnez **Add repository**.
5. Collez l'URL du manifest NiakVIO.
6. Sélectionnez **Add**.
7. Vérifiez que **Enable plugin providers globally** est activé.
8. Vérifiez que le repository NiakVIO et ses providers apparaissent dans la liste.

NuvioTV propose également **Manage from phone** : ouvrez cette option, scannez le QR code, puis ajoutez ou supprimez le repository depuis votre téléphone. Confirmez ensuite la modification sur la TV si NuvioTV le demande.

## Vérifier que NiakVIO est actif

Une installation correcte doit afficher :

- NiakVIO dans la liste des repositories installés ;
- les providers NiakVIO sous le repository ;
- les plugins activés globalement ;
- les sources NiakVIO dans le sélecteur de streams sur les contenus compatibles.

Si le repository est installé mais qu'aucun stream n'apparaît, commencez par rafraîchir le repository, puis vérifiez l'activation globale des plugins et l'activation du provider concerné.

## Mises à jour

Il n'est pas nécessaire de remplacer l'URL à chaque mise à jour de NiakVIO. Les URLs de manifest restent stables.

Utilisez l'action **Refresh repository** de Nuvio si vous voulez forcer une actualisation immédiate.
