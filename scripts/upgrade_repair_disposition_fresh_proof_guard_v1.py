#!/usr/bin/env python3
"""Make fresh explicit stream-proof invalidation outrank stale quick-yield rows."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "finalize_provider_repair_disposition_v1_impl.py"
MARKER = "NIAKVIO_FRESH_STREAM_PROOF_GUARD_V1"


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        print("REPAIR_DISPOSITION_FRESH_PROOF_GUARD_V1_OK changed=false")
        return 0
    old = '''        current = set(verified.get(provider) or set())\n        protected = set(locked.get(provider) or set())\n'''
    new = '''        current = set(verified.get(provider) or set())\n        # NIAKVIO_FRESH_STREAM_PROOF_GUARD_V1\n        # Explicit fresh invalidation is newer authority than historical quick-yield.\n        # Keep old rows as evidence, but they cannot restore a proven lane until\n        # a fresh identity-safe positive replaces current_stream_proof.\n        current_stream_proof = patch.get("current_stream_proof") if isinstance(patch.get("current_stream_proof"), dict) else {}\n        if (\n            current_stream_proof.get("requiresFreshIdentitySafePositive") is True\n            and current_stream_proof.get("streamPositive") is False\n        ):\n            current = set()\n            for semantic in required:\n                lane_statuses[provider][semantic].discard("playable_verified")\n                lane_statuses[provider][semantic].add("fresh_identity_safe_positive_required")\n        protected = set(locked.get(provider) or set())\n'''
    if text.count(old) != 1:
        raise SystemExit(f"fresh-proof guard anchor count={text.count(old)}")
    TARGET.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("REPAIR_DISPOSITION_FRESH_PROOF_GUARD_V1_OK changed=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
