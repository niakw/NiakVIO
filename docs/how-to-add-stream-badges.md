# How to add NiakVIO StreamBadge rules to Nuvio

[Français](fr/how-to-add-stream-badges.md) · [Back to README](../README.md)

NiakVIO provides Fusion-style StreamBadge rules for stream cards.

## Recommended feed

Use **Fusion v2** for the normal setup:

```text
https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/stream-badges-fusion-v2.json
```

Optional theme-specific feeds also exist:

- Dark: `assets/stream-badges-dark.json`
- Light: `assets/stream-badges-light.json`

For most users, **Fusion v2 is the correct choice**.

## Nuvio Mobile and Nuvio Desktop

Current Nuvio UI path:

1. Open **Settings**.
2. Open **Appearance**.
3. Open **Streams**.
4. Under **FUSION STYLE**, open **Fusion badge URLs**.
5. Paste the NiakVIO Fusion v2 JSON URL.
6. Select **Import**.
7. Confirm that the URL appears in the imported list and is **Active**.
8. Optional: use **Preview** to verify the imported badges.
9. Optional: set **Badge position** to **Top** or **Bottom**.

Nuvio currently supports multiple imported badge URLs. If several are installed, make sure the NiakVIO URL you want to use is the active one.

## NuvioTV

Current NuvioTV UI path:

1. Open **Settings**.
2. Open **Layout**.
3. Expand **Streams**.
4. Under **Fusion Style**, open **Fusion badge URLs**.
5. NuvioTV starts its local badge configuration screen and shows a **QR code**.
6. Scan the QR code with your phone while the phone and TV are on the same local network.
7. In the web page opened on your phone, paste the NiakVIO Fusion v2 JSON URL.
8. Select **Import**.
9. Verify that the feed is shown as **Active** and optionally use **Preview**.
10. You can also change **Badge position** from the same configuration flow / TV settings.

The TV stores imported badge rules locally. If an older NiakVIO Fusion feed was already imported and does not refresh as expected, delete the old import and add the current **Fusion v2** URL again.

## Verify the result

Open a title with available streams. Compatible stream cards should display the imported Fusion badges when the stream metadata matches a rule.

If nothing appears:

- verify that the imported URL is active;
- use **Preview** to confirm that badges were loaded;
- refresh/re-import the current Fusion v2 URL;
- remember that a badge only appears when the stream metadata matches its rule.
