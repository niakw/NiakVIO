#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 anchor, got {count}")
    return text.replace(old, new, 1)


def patch_client_scope() -> None:
    path = "scripts/prepare_native_corpus_client.py"
    text = read(path)
    if "def provider_scope_ids(" not in text:
        anchor = 'MATERIALIZED_SENTINEL = ROOT / ".native-provider-overrides-materialized"\n'
        helper = '''MATERIALIZED_SENTINEL = ROOT / ".native-provider-overrides-materialized"


def provider_scope_ids() -> set[str] | None:
    """Optional exact provider scope for a native Lab campaign.

    The scope file is repository-local JSON. Hub matrices expose provider ids via
    ``rows[].manifestId`` (or ``rows[].provider`` for compatible inventories).
    When configured, this is an execution allowlist, not merely a reporting filter.
    """
    raw = os.environ.get("NIAKVIO_PROVIDER_SCOPE_MATRIX", "").strip()
    if not raw:
        return None
    candidate = Path(raw)
    scope_path = candidate if candidate.is_absolute() else ROOT / candidate
    scope_path = scope_path.resolve()
    try:
        scope_path.relative_to(ROOT.resolve())
    except ValueError as error:
        raise SystemExit(f"native provider scope must live inside repository: {raw}") from error
    if not scope_path.is_file():
        raise SystemExit(f"native provider scope not found: {scope_path}")
    data = json.loads(scope_path.read_text(encoding="utf-8"))
    rows = data.get("rows") if isinstance(data.get("rows"), list) else []
    ids = {
        str(row.get("manifestId") or row.get("provider") or "").strip().casefold()
        for row in rows if isinstance(row, dict)
        if str(row.get("manifestId") or row.get("provider") or "").strip()
    }
    expected = int(data.get("hubCount") or data.get("providerCount") or len(ids))
    if not ids or len(ids) != expected:
        raise SystemExit(
            f"native provider scope invalid: ids={len(ids)} expected={expected} file={scope_path}"
        )
    print(f"FIELD_NATIVE_PROVIDER_SCOPE file={scope_path.relative_to(ROOT)} providers={len(ids)}")
    return ids
'''
        text = replace_once(text, anchor, helper, "client scope helper")

    old = '''    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    providers: list[dict] = []
    seen: set[str] = set()
    for row in data.get("scrapers", []):'''
    new = '''    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    scope_ids = provider_scope_ids()
    providers: list[dict] = []
    seen: set[str] = set()
    for row in data.get("scrapers", []):'''
    if old in text:
        text = replace_once(text, old, new, "client scope init")
    elif "scope_ids = provider_scope_ids()" not in text:
        raise SystemExit("client scope init anchor missing")

    old = '''        if not provider_id or not filename or key in seen:
            continue
        seen.add(key)
        providers.append('''
    new = '''        if not provider_id or not filename or key in seen:
            continue
        if scope_ids is not None and key not in scope_ids:
            continue
        seen.add(key)
        providers.append('''
    if old in text:
        text = replace_once(text, old, new, "client scope filter")
    elif "scope_ids is not None and key not in scope_ids" not in text:
        raise SystemExit("client scope filter anchor missing")

    old = '''    if not providers:
        raise SystemExit(f"selected manifest contains no stageable providers: {manifest_file}")
    return providers'''
    new = '''    if not providers:
        raise SystemExit(f"selected manifest contains no stageable providers: {manifest_file}")
    if scope_ids is not None:
        missing = sorted(scope_ids - seen)
        if missing:
            raise SystemExit(
                "native provider scope references provider(s) absent from manifest: " + ",".join(missing)
            )
        if len(providers) != len(scope_ids):
            raise SystemExit(f"native provider scope mismatch: staged={len(providers)} expected={len(scope_ids)}")
    return providers'''
    if old in text:
        text = replace_once(text, old, new, "client scope validation")
    elif "native provider scope mismatch" not in text:
        raise SystemExit("client scope validation anchor missing")
    write(path, text)


