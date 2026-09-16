#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str, label: str) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if new in text and old not in text:
        print(f"{label}: already applied")
        return
    if text.count(old) != 1:
        raise AssertionError(f"{label}: expected one old anchor, got {text.count(old)}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{label}: applied")


def patch_apply_order() -> None:
    path = ROOT / "scripts/apply_provider_overrides.py"
    text = path.read_text(encoding="utf-8")
    old_order = '''    "CORE.STREAM_PRESENTATION.V1",\n    "CORE.PROVIDER_BRANDING.V1",\n    "CORE.STREAM_SANITIZER.V6",\n    "CORE.RUNTIME_MEDIA_SAFETY.V4",\n'''
    new_order = '''    "CORE.STREAM_PRESENTATION.V1",\n    "CORE.STREAM_SANITIZER.V6",\n    "CORE.RUNTIME_MEDIA_SAFETY.V4",\n    "CORE.PROVIDER_BRANDING.V1",\n'''
    if old_order in text:
        text = text.replace(old_order, new_order, 1)
    elif new_order not in text:
        raise AssertionError("canonical Core order anchor drifted")

    start_marker = "        # Provider branding is deliberately the final Core stream layer."
    terminal_marker = "        # Terminal stream validation is a Core-wide publication boundary."
    end_marker = "        # END PROVIDER is the final byte boundary."
    if start_marker in text:
        start = text.index(start_marker)
        end = text.index(terminal_marker, start)
        block = text[start:end]
        text = text[:start] + text[end:]
        block = block.replace(
            "        # Provider branding is deliberately the final Core stream layer. Upstream\n"
            "        # stream names can contain quality/language/codec facts; presentation must\n"
            "        # read those originals before the committed emoji/name replaces the local\n"
            "        # row label and title prefix.\n",
            "        # Provider branding is the final client-visible projection. It must run\n"
            "        # after terminal media validation and runtime safety so title/name use the\n"
            "        # final verified/recovered quality exactly once. Source labels stay in\n"
            "        # preserved source* facts and never re-expand the UI title.\n",
        )
        insert_at = text.index(end_marker)
        text = text[:insert_at] + block + text[insert_at:]
    else:
        branding_at = text.find('"scope": "global_provider_branding"')
        safety_at = text.find('"scope": "global_runtime_media_safety"')
        if branding_at < safety_at:
            raise AssertionError("branding order not migrated")
    path.write_text(text, encoding="utf-8")
    print("apply_overrides: final branding relocated")


def patch_branding() -> None:
    path = ROOT / "scripts/provider_patches/global_provider_branding_v1.py"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "post-presentation-lossless-source-label-v8",
        "post-safety-uniform-final-label-v9",
    )
    old = '''function visibleTitle(r,v,old){var parts=[v],sources=sourceParts(r);for(var i=0;i<sources.length;i++){var value=sources[i],n=norm(value),pn=norm(c.providerName),vl=norm(v);if(n&&n!==pn&&n!==vl)addUnique(parts,value)}var q=qualityToken(r&&r.quality)||oldQuality(old),base=parts.join(" • ");return q&&!containsQuality(parts,q)?base+" - "+q:base}\nfunction brand(r){if(!r||typeof r!=="object")return r;var o=Object.assign({},r),v=label();if(!v)return o;var display=visibleTitle(o,v,o.title);o.title=display;o.name=display;return o}\n'''
    new = '''function visibleTitle(r,v,old){var q=qualityToken(r&&r.quality)||oldQuality(old);return q?v+" - "+q:v}\nfunction brand(r){if(!r||typeof r!=="object")return r;var o=Object.assign({},r),v=label();if(!v)return o;if(placeholder(o.quality))delete o.quality;var display=visibleTitle(o,v,o.title);o.title=display;o.name=display;return o}\n'''
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise AssertionError("provider branding V9 anchor drifted")
    text = text.replace(
        "V8 restores the historical lossless client-visible label contract: Core may\nnormalize quality/facts, but provider/player labels already returned by the\nprovider remain visible in ``title``/``name``.",
        "V9 makes the final client-visible title deterministic after media safety: Core\nuses only the committed provider identity plus final verified/recovered quality in\n``title``/``name``. Provider/player labels remain preserved as source facts.",
    )
    path.write_text(text, encoding="utf-8")
    print("branding: V9 uniform final label")


