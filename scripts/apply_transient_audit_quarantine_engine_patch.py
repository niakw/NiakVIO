#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch_reapply() -> None:
    path = ROOT / "scripts" / "reapply_published_overrides.py"
    text = path.read_text(encoding="utf-8")
    marker_anchor = 'ADAPTIVE_DOMAIN_SCRIPT = ROOT / "scripts" / "provider_patches" / "adaptive_domain_recovery.py"\n'
    if 'AUDIT_QUARANTINE_MARKER = "NUVIO_PROVIDER_QUARANTINE_V1"' not in text:
        if marker_anchor not in text:
            raise SystemExit("reapply constant anchor missing")
        text = text.replace(
            marker_anchor,
            marker_anchor
            + 'AUDIT_QUARANTINE_MARKER = "NUVIO_PROVIDER_QUARANTINE_V1"\n'
            + 'AUDIT_QUARANTINE_MODE = "catalogue_audit_safety_quarantine"\n',
            1,
        )

    start_anchor = "        original = path.read_bytes()\n"
    end_anchor = "        changed = patched != original\n"
    start = text.index(start_anchor)
    end = text.index(end_anchor, start)
    body = text[start + len(start_anchor):end]
    if "audit_terminal_quarantine" not in body:
        provenance_line = "        provider_provenance = provenance_rows.get(provider_id) if provenance_rows else None\n"
        if provenance_line not in body:
            raise SystemExit("reapply provenance anchor missing")
        body = body.replace(provenance_line, "", 1)
        indented = "".join(("    " + line if line.strip() else line) for line in body.splitlines(keepends=True))
        replacement = (
            start_anchor
            + provenance_line
            + "        audit_terminal_quarantine = (\n"
            + '            AUDIT_QUARANTINE_MARKER.encode("utf-8") in original\n'
            + "            and isinstance(provider_provenance, dict)\n"
            + '            and str(provider_provenance.get("activation_mode") or "") == AUDIT_QUARANTINE_MODE\n'
            + "        )\n"
            + "        if audit_terminal_quarantine:\n"
            + "            patched = original\n"
            + "            records = []\n"
            + "        else:\n"
            + indented
        )
        text = text[:start] + replacement + text[end:]
    path.write_text(text, encoding="utf-8")


def patch_validator() -> None:
    path = ROOT / "scripts" / "validate_published_overrides.py"
    text = path.read_text(encoding="utf-8")
    if "import hashlib\n" not in text:
        text = text.replace(
            "from __future__ import annotations\n\n",
            "from __future__ import annotations\n\nimport hashlib\n",
            1,
        )
    constants_anchor = "GENERATED_RUNTIME_PROFILE_MARKERS = {\n"
    if 'AUDIT_QUARANTINE_MARKER = "NUVIO_PROVIDER_QUARANTINE_V1"' not in text:
        idx = text.index(constants_anchor)
        text = (
            text[:idx]
            + 'AUDIT_QUARANTINE_MARKER = "NUVIO_PROVIDER_QUARANTINE_V1"\n'
            + 'AUDIT_QUARANTINE_MODE = "catalogue_audit_safety_quarantine"\n\n'
            + text[idx:]
        )
    anchor = '        records = provider_provenance.get("local_patches") or []\n'
    if 'audit_quarantine = str(provider_provenance.get("activation_mode")' not in text:
        insertion = '''        audit_quarantine = str(provider_provenance.get("activation_mode") or "") == AUDIT_QUARANTINE_MODE
        if audit_quarantine:
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            if entry.get("enabled") is not False:
                errors.append(f"{cid}: audit safety quarantine is not disabled")
            if AUDIT_QUARANTINE_MARKER not in text:
                errors.append(f"{cid}: audit safety quarantine marker is missing")
            if provider_provenance.get("activation_eligible") is not False:
                errors.append(f"{cid}: audit safety quarantine remains activation eligible")
            if str(provider_provenance.get("published_filename") or "") != target.relative_to(ROOT).as_posix():
                errors.append(f"{cid}: audit safety quarantine provenance path mismatch")
            if str(provider_provenance.get("patched_sha256") or "") != digest:
                errors.append(f"{cid}: audit safety quarantine provenance SHA mismatch")
            continue
'''
        if anchor not in text:
            raise SystemExit("published validator anchor missing")
        text = text.replace(anchor, insertion + anchor, 1)
    path.write_text(text, encoding="utf-8")


def patch_audit() -> None:
    path = ROOT / "scripts" / "audit_catalogue_identity_media.py"
    text = path.read_text(encoding="utf-8")
    if "import sys\n" not in text:
        text = text.replace("import subprocess\n", "import subprocess\nimport sys\n", 1)
    return_anchor = "    return 1 if playable_false_positive or wrong_content or hls_failures else 0\n"
    if "NUVIO_CATALOGUE_AUDIT_QUARANTINE_DONE" not in text:
        replacement = '''    conclusive_failure = bool(playable_false_positive or wrong_content or hls_failures)
    evidence_path = Path("/tmp/release-generation.json")
    if (
        conclusive_failure
        and evidence_path.is_file()
        and os.environ.get("NUVIO_CATALOGUE_AUDIT_QUARANTINE_DONE") != "1"
    ):
        pre_quarantine = OUTPUT.with_name(OUTPUT.stem + ".pre-quarantine" + OUTPUT.suffix)
        pre_quarantine.write_text(OUTPUT.read_text(encoding="utf-8"), encoding="utf-8")
        subprocess.run([
            sys.executable,
            str(ROOT / "scripts" / "quarantine_catalogue_audit_failures.py"),
            "--audit", str(OUTPUT),
            "--evidence", str(evidence_path),
            "--workflow-run-id", str(os.environ.get("GITHUB_RUN_ID") or "0"),
            "--tested-commit-sha", str(os.environ.get("GITHUB_SHA") or ""),
        ], cwd=ROOT, check=True)
        rerun_env = dict(os.environ)
        rerun_env["NUVIO_CATALOGUE_AUDIT_QUARANTINE_DONE"] = "1"
        print("catalogue/media audit: conclusive offenders quarantined; rerunning exact audit")
        rerun = subprocess.run([sys.executable, str(Path(__file__).resolve())], cwd=ROOT, env=rerun_env, check=False)
        return int(rerun.returncode)
    return 1 if conclusive_failure else 0
'''
        if return_anchor not in text:
            raise SystemExit("catalogue audit return anchor missing")
        text = text.replace(return_anchor, replacement, 1)
    path.write_text(text, encoding="utf-8")


def validate_markers() -> None:
    checks = {
        ROOT / "scripts" / "reapply_published_overrides.py": [
            "audit_terminal_quarantine",
            "catalogue_audit_safety_quarantine",
        ],
        ROOT / "scripts" / "validate_published_overrides.py": [
            "audit safety quarantine provenance SHA mismatch",
        ],
        ROOT / "scripts" / "audit_catalogue_identity_media.py": [
            "NUVIO_CATALOGUE_AUDIT_QUARANTINE_DONE",
            "quarantine_catalogue_audit_failures.py",
        ],
    }
    for path, needles in checks.items():
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                raise SystemExit(f"missing patched marker {needle!r} in {path.relative_to(ROOT)}")


def main() -> int:
    patch_reapply()
    patch_validator()
    patch_audit()
    validate_markers()
    print("transient audit quarantine boundaries patched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
