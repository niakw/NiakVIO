# How to add a NiakVIO manifest to Nuvio

[Français](fr/how-to-add-manifest.md) · [Back to README](../README.md)

> [!TIP]
> For most users, install the **general manifest**. You only need one NiakVIO projection.

## ⚡ Recommended manifest

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/manifest.json
```

NiakVIO is installed in Nuvio as a **plugin repository manifest**.

<details>
<summary><strong>Other manifest projections</strong></summary>

<br>

### French-focused

Use this if you only want the French-focused provider selection, based on language information explicitly declared by providers or streams.

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/vf/manifest.json
```

### General without anime-oriented providers

Copy of the general catalogue with clearly anime-oriented providers removed. A provider is excluded when it declares **anime as its only supported type**, or when its committed provider id/name contains **`anim`** (case-insensitive). Mixed movie/TV/anime providers remain when their id/name is not anime-oriented.

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/no-anime/manifest.json
```

### French-focused without anime-oriented providers

The same deterministic filter applied to the French-focused manifest.

```text
https://raw.githubusercontent.com/niakw/NiakVIO/refs/heads/main/vf-no-anime/manifest.json
```

</details>

> [!NOTE]
> Installing multiple overlapping manifests is usually unnecessary. Pick the projection that matches what you want Nuvio to expose.

---

## 📱 Nuvio Mobile & Desktop

1. Open **Settings**.
2. Open **Content & Discovery**.
3. Open **Plugins**.
4. In **ADD REPOSITORY**, paste the NiakVIO manifest URL into **Plugin manifest URL**.
5. Select **Install Plugin Repository**.
6. Make sure **Enable plugin providers globally** is enabled.
7. Confirm that NiakVIO appears under **INSTALLED REPOSITORIES** and that its providers are listed below.

> [!IMPORTANT]
> If Nuvio shows **TMDB API key missing**, configure TMDB in Nuvio settings. Current plugin providers may rely on TMDB metadata for correct movie / series / episode matching.

---

## 📺 NuvioTV

1. Open **Settings**.
2. Open **Content Discovery**.
3. Open **Plugins**.
4. Choose **Add repository**.
5. Paste the NiakVIO manifest URL.
6. Select **Add**.
7. Make sure **Enable plugin providers globally** is enabled.
8. Confirm that the NiakVIO repository and its providers appear in the list.

<details>
<summary><strong>Manage from phone</strong></summary>

<br>

NuvioTV also provides **Manage from phone**: open it, scan the QR code, then add or remove the repository from your phone. Confirm the pending repository change on the TV when prompted.

</details>

---

## ✅ Verify that it is active

A successful installation should show:

- the NiakVIO repository in the installed repository list;
- NiakVIO providers below it;
- providers enabled globally;
- NiakVIO sources appearing in the stream picker for compatible titles.

If the repository is installed but streams do not appear, **refresh the repository first**, then check that plugin providers are globally enabled and that the relevant provider itself is enabled.

## 🔄 Updating NiakVIO

You do not need to replace the URL when NiakVIO is updated. The manifest URLs are stable.

Use Nuvio's **Refresh repository** action when you want to force an immediate refresh.
