#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "automation" / "targeted-provider-contexts.json"
OUTPUT = ROOT / "automation" / "targeted-provider-findings.md"


def compact(text: str, limit: int = 1800) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text[:limit]


def code_chunks(contexts: dict[str, list[str]], *, per_key: int = 2) -> list[str]:
    rows: list[str] = []
    for key, values in contexts.items():
        for value in values[:per_key]:
            rows.append(f"### `{key}`\n\n```text\n{compact(value)}\n```\n")
    return rows


def probe_lines(probes: list[dict[str, Any]]) -> list[str]:
    rows: list[str] = []
    for probe in probes:
        preview = compact(probe.get("json_preview") or "", 600)
        rows.append(
            f"- `{probe.get('requested_url')}` → status `{probe.get('status')}`, "
            f"type `{probe.get('content_type')}`, erreur `{probe.get('error')}`"
            + (f" — `{preview}`" if preview else "")
        )
    return rows


def worker_lines(worker: dict[str, Any]) -> list[str]:
    return [
        f"- returncode: `{worker.get('returncode')}`",
        f"- streams: `{worker.get('stream_count')}`",
        f"- erreur: `{worker.get('error')}`",
        f"- stdout: `{compact(worker.get('stdout_tail') or '', 1800)}`",
        f"- stderr: `{compact(worker.get('stderr_tail') or '', 1200)}`",
    ]


def main() -> int:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    out: list[str] = ["# Diagnostic ciblé des providers VF\n", f"Fixture : **{data.get('fixture')}**\n"]

    streamzo = data["streamzo"]
    out += ["\n## StreamZo\n", "### Probes API\n", *probe_lines(streamzo.get("probes") or []), "\n### Appels trouvés dans le bundle\n"]
    out += code_chunks(streamzo.get("app_contexts") or {}, per_key=2)
    out += ["\n### Données présentes dans la page Interstellar\n"]
    out += code_chunks(streamzo.get("page_contexts") or {}, per_key=1)
    out += ["\n### Worker actuel\n", *worker_lines(streamzo.get("worker") or {})]

    french = data["frenchstream"]
    out += ["\n## Frenchstream\n", f"Base résolue : `{french.get('base')}`\n", "### Page de recherche\n"]
    out += code_chunks(french.get("search_contexts") or {}, per_key=2)
    out += ["\n### Scripts de recherche/lecteur\n"]
    for url, script in (french.get("scripts") or {}).items():
        out.append(f"### `{url}`\n")
        out += code_chunks(script.get("contexts") or {}, per_key=1)
    out += ["\n### Worker actuel\n", *worker_lines(french.get("worker") or {})]

    movix = data["movix"]
    out += ["\n## Movix\n", f"Bundle : `{movix.get('bundle_url')}`\n", "### Probes API\n", *probe_lines(movix.get("probes") or []), "\n### Appels trouvés dans le bundle\n"]
    out += code_chunks(movix.get("bundle_contexts") or {}, per_key=2)
    out += ["\n### Worker actuel\n", *worker_lines(movix.get("worker") or {})]

    OUTPUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