def patch_presentation() -> None:
    path = ROOT / "scripts/provider_patches/global_stream_presentation_v1.py"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        'REVISION = "all-providers-client-projection-language-roles-v23"',
        'REVISION = "all-providers-client-projection-evidence-language-v24"',
    )
    old = 'function language(r){var explicit=meaningful(r&&r.language)?s(r.language):"",all=blob(r),u=explicit.toUpperCase(),a=all.toUpperCase(),vfMode=s(c.providerLanguageMode).toLowerCase()==="vf";'
    new = 'function language(r){var explicit=meaningful(r&&r.language)?s(r.language):"",all=[r&&r.language,r&&r.languages,r&&r.languageTracks,r&&r.audioLanguage,r&&r.audioLanguages,r&&r.audioTracks].map(s).join(" "),u=explicit.toUpperCase(),a=all.toUpperCase(),vfMode=s(c.providerLanguageMode).toLowerCase()==="vf";'
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise AssertionError("presentation language evidence anchor drifted")
    old_tail = 'if(!u){if(hasVost)return"VOSTFR";if(hasVf)return"VF";if(isVo(a))return"VO"}return s(c.languageFallback)||(vfMode?"VF":"VO")}'
    new_tail = 'if(!u){if(hasVost)return"VOSTFR";if(hasVf)return"VF";if(isVo(a))return"VO"}return""}'
    if old_tail in text:
        text = text.replace(old_tail, new_tail, 1)
    elif new_tail not in text:
        raise AssertionError("presentation language fallback anchor drifted")
    old_detail = 'var raw=s(r&&r.language),all=[raw,r&&r.name,r&&r.title,r&&r.label,r&&r.sourceLabel,r&&r.audio].map(s).join(" ").toLowerCase().replace(/[_-]+/g," ").replace(/\\s+/g," ").trim();'
    new_detail = 'var raw=s(r&&r.language),all=[raw,r&&r.languages,r&&r.languageTracks,r&&r.audioLanguage,r&&r.audioLanguages,r&&r.audioTracks].map(s).join(" ").toLowerCase().replace(/[_-]+/g," ").replace(/\\s+/g," ").trim();'
    if old_detail in text:
        text = text.replace(old_detail, new_detail, 1)
    elif new_detail not in text:
        raise AssertionError("detailed language evidence anchor drifted")
    path.write_text(text, encoding="utf-8")
    print("presentation: V24 evidence-only language")


def patch_engine_mirror() -> None:
    path = ROOT / "engine_v2/src/stream-presentation.mjs"
    text = path.read_text(encoding="utf-8")
    old = '  const hints = [stream.description, stream.title, stream.sourceLabel, stream.filename].map(clean).filter(Boolean).join(" ").toUpperCase();\n'
    new = '  const hints = [stream.language, stream.languages, stream.languageTracks, stream.audioLanguage, stream.audio_languages, stream.audioTracks].map(clean).filter(Boolean).join(" ").toUpperCase();\n'
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise AssertionError("engine language hint anchor drifted")
    path.write_text(text, encoding="utf-8")
    print("engine mirror: evidence-only language")


def patch_normalizer_and_tests() -> None:
    replace_once(
        "scripts/normalize_stream_presentation_v12.py",
        'REVISION_V23 = "all-providers-client-projection-language-roles-v23"\nSUPPORTED_REVISIONS = (REVISION_V23, REVISION_V22)',
        'REVISION_V23 = "all-providers-client-projection-language-roles-v23"\nREVISION_V24 = "all-providers-client-projection-evidence-language-v24"\nSUPPORTED_REVISIONS = (REVISION_V24, REVISION_V23, REVISION_V22)',
        "normalizer revision",
    )
    p = ROOT / "scripts/normalize_stream_presentation_v12.py"
    t = p.read_text(encoding="utf-8")
    t = t.replace("canonical V22 or V23 source", "canonical V22, V23 or V24 source")
    t = t.replace("if revision == REVISION_V23:", "if revision in (REVISION_V24, REVISION_V23):")
    p.write_text(t, encoding="utf-8")

    p = ROOT / "tests/global_stream_presentation_test.py"
    t = p.read_text(encoding="utf-8")
    t = t.replace(
        'assert presentation.REVISION == "all-providers-client-projection-language-roles-v23"',
        'assert presentation.REVISION == "all-providers-client-projection-evidence-language-v24"',
    ).replace(
        'assert "all-providers-client-projection-language-roles-v23" in patched',
        'assert "all-providers-client-projection-evidence-language-v24" in patched',
    )
    p.write_text(t, encoding="utf-8")

    p = ROOT / "tests/global_stream_presentation_pipeline_test.py"
    t = p.read_text(encoding="utf-8")
    t = t.replace(
        '    assert native["row"]["language"] == "VO", native\n    assert "🌐 VO" in native["row"]["description"], native\n',
        '    assert not native["row"].get("language"), native\n    assert "🌐 VO" not in native["row"]["description"], native\n',
    )
    old_order = '''    assert output.index("NUVIO_GLOBAL_STREAM_PRESENTATION_V1") < output.index("NUVIO_GLOBAL_PROVIDER_BRANDING_V1"), provider\n    assert output.index("NUVIO_GLOBAL_PROVIDER_BRANDING_V1") < output.index("/* STARTFIX:CORE.STREAM_SANITIZER.V6 */"), provider\n'''
    new_order = '''    assert output.index("NUVIO_GLOBAL_STREAM_PRESENTATION_V1") < output.index("/* STARTFIX:CORE.STREAM_SANITIZER.V6 */"), provider\n    assert output.index("/* STARTFIX:CORE.STREAM_SANITIZER.V6 */") < output.index("NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1"), provider\n    assert output.index("NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1") < output.index("NUVIO_GLOBAL_PROVIDER_BRANDING_V1"), provider\n'''
    if old_order in t:
        t = t.replace(old_order, new_order, 1)
    p.write_text(t, encoding="utf-8")

    p = ROOT / "tests/stream_output_sanitizer_fail_closed_test.py"
    t = p.read_text(encoding="utf-8")
    t = t.replace(
        'assert branding_pos >= 0 and sanitizer_pos > branding_pos, (branding_pos, sanitizer_pos)',
        'assert branding_pos >= 0 and branding_pos > sanitizer_pos, (branding_pos, sanitizer_pos)',
    )
    p.write_text(t, encoding="utf-8")
    print("presentation tests: updated")


