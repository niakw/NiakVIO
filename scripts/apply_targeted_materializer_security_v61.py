#!/usr/bin/env python3
"""Align one-provider materialization with authoritative publication finalization.

The full publication path owns two deterministic final stages that targeted
materialization must reproduce before writing an asset:
1. provider security normalization after Provider/Core composition;
2. the canonical content-addressed publication filename grammar.

Without these stages a domain-only rebuild can either reintroduce unsafe console
sinks or create bytes that are already fixed-point while the manifest points at a
non-canonical filename, causing the final minimizer gate to fail.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "materialize_provider_v3_one.py"
SECURITY_MARKER = "TARGETED_MATERIALIZER_SECURITY_FINALIZATION_V61"
NAME_MARKER = "TARGETED_MATERIALIZER_PUBLISHED_NAME_V61"


def main() -> int:
    text = PATH.read_text(encoding="utf-8")
    changed = False

    import_anchor = "import materialize_provider_v3_all as allmat\n"
    if SECURITY_MARKER not in text:
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
        changed = True

    if NAME_MARKER not in text:
        security_import = "from provider_security_hardening import assert_hardened, harden_bytes\n"
        publication_import = "from reapply_published_overrides import published_name\n"
        if publication_import not in text:
            if text.count(security_import) != 1:
                raise SystemExit("targeted materializer publication import anchor missing/ambiguous")
            text = text.replace(security_import, security_import + publication_import, 1)

        name_anchor = '''    digest = hashlib.sha256(bundle).hexdigest()
    filename = f"{provider_id}-{digest[:16]}.js"
    relative = f"providers/{filename}"
'''
        name_replacement = '''    digest = hashlib.sha256(bundle).hexdigest()
    # TARGETED_MATERIALIZER_PUBLISHED_NAME_V61
    # Reuse the authoritative finalizer grammar so fixed-point bytes also have
    # a fixed-point content-addressed reference. Never invent a second naming
    # convention in the targeted rebuild path.
    previous_relative = str(entry.get("filename") or "").strip()
    previous_path = Path(previous_relative) if previous_relative else Path(f"{provider_id}--nuvio--seed.js")
    filename = published_name(provider_id, previous_path, digest)
    relative = f"providers/{filename}"
'''
        if text.count(name_anchor) != 1:
            raise SystemExit("targeted materializer published-name anchor missing/ambiguous")
        text = text.replace(name_anchor, name_replacement, 1)
        changed = True

    PATH.write_text(text, encoding="utf-8")
    print(
        "V61_TARGETED_PUBLICATION_PATCH "
        f"changed={str(changed).lower()} security={str(SECURITY_MARKER in text).lower()} "
        f"canonical_name={str(NAME_MARKER in text).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
