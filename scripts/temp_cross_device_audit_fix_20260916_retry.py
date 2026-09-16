#!/usr/bin/env python3
from __future__ import annotations
import runpy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ns=runpy.run_path(str(ROOT/'scripts/temp_cross_device_audit_fix_20260916.py'), run_name='cross_device_base')
ns['main']()

# VF audio + VOSTFR subtitles is not multi-audio. Keep subtitle evidence separate.
p=ROOT/'tests/global_stream_presentation_test.py'
t=p.read_text(encoding='utf-8')
t=t.replace('assert row["language"] == "MULTI (VF/VO)", row','assert row["language"] == "VF", row')
t=t.replace('assert {"4k-ultra-hd", "webdl", "hevc", "multi"}.issubset(set(row["badgeIds"])), row','assert {"4k-ultra-hd", "webdl", "hevc", "vf", "vostfr"}.issubset(set(row["badgeIds"])), row\nassert "multi" not in set(row["badgeIds"]), row')
t=t.replace('assert lines[2] == "🇫🇷 MULTI (VF/VO)", lines','assert lines[2] == "🇫🇷 VF", lines')
t=t.replace('assert "🇫🇷 MULTI (VF/VO)" in roundtrip["description"], roundtrip','assert "🇫🇷 VF" in roundtrip["description"], roundtrip')
t=t.replace('assert "🇫🇷 MULTI (VF/VO)" in tv_row["description"]','assert "🇫🇷 VF" in tv_row["description"]')
p.write_text(t,encoding='utf-8')

# Sanitizer owns media validation, final branding owns client-visible title/name.
p=ROOT/'scripts/provider_patches/stream_output_sanitizer_v6.py'
t=p.read_text(encoding='utf-8')
old='''CORE_PREDECESSOR_MARKERS = TARGET_MEDIA_MARKERS + (\n    "/* NUVIO_GLOBAL_STREAM_PRESENTATION_V1:",\n    "/* NUVIO_GLOBAL_PROVIDER_BRANDING_V1:",\n)'''
new='''CORE_PREDECESSOR_MARKERS = TARGET_MEDIA_MARKERS + (\n    "/* NUVIO_GLOBAL_STREAM_PRESENTATION_V1:",\n)'''
if old in t:
    t=t.replace(old,new,1)
elif new not in t:
    raise AssertionError('sanitizer predecessor marker shape drifted')
t=t.replace(
    'A second subtlety matters on durable/LKG rematerialization. Some target-media\nprofiles deliberately remove their old wrapper and append a fresh one.',
    'A second subtlety matters on durable/LKG rematerialization. Some target-media\nprofiles deliberately remove their old wrapper and append a fresh one. Final\nprovider branding is intentionally outside this boundary: sanitizer validates\nmedia first, then branding projects the final verified quality exactly once.'
)
p.write_text(t,encoding='utf-8')

p=ROOT/'tests/stream_output_sanitizer_fail_closed_test.py'
t=p.read_text(encoding='utf-8')
t=t.replace(
    '# Core stream presentation/branding can also be rematerialized after an old\n    # sanitizer. The strict terminal layer must move after them as well.',
    '# Stream presentation is inside the sanitizer, while final provider branding\n    # is outside it. Reapplying V6 must preserve branding after the sanitizer.'
)
t=t.replace(
    'assert branding_pos >= 0 and sanitizer_pos > branding_pos, (branding_pos, sanitizer_pos)',
    'assert branding_pos >= 0 and branding_pos > sanitizer_pos, (branding_pos, sanitizer_pos)'
)
p.write_text(t,encoding='utf-8')

