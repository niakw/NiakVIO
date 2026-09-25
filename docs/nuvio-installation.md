# Install Nuvio and NiakVIO

[Français](fr/nuvio-installation.md) · [Back to README](../README.md)

This guide covers a clean first installation of **Nuvio + NiakVIO** on Desktop, Mobile and Android TV.

> [!TIP]
> The easiest setup is to configure your account and plugins from **Desktop or Mobile first**, then open NuvioTV and let the account configuration synchronize.

## 1. Install an official Nuvio client

Use the official Nuvio projects:

- **Android TV / Google TV:** [NuvioTV releases](https://github.com/NuvioMedia/NuvioTV/releases/latest)
- **Android / iOS:** [NuvioMobile](https://github.com/NuvioMedia/NuvioMobile)
- **Windows / macOS:** [NuvioDesktop releases](https://github.com/NuvioMedia/NuvioDesktop/releases)

> [!NOTE]
> Nuvio Desktop is currently an alpha client. Expect the Desktop UI and local storage layout to evolve between releases.

### Android TV / Google TV APK

If NuvioTV is not available through your preferred store, open the official GitHub release page on the TV or download the APK on another device and transfer it.

For most TVs, the **universal APK** is the simplest choice when you are not sure which CPU architecture the device uses:

```text
app-full-universal-release.apk
```

A device-specific APK can be smaller, but only use it when you know the TV architecture.

If Android asks for permission to install unknown apps, enable it only for the browser or file manager you are actively using, install NuvioTV, then disable that permission again if you do not need it.

## 2. Sign in and enable account synchronization

Create or sign in to your Nuvio account on Mobile/Desktop. On TV, use the account connection screen or QR code when offered.

The account is important because it lets Nuvio synchronize supported configuration across your devices. In practice, this makes it much easier to install and maintain the plugin from a phone or computer instead of entering long manifest URLs with a TV remote.

If Nuvio offers **Essential** and **Advanced** experiences, Advanced is convenient when you want direct access to plugin/addon and diagnostic settings. You can change this later.

## 3. Recommended Nuvio stack

Keep the stack simple: **one tool per role**.

| Role | Recommended |
| --- | --- |
| Providers | **NiakVIO** |
| Metadata / catalogue | **Ultra MAX** |
| Subtitles | **SubSense** |
| Favorites / tracking | **SIMKL** |

See the full [Recommended Nuvio setup](../README.md#-recommended-nuvio-setup) in the README.

> [!TIP]
> Avoid installing several overlapping provider packs unless you are deliberately testing them. Overlapping packs make source lists harder to read and make troubleshooting much less deterministic.

## 4. Install NiakVIO from Desktop or Mobile

For most users, install the **general manifest**:

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/manifest.json
```

Then in Nuvio:

1. Open **Settings**.
2. Open **Content & Discovery**.
3. Open **Plugins**.
4. In **Add repository / ADD REPOSITORY**, paste the NiakVIO manifest URL into **Plugin manifest URL**.
5. Choose **Install Plugin Repository**.
6. Make sure **Enable plugin providers globally** is enabled.
7. Confirm that **NiakVIO** appears under the installed repositories and that its providers are listed.

> [!IMPORTANT]
> If Nuvio reports **TMDB API key missing**, configure TMDB in Nuvio settings. Provider matching can depend on TMDB metadata for the correct movie, series, season or episode identity.

### Other NiakVIO projections

Only install **one** projection unless you have a specific reason to do otherwise.

| Projection | Manifest |
| --- | --- |
| General | `https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/manifest.json` |
| French-focused | `https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/vf/manifest.json` |
| General without anime-oriented providers | `https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/no-anime/manifest.json` |
| French-focused without anime-oriented providers | `https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/vf-no-anime/manifest.json` |

More details: [manifest guide](how-to-add-manifest.md).

## 5. Open NuvioTV and verify synchronization

After the plugin is correct on Desktop/Mobile:

1. Fully close NuvioTV if it is already open.
2. Reopen NuvioTV while signed in to the same account.
3. Open **Settings → Content Discovery → Plugins**.
4. Confirm that NiakVIO is present and providers are enabled globally.
5. Compare the provider list with the current NiakVIO manifest rather than relying on an old hard-coded provider count.

NuvioTV may also expose **Manage from phone**. You can scan its QR code, manage the repository from the phone, then approve the change on TV when prompted.

## 6. Quick functional check

Pick a compatible movie, series or anime and open the source picker.

A healthy setup should show:

- the NiakVIO repository in the plugin list;
- NiakVIO providers below it;
- plugin providers enabled globally;
- NiakVIO sources appearing for compatible content after provider lookup completes.

Provider lookup is not instantaneous. Give providers a short moment to finish before deciding that the plugin is empty.

## 7. If the plugin looks stale or inconsistent

Typical symptoms include:

- a provider count that no longer matches the repository;
- providers appearing on Mobile/Desktop but not on TV;
- a plugin that works, disappears, then comes back;
- old provider names or stale repository metadata after an update.

Do **not** repeatedly add the same manifest. Use the dedicated recovery procedure instead:

First try **Settings → Content & Discovery → Plugins → NiakVIO → Refresh**. If the repository still looks stale:

➡️ **[Update, refresh, reinstall and clear Nuvio cache](niakvio-update-reinstall-cache.md)**

The preferred recovery order is **repository Refresh first**, then close/reopen and account resync, then repository reinstall, then cache cleanup. Reinstalling the whole Nuvio application is the last resort.
