#!/usr/bin/env python3
"""Make one-provider materialization honor the publication security stage.

The full publication finalizer applies deterministic provider security hardening
after Provider/Core composition and before fixed-point/minimizer validation.
Targeted materialization must produce the same security-normalized bytes; otherwise
a domain-only rebuild can reintroduce console sinks or other already-normalized
provider hazards.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "materialize_provider_v3_one.py"
MARKER = "TARGETED_MATERIALIZER_SECURITY_FINALIZATION_V61"


def main() -> int:
    text = PATH.read_text(encoding="utf-8")
    if MARKER in text:
        print("V61_TARGETED_SECURITY_PATCH already_applied=true")
        return 0

    import_anchor = "import materialize_provider_v3_all as allmat\n"
    import_replacement = (
        import_anchor
        + "from provider_security_hardening import assert_hardened, harden_bytes\n"
    )
    if text.count(import_anchor) != 1:
        raise SystemExit("targeted materializer security import anchor missing/ambiguous")
    text = text.replace(import_anchor, import_replacement, 1)

    anchor = '''    bundle, applied = allmat.apply_overrides(
        provider_id,
        bundle,
        phase="discovery",
        include_global_core=True,
        config_path=allmat.DEFAULT_OVERRIDES,
    )
    text = bundle.decode("utf-8", errors="strict")
'''
    replacement = '''    bundle, applied = allmat.apply_overrides(
        provider_id,
        bundle,
        phase="discovery",
        include_global_core=True,
        config_path=allmat.DEFAULT_OVERRIDES,
    )

    # TARGETED_MATERIALIZER_SECURITY_FINALIZATION_V61
    # Match the authoritative publication pipeline: deterministic security
    # normalization owns the final provider bytes after Provider/Core composition.
    # This is not a post-publication mutation; it is part of composition before
    # minimizer/fixed-point validation and before the asset is written.
    bundle, security_report = harden_bytes(bundle)
    text = bundle.decode("utf-8", errors="strict")
    assert_hardened(text)
'''
    if text.count(anchor) != 1:
        raise SystemExit("targeted materializer security composition anchor missing/ambiguous")
    text = text.replace(anchor, replacement, 1)

    # Record the normalization stage in the one-provider materialization report.
    report_anchor = '''        "minimizer": minimizer_report,
'''
    report_replacement = '''        "minimizer": minimizer_report,
        "securityFinalization": {
            "revision": 1,
            "normalized": bool(security_report.get("changed")),
            "consoleSinkChanges": int(security_report.get("consoleSinkChanges") or 0),
            "consoleShadow": bool(security_report.get("consoleShadow")),
            "hostnameChanges": int(security_report.get("hostnameChanges") or 0),
        },
'''
    if text.count(report_anchor) != 1:
        raise SystemExit("targeted materializer security report anchor missing/ambiguous")
    text = text.replace(report_anchor, report_replacement, 1)

    PATH.write_text(text, encoding="utf-8")
    print("V61_TARGETED_SECURITY_PATCH applied=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
