#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


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


def sheet_xml(matrix: list[list[object]], widths: list[float]) -> str:
    rows = []
    for row_index, row in enumerate(matrix, 1):
        cells = [xcell(f"{col_letter(column_index)}{row_index}", value, 1 if row_index == 1 else 0)
                 for column_index, value in enumerate(row, 1)]
        rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    columns = "".join(
        f'<col min="{index}" max="{index}" width="{width}" customWidth="1"/>'
        for index, width in enumerate(widths, 1)
    )
    autofilter = f'<autoFilter ref="A1:{col_letter(len(widths))}{max(1, len(matrix))}"/>'
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" '
        'activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
        f'<cols>{columns}</cols><sheetData>{"".join(rows)}</sheetData>{autofilter}</worksheet>'
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--json', type=Path, required=True)
    parser.add_argument('--csv', type=Path, required=True)
    parser.add_argument('--xlsx', type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.json.read_text(encoding='utf-8'))
    rows = list(payload.get('candidates') or [])
    for row in rows:
        row['max_resolution'] = int(row.get('max_resolution') or 0)
        row['quality_tier'] = str(row.get('quality_tier') or ('4K/UHD' if row['max_resolution'] >= 2160 else 'HD/unknown'))
        row['hdr'] = bool(row.get('hdr'))
        row['multi_audio'] = bool(row.get('multi_audio'))
        row['original_audio'] = bool(row.get('original_audio'))
        row['quality_confidence'] = str(row.get('quality_confidence') or '')
        row['access_model'] = str(row.get('access_model') or '')

    uhd = [row for row in rows if row['max_resolution'] >= 2160]
    multi = [row for row in rows if row['multi_audio'] or row['original_audio']]
    payload['schema_version'] = max(int(payload.get('schema_version') or 2), 3)
    payload['uhd_count'] = len(uhd)
    payload['multi_audio_or_original_count'] = len(multi)
    payload['quality_policy'] = {
        'uhd_threshold': 2160,
        'quality_is_structured': True,
        'geographic_floor_preserved': True,
    }
    args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    columns = [
        'rank','market','languages','name','content','tier','score','max_resolution','quality_tier',
        'hdr','multi_audio','original_audio','quality_confidence','access_model','route','hub','hub_type','note','source_url'
    ]
    with args.csv.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([row.get(column, '') for column in columns])

    quality_headers = [
        'Rank qualité','Pays / marché','Candidat','Langue(s)','Contenu','Max résolution','Tier qualité',
        'HDR','Multi-audio','Audio original / VO','Confiance qualité','Accès','Route web réelle',
        'Hub / Telegram / status','Pourquoi / prochaine étape','Source qualité'
    ]
    quality_rows = sorted(rows, key=lambda row: (-row['max_resolution'], -int(row.get('score') or 0), str(row.get('market') or '').casefold(), str(row.get('name') or '').casefold()))
    matrix = [quality_headers] + [[
        row.get('rank',''), row.get('market',''), row.get('name',''), row.get('languages',''), row.get('content',''),
        row.get('max_resolution') or '', row.get('quality_tier',''), 'Oui' if row.get('hdr') else '',
        'Oui' if row.get('multi_audio') else '', 'Oui' if row.get('original_audio') else '',
        row.get('quality_confidence',''), row.get('access_model',''), row.get('route',''), row.get('hub',''),
        row.get('note',''), row.get('source_url','')
    ] for row in quality_rows]

    with zipfile.ZipFile(args.xlsx, 'r') as src:
        files = {name: src.read(name) for name in src.namelist()}

    content_types = files['[Content_Types].xml'].decode('utf-8')
    if '/xl/worksheets/sheet5.xml' not in content_types:
        content_types = content_types.replace('</Types>', '<Override PartName="/xl/worksheets/sheet5.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')

    workbook = files['xl/workbook.xml'].decode('utf-8')
    if 'Quality 4K-UHD' not in workbook:
        workbook = workbook.replace('</sheets>', '<sheet name="Quality 4K-UHD" sheetId="5" r:id="rId6"/></sheets>')

    rels = files['xl/_rels/workbook.xml.rels'].decode('utf-8')
    if 'worksheets/sheet5.xml' not in rels:
        rels = rels.replace('</Relationships>', '<Relationship Id="rId6" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet5.xml"/></Relationships>')

    files['[Content_Types].xml'] = content_types.encode('utf-8')
    files['xl/workbook.xml'] = workbook.encode('utf-8')
    files['xl/_rels/workbook.xml.rels'] = rels.encode('utf-8')
    files['xl/worksheets/sheet5.xml'] = sheet_xml(matrix, [12,22,28,24,18,14,18,8,12,15,16,22,36,40,60,40]).encode('utf-8')

    tmp = args.xlsx.with_suffix('.quality.tmp.xlsx')
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as dst:
        for name, data in files.items():
            dst.writestr(name, data)
    tmp.replace(args.xlsx)
    print(f'quality enrichment complete: candidates={len(rows)} uhd={len(uhd)} multilingual_or_original={len(multi)}')


if __name__ == '__main__':
    main()