def patch_gate_scope() -> None:
    path = "scripts/gate_native_declared_provider_matrix.py"
    text = read(path)
    if "def load_scope_ids(" not in text:
        anchor = '''def route(provider: str, media_type: str) -> tuple[str, str]:
    return (provider.casefold(), media_type.casefold())
'''
        helper = '''def route(provider: str, media_type: str) -> tuple[str, str]:
    return (provider.casefold(), media_type.casefold())


def load_scope_ids(scope_path: Path | None) -> set[str] | None:
    raw_env = __import__("os").environ.get("NIAKVIO_PROVIDER_SCOPE_MATRIX", "").strip()
    path = scope_path
    if path is None and raw_env:
        candidate = Path(raw_env)
        path = candidate if candidate.is_absolute() else Path.cwd() / candidate
    if path is None:
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("rows") if isinstance(data.get("rows"), list) else []
    ids = {
        str(row.get("manifestId") or row.get("provider") or "").strip().casefold()
        for row in rows if isinstance(row, dict)
        if str(row.get("manifestId") or row.get("provider") or "").strip()
    }
    expected = int(data.get("hubCount") or data.get("providerCount") or len(ids))
    if not ids or len(ids) != expected:
        raise SystemExit(f"invalid native provider scope: ids={len(ids)} expected={expected} path={path}")
    return ids
'''
        text = replace_once(text, anchor, helper, "gate scope helper")

    old = '''    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("logs", nargs="+", type=Path)'''
    new = '''    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--scope-matrix", type=Path, default=None)
    parser.add_argument("logs", nargs="+", type=Path)'''
    if old in text:
        text = replace_once(text, old, new, "gate scope arg")
    elif 'parser.add_argument("--scope-matrix"' not in text:
        raise SystemExit("gate scope arg anchor missing")

    old = '''    fixture_by_type = ((corpus.get("native_reader_acceptance") or {}).get("fixture_by_type") or {})

    expected: set[tuple[str, str]] = set()'''
    new = '''    fixture_by_type = ((corpus.get("native_reader_acceptance") or {}).get("fixture_by_type") or {})
    scope_ids = load_scope_ids(args.scope_matrix)

    expected: set[tuple[str, str]] = set()'''
    if old in text:
        text = replace_once(text, old, new, "gate scope load")
    elif "scope_ids = load_scope_ids" not in text:
        raise SystemExit("gate scope load anchor missing")

    old = '''        key = provider.casefold()
        if row.get("enabled") is not True:
            disabled_ids.add(key)
            continue
        provider_ids.add(key)'''
    new = '''        key = provider.casefold()
        if scope_ids is not None and key not in scope_ids:
            disabled_ids.add(key)
            continue
        if scope_ids is None and row.get("enabled") is not True:
            disabled_ids.add(key)
            continue
        provider_ids.add(key)'''
    if old in text:
        text = replace_once(text, old, new, "gate scope filter")
    elif "scope_ids is not None and key not in scope_ids" not in text:
        raise SystemExit("gate scope filter anchor missing")

    marker = '''    missing_fixture_types = [kind for kind in TYPES if not str(fixture_by_type.get(kind) or "").strip()]'''
    insert = '''    if scope_ids is not None:
        missing_scope = sorted(scope_ids - provider_ids)
        if missing_scope:
            raise SystemExit("scope provider(s) missing from manifest: " + ",".join(missing_scope))
        if len(provider_ids) != len(scope_ids):
            raise SystemExit(f"scope mismatch: providers={len(provider_ids)} expected={len(scope_ids)}")

    missing_fixture_types = [kind for kind in TYPES if not str(fixture_by_type.get(kind) or "").strip()]'''
    if "missing_scope = sorted(scope_ids - provider_ids)" not in text:
        text = replace_once(text, marker, insert, "gate scope validation")

    # iOS rotating slugs cannot be mapped back through static fixture_by_type on
    # PROVIDER_END. FIELD_NATIVE_IOS_RESULT already carries mediaType; count that
    # event as the terminal route observation directly.
    old = '''                    if r[0] in provider_ids:
                        lane_outcomes[r] = merge_outcome(lane_outcomes[r], outcome)
                    elif r[0] in disabled_ids:'''
    new = '''                    if r[0] in provider_ids:
                        completed.add(r)
                        lane_outcomes[r] = merge_outcome(lane_outcomes[r], outcome)
                    elif r[0] in disabled_ids:'''
    # Restrict replacement to the first occurrence inside the iOS block.
    if old in text:
        text = text.replace(old, new, 1)
    write(path, text)


