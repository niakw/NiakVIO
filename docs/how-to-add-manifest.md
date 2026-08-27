# How to add a NiakVIO manifest to Nuvio

[Français](fr/how-to-add-manifest.md) · [Back to README](../README.md)

NiakVIO is installed in Nuvio as a **plugin repository manifest**.

## Which manifest should I use?

### General manifest — recommended

Use this unless you specifically want a French-focused subset.

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/manifest.json
```

### French-focused manifest

Use this if you only want the French-focused provider selection, based on language information explicitly declared by providers or streams.

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/vf/manifest.json
```

> Installing both is usually unnecessary because they overlap. For most users, install the **General manifest only**.

## Nuvio Mobile and Nuvio Desktop

Current Nuvio UI path:

1. Open **Settings**.
2. Open **Content & Discovery**.
3. Open **Plugins**.
4. In **ADD REPOSITORY**, paste the NiakVIO manifest URL into **Plugin manifest URL**.
5. Select **Install Plugin Repository**.
6. Make sure **Enable plugin providers globally** is enabled.
7. Confirm that NiakVIO appears under **INSTALLED REPOSITORIES** and that its providers are listed below.

If Nuvio shows **TMDB API key missing**, configure TMDB in Nuvio settings. Current plugin providers may rely on TMDB metadata for correct movie / series / episode matching.

## NuvioTV

Current NuvioTV UI path:

1. Open **Settings**.
2. Open **Content Discovery**.
3. Open **Plugins**.
4. Choose **Add repository**.
5. Paste the NiakVIO manifest URL.
6. Select **Add**.
7. Make sure **Enable plugin providers globally** is enabled.
8. Confirm that the NiakVIO repository and its providers appear in the list.

NuvioTV also provides **Manage from phone**: open it, scan the QR code, then add or remove the repository from your phone. Confirm the pending repository change on the TV when prompted.

## Verify that it is active

A successful installation should show:

- the NiakVIO repository in the installed repository list;
- NiakVIO providers below it;
- providers enabled globally;
- NiakVIO sources appearing in the stream picker for compatible titles.

If the repository was installed but streams do not appear, refresh the repository first, then check that plugin providers are globally enabled and that the relevant provider itself is enabled.

## Updating NiakVIO

You do not need to replace the URL when NiakVIO is updated. The manifest URLs are stable.

Use Nuvio's **Refresh repository** action when you want to force an immediate refresh.
