# Mettre à jour / actualiser NiakVIO, réinstaller et nettoyer le cache Nuvio

[English](../niakvio-update-reinstall-cache.md) · [Retour au README](../../README.fr.md)

Utilisez ce guide lorsque NiakVIO semble conserver un ancien état après une mise à jour : ancienne liste de providers, différences Desktop/Mobile/TV ou disparition de sources après un changement du repository.

> [!TIP]
> **Commencez par l'action native Actualiser / Refresh du repository dans Nuvio.** Le cache et la réinstallation de l'application sont des étapes d'escalade, pas la procédure normale de mise à jour de NiakVIO.

## 1. Option la plus simple — actualiser NiakVIO depuis les paramètres Nuvio

Sur les builds Desktop/Mobile compatibles plugins :

1. ouvrez **Paramètres → Content & Discovery → Plugins** ;
2. ouvrez le repository installé **NiakVIO** ;
3. utilisez l'action / l'icône **Refresh / Actualiser** du repository ;
4. laissez Nuvio retélécharger le manifest et les définitions des providers ;
5. vérifiez que **Enable plugin providers globally** reste activé ;
6. retestez un contenu.

Sur NuvioTV lorsque les réglages plugins sont disponibles, ouvrez **Paramètres → Plugins** (ou **Content Discovery → Plugins** selon l'interface), sélectionnez NiakVIO et utilisez **Refresh repository / Actualiser**.

L'implémentation Nuvio traite explicitement Refresh comme un retéléchargement du manifest et des scrapers/providers. C'est donc la première action à essayer.

### Arrêtez-vous ici si cela fonctionne

Si la liste des providers est à jour et que les streams reviennent, **n'allez pas plus loin**. Inutile de vider le cache ou de réinstaller l'application « par sécurité ».

> [!NOTE]
> Le repository NiakVIO et les feeds StreamBadge sont séparés. Actualiser le plugin met à jour les providers, mais un ancien feed de badges importé peut encore nécessiter une suppression/réimport avec l'URL StreamBadge versionnée actuelle.

## 2. Le repository est à jour mais l'interface semble encore ancienne

1. fermez complètement Nuvio sur l'appareil concerné ;
2. rouvrez l'application ;
3. revenez dans **Plugins** et vérifiez le repository/la liste NiakVIO ;
4. relancez une recherche de streams neuve.

Un repository peut déjà être récent alors qu'un écran existant conserve encore une ancienne requête/réponse.

Avec plusieurs appareils, rendez Desktop/Mobile correct en premier, laissez la synchronisation se stabiliser, puis rouvrez la TV.

## 3. Réinstaller uniquement le repository NiakVIO

Si Refresh échoue ou si le repository reste obsolète :

1. supprimez **NiakVIO** dans **Paramètres → Content & Discovery → Plugins** ;
2. fermez puis rouvrez complètement Nuvio ;
3. ajoutez de nouveau le manifest courant :

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/manifest.json
```

4. activez **Enable plugin providers globally** ;
5. vérifiez que NiakVIO apparaît **une seule fois** ;
6. laissez la synchronisation du compte se propager avant de vérifier la TV.

Si vous utilisez volontairement une autre projection NiakVIO, réinstallez cette même projection. N'empilez pas plusieurs projections pour tenter de résoudre un bug.

## 4. Nettoyer le cache uniquement après échec de Refresh + réinstallation du repository

### Android / Android TV / Google TV

1. ouvrez les **Paramètres système → Applications → Nuvio / NuvioTV** ;
2. choisissez **Forcer l'arrêt** ;
3. ouvrez **Stockage et cache** ;
4. choisissez **Vider le cache** ;
5. rouvrez Nuvio puis actualisez de nouveau NiakVIO.

> [!CAUTION]
> **Effacer les données / le stockage** est beaucoup plus destructeur : état local et identifiants peuvent disparaître. Ne l'utilisez pas pour une mise à jour normale du plugin.

### macOS

Fermez Nuvio :

```bash
osascript -e 'quit app "Nuvio"' 2>/dev/null || true
pkill -x Nuvio 2>/dev/null || true
```

Prévisualisez les caches correspondants :

```bash
for p in   "$HOME/Library/Caches/"*Nuvio*   "$HOME/Library/Caches/"*nuvio*   "$HOME/Library/Caches/com.nuvio.media"; do
  [ -e "$p" ] && printf '%s\n' "$p"
done
```

Supprimez uniquement ces caches :

```bash
for p in   "$HOME/Library/Caches/"*Nuvio*   "$HOME/Library/Caches/"*nuvio*   "$HOME/Library/Caches/com.nuvio.media"; do
  [ -e "$p" ] && rm -rf -- "$p"
done
```

Nettoyage optionnel des sous-dossiers de cache d'Application Support :

```bash
for root in   "$HOME/Library/Application Support/Nuvio"   "$HOME/Library/Application Support/com.nuvio.media"; do
  [ -d "$root" ] || continue
  find "$root" -type d \( -name Cache -o -name Caches -o -name GPUCache -o -name 'Code Cache' \) -prune -exec rm -rf -- {} +
done
```

Le dossier principal Application Support reste volontairement intact.

### Windows — PowerShell

Fermez Nuvio :

```powershell
Get-Process Nuvio -ErrorAction SilentlyContinue | Stop-Process -Force
```

Repérez les racines existantes :

```powershell
$roots = @(
  "$env:LOCALAPPDATA\Nuvio",
  "$env:APPDATA\Nuvio",
  "$env:LOCALAPPDATA\com.nuvio.media",
  "$env:APPDATA\com.nuvio.media"
) | Where-Object { Test-Path $_ }
```

Prévisualisez les dossiers de cache :

```powershell
$cacheNames = @('Cache', 'Caches', 'Code Cache', 'GPUCache')
if ($roots) {
  Get-ChildItem -Path $roots -Directory -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object { $cacheNames -contains $_.Name } |
    Select-Object -ExpandProperty FullName
}
```

Supprimez uniquement ces dossiers :

```powershell
if ($roots) {
  Get-ChildItem -Path $roots -Directory -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object { $cacheNames -contains $_.Name } |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}
```

### iPhone / iPad

iOS ne propose pas le même bouton Vider le cache qu'Android. Utilisez cet ordre :

1. actualisez NiakVIO dans Plugins ;
2. fermez complètement Nuvio ;
3. rouvrez et retestez ;
4. supprimez/réinstallez le repository NiakVIO si nécessaire ;
5. ne réinstallez l'application Nuvio entière qu'en dernier recours.

## 5. La TV reste différente de Desktop/Mobile

Utilisez Desktop/Mobile comme surface de gestion la plus simple :

1. actualisez ou réinstallez NiakVIO là en premier ;
2. laissez la synchronisation compte/plugin se stabiliser ;
3. fermez complètement NuvioTV ;
4. rouvrez la TV ;
5. vérifiez **Paramètres → Plugins** et l'activation globale des providers.

Si seule la TV reste obsolète, forcez l'arrêt de NuvioTV et videz **uniquement le cache**, puis rouvrez. N'ajoutez pas une deuxième copie du repository.

## 6. Réinitialisation complète de l'application — dernier recours

Ne réinstallez Nuvio ou n'effacez son stockage que lorsque :

- Refresh du repository échoue plusieurs fois ;
- supprimer/réinstaller NiakVIO ne corrige rien ;
- le nettoyage du cache ne change rien ;
- le problème concerne largement Nuvio et pas un seul provider upstream.

La panne d'un seul provider ne signifie pas que le repository NiakVIO ou le cache Nuvio est cassé.

## Vérification finale

Après récupération :

- NiakVIO apparaît une seule fois ;
- la bonne projection/manifest est installée ;
- les plugin providers sont activés globalement ;
- la liste courante des providers est visible ;
- un contenu compatible retourne des sources NiakVIO ;
- les autres appareils convergent après synchronisation.

Pour une première installation : **[Installer Nuvio et NiakVIO](nuvio-installation.md)**.