def patch_android_launcher() -> None:
    path = ROOT / "scripts/native_player_diagnostics_codegen.py"
    text = path.read_text(encoding="utf-8")
    old = '''            // Start the official production MainActivity explicitly inside the exact package\n            // under instrumentation. applicationId can differ between official client\n            // revisions/build variants, so the Lab must not hard-code a debug package.\n            val intent = Intent().setClassName(\n                context.packageName,\n                MainActivity::class.java.name,\n            )\n            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)\n'''
    new = '''            // Resolve the installed production launcher by activity class, not by the\n            // Kotlin namespace/targetContext package. Official build variants may keep\n            // com.nuvio.app.MainActivity while using a different applicationId.\n            val launcherQuery = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)\n            val launchActivity = context.packageManager.queryIntentActivities(launcherQuery, 0)\n                .firstOrNull { info -> info.activityInfo?.name == MainActivity::class.java.name }\n                ?: context.packageManager.queryIntentActivities(launcherQuery, 0)\n                    .firstOrNull { info ->\n                        info.activityInfo?.name?.endsWith(".MainActivity") == true &&\n                            info.activityInfo?.applicationInfo?.sourceDir == context.applicationInfo.sourceDir\n                    }\n                ?: return NativePlayerProbe("error", "nuvio-mobile", "MainActivity", "NO_LAUNCH_ACTIVITY", 0, "player_setup", host, null)\n            val intent = Intent().setClassName(\n                launchActivity.activityInfo.packageName,\n                launchActivity.activityInfo.name,\n            )\n            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)\n'''
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise AssertionError("mobile launcher V37 anchor drifted")
    path.write_text(text, encoding="utf-8")

    test = ROOT / "tests/native_mobile_player_launch_v36_test.py"
    t = test.read_text(encoding="utf-8")
    t = '''#!/usr/bin/env python3\nfrom pathlib import Path\n\nROOT=Path(__file__).resolve().parents[1]\ntext=(ROOT/'scripts/native_player_diagnostics_codegen.py').read_text(encoding='utf-8')\nassert 'queryIntentActivities(launcherQuery, 0)' in text\nassert 'info.activityInfo?.name == MainActivity::class.java.name' in text\nassert 'launchActivity.activityInfo.packageName' in text\nassert 'launchActivity.activityInfo.name' in text\nassert 'context.packageName,\\n                MainActivity::class.java.name' not in text\nassert '\"com.nuviodebug.com\",\\n                MainActivity::class.java.name' not in text\nprint('native mobile player launch V37 applicationId resolution test passed')\n'''
    test.write_text(t, encoding="utf-8")
    print("android mobile Lab: applicationId-safe launcher")


