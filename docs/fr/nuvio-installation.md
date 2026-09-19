# Installer Nuvio et NiakVIO

[English](../nuvio-installation.md) · [Retour au README](../../README.fr.md)

Ce guide couvre une installation propre de **Nuvio + NiakVIO** sur Desktop, Mobile et Android TV.

> [!TIP]
> Le plus simple est de configurer le compte et les plugins depuis **Desktop ou Mobile en premier**, puis d’ouvrir NuvioTV et de laisser la configuration du compte se synchroniser.

## 1. Installer un client Nuvio officiel

Utilisez les projets Nuvio officiels :

- **Android TV / Google TV :** [releases NuvioTV](https://github.com/NuvioMedia/NuvioTV/releases/latest)
- **Android / iOS :** [NuvioMobile](https://github.com/NuvioMedia/NuvioMobile)
- **Windows / macOS :** [releases NuvioDesktop](https://github.com/NuvioMedia/NuvioDesktop/releases)

> [!NOTE]
> Nuvio Desktop est actuellement un client alpha. L’interface et le stockage local peuvent encore évoluer entre les versions.

### APK Android TV / Google TV

Si NuvioTV n’est pas disponible sur votre store, ouvrez la page de release GitHub officielle depuis la TV ou téléchargez l’APK sur un autre appareil puis transférez-le.

Pour la plupart des TV, l’**APK universel** est le choix le plus simple lorsque vous ne connaissez pas l’architecture CPU de l’appareil :

```text
app-full-universal-release.apk
```

Un APK spécifique à l’architecture peut être plus léger, mais ne l’utilisez que si vous connaissez l’architecture de la TV.

Si Android demande l’autorisation d’installer des applications inconnues, activez-la uniquement pour le navigateur ou gestionnaire de fichiers utilisé, installez NuvioTV, puis désactivez cette permission si vous n’en avez plus besoin.

## 2. Se connecter et activer la synchronisation du compte

Créez ou connectez-vous à votre compte Nuvio sur Mobile/Desktop. Sur TV, utilisez l’écran de connexion au compte ou le QR code lorsqu’il est proposé.

Le compte est important car il permet à Nuvio de synchroniser les éléments de configuration pris en charge entre vos appareils. Cela évite notamment de saisir de longues URLs de manifest avec une télécommande.

Si Nuvio propose les expériences **Essentiel** et **Avancé**, le mode Avancé est pratique pour accéder directement aux réglages plugins/addons et aux diagnostics. Vous pourrez le modifier plus tard.

## 3. Stack Nuvio recommandée

Gardez une stack simple : **un outil par rôle**.

| Rôle | Recommandé |
| --- | --- |
| Providers | **NiakVIO** |
| Métadonnées / catalogue | **Ultra MAX** |
| Sous-titres | **SubSense** |
| Favoris / suivi | **SIMKL** |

Voir la [Configuration Nuvio recommandée](../../README.fr.md#-configuration-nuvio-recommandée) dans le README.

> [!TIP]
> Évitez d’installer plusieurs packs providers qui se recouvrent, sauf si vous les testez volontairement. Les doublons rendent la liste des sources moins lisible et compliquent fortement le diagnostic.

## 4. Installer NiakVIO depuis Desktop ou Mobile

Pour la plupart des utilisateurs, installez le **manifest général** :

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/manifest.json
```

Puis dans Nuvio :

1. Ouvrez **Paramètres / Settings**.
2. Ouvrez **Content & Discovery**.
3. Ouvrez **Plugins**.
4. Dans **Add repository / ADD REPOSITORY**, collez l’URL NiakVIO dans **Plugin manifest URL**.
5. Choisissez **Install Plugin Repository**.
6. Vérifiez que **Enable plugin providers globally** est activé.
7. Confirmez que **NiakVIO** apparaît dans les repositories installés et que ses providers sont listés.

> [!IMPORTANT]
> Si Nuvio affiche **TMDB API key missing**, configurez TMDB dans les paramètres Nuvio. Le matching provider peut dépendre des métadonnées TMDB pour identifier correctement un film, une série, une saison ou un épisode.

### Autres projections NiakVIO

N’installez qu’**une seule** projection sauf besoin précis.

| Projection | Manifest |
| --- | --- |
| Général | `https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/manifest.json` |
| Orienté français | `https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/vf/manifest.json` |
| Général sans providers orientés anime | `https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/no-anime/manifest.json` |
| Français sans providers orientés anime | `https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/vf-no-anime/manifest.json` |

Plus de détails : [guide manifest](how-to-add-manifest.md).

## 5. Ouvrir NuvioTV et vérifier la synchronisation

Quand le plugin est correct sur Desktop/Mobile :

1. Fermez complètement NuvioTV s’il est déjà ouvert.
2. Rouvrez NuvioTV connecté au même compte.
3. Ouvrez **Settings → Content Discovery → Plugins**.
4. Confirmez que NiakVIO est présent et que les providers sont activés globalement.
5. Comparez la liste des providers au manifest NiakVIO actuel plutôt qu’à un ancien nombre figé.

NuvioTV peut également proposer **Manage from phone**. Scannez le QR code, gérez le repository depuis le téléphone, puis confirmez la modification sur la TV si Nuvio le demande.

## 6. Vérification fonctionnelle rapide

Choisissez un film, une série ou un anime compatible et ouvrez la liste des sources.

Une installation saine doit montrer :

- le repository NiakVIO dans la liste des plugins ;
- les providers NiakVIO sous le repository ;
- les plugin providers activés globalement ;
- les sources NiakVIO pour les contenus compatibles une fois la recherche terminée.

La recherche provider n’est pas instantanée. Laissez quelques secondes aux providers avant de conclure que le plugin est vide.

## 7. Si le plugin paraît obsolète ou incohérent

Symptômes typiques :

- nombre de providers différent du dépôt actuel ;
- providers présents sur Mobile/Desktop mais absents sur TV ;
- plugin qui fonctionne, disparaît puis revient ;
- anciens noms de providers ou métadonnées de repository après une mise à jour.

N’ajoutez **pas** plusieurs fois le même manifest. Utilisez plutôt la procédure de récupération dédiée :

➡️ **[Mettre à jour, réinstaller NiakVIO et vider le cache Nuvio](niakvio-update-reinstall-cache.md)**

L’ordre recommandé est **Desktop/Mobile d’abord, TV ensuite**, puis réinstallation propre du plugin depuis Desktop/Mobile et contrôle de la synchronisation TV.
