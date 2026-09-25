# Update / refresh NiakVIO, reinstall and clear Nuvio cache

[Français](fr/niakvio-update-reinstall-cache.md) · [Back to README](../README.md)

Use this guide when NiakVIO looks stale after an update: an old provider list remains visible, Desktop/Mobile and TV disagree, or sources disappear after a repository change.

> [!TIP]
> **Start with Nuvio's own repository Refresh action.** Cache deletion and app reinstallation are escalation steps, not the normal way to update NiakVIO.

## 1. Easiest option — Refresh NiakVIO from Nuvio settings

On plugin-enabled Desktop/Mobile builds:

1. open **Settings → Content & Discovery → Plugins**;
2. open the installed **NiakVIO** repository;
3. press the **Refresh** action/icon for that repository;
4. let Nuvio re-download the manifest and provider definitions;
5. confirm **Enable plugin providers globally** is still enabled;
6. test a title again.

On NuvioTV with plugin settings available, open **Settings → Plugins** (or **Content Discovery → Plugins** depending on the UI), select NiakVIO and use **Refresh repository**.

The Nuvio plugin implementation explicitly treats Refresh as a repository re-download of the manifest and scrapers/providers. This should therefore be the first update action.

### Stop here when it works

If the provider list is current and streams return again, **do nothing else**. Do not clear cache or reinstall the app “just in case”.

> [!NOTE]
> NiakVIO's plugin repository and StreamBadge feeds are separate. Repository Refresh updates providers, but an old imported StreamBadge feed may still need to be removed/re-imported with the current versioned badge URL.

## 2. Refresh succeeded but the UI still looks stale

1. fully close Nuvio on the affected device;
2. reopen it;
3. return to **Plugins** and verify the NiakVIO repository/provider list;
4. retry a title with a fresh stream lookup.

A repository can already be current while an existing screen still shows an older request/result state.

When several devices use the same account, make Desktop/Mobile correct first, let synchronization settle, then reopen TV.

## 3. Reinstall only the NiakVIO repository

If Refresh itself fails or the repository remains stale:

1. remove **NiakVIO** from **Settings → Content & Discovery → Plugins**;
2. fully close and reopen Nuvio;
3. add the current manifest again:

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/manifest.json
```

4. enable **Enable plugin providers globally**;
5. confirm NiakVIO appears exactly once;
6. let account synchronization propagate before checking TV.

If you intentionally use another NiakVIO projection, reinstall that same projection instead. Do not stack overlapping projections as a troubleshooting method.

## 4. Clear cache only after Refresh and repository reinstall fail

### Android / Android TV / Google TV

1. open system **Settings → Apps → Nuvio / NuvioTV**;
2. choose **Force stop**;
3. open **Storage & cache**;
4. choose **Clear cache**;
5. reopen Nuvio and Refresh NiakVIO again.

> [!CAUTION]
> **Clear storage / Clear data** is much more destructive and may remove app state or credentials. Do not use it for a routine plugin update.

### macOS

Stop Nuvio:

```bash
osascript -e 'quit app "Nuvio"' 2>/dev/null || true
pkill -x Nuvio 2>/dev/null || true
```

Preview matching cache folders:

```bash
for p in   "$HOME/Library/Caches/"*Nuvio*   "$HOME/Library/Caches/"*nuvio*   "$HOME/Library/Caches/com.nuvio.media"; do
  [ -e "$p" ] && printf '%s\n' "$p"
done
```

Delete only those cache folders:

```bash
for p in   "$HOME/Library/Caches/"*Nuvio*   "$HOME/Library/Caches/"*nuvio*   "$HOME/Library/Caches/com.nuvio.media"; do
  [ -e "$p" ] && rm -rf -- "$p"
done
```

Optional cache-only cleanup inside Application Support:

```bash
for root in   "$HOME/Library/Application Support/Nuvio"   "$HOME/Library/Application Support/com.nuvio.media"; do
  [ -d "$root" ] || continue
  find "$root" -type d \( -name Cache -o -name Caches -o -name GPUCache -o -name 'Code Cache' \) -prune -exec rm -rf -- {} +
done
```

The main Application Support directory is intentionally left intact.

### Windows — PowerShell

Stop Nuvio:

```powershell
Get-Process Nuvio -ErrorAction SilentlyContinue | Stop-Process -Force
```

Find existing roots:

```powershell
$roots = @(
  "$env:LOCALAPPDATA\Nuvio",
  "$env:APPDATA\Nuvio",
  "$env:LOCALAPPDATA\com.nuvio.media",
  "$env:APPDATA\com.nuvio.media"
) | Where-Object { Test-Path $_ }
```

Preview cache-only folders:

```powershell
$cacheNames = @('Cache', 'Caches', 'Code Cache', 'GPUCache')
if ($roots) {
  Get-ChildItem -Path $roots -Directory -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object { $cacheNames -contains $_.Name } |
    Select-Object -ExpandProperty FullName
}
```

Delete only those cache folders:

```powershell
if ($roots) {
  Get-ChildItem -Path $roots -Directory -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object { $cacheNames -contains $_.Name } |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}
```

### iPhone / iPad

iOS does not expose Android's per-app Clear cache button. Escalate in this order:

1. Refresh NiakVIO in Plugins;
2. fully close Nuvio;
3. reopen and retry;
4. remove/reinstall the NiakVIO repository if necessary;
5. reinstall the whole Nuvio app only as a final app-level reset.

## 5. TV still differs from Desktop/Mobile

Use Desktop/Mobile as the easiest management surface:

1. Refresh or reinstall NiakVIO there first;
2. let account/plugin synchronization settle;
3. fully close NuvioTV;
4. reopen TV;
5. verify **Settings → Plugins** and global provider enablement.

If only TV remains stale, force-stop NuvioTV and clear **cache only**, then reopen it. Do not add a second repository copy.

## 6. Full application reset — last resort

Only consider reinstalling Nuvio itself or clearing application storage when:

- repository Refresh repeatedly fails;
- removing/reinstalling NiakVIO does not repair the state;
- cache-only cleanup does not help;
- the problem affects Nuvio broadly, not one upstream provider.

A single provider failing is not evidence that the NiakVIO repository or Nuvio cache is broken.

## Verification checklist

After recovery:

- NiakVIO appears exactly once;
- the expected manifest/projection is installed;
- plugin providers are enabled globally;
- the current provider list is visible;
- compatible titles return NiakVIO source rows;
- other devices converge after synchronization.

For a first installation, see **[Install Nuvio and NiakVIO](nuvio-installation.md)**.
