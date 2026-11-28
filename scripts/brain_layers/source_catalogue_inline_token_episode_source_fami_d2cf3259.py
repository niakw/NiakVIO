import json
import re
from html_script_blocks import extract_script_blocks
SLOT_PREFIX = 'eps'
VALUE_PREFIX = 'lien:'
DECLARATIONS = ('const', 'let', 'var')
AXIS = 'reader-slots'
ORDER = 'numeric'

def parse_episode_source(html, episode):
    if type(episode) is not int or not 1 <= episode <= 4096:
        return []
    if not isinstance(html, str) or len(html) > 1048576:
        return []
    chunks = extract_script_blocks(html)
    pattern = re.compile(r"\b(?:" + "|".join(DECLARATIONS) + r")\s+" +
                         re.escape(SLOT_PREFIX) + r"([1-9][0-9]{0,3})\s*=\s*")
    rows = {}
    decoder = json.JSONDecoder()
    for chunk in chunks:
        for match in pattern.finditer(chunk):
            slot = int(match.group(1))
            if slot in rows or len(rows) >= 128:
                return []
            try:
                values, _ = decoder.raw_decode(chunk[match.end():])
            except ValueError:
                return []
            if not isinstance(values, list) or len(values) > 4096:
                return []
            if any(x is not None and not isinstance(x, str) for x in values):
                return []
            rows[slot] = values
    keys = sorted(rows) if ORDER == "numeric" else list(rows)
    if AXIS == "reader-slots":
        selected = [rows[k][episode - 1] for k in keys if episode <= len(rows[k])]
    else:
        selected = rows.get(episode, [])
    # Preserve matrix position before filtering blanks, never shift episode indices.
    out = []
    for value in selected:
        if (isinstance(value, str) and value.startswith(VALUE_PREFIX)
                and re.fullmatch(r"[A-Za-z0-9_.:-]{1,200}", value[len(VALUE_PREFIX):])
                and value not in out):
            out.append(value)
    return out
