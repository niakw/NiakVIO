"""Project untrusted preflight artifacts to bounded player markup facts."""
import re

TAGS = {'iframe', 'video', 'source', 'a', 'button', 'option', 'div', 'li', 'input'}
ATTRIBUTES = {
    'src', 'data-src', 'href', 'value', 'data-url', 'data-link', 'data-player',
    'data-embed', 'data-video', 'data-code', 'data-iframe', 'data-source',
    'data-player-id', 'data-index', 'data-server',
}
KINDS = {
    'empty', 'absolute_url', 'relative_url', 'fragment', 'inline_markup',
    'escaped_markup', 'encoded_markup', 'encoded_url', 'other',
}


def bounded_count(value, limit):
    return max(0, min(limit, value)) if type(value) is int else 0


def public_player_markup(context, source_sha):
    if not isinstance(source_sha, str) or not re.fullmatch(r'[0-9a-f]{40}', source_sha) or context.get('sourceSha') != source_sha:
        raise ValueError('preflight evidence does not match the experiment source')
    provider = str(context.get('provider') or '')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}', provider):
        raise ValueError('invalid preflight provider')
    observations = []
    events = context.get('network_evidence')
    for event in (events[:12] if isinstance(events, list) else []):
        if not isinstance(event, dict):
            continue
        structure = event.get('response_structure')
        markup = structure.get('player_markup') if isinstance(structure, dict) else None
        if not isinstance(markup, dict):
            continue
        rows = []
        raw_rows = markup.get('rows')
        for row in (raw_rows[:8] if isinstance(raw_rows, list) else []):
            if not isinstance(row, dict) or row.get('tag') not in TAGS:
                continue
            raw_kinds = row.get('value_kinds')
            kinds = {name: kind for name, kind in raw_kinds.items()
                     if name in ATTRIBUTES and isinstance(kind, str) and kind in KINDS} if isinstance(raw_kinds, dict) else {}
            kinds = dict(list(kinds.items())[:8])
            if not kinds:
                continue
            count = bounded_count(row.get('count'), 128)
            rows.append({'tag': row['tag'], 'value_kinds': kinds, 'count': count,
                         'distinct_values': min(count, bounded_count(row.get('distinct_values'), 128))})
        host = str(event.get('host') or '')
        stage = str(event.get('stage') or '')
        observations.append({
            'fixture': re.sub(r'[\x00-\x1f\x7f]', '', str(event.get('fixture') or ''))[:120],
            'host': host if re.fullmatch(r'[a-z0-9.-]{1,160}', host) else '',
            'stage': stage if re.fullmatch(r'[a-z_]{1,40}', stage) else '',
            'player_markup': {'rows': rows, 'sampled_chars': bounded_count(markup.get('sampled_chars'), 131072),
                              'truncated': markup.get('truncated') is True},
        })
    return {'sourceSha': source_sha, 'provider': provider, 'observations': observations,
            'publicationAuthority': False, 'proofAuthority': False}