# Android Mobile installed-launcher contract.
p=ROOT/'scripts/finalize_native_android_reader_source.py'
t=p.read_text(encoding='utf-8')
start=t.index('MOBILE_CONTEXT_LAUNCH =')
end=t.index('\n\n\ndef finalize_source', start)
constants='''MOBILE_CONTEXT_LAUNCH = "context.packageManager.getLaunchIntentForPackage(context.packageName)"\nMOBILE_EXPLICIT_SET_CLASS = "Intent().setClassName("\nMOBILE_EXPLICIT_CONTEXT_PACKAGE = "context.packageName,"\nMOBILE_EXPLICIT_TARGET_PACKAGE = "MainActivity::class.java.packageName,"\nMOBILE_EXPLICIT_MAIN_ACTIVITY = "MainActivity::class.java.name"\nMOBILE_LAUNCHER_QUERY = "val launcherQuery = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)"\nMOBILE_QUERY_ACTIVITIES = "context.packageManager.queryIntentActivities(launcherQuery, 0)"\nMOBILE_INSTALLED_PACKAGE = "launchActivity.activityInfo.packageName,"\nMOBILE_INSTALLED_ACTIVITY = "launchActivity.activityInfo.name,"\nMOBILE_LEGACY_EXPLICIT_LAUNCH = \'''Intent().setClassName(\n                "com.nuviodebug.com",\n                MainActivity::class.java.name,\n            )\'''\n'''
t=t[:start]+constants+t[end:]
old_block='''    if client == "mobile":\n        # Instrumentation can expose the test APK package via context.packageName.\n        # The production MainActivity class itself is the authoritative source for\n        # the target package, independent of applicationId/build-variant drift.\n        explicit_set_class_count = source.count(MOBILE_EXPLICIT_SET_CLASS)\n        explicit_context_count = source.count(MOBILE_EXPLICIT_CONTEXT_PACKAGE)\n        explicit_main_count = source.count(MOBILE_EXPLICIT_MAIN_ACTIVITY)\n        if explicit_set_class_count != 1 or explicit_context_count != 1 or explicit_main_count != 1:\n            raise ValueError(\n                "expected exactly one generated mobile MainActivity setClassName launch probe, "\n                f"found setClassName={explicit_set_class_count} contextPackage={explicit_context_count} "\n                f"mainActivity={explicit_main_count}"\n            )\n        source = source.replace(MOBILE_EXPLICIT_CONTEXT_PACKAGE, MOBILE_EXPLICIT_TARGET_PACKAGE, 1)\n        if MOBILE_CONTEXT_LAUNCH in source:\n            raise ValueError("obsolete mobile package-launch probe survived code generation")\n        if MOBILE_LEGACY_EXPLICIT_LAUNCH in source:\n            raise ValueError("hard-coded mobile debug package survived code generation")\n'''
new_block='''    if client == "mobile":\n        # The installed launcher component is authoritative. Kotlin namespace,\n        # instrumentation package and applicationId are allowed to differ.\n        explicit_set_class_count = source.count(MOBILE_EXPLICIT_SET_CLASS)\n        launcher_query_count = source.count(MOBILE_LAUNCHER_QUERY)\n        query_count = source.count(MOBILE_QUERY_ACTIVITIES)\n        installed_package_count = source.count(MOBILE_INSTALLED_PACKAGE)\n        installed_activity_count = source.count(MOBILE_INSTALLED_ACTIVITY)\n        if (\n            explicit_set_class_count != 1\n            or launcher_query_count != 1\n            or query_count < 1\n            or installed_package_count != 1\n            or installed_activity_count != 1\n        ):\n            raise ValueError(\n                "expected one generated applicationId-safe Mobile launcher probe, "\n                f"setClassName={explicit_set_class_count} launcherQuery={launcher_query_count} "\n                f"queries={query_count} package={installed_package_count} activity={installed_activity_count}"\n            )\n        for obsolete in (\n            MOBILE_CONTEXT_LAUNCH,\n            MOBILE_EXPLICIT_CONTEXT_PACKAGE,\n            MOBILE_EXPLICIT_TARGET_PACKAGE,\n            MOBILE_LEGACY_EXPLICIT_LAUNCH,\n        ):\n            if obsolete in source:\n                raise ValueError("obsolete namespace/package-based Mobile launcher survived code generation")\n'''
if old_block not in t:
    raise AssertionError('native Android finalizer old mobile block drifted')
