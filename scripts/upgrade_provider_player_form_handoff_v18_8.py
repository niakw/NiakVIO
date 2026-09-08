#!/usr/bin/env python3
"""V18.8: submit bounded same-origin hidden player forms after GET extraction misses.

Some generic file-host players expose the terminal media only after a hidden-form
handoff on the canonical player page. This capability is deliberately structural:
it recognizes a bounded F1-style hidden form, echoes only its hidden fields back
to the same origin, optionally restores the opaque file_code from the current
player URL, and then reuses the existing packed-player/media extraction path.

No provider/domain/fixture rule is encoded and no form body is ever traced.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_PLAYER_FORM_HANDOFF_V18_8"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch() -> bool:
    text = BASE.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False
    for required in (
        "NIAKVIO_PROVIDER_PACKED_PLAYER_V18_6",
        "NIAKVIO_PROVIDER_PLAYER_ROUTE_VARIANT_V18_7",
    ):
        if required not in text:
            raise AssertionError(f"V18.8 requires {required}")

    anchor = "async function _crawlDirectMedia(seedUrls, referer, maxDepth) {\n"
    helper = r'''/* NIAKVIO_PROVIDER_PLAYER_FORM_HANDOFF_V18_8 */
function _spv188HtmlAttr(tag, name) {
  const source = _text(tag);
  const escaped = _text(name).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const quoted = source.match(new RegExp("\\b" + escaped + "\\s*=\\s*([\\\"'])((?:\\\\.|(?!\\1).)*)\\1", "i"));
  if (quoted) return quoted[2].replace(/&amp;/gi, "&").replace(/&quot;/gi, '"').replace(/&#39;/gi, "'");
  const bare = source.match(new RegExp("\\b" + escaped + "\\s*=\\s*([^\\s>]+)", "i"));
  return bare ? bare[1] : "";
}
function _spv188PlayerForm(html, pageUrl) {
  const source = _text(html).slice(0, 524288);
  if (!source || !/^https?:\/\//i.test(_text(pageUrl))) return null;
  const forms = /<form\b([^>]*)>([\s\S]*?)<\/form\s*>/gi;
  let match, scanned = 0;
  while ((match = forms.exec(source)) && scanned++ < 8) {
    const attrs = match[1] || "";
    if (_spv188HtmlAttr(attrs, "id").toUpperCase() !== "F1") continue;
    const method = _spv188HtmlAttr(attrs, "method").toUpperCase();
    if (method && method !== "POST") continue;
    let page, target;
    try {
      page = new URL(pageUrl);
      target = new URL(_spv188HtmlAttr(attrs, "action") || page.toString(), page.toString());
    } catch (_) { return null; }
    if (!/^https?:$/i.test(target.protocol) || target.origin !== page.origin) return null;
    const params = new URLSearchParams();
    const inputs = match[2].match(/<input\b[^>]*>/gi) || [];
    for (const tag of inputs.slice(0, 32)) {
      const type = _spv188HtmlAttr(tag, "type").toLowerCase();
      if (type && type !== "hidden") continue;
      const name = _spv188HtmlAttr(tag, "name");
      if (!/^[A-Za-z0-9_.:-]{1,64}$/.test(name)) continue;
      const value = _spv188HtmlAttr(tag, "value").slice(0, 2048);
      params.append(name, value);
    }
    if (!params.has("file_code")) {
      const code = page.pathname.split("/").filter(Boolean).pop() || "";
      if (/^[A-Za-z0-9_-]{3,160}$/.test(code)) params.set("file_code", code);
    }
    if (![...params.keys()].length) return null;
    target.hash = "";
    return { url: target.toString(), body: params.toString() };
  }
  return null;
}
'''
    text = once(text, anchor, helper + anchor, "v18.8-form-helper")

    old_text = '''      let urls = [];
      if (contentType.includes("application/json")) {
        const json = await response.json();
        urls = _sourceUrls(json, responseUrl);
      } else {
        const playerText = await response.text();
        const decodedPlayerText = _spv186UnpackPackedPlayer(playerText);
        urls = _extractUrls(decodedPlayerText, responseUrl);
      }
      const direct = urls.filter(_directMedia);
'''
    new_text = '''      let urls = [];
      let playerText = "";
      if (contentType.includes("application/json")) {
        const json = await response.json();
        urls = _sourceUrls(json, responseUrl);
      } else {
        playerText = await response.text();
        const decodedPlayerText = _spv186UnpackPackedPlayer(playerText);
        urls = _extractUrls(decodedPlayerText, responseUrl);
      }
      const direct = urls.filter(_directMedia);
'''
    text = once(text, old_text, new_text, "v18.8-retain-player-html")

    old_handoff = '''      if (direct.length) {
        streams.push(..._streams(direct, responseUrl));
        continue;
      }
      // The same opaque player id is often exposed under a landing/embed path
'''
    new_handoff = '''      if (direct.length) {
        streams.push(..._streams(direct, responseUrl));
        continue;
      }
      const formRequest = playerText ? _spv188PlayerForm(playerText, responseUrl) : null;
      if (formRequest && requests < 10) {
        try {
          requests += 1;
          const postResponse = await fetch(formRequest.url, {
            method: "POST",
            headers: {
              Accept: "text/html,application/xhtml+xml,*/*;q=0.8",
              "Content-Type": "application/x-www-form-urlencoded",
              Referer: responseUrl
            },
            body: formRequest.body,
            redirect: "follow"
          });
          if (postResponse && postResponse.ok) {
            const postUrl = _text(postResponse.url || formRequest.url);
            const postText = await postResponse.text();
            const postDecoded = _spv186UnpackPackedPlayer(postText);
            const postUrls = _extractUrls(postDecoded, postUrl);
            const postDirect = postUrls.filter(_directMedia);
            if (postDirect.length) {
              streams.push(..._streams(postDirect, postUrl));
              continue;
            }
            if (row.depth < Math.max(0, Number(maxDepth) || 0)) {
              for (const nested of postUrls.filter(_crawlEligible).slice(0, 6)) {
                const next = _crawlCanonical(nested);
                if (next && !seen.has(next)) queue.push({ url: next, depth: row.depth + 1, referer: postUrl });
              }
            }
          }
        } catch (_) {}
      }
      // The same opaque player id is often exposed under a landing/embed path
'''
    text = once(text, old_handoff, new_handoff, "v18.8-submit-player-form")

    BASE.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    if value.count(MARKER) != 1:
        raise AssertionError(f"V18.8 marker count={value.count(MARKER)}")
    for needle in (
        "function _spv188PlayerForm(html, pageUrl)",
        '!== "F1"',
        "target.origin !== page.origin",
        'params.has("file_code")',
        "const formRequest = playerText ? _spv188PlayerForm(playerText, responseUrl) : null;",
        'method: "POST"',
        '"Content-Type": "application/x-www-form-urlencoded"',
        "const postDecoded = _spv186UnpackPackedPlayer(postText);",
        "const postDirect = postUrls.filter(_directMedia);",
    ):
        if needle not in value:
            raise AssertionError(f"V18.8 missing {needle}")
    section = value.split("/* NIAKVIO_PROVIDER_PLAYER_FORM_HANDOFF_V18_8 */", 1)[1].split(
        "async function _crawlDirectMedia", 1
    )[0].casefold()
    for forbidden in (
        "mugiwara",
        "smoothpre",
        "ansembed",
        "jujutsu",
        "vidhide",
        "eval(",
    ):
        if forbidden in section:
            raise AssertionError(f"V18.8 provider-specific/unsafe token leaked: {forbidden}")


def main() -> int:
    changed = patch()
    print(
        f"PROVIDER_PLAYER_FORM_HANDOFF_V18_8_OK changed={str(changed).lower()} "
        "same_origin=1 hidden_fields_max=32 html_bytes_max=524288 post_budgeted=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
