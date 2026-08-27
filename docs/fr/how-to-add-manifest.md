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

À utiliser si vous souhaitez uniquement la sélection orientée français, sur la base d'informations de langue explicitement déclarées par les providers ou les flux.

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/vf/manifest.json
```

### Manifest VO sans anime

Copie du manifest général avec retrait des providers clairement orientés anime. Un provider est exclu s'il déclare **uniquement `anime`** dans ses types, ou si son **id/nom contient `anim`** (sans tenir compte de la casse). Un provider mixte film/série/anime reste présent si son id/nom n'est pas orienté anime.

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/no-anime/manifest.json
```

### Manifest VF sans anime

Le même filtre déterministe est appliqué à la copie du manifest francophone.

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/vf-no-anime/manifest.json
```

> Installer plusieurs manifests qui se recoupent est généralement inutile. Choisissez la projection correspondant à ce que vous voulez afficher dans Nuvio.

## Nuvio Mobile et Nuvio Desktop

Chemin actuel dans l'interface Nuvio :

1. Ouvrez **Paramètres**.
2. Ouvrez **Contenu et découverte**.
3. Ouvrez **Plugins**.
4. Dans **AJOUTER UN DÉPÔT**, collez l'URL du manifest NiakVIO dans **URL du manifeste du plugin**.
5. Sélectionnez **Installer le dépôt de plugin**.
6. Vérifiez que **Activer les fournisseurs de plugins** est activé.
7. Vérifiez que NiakVIO apparaît dans **DÉPÔTS INSTALLÉS** et que ses providers sont listés.

Si Nuvio affiche **TMDB API key missing**, configurez TMDB dans les réglages Nuvio. Certains providers utilisent les métadonnées TMDB pour assurer le bon matching film / série / épisode.

## NuvioTV

Chemin actuel dans NuvioTV :

1. Ouvrez **Paramètres**.
2. Ouvrez **Contenu et découverte**.
3. Ouvrez **Plugins**.
4. Sélectionnez **Ajouter un dépôt**.
5. Collez l'URL du manifest NiakVIO.
6. Sélectionnez **Ajouter**.
7. Vérifiez que **Activer les fournisseurs de plugins globalement** est activé.
8. Vérifiez que le repository NiakVIO et ses providers apparaissent dans la liste.

NuvioTV propose également **Gérer depuis le téléphone** : ouvrez cette option, scannez le QR code, puis ajoutez ou supprimez le repository depuis votre téléphone. Confirmez ensuite la modification sur la TV si NuvioTV le demande.

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
