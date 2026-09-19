# Update, refresh, reinstall NiakVIO and clear Nuvio cache

[Français](fr/niakvio-update-reinstall-cache.md) · [Back to README](../README.md)

Use this procedure when NiakVIO behaves inconsistently after an update or when Nuvio appears to keep stale plugin state.

Typical symptoms:

- the provider count does not match the current repository;
- Desktop/Mobile and TV show different provider lists;
- providers disappear and reappear between launches;
- old provider names or old repository metadata remain visible;
- refreshing the repository does not update the client;
- the plugin is installed but sources no longer appear as expected.

> [!IMPORTANT]
> Prefer the sequence below before reinstalling the whole Nuvio application. The goal is to reset the **plugin + cache state** while preserving your account, profiles and normal app data whenever possible.

## Preferred recovery order

Follow this order exactly when several devices are involved:

1. **Remove NiakVIO on Desktop/Mobile first.**
2. Remove NiakVIO on TV if it is still present there or if synchronization did not propagate the removal.
3. **Fully stop Nuvio** on each affected device.
4. **Clear the Nuvio cache** on each affected device.
5. Reopen **Desktop or Mobile first**.
6. Reinstall NiakVIO from Desktop/Mobile using the current manifest.
7. Confirm the repository and provider list there.
8. Only then reopen NuvioTV.
9. Check that the TV received the synchronized plugin state and that its provider list matches the current repository.

This order avoids using a stale TV state as the source of truth while the account is resynchronizing.

## 1. Remove the plugin repository

On Desktop/Mobile:

1. Open **Settings → Content & Discovery → Plugins**.
2. Find **NiakVIO** under installed repositories.
3. Remove/uninstall the NiakVIO repository.
4. If the same account is used on several Desktop/Mobile devices, let the account synchronize before continuing.

On TV:

1. Open **Settings → Content Discovery → Plugins**.
2. Remove NiakVIO if it is still listed.
3. If the TV offers **Manage from phone**, you may also remove the repository there and confirm the pending change on TV.

Do not install a second copy of the same manifest on top of a stale one.

## 2. Fully stop Nuvio and clear its cache

### Android / Android TV / Google TV

Use the system application settings:

1. Open **Settings → Apps → Nuvio / NuvioTV**.
2. Choose **Force stop**.
3. Open **Storage & cache**.
4. Choose **Clear cache**.

> [!CAUTION]
> Do **not** use **Clear storage / Clear data** as the normal troubleshooting step. That is much more destructive and may remove local app state, profiles or credentials. Use it only as a final app-level reset when you intentionally want that behavior.

A device reboot does not necessarily clear the application cache. Use the actual **Clear cache** action.

### macOS — Terminal

The official Desktop client currently uses the application identifier `com.nuvio.media`. The commands below first stop Nuvio, then show matching cache locations before deleting them.

**1. Stop Nuvio:**

```bash
osascript -e 'quit app "Nuvio"' 2>/dev/null || true
pkill -x Nuvio 2>/dev/null || true
```

**2. Preview cache folders that match Nuvio:**

```bash
for p in \
  "$HOME/Library/Caches/"*Nuvio* \
  "$HOME/Library/Caches/"*nuvio* \
  "$HOME/Library/Caches/com.nuvio.media"; do
  [ -e "$p" ] && printf '%s\n' "$p"
done
```

**3. Delete only those cache folders:**

```bash
for p in \
  "$HOME/Library/Caches/"*Nuvio* \
  "$HOME/Library/Caches/"*nuvio* \
  "$HOME/Library/Caches/com.nuvio.media"; do
  [ -e "$p" ] && rm -rf -- "$p"
done
```

**4. Optional: remove cache-only subfolders inside Nuvio Application Support, without deleting the whole application-data directory:**

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

These commands intentionally leave the main Nuvio Application Support directory intact.

### Windows — PowerShell

Open **PowerShell**. The commands below stop Nuvio, discover likely Nuvio data roots, preview cache-only directories, then remove only those cache directories.

**1. Stop Nuvio:**

```powershell
Get-Process Nuvio -ErrorAction SilentlyContinue | Stop-Process -Force
```

**2. Build the list of Nuvio roots that actually exist:**

```powershell
$roots = @(
  "$env:LOCALAPPDATA\Nuvio",
  "$env:APPDATA\Nuvio",
  "$env:LOCALAPPDATA\com.nuvio.media",
  "$env:APPDATA\com.nuvio.media"
) | Where-Object { Test-Path $_ }
```

**3. Preview cache folders:**

```powershell
$cacheNames = @('Cache', 'Caches', 'Code Cache', 'GPUCache')

if ($roots) {
  Get-ChildItem -Path $roots -Directory -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object { $cacheNames -contains $_.Name } |
    Select-Object -ExpandProperty FullName
}
```

**4. Delete only those cache folders:**

```powershell
if ($roots) {
  Get-ChildItem -Path $roots -Directory -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object { $cacheNames -contains $_.Name } |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}
```

This does **not** intentionally delete the whole Nuvio profile or application-data root.

### iPhone / iPad

iOS does not expose a normal per-app **Clear cache** button comparable to Android.

Use this order:

1. remove the NiakVIO repository;
2. fully close Nuvio from the app switcher;
3. reopen Nuvio and let the account synchronize;
4. reinstall NiakVIO from Mobile/Desktop.

Only reinstall the entire Nuvio app if plugin removal/reinstallation and account resynchronization do not fix the stale state.

## 3. Reinstall NiakVIO from Desktop or Mobile

Reopen **Desktop or Mobile first** and install the current general manifest:

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/manifest.json
```

In Nuvio:

1. open **Settings → Content & Discovery → Plugins**;
2. choose **Add repository / ADD REPOSITORY**;
3. paste the manifest into **Plugin manifest URL**;
4. choose **Install Plugin Repository**;
5. enable **Enable plugin providers globally**;
6. confirm that NiakVIO appears exactly once.

If you intentionally use another NiakVIO projection, reinstall that projection instead of the general manifest. Do not stack overlapping NiakVIO projections unless you are deliberately testing them.

## 4. Reopen the TV last

After Desktop/Mobile is correct:

1. reopen NuvioTV;
2. wait for the account/plugin state to synchronize;
3. open **Settings → Content Discovery → Plugins**;
4. confirm that NiakVIO appears exactly once;
5. confirm plugin providers are enabled globally;
6. compare the provider list with the current repository.

If the TV still shows the old state, force-stop NuvioTV and clear its Android cache once more, then reopen it **without reinstalling a second repository copy**.

## 5. Verify the recovery

Check all of the following:

- NiakVIO appears once on Desktop/Mobile;
- NiakVIO appears once on TV;
- the same account is in use on all devices;
- provider lists are consistent with the current manifest;
- plugin providers are globally enabled;
- compatible content produces NiakVIO source rows after lookup completes.

> [!TIP]
> Do not rely on an old hard-coded provider number. NiakVIO's maintained catalogue can evolve. The current repository/manifest is the reference.

## 6. Still broken?

Before reinstalling the entire Nuvio client, check:

- that the manifest URL is correct and reachable;
- that you did not install multiple overlapping NiakVIO projections;
- that the same Nuvio account is used on Desktop/Mobile/TV;
- that TMDB is configured if Nuvio reports a missing TMDB key;
- that the problem is not limited to one provider while the rest of NiakVIO works.

A single upstream provider can temporarily fail even when the plugin installation itself is healthy.

For a first-time setup, see **[Install Nuvio and NiakVIO](nuvio-installation.md)**.
