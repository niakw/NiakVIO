#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

ATTR = re.compile(r'([A-Z0-9-]+)=("[^"]*"|[^,]*)')


def attrs(line: str) -> dict[str, str]:
    raw = line.split(':', 1)[1] if ':' in line else ''
    out = {}
    for match in ATTR.finditer(raw):
        out[match.group(1).upper()] = match.group(2).strip().strip('"')
    return out


def get(url: str, headers: dict[str, str]) -> tuple[str, str, int, str]:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        return (
            response.read(2_000_000).decode('utf-8', 'replace').lstrip('\ufeff \t\r\n'),
            response.geturl(),
            response.status,
            response.headers.get('Content-Type', ''),
        )


def main() -> int:
    payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    output = []
    for index, item in enumerate(payload.get('streams') or []):
        row = item.get('row') if isinstance(item, dict) and isinstance(item.get('row'), dict) else {}
        media = item.get('media') if isinstance(item, dict) and isinstance(item.get('media'), dict) else {}
        if not media.get('playable') or media.get('kind') != 'hls':
            continue
        h = {str(k): str(v) for k, v in (row.get('headers') or {}).items()} if isinstance(row.get('headers'), dict) else {}
        h.setdefault('User-Agent', 'Mozilla/5.0 (Linux; Android 14; Android TV) NuvioTV')
        h.setdefault('Accept', '*/*')
        try:
            text, final_url, status, content_type = get(str(row.get('url') or ''), h)
        except Exception as exc:
            output.append({'index': index, 'error': str(exc)[:240]})
            continue
        variants = []
        lines = [line.strip() for line in text.splitlines()]
        for pos, line in enumerate(lines):
            if not line.upper().startswith('#EXT-X-STREAM-INF:'):
                continue
            a = attrs(line)
            width = height = 0
            if 'RESOLUTION' in a and 'x' in a['RESOLUTION'].lower():
                try:
                    width, height = [int(v) for v in a['RESOLUTION'].lower().split('x', 1)]
                except Exception:
                    pass
            bandwidth = 0
            try:
                bandwidth = int(a.get('AVERAGE-BANDWIDTH') or a.get('BANDWIDTH') or 0)
            except Exception:
                pass
            child = ''
            for candidate in lines[pos + 1:]:
                if candidate and not candidate.startswith('#'):
                    child = urljoin(final_url, candidate)
                    break
            variants.append({'width': width, 'height': height, 'bandwidth': bandwidth, 'child': child[:180]})
        output.append({
            'index': index,
            'name': str(row.get('name') or '')[:180],
            'quality': str(row.get('quality') or '')[:80],
            'language': str(row.get('language') or '')[:80],
            'status': status,
            'content_type': content_type,
            'variant_count': len(variants),
            'max_height': max((v['height'] for v in variants), default=0),
            'max_bandwidth': max((v['bandwidth'] for v in variants), default=0),
            'variants': variants,
        })
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