t=t.replace(old_block,new_block,1)
old_final='''    if client == "mobile" and (\n        MOBILE_EXPLICIT_SET_CLASS not in source\n        or MOBILE_EXPLICIT_TARGET_PACKAGE not in source\n        or MOBILE_EXPLICIT_MAIN_ACTIVITY not in source\n        or MOBILE_EXPLICIT_CONTEXT_PACKAGE in source\n        or MOBILE_LEGACY_EXPLICIT_LAUNCH in source\n    ):\n        raise ValueError("target-package NuvioMobile MainActivity setClassName launch was not materialized")\n'''
new_final='''    if client == "mobile" and (\n        MOBILE_EXPLICIT_SET_CLASS not in source\n        or MOBILE_LAUNCHER_QUERY not in source\n        or MOBILE_QUERY_ACTIVITIES not in source\n        or MOBILE_INSTALLED_PACKAGE not in source\n        or MOBILE_INSTALLED_ACTIVITY not in source\n        or MOBILE_EXPLICIT_CONTEXT_PACKAGE in source\n        or MOBILE_EXPLICIT_TARGET_PACKAGE in source\n        or MOBILE_LEGACY_EXPLICIT_LAUNCH in source\n    ):\n        raise ValueError("applicationId-safe NuvioMobile launcher resolution was not materialized")\n'''
if old_final not in t:
    raise AssertionError('native Android finalizer final assertion drifted')
t=t.replace(old_final,new_final,1)
t=t.replace(
    '* NuvioMobile\'s reader probe starts the production MainActivity class explicitly in\n  the application package that owns that class. Instrumentation context/package names\n  can refer to the test APK, so they are not authoritative for the target component.',
    '* NuvioMobile\'s reader probe resolves the installed launcher component through\n  PackageManager. Kotlin namespace and instrumentation context are not authoritative\n  for the installed applicationId.'
)
p.write_text(t,encoding='utf-8')

# Align direct finalizer/codegen tests.
p=ROOT/'tests/finalize_native_android_reader_source_test.py'
p.write_text('''#!/usr/bin/env python3\nfrom __future__ import annotations\nimport sys\nfrom pathlib import Path\nROOT=Path(__file__).resolve().parents[1]\nsys.path.insert(0,str(ROOT/"scripts"))\nfrom finalize_native_android_reader_source import finalize_source\nENTRY='emit("FIELD_NATIVE_PLAYER_BEGIN client=mobile fixture=x provider64=x index=0 entry=nuvio-production-player")'\ncurrent_mobile=f\'''\nimport android.content.Intent\nimport com.nuvio.app.MainActivity\n{ENTRY}\nval launcherQuery = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)\nval launchActivity = context.packageManager.queryIntentActivities(launcherQuery, 0)\n    .firstOrNull {{ info -> info.activityInfo?.name == MainActivity::class.java.name }}\n    ?: context.packageManager.queryIntentActivities(launcherQuery, 0).first()\nval intent = Intent().setClassName(\n    launchActivity.activityInfo.packageName,\n    launchActivity.activityInfo.name,\n)\n\'''\nfinalized=finalize_source(current_mobile,"mobile")\nassert "FIELD_NATIVE_PLAYER_ENTRY client=mobile" in finalized\nassert "FIELD_NATIVE_PLAYER_BEGIN client=mobile" not in finalized\nassert "queryIntentActivities(launcherQuery, 0)" in finalized\nassert "launchActivity.activityInfo.packageName" in finalized\nassert "launchActivity.activityInfo.name" in finalized\nassert "MainActivity::class.java.packageName" not in finalized\nlegacy=f\'''{ENTRY}\nval intent = Intent().setClassName(context.packageName, MainActivity::class.java.name)\n\'''\ntry: finalize_source(legacy,"mobile")\nexcept ValueError: pass\nelse: raise AssertionError("namespace-based package launch must be rejected")\ntv='emit("FIELD_NATIVE_PLAYER_BEGIN client=tv fixture=x provider64=x index=0 entry=nuvio-production-player")'\nout=finalize_source(tv,"tv")\nassert "FIELD_NATIVE_PLAYER_ENTRY client=tv" in out\nprint("native Android reader finalizer installed-launcher contract passed")\n''',encoding='utf-8')