def patch_ios_scope() -> None:
    path = "scripts/prepare_native_ios_reader_acceptance.py"
    text = read(path)
    if "def provider_scope_ids(" not in text:
        anchor = 'IOS_KOTLIN_TARGET = Path("nuvio-mobile/composeApp/src/iosFull/kotlin/com/nuvio/app/NiakvioIosLab.kt")\n'
        helper = '''IOS_KOTLIN_TARGET = Path("nuvio-mobile/composeApp/src/iosFull/kotlin/com/nuvio/app/NiakvioIosLab.kt")


def provider_scope_ids() -> list[str]:
    raw = __import__("os").environ.get("NIAKVIO_PROVIDER_SCOPE_MATRIX", "").strip()
    if not raw:
        return []
    candidate = Path(raw)
    path = candidate if candidate.is_absolute() else ROOT / candidate
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("rows") if isinstance(data.get("rows"), list) else []
    ids = sorted({
        str(row.get("manifestId") or row.get("provider") or "").strip().casefold()
        for row in rows if isinstance(row, dict)
        if str(row.get("manifestId") or row.get("provider") or "").strip()
    })
    expected = int(data.get("hubCount") or data.get("providerCount") or len(ids))
    if not ids or len(ids) != expected:
        raise SystemExit(f"invalid iOS provider scope: ids={len(ids)} expected={expected} path={path}")
    return ids
'''
        text = replace_once(text, anchor, helper, "ios scope helper")

    old = '''private val fixtures = __FIXTURES__
private var started = false'''
    new = '''private val fixtures = __FIXTURES__
private val scopeProviderIds = __SCOPE_PROVIDER_IDS__
private var started = false'''
    if old in text:
        text = replace_once(text, old, new, "ios scope template")
    elif "scopeProviderIds = __SCOPE_PROVIDER_IDS__" not in text:
        raise SystemExit("ios scope template anchor missing")

    old = '''    val allIosProviders = manifest.scrapers.filter {
        supportsIos(it.supportedPlatforms, it.disabledPlatforms)
    }'''
    new = '''    val allIosProviders = manifest.scrapers.filter {
        supportsIos(it.supportedPlatforms, it.disabledPlatforms) &&
            (scopeProviderIds.isEmpty() || it.id.lowercase() in scopeProviderIds)
    }'''
    if old in text:
        text = replace_once(text, old, new, "ios scope runtime filter")
    elif "scopeProviderIds.isEmpty()" not in text:
        raise SystemExit("ios scope runtime filter anchor missing")

    if "def kotlin_string_set(" not in text:
        anchor = '''def kotlin_fixture_list(rows: list[dict]) -> str:
'''
        helper = '''def kotlin_string_set(values: list[str]) -> str:
    if not values:
        return "emptySet<String>()"
    return "setOf(" + ", ".join(json.dumps(value) for value in values) + ")"


def kotlin_fixture_list(rows: list[dict]) -> str:
'''
        text = replace_once(text, anchor, helper, "ios string set helper")

    old = '''    source = KOTLIN_TEMPLATE.replace("__PROVIDER_TIMEOUT_MS__", str(PROVIDER_TIMEOUT_MS))
    source = source.replace("__FIXTURES__", kotlin_fixture_list(rows))'''
    new = '''    scope_ids = provider_scope_ids()
    source = KOTLIN_TEMPLATE.replace("__PROVIDER_TIMEOUT_MS__", str(PROVIDER_TIMEOUT_MS))
    source = source.replace("__FIXTURES__", kotlin_fixture_list(rows))
    source = source.replace("__SCOPE_PROVIDER_IDS__", kotlin_string_set(scope_ids))'''
    if old in text:
        text = replace_once(text, old, new, "ios scope materialize")
    elif 'source.replace("__SCOPE_PROVIDER_IDS__"' not in text:
        raise SystemExit("ios scope materialize anchor missing")

    old = '''    print("FIELD_NATIVE_IOS_PREPARED fixtures=" + ",".join(row["slug"] for row in rows))'''
    new = '''    print(
        "FIELD_NATIVE_IOS_PREPARED fixtures=" + ",".join(row["slug"] for row in rows)
        + f" provider_scope={len(scope_ids) if scope_ids else 'all'}"
    )'''
    if old in text:
        text = replace_once(text, old, new, "ios scope telemetry")
    write(path, text)


def main() -> int:
    patch_client_scope()
    patch_gate_scope()
    patch_ios_scope()
    print("hub46 native scope integration patch complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