def patch_runtime_contract() -> None:
    path = ROOT / "automation/platform-runtime-contracts.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["audited_at"] = "2026-09-16"
    data["observed_native_differences"] = {
        "evidence_date": "2026-09-16",
        "niakvio_sha": "6b28f3b2c53f5ca6cfb4bc11a3af139c21d6dee1",
        "runs": {"android": 35033132967, "ios": 35033132980, "desktop": 35033133048},
        "anti_inference_rules": [
            "Provider extraction, client projection and player readiness are independent verdicts; a player failure never erases a positive provider extraction.",
            "A red exhaustive matrix is not a provider-wide failure when the same platform artifact contains count>0 rows.",
            "TV late-result/stale symptoms must not be generalized to Desktop: the 2026-09-16 macOS user test observed correct reset after changing work.",
            "Quality shown to the client must be the final post-sanitizer quality; source/declaration quality cannot remain in title when media proof changes it.",
            "Language/badges require stream-level evidence. Provider catalogue language is a capability hint, not proof that a returned media track is French/VO/VF.",
        ],
        "devices": [
            {"device": "Android TV", "artifact": "native-tv-full-35033132967 (~613 MB; job diagnostics + user device evidence)", "provider_extraction": "User TV: Interstellar Purstream/Papadustream/Castle/StreamZo/Kehflix; HOTD S1E2 Purstream/StreamZo/Castle/VidRock/HindMoviez; Hell Mode S2E12 French-Manga/VoirAnime.homes.", "player": "User-visible streams exist; provider/player verdict must remain per-row.", "ux": "Common TV defects: non-uniform title, duplicated/conflicting quality, Inconnue placeholder, language/badge mismatch, late rows without badges, no visible 4K provider.", "classification": "real product UX + provider coverage work; runner red does not cancel user positives"},
            {"device": "Android Mobile", "artifact": "native-mobile-android-full-35033132967", "provider_extraction": "2073 results; VidRock count>0 on movie + TV.", "player": "2/2 extracted VidRock rows fail only at Activity launch: Unable to resolve cmp=com.nuvio.app/.MainActivity.", "ux": "Launcher diagnostic must resolve installed applicationId independently from Kotlin namespace.", "classification": "Lab launcher false red after positive extraction"},
            {"device": "iOS", "artifact": "native-mobile-ios-full-35033132980", "provider_extraction": "3299 results; 89 count>0 (VidRock 58, VoirAnime 31).", "player": "89/89 production-player probes ready; exhaustive Hub-46 gate success.", "ux": "Ktor/Darwin path is a positive control against simultaneous provider-bundle failure.", "classification": "native green positive control"},
            {"device": "macOS", "artifact": "native-desktop-full-macos-35033133048 + user testmac1609 logs", "provider_extraction": "Artifact: HindMoviez movie count=4; VidRock movie=1 + TV=1. User UI: VidRock visible on Interstellar/HOTD, Hell Mode zero.", "player": "Artifact 6/6 mpv_create_failed; user log player attach -> mpv_create failed and visible VidRock does not launch.", "ux": "User work-change test resets streams correctly. Logs separately show WookaFR DNS failure and MovieBox/Workers.dev timeouts.", "classification": "positive extraction + real macOS player/client blocker; no evidence of current stale reset bug on macOS"},
            {"device": "Windows", "artifact": "native-desktop-full-windows-35033133048", "provider_extraction": "2116 results; HindMoviez + VidRock positive on movie and TV (4 positive result rows / 10 streams).", "player": "9 ready / 1 timeout.", "ux": "Exhaustive matrix red must not be reported as Desktop-wide zero.", "classification": "native positives; matrix coverage red"},
        ],
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    renderer = ROOT / "scripts/render_platform_runtime_contracts.py"
    text = renderer.read_text(encoding="utf-8")
    anchor = '    return "\\n".join(lines).rstrip() + "\\n"\n'
    block = '''    observed = data.get("observed_native_differences") or {}\n    devices = observed.get("devices") or []\n    if devices:\n        lines += [\n            "## Évidence croisée Native + tests utilisateur",\n            "",\n            f"Évidence datée **{esc(observed.get('evidence_date'))}**, NiakVIO SHA `{esc(observed.get('niakvio_sha'))}`.",\n            "",\n            "| Device | Extraction provider | Player | UX / transport | Classification |",\n            "| --- | --- | --- | --- | --- |",\n        ]\n        for row in devices:\n            lines.append(\n                "| " + esc(row.get("device")) + " | " + esc(row.get("provider_extraction")) + " | "\n                + esc(row.get("player")) + " | " + esc(row.get("ux")) + " | " + esc(row.get("classification")) + " |"\n            )\n        lines += ["", "### Règles anti-régression / anti-faux-diagnostic", ""]\n        for rule in observed.get("anti_inference_rules") or []:\n            lines.append("- " + esc(rule))\n        lines.append("")\n\n    return "\\n".join(lines).rstrip() + "\\n"\n'''
    if anchor in text:
        text = text.replace(anchor, block, 1)
    elif "## Évidence croisée Native + tests utilisateur" not in text:
        raise AssertionError("runtime renderer return anchor drifted")
    renderer.write_text(text, encoding="utf-8")
    print("runtime contract: user/native cross-device evidence added")


def main() -> int:
    patch_apply_order()
    patch_branding()
    patch_presentation()
    patch_engine_mirror()
    patch_normalizer_and_tests()
    patch_android_launcher()
    patch_runtime_contract()
    print("CROSS_DEVICE_AUDIT_FIX_APPLIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
