# Mettre à jour, réinstaller NiakVIO et vider le cache Nuvio

[English](../niakvio-update-reinstall-cache.md) · [Retour au README](../../README.fr.md)

Utilisez cette procédure lorsque NiakVIO se comporte de façon incohérente après une mise à jour ou lorsque Nuvio semble conserver un ancien état du plugin.

Symptômes typiques :

- le nombre de providers ne correspond plus au dépôt actuel ;
- Desktop/Mobile et TV affichent des listes de providers différentes ;
- des providers disparaissent puis reviennent entre deux lancements ;
- d’anciens noms de providers ou métadonnées de repository restent visibles ;
- le refresh du repository ne met pas le client à jour ;
- le plugin est installé mais les sources n’apparaissent plus comme prévu.

> [!IMPORTANT]
> Suivez la séquence ci-dessous avant de réinstaller complètement l’application Nuvio. Le but est de réinitialiser **le plugin + le cache** tout en conservant autant que possible le compte, les profils et les données normales de l’application.

## Ordre de récupération recommandé

Si plusieurs appareils sont concernés, gardez cet ordre :

1. **Supprimer NiakVIO sur Desktop/Mobile en premier.**
2. Supprimer NiakVIO sur la TV s’il y est encore présent ou si la suppression ne s’est pas synchronisée.
3. **Forcer l’arrêt complet de Nuvio** sur chaque appareil concerné.
4. **Vider le cache Nuvio** sur chaque appareil concerné.
5. Rouvrir **Desktop ou Mobile en premier**.
6. Réinstaller NiakVIO depuis Desktop/Mobile avec le manifest actuel.
7. Vérifier le repository et la liste des providers sur Desktop/Mobile.
8. Ouvrir ensuite seulement NuvioTV.
9. Vérifier que la TV a bien récupéré l’état synchronisé du plugin et que sa liste correspond au dépôt actuel.

Cet ordre évite de prendre un état TV obsolète comme référence pendant la resynchronisation du compte.

## 1. Supprimer le repository du plugin

Sur Desktop/Mobile :

1. Ouvrez **Settings → Content & Discovery → Plugins**.
2. Repérez **NiakVIO** dans les repositories installés.
3. Supprimez/désinstallez le repository NiakVIO.
4. Si plusieurs appareils Desktop/Mobile utilisent le même compte, laissez le compte se synchroniser avant de poursuivre.

Sur TV :

1. Ouvrez **Settings → Content Discovery → Plugins**.
2. Supprimez NiakVIO s’il apparaît encore.
3. Si la TV propose **Manage from phone**, vous pouvez également supprimer le repository depuis le téléphone puis confirmer la modification sur la TV.

N’installez pas une deuxième copie du même manifest par-dessus un état obsolète.

## 2. Forcer l’arrêt de Nuvio et vider son cache

### Android / Android TV / Google TV

Passez par les paramètres système :

1. Ouvrez **Paramètres → Applications → Nuvio / NuvioTV**.
2. Choisissez **Forcer l’arrêt**.
3. Ouvrez **Stockage et cache**.
4. Choisissez **Vider le cache**.

> [!CAUTION]
> N’utilisez **pas** **Effacer les données / Effacer le stockage** comme étape normale de dépannage. Cette action est beaucoup plus destructive et peut supprimer l’état local, des profils ou des identifiants. Gardez-la uniquement comme reset complet volontaire en dernier recours.

Un simple redémarrage de l’appareil ne vide pas forcément le cache applicatif. Utilisez bien l’action **Vider le cache**.

### macOS — Terminal

Le client Desktop officiel utilise actuellement l’identifiant d’application `com.nuvio.media`. Les commandes ci-dessous ferment d’abord Nuvio, affichent les chemins de cache détectés, puis suppriment uniquement ces caches.

**1. Fermer complètement Nuvio :**

```bash
osascript -e 'quit app "Nuvio"' 2>/dev/null || true
pkill -x Nuvio 2>/dev/null || true
```

**2. Prévisualiser les dossiers de cache correspondant à Nuvio :**

```bash
for p in \
  "$HOME/Library/Caches/"*Nuvio* \
  "$HOME/Library/Caches/"*nuvio* \
  "$HOME/Library/Caches/com.nuvio.media"; do
  [ -e "$p" ] && printf '%s\n' "$p"
done
```

**3. Supprimer uniquement ces dossiers de cache :**

```bash
for p in \
  "$HOME/Library/Caches/"*Nuvio* \
  "$HOME/Library/Caches/"*nuvio* \
  "$HOME/Library/Caches/com.nuvio.media"; do
  [ -e "$p" ] && rm -rf -- "$p"
done
```

**4. Optionnel : supprimer les sous-dossiers de cache présents dans Application Support sans supprimer le dossier de données principal :**

