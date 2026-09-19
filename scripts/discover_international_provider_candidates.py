#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
import urllib.parse
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANUAL = ROOT / "automation" / "international-provider-manual-candidates.json"
DEFAULT_CATALOG = ROOT / "provider_catalog.json"
DEFAULT_HUBS = ROOT / "provider-hubs.json"
DEFAULT_OUT_JSON = ROOT / "research" / "international-provider-candidates.json"
DEFAULT_OUT_CSV = ROOT / "research" / "international-provider-candidates.csv"
DEFAULT_OUT_XLSX = ROOT / "research" / "international-provider-candidates.xlsx"

REJECTED_ROUTE_HOST_SUFFIXES = (
    "github.com", "githubusercontent.com", "gitlab.com", "bitbucket.org",
    "codeberg.org", "sourceforge.net",
)


def norm(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode().casefold()
    return re.sub(r"[^a-z0-9]+", "", text)


def valid_public_candidate_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(str(url or ""))
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    hostname = parsed.hostname.casefold().strip(".")
    return not any(hostname == suffix or hostname.endswith("." + suffix) for suffix in REJECTED_ROUTE_HOST_SUFFIXES)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def known_catalog_names(path: Path) -> set[str]:
    data = load_json(path)
    output: set[str] = set()
    for row in data.get("providers") or []:
        if not isinstance(row, dict):
            continue
        scraper = row.get("scraper") or {}
        for value in (row.get("canonicalId"), scraper.get("id"), scraper.get("name")):
            key = norm(value)
            if key:
                output.add(key)
    return output


def canonical_candidates(manual: dict, known: set[str]) -> tuple[list[dict], list[dict]]:
    accepted: dict[str, dict] = {}
    rejected: list[dict] = []
    for raw in manual.get("candidates") or []:
        if not isinstance(raw, dict):
            continue
        row = dict(raw)
        name = str(row.get("name") or "").strip()
        market = str(row.get("market") or "").strip()
        route = str(row.get("route") or "").strip()
        hub = str(row.get("hub") or "").strip()
        key = norm(name)
        reason = ""
        if not key or not market:
            reason = "missing_identity_or_market"
        elif key in known:
            reason = "already_in_niakvio"
        elif not valid_public_candidate_url(route):
            reason = "missing_or_rejected_web_route"
        elif hub and not valid_public_candidate_url(hub):
            reason = "rejected_hub_url"
        if reason:
            rejected.append({"name": name, "market": market, "route": route, "reason": reason})
            continue

        row["score"] = max(0, min(100, int(row.get("score") or 0)))
        row["hub"] = hub
        row["route"] = route
        row["source_url"] = str(row.get("source_url") or "").strip()
        row["source_kind"] = str(row.get("source_kind") or "manual_curated")
        row["hub_type"] = str(row.get("hub_type") or ("direct-only" if not hub else "hub"))
        current = accepted.get(key)
        if current is None or row["score"] > current["score"]:
            accepted[key] = row

    return list(accepted.values()), rejected


def select_coverage_first(rows: list[dict], max_candidates: int, min_per_market: int, per_market_cap: int) -> list[dict]:
    by_market: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_market[row["market"]].append(row)
    for values in by_market.values():
        values.sort(key=lambda row: (-int(row["score"]), row["name"].casefold()))

    markets = sorted(by_market, key=lambda market: (-by_market[market][0]["score"], market.casefold()))
    chosen: list[dict] = []
    used: dict[str, int] = defaultdict(int)

    floor = max(1, min(min_per_market, per_market_cap))
    for depth in range(floor):
        for market in markets:
            if len(chosen) >= max_candidates:
                break
            if depth < len(by_market[market]):
                chosen.append(by_market[market][depth])
                used[market] += 1
        if len(chosen) >= max_candidates:
            break

    while len(chosen) < max_candidates:
        progressed = False
        for market in markets:
            if len(chosen) >= max_candidates:
                break
            idx = used[market]
            if idx < min(per_market_cap, len(by_market[market])):
                chosen.append(by_market[market][idx])
                used[market] += 1
                progressed = True
        if not progressed:
            break

    chosen.sort(key=lambda row: (row["market"].casefold(), -int(row["score"]), row["name"].casefold()))
    score_order = sorted(chosen, key=lambda row: (-int(row["score"]), row["market"].casefold(), row["name"].casefold()))
    rank_by_identity = {id(row): rank for rank, row in enumerate(score_order, 1)}
    for row in chosen:
        row["rank"] = rank_by_identity[id(row)]
        row["tier"] = "A" if row["score"] >= 90 else ("B" if row["score"] >= 82 else "C")
    return chosen


def build_hub_gaps(hubs_path: Path, manual: dict) -> list[dict]:
    data = load_json(hubs_path)
    suggestions = manual.get("hub_suggestions") or {}
    rows: list[dict] = []
    for provider_id, provider in (data.get("providers") or {}).items():
        if not isinstance(provider, dict) or provider.get("hub"):
            continue
        suggestion = suggestions.get(provider_id) or {}
        sources = provider.get("sources") or []
        source_types = sorted({
            str(source.get("type") or "")
            for source in sources
            if isinstance(source, dict) and source.get("type")
        })
        search_queries = provider.get("search_queries") or []
        direct = str(provider.get("direct") or "")
        suggested_hub = str(suggestion.get("hub") or "")
        rows.append({
            "provider_id": provider_id,
            "name": provider.get("name") or provider_id,
            "category": provider.get("category") or "",
            "direct": direct,
            "suggested_hub": suggested_hub,
            "suggested_hub_type": suggestion.get("hub_type") or "",
            "suggestion_confidence": suggestion.get("confidence") or "",
            "search_queries": " | ".join(str(value) for value in search_queries),
            "current_source_types": ", ".join(source_types),
            "priority": 100 if not direct else (95 if suggested_hub else 75),
            "note": suggestion.get("note") or (
                "No stable hub recorded; keep LKG/direct route and search for an official address hub, "
                "public Telegram address channel or stable status page."
            ),
            "source_url": suggestion.get("source_url") or "",
        })
    rows.sort(key=lambda row: (-int(row["priority"]), str(row["category"]).casefold(), str(row["name"]).casefold()))
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "rank", "market", "languages", "name", "content", "tier", "score",
        "route", "hub", "hub_type", "note", "source_url",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([row.get(column, "") for column in columns])


def xcell(ref: str, value: object, style: int = 0) -> str:
    style_attr = f' s="{style}"' if style else ""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f'<c r="{ref}"{style_attr}><v>{value}</v></c>'
    return f'<c r="{ref}" t="inlineStr"{style_attr}><is><t>{escape(str(value or ""))}</t></is></c>'


def col_letter(number: int) -> str:
    output = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        output = chr(65 + remainder) + output
    return output


def sheet_xml(matrix: list[list[object]], widths: list[float], freeze: bool = True) -> str:
    rows = []
    for row_index, row in enumerate(matrix, 1):
        cells = [
            xcell(f"{col_letter(column_index)}{row_index}", value, 1 if row_index == 1 else 0)
            for column_index, value in enumerate(row, 1)
        ]
        rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    columns = "".join(
        f'<col min="{index}" max="{index}" width="{width}" customWidth="1"/>'
        for index, width in enumerate(widths, 1)
    )
    views = (
        '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" '
        'activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
        if freeze else '<sheetViews><sheetView workbookViewId="0"/></sheetViews>'
    )
    autofilter = f'<autoFilter ref="A1:{col_letter(len(widths))}{max(1, len(matrix))}"/>'
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        + views + f'<cols>{columns}</cols><sheetData>{"".join(rows)}</sheetData>{autofilter}</worksheet>'
    )


