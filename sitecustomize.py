"""Load and harden the one-shot Core repair, then remove this root shim."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
SELF = Path(__file__).resolve()
CORE = ROOT / "scripts" / "core_rebuild_safety.py"
TEST = ROOT / "tests" / "core_terminal_export_floor_test.py"


def harden_remote_orphans() -> None:
    text = CORE.read_text(encoding="utf-8")
    start = text.index("def _strip_runtime_domain_orphan_calls(")
    end = text.index("\n\ndef _inject_runtime_domain_overrides(", start)
    helper = r'''def _strip_runtime_domain_orphan_calls(
    text: str,
    insertion: int | None,
    payload: str,
) -> tuple[str, int]:
    """Remove exact no-op call-argument relics left by historical IIFE stripping.

    Terser may leave ``typeof globalThis...,[rules];`` at a byte position that is
    no longer the canonical wrapper insertion point.  The expression has no call
    and no assignment; it only evaluates the global object and a literal array.
    Remove only the exact current generated payload (with or without redundant
    outer parentheses).  A different payload remains untouched, so unrelated
    provider expressions still fail closed instead of being guessed away.
    """
    if insertion is None:
        return text, 0
    variants = (
        f'(typeof globalThis!=="undefined"?globalThis:this,{payload});',
        f'typeof globalThis!=="undefined"?globalThis:this,{payload};',
    )
    removed = 0
    output = text
    for variant in variants:
        count = output.count(variant)
        if count:
            output = output.replace(variant, "")
            removed += count
    return output, removed
'''
    text = text[:start] + helper + text[end:]
    CORE.write_text(text, encoding="utf-8")

    test = TEST.read_text(encoding="utf-8")
    start = test.index("def test_runtime_domain_orphan_invocations_collapse_fail_closed()")
    end = test.index("\ndef test_runtime_domain_duplicate_bootstraps_collapse_fail_closed()", start)
    regression = '''def test_runtime_domain_orphan_invocations_collapse_fail_closed() -> None:\n    rules = {"old.example": "new.example"}\n    provider = "const prelude=1;const providerByte=1;function getStreams(){};module.exports=__provider;\\n"\n    canonical, _ = inject_domain_overrides(provider, rules)\n    call_start = canonical.index('(typeof globalThis!=="undefined"?globalThis:this,')\n    call_end = canonical.index(";", call_start) + 1\n    orphan = canonical[call_start:call_end]\n    terser_orphan = orphan[1:-1] + ";"\n\n    # Put both historical relic forms inside provider bytes, deliberately away\n    # from the canonical wrapper insertion point. This is the production shape\n    # that previously grew one expression per rebuild pass.\n    remote_at = canonical.index("const providerByte=1;")\n    damaged = canonical[:remote_at] + orphan + terser_orphan + canonical[remote_at:]\n    repaired, _ = inject_domain_overrides(damaged, rules)\n    assert repaired == canonical\n\n    markerless = damaged.replace("/* NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1 */\\n", "", 1)\n    repaired_markerless, _ = inject_domain_overrides(markerless, rules)\n    assert repaired_markerless == canonical\n\n    foreign = terser_orphan.replace("new.example", "foreign.example")\n    foreign_input = canonical[:remote_at] + foreign + canonical[remote_at:]\n    foreign_output, _ = inject_domain_overrides(foreign_input, rules)\n    assert foreign in foreign_output\n    assert foreign_output.count("__nuvioDomainOverrideV1") == 1\n\n\n'''
    test = test[:start] + regression + test[end + 1:]
    TEST.write_text(test, encoding="utf-8")


try:
    # The inner bootstrap first materializes the complete-IIFE scanner and the
    # baseline orphan helper into durable Core source, then self-removes.
    import scripts.sitecustomize  # noqa: F401
    harden_remote_orphans()
finally:
    # Core publication commits only the durable source/tests and the deletion of
    # both temporary shims/workflow once the full fixed point has succeeded.
    if SELF.exists():
        SELF.unlink()
