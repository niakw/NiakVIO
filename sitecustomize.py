"""One-shot runner bootstrap for the final runtime-domain fixed-point repair.

The inner bootstrap materializes the durable scanner/orphan cleaner first. This
shim then fixes the remaining ordering bug: historical orphan calls must be
removed *before* wrapper spans/insertion are computed, otherwise deleting an
orphan before the wrapper shifts the canonical insertion point and grows the
provider on every rebuild. A regression covering that exact ordering is added.
Successful Core publication deletes both bootstraps and publishes only the
durable Core/test changes.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
CORE = ROOT / "scripts" / "core_rebuild_safety.py"
TEST = ROOT / "tests" / "core_terminal_export_floor_test.py"
SELF = Path(__file__).resolve()


def patch_cleanup_order() -> None:
    text = CORE.read_text(encoding="utf-8")

    old = '''    marker = "NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1"\n    marker_comment = f"/* {marker} */"\n    spans = _runtime_domain_wrapper_spans(text)\n'''
    new = '''    marker = "NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1"\n    marker_comment = f"/* {marker} */"\n    # Historical invocation-only debris can occur before the canonical wrapper.\n    # Remove it before computing spans so the insertion coordinate is derived\n    # from the cleaned provider bytes and cannot drift after deletion.\n    text, orphan_count = _strip_runtime_domain_orphan_calls(text, rules)\n    spans = _runtime_domain_wrapper_spans(text)\n'''
    if new not in text:
        if old not in text:
            raise RuntimeError("runtime-domain span ordering anchor missing")
        text = text.replace(old, new, 1)

    post_cleanup = "    base, orphan_count = _strip_runtime_domain_orphan_calls(base, rules)\n"
    if post_cleanup in text:
        text = text.replace(post_cleanup, "", 1)

    guarded = "    if existing_span is not None and orphan_count == 0 and marker_comment in text[existing_span[0]:existing_span[1]]:\n"
    stable = "    if existing_span is not None and marker_comment in text[existing_span[0]:existing_span[1]]:\n"
    if guarded in text:
        text = text.replace(guarded, stable, 1)
    elif stable not in text:
        raise RuntimeError("runtime-domain existing-span condition missing")

    if text.count("_strip_runtime_domain_orphan_calls(text, rules)") != 1:
        raise RuntimeError("runtime-domain orphan cleanup must run exactly once before span discovery")
    if "_strip_runtime_domain_orphan_calls(base" in text:
        raise RuntimeError("post-span runtime-domain cleanup remains")

    CORE.write_text(text, encoding="utf-8")


def patch_regression() -> None:
    text = TEST.read_text(encoding="utf-8")
    name = "test_runtime_domain_orphan_before_wrapper_keeps_insertion_stable"
    if f"def {name}()" not in text:
        anchor = "def test_runtime_domain_duplicate_bootstraps_collapse_fail_closed() -> None:\n"
        if anchor not in text:
            raise RuntimeError("runtime-domain regression anchor missing")
        regression = '''def test_runtime_domain_orphan_before_wrapper_keeps_insertion_stable() -> None:\n    import base64, json\n\n    rules = {"old.example": "new.example"}\n    provider = "const providerByte=1;function getStreams(){};module.exports=__provider;\\n"\n    canonical, _ = inject_domain_overrides(provider, rules)\n    payload = json.dumps(\n        [[base64.b64encode(b"old.example").decode("ascii"), "new.example"]],\n        separators=(",", ":"),\n    )\n    orphan = f'typeof globalThis!=="undefined"?globalThis:this,{payload};'\n\n    damaged = orphan + canonical\n    repaired, _ = inject_domain_overrides(damaged, rules)\n    assert repaired == canonical\n\n    damaged_twice = orphan + orphan + canonical\n    repaired_twice, _ = inject_domain_overrides(damaged_twice, rules)\n    assert repaired_twice == canonical\n\n\n'''
        text = text.replace(anchor, regression + anchor, 1)

    call = f"    {name}()\n"
    anchor = "    test_runtime_domain_duplicate_bootstraps_collapse_fail_closed()\n"
    if call not in text:
        if anchor not in text:
            raise RuntimeError("runtime-domain regression call anchor missing")
        text = text.replace(anchor, call + anchor, 1)

    TEST.write_text(text, encoding="utf-8")


try:
    import scripts.sitecustomize  # noqa: F401
    patch_cleanup_order()
    patch_regression()
finally:
    if SELF.exists():
        SELF.unlink()