p=ROOT/'tests/native_lab_reader_observation_contract_test.py'
t=p.read_text(encoding='utf-8')
old='''# Codegen may initially use instrumentation context as a neutral placeholder. The\n# mandatory finalizer owns the authoritative target-component rewrite and must reject\n# any finalized Mobile source that still points at the test APK package.\nassert 'MOBILE_EXPLICIT_TARGET_PACKAGE = "MainActivity::class.java.packageName,"' in mobile_finalizer\nassert "source = source.replace(MOBILE_EXPLICIT_CONTEXT_PACKAGE, MOBILE_EXPLICIT_TARGET_PACKAGE, 1)" in mobile_finalizer\nassert "or MOBILE_EXPLICIT_CONTEXT_PACKAGE in source" in mobile_finalizer\n'''
new='''# Mobile launcher resolution is based on the installed component. The finalizer\n# validates it and rejects namespace/applicationId assumptions.\nassert 'MOBILE_LAUNCHER_QUERY = "val launcherQuery = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)"' in mobile_finalizer\nassert 'MOBILE_INSTALLED_PACKAGE = "launchActivity.activityInfo.packageName,"' in mobile_finalizer\nassert 'MOBILE_INSTALLED_ACTIVITY = "launchActivity.activityInfo.name,"' in mobile_finalizer\nassert "MOBILE_EXPLICIT_TARGET_PACKAGE in source" in mobile_finalizer\n'''
if old not in t:
    raise AssertionError('native observation finalizer assertions drifted')
t=t.replace(old,new,1)
p.write_text(t,encoding='utf-8')

p=ROOT/'tests/native_player_diagnostics_codegen_test.py'
t=p.read_text(encoding='utf-8')
t=t.replace('assert "MainActivity::class.java.packageName," in mobile','assert "queryIntentActivities(launcherQuery, 0)" in mobile\nassert "launchActivity.activityInfo.packageName," in mobile\nassert "launchActivity.activityInfo.name," in mobile\nassert "MainActivity::class.java.packageName," not in mobile')
p.write_text(t,encoding='utf-8')

# Manifest contains visible rows (active + explicitly disabled retained rows).
p=ROOT/'tests/core_runtime_nonregression_contract_test.py'
t=p.read_text(encoding='utf-8')
t=t.replace('from current_provider_scope import active_provider_count','from current_provider_scope import active_provider_count, visible_provider_count')
t=t.replace('EXPECTED = active_provider_count()','ACTIVE_EXPECTED = active_provider_count()\nVISIBLE_EXPECTED = visible_provider_count()')
t=t.replace('CURRENT_PROVIDER_COUNT','VISIBLE_EXPECTED')
t=t.replace('== EXPECTED','== VISIBLE_EXPECTED')
t=t.replace('f"providers={EXPECTED} provider_timeout_ms=', 'f"providers_visible={VISIBLE_EXPECTED} providers_active={ACTIVE_EXPECTED} provider_timeout_ms=')
p.write_text(t,encoding='utf-8')

# Global guard must protect the new owner order too: media validation first,
# final client-visible branding afterwards. The old condition rejected all 46
# rows solely because it required the opposite historical order.
p=ROOT/'tests/global_stream_output_guard_test.py'
t=p.read_text(encoding='utf-8')
t=t.replace(
    'if branding >= 0 and sanitizer <= branding:\n        weak.append(provider_id)',
    'if branding >= 0 and branding <= sanitizer:\n        weak.append(provider_id)'
)
t=t.replace(
    'managed_terminal_sanitizer={len(rows)} startfix_v3=true fail_closed_v6=true v7_extension_accepted=true',
    'managed_media_sanitizer={len(rows)} startfix_v3=true fail_closed_v6=true v7_extension_accepted=true final_branding_after_media=true'
)
p.write_text(t,encoding='utf-8')

print('retry: presentation, sanitizer, launcher, scope and global guard contracts aligned')