```bash
for root in \
  "$HOME/Library/Application Support/Nuvio" \
  "$HOME/Library/Application Support/com.nuvio.media"; do
  [ -d "$root" ] || continue
  find "$root" -type d \( \
    -name Cache -o \
    -name Caches -o \
    -name GPUCache -o \
    -name 'Code Cache' \
  \) -prune -exec rm -rf -- {} +
done
```

Ces commandes laissent volontairement intact le dossier principal de données Nuvio dans Application Support.

### Windows — PowerShell

Ouvrez **PowerShell**. Les commandes suivantes ferment Nuvio, détectent les racines de données Nuvio existantes, affichent les dossiers de cache puis suppriment uniquement ces caches.

**1. Fermer Nuvio :**

```powershell
Get-Process Nuvio -ErrorAction SilentlyContinue | Stop-Process -Force
```

**2. Construire la liste des chemins Nuvio réellement présents :**

```powershell
$roots = @(
  "$env:LOCALAPPDATA\Nuvio",
  "$env:APPDATA\Nuvio",
  "$env:LOCALAPPDATA\com.nuvio.media",
  "$env:APPDATA\com.nuvio.media"
) | Where-Object { Test-Path $_ }
```

**3. Prévisualiser les dossiers de cache :**

```powershell
$cacheNames = @('Cache', 'Caches', 'Code Cache', 'GPUCache')

if ($roots) {
  Get-ChildItem -Path $roots -Directory -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object { $cacheNames -contains $_.Name } |
    Select-Object -ExpandProperty FullName
}
```

**4. Supprimer uniquement ces dossiers de cache :**

```powershell
if ($roots) {
  Get-ChildItem -Path $roots -Directory -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object { $cacheNames -contains $_.Name } |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}
```

Cette procédure ne supprime **pas volontairement** tout le profil Nuvio ni la racine complète des données applicatives.

### iPhone / iPad

iOS ne propose pas de bouton standard **Vider le cache** comparable à Android.

Utilisez cet ordre :

1. supprimez le repository NiakVIO ;
2. fermez complètement Nuvio depuis le sélecteur d’applications ;
3. rouvrez Nuvio et laissez le compte se synchroniser ;
4. réinstallez NiakVIO depuis Mobile/Desktop.

Ne réinstallez toute l’application Nuvio que si la suppression/réinstallation du plugin et la resynchronisation du compte ne corrigent pas l’état obsolète.

## 3. Réinstaller NiakVIO depuis Desktop ou Mobile

Rouvrez **Desktop ou Mobile en premier** puis installez le manifest général actuel :

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/manifest.json
```

Dans Nuvio :

1. ouvrez **Settings → Content & Discovery → Plugins** ;
2. choisissez **Add repository / ADD REPOSITORY** ;
3. collez le manifest dans **Plugin manifest URL** ;
4. choisissez **Install Plugin Repository** ;
5. activez **Enable plugin providers globally** ;
6. vérifiez que NiakVIO apparaît **une seule fois**.

Si vous utilisez volontairement une autre projection NiakVIO, réinstallez cette projection à la place du manifest général. N’empilez pas plusieurs projections NiakVIO qui se recouvrent sauf si vous les testez volontairement.

## 4. Rouvrir la TV en dernier

Quand Desktop/Mobile est correct :

1. rouvrez NuvioTV ;
2. laissez l’état du compte/plugin se synchroniser ;
3. ouvrez **Settings → Content Discovery → Plugins** ;
4. vérifiez que NiakVIO apparaît **une seule fois** ;
5. vérifiez que les plugin providers sont activés globalement ;
6. comparez la liste des providers au dépôt actuel.

Si la TV affiche encore l’ancien état, forcez à nouveau l’arrêt de NuvioTV et videz son cache Android, puis rouvrez-la **sans réinstaller une deuxième copie du repository**.

## 5. Vérifier la récupération

Contrôlez les points suivants :

- NiakVIO apparaît une seule fois sur Desktop/Mobile ;
- NiakVIO apparaît une seule fois sur TV ;
- le même compte est utilisé sur tous les appareils ;
- les listes providers sont cohérentes avec le manifest actuel ;
- les plugin providers sont activés globalement ;
- les contenus compatibles affichent des sources NiakVIO une fois la recherche terminée.

> [!TIP]
> Ne vous fiez pas à un ancien nombre figé de providers. Le catalogue maintenu NiakVIO peut évoluer. Le repository/manifest actuel fait foi.

## 6. Toujours cassé ?

Avant de réinstaller complètement le client Nuvio, vérifiez :

- que l’URL du manifest est correcte et accessible ;
- que vous n’avez pas installé plusieurs projections NiakVIO qui se recouvrent ;
- que le même compte Nuvio est utilisé sur Desktop/Mobile/TV ;
- que TMDB est configuré si Nuvio signale une clé TMDB manquante ;
- que le problème ne concerne pas seulement un provider alors que le reste de NiakVIO fonctionne.

Un provider upstream peut tomber temporairement en panne même si l’installation du plugin est parfaitement saine.

Pour une première installation, voir **[Installer Nuvio et NiakVIO](nuvio-installation.md)**.