def write_xlsx(path: Path, rows: list[dict], gaps: list[dict], meta: dict) -> None:
    candidate_headers = [
        "Rank qualité", "Pays / marché", "Langue(s)", "Candidat", "Contenu", "Tier",
        "Score /100", "Route web réelle", "Hub / Telegram / status", "Type de hub",
        "Pourquoi / prochaine étape", "Source de découverte",
    ]
    candidates = [candidate_headers] + [[
        row["rank"], row["market"], row.get("languages", ""), row["name"], row.get("content", ""),
        row["tier"], row["score"], row["route"], row.get("hub", ""), row.get("hub_type", ""),
        row.get("note", ""), row.get("source_url", ""),
    ] for row in rows]

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["market"]].append(row)
    coverage = [["Pays / marché", "Nb retenu", "Meilleur score", "Avec hub stable", "Objectif couverture"]]
    for market in sorted(grouped, key=str.casefold):
        values = grouped[market]
        coverage.append([
            market,
            len(values),
            max(int(row["score"]) for row in values),
            sum(1 for row in values if row.get("hub")),
            "OK" if len(values) >= meta["min_per_market"] else "SOURCE RARE",
        ])

    gap_headers = [
        "Priorité", "Provider NiakVIO", "ID", "Catégorie", "Direct/LKG actuel",
        "Hub proposé", "Type", "Confiance", "Recherche existante", "Sources actuelles",
        "Action", "Source proposition",
    ]
    gap_matrix = [gap_headers] + [[
        row["priority"], row["name"], row["provider_id"], row["category"], row["direct"],
        row["suggested_hub"], row["suggested_hub_type"], row["suggestion_confidence"],
        row["search_queries"], row["current_source_types"], row["note"], row["source_url"],
    ] for row in gaps]

    method = [
        ["Champ", "Détail"],
        ["Generated at", meta["generated_at"]],
        ["Candidates", len(rows)],
        ["Markets", len(grouped)],
        ["Selection", meta["selection"]],
        ["Rule", "Actual provider/site routes only. GitHub/GitLab/Bitbucket links are rejected as candidate route/hub."],
        ["Rule", "Coverage-first: every represented market receives the configured minimum before extra rows are added."],
        ["Rule", "Known NiakVIO providers are removed from Candidates, but current NiakVIO entries without a stable hub are listed separately."],
        ["Hub trust", "Stable site hub / status domain / public Telegram address channel can be authoritative; terminal route still requires runtime validation."],
        ["Publication safety", "Research catalogue only. This workflow does not enable providers or mutate provider JS/manifests/provider-hubs.json."],
    ]

    matrices = [candidates, coverage, gap_matrix, method]
    widths = [
        [12, 22, 14, 28, 20, 8, 11, 34, 40, 20, 56, 38],
        [24, 12, 14, 16, 20],
        [10, 28, 24, 24, 34, 38, 20, 12, 44, 28, 62, 38],
        [24, 105],
    ]

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        + "".join(
            f'<Override PartName="/xl/worksheets/sheet{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            for index in range(1, 5)
        )
        + '</Types>'
    )
    relationships = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets>'
        '<sheet name="Candidates" sheetId="1" r:id="rId1"/>'
        '<sheet name="Coverage" sheetId="2" r:id="rId2"/>'
        '<sheet name="NiakVIO hub gaps" sheetId="3" r:id="rId3"/>'
        '<sheet name="Method" sheetId="4" r:id="rId4"/>'
        '</sheets></workbook>'
    )
    workbook_relationships = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(
            f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>'
            for index in range(1, 5)
        )
        + '<Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '</Relationships>'
    )
    styles = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
        '<font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills count="3"><fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FF1F4E78"/><bgColor indexed="64"/></patternFill></fill></fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/></cellXfs>'
        '</styleSheet>'
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml', content_types)
        archive.writestr('_rels/.rels', relationships)
        archive.writestr('xl/workbook.xml', workbook)
        archive.writestr('xl/_rels/workbook.xml.rels', workbook_relationships)
        archive.writestr('xl/styles.xml', styles)
        for index, (matrix, width) in enumerate(zip(matrices, widths), 1):
            archive.writestr(f'xl/worksheets/sheet{index}.xml', sheet_xml(matrix, width))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--manual', type=Path, default=DEFAULT_MANUAL)
    parser.add_argument('--catalog', type=Path, default=DEFAULT_CATALOG)
    parser.add_argument('--hubs', type=Path, default=DEFAULT_HUBS)
    parser.add_argument('--max-candidates', type=int, default=100)
    parser.add_argument('--min-per-market', type=int, default=2)
    parser.add_argument('--per-market-cap', type=int, default=4)
    parser.add_argument('--out-json', type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument('--out-csv', type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument('--out-xlsx', type=Path, default=DEFAULT_OUT_XLSX)
    args = parser.parse_args()

    max_candidates = max(1, min(100, args.max_candidates))
    per_market_cap = max(1, min(10, args.per_market_cap))
    min_per_market = max(1, min(args.min_per_market, per_market_cap))

    manual = load_json(args.manual)
    known = known_catalog_names(args.catalog)
    pool, rejected = canonical_candidates(manual, known)
    selected = select_coverage_first(pool, max_candidates, min_per_market, per_market_cap)
    gaps = build_hub_gaps(args.hubs, manual)

    markets = sorted({row['market'] for row in selected}, key=str.casefold)
    meta = {
        'schema_version': 2,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'candidate_count': len(selected),
        'market_count': len(markets),
        'markets': markets,
        'min_per_market': min_per_market,
        'per_market_cap': per_market_cap,
        'selection': f'coverage-first, min={min_per_market}/market when available, cap={per_market_cap}, hard cap={max_candidates}',
        'rejected_count': len(rejected),
        'hub_gap_count': len(gaps),
    }
    payload = {**meta, 'candidates': selected, 'hub_gaps': gaps, 'rejected': rejected}
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    write_csv(args.out_csv, selected)
    write_xlsx(args.out_xlsx, selected, gaps, meta)
    print(
        f'international discovery complete: candidates={len(selected)} markets={len(markets)} '
        f'hub_gaps={len(gaps)} rejected={len(rejected)}'
    )


if __name__ == '__main__':
    main()
