"""Project HTTP diagnostics to fixed categories, never headers or body text."""
import re

HTTP_ENUMS = {
    'content_kind': {'html', 'json', 'text', 'media', 'binary', 'unknown'},
    'url_relation': {'same_url', 'same_origin', 'cross_origin', 'unknown'},
    'body_state': {'not_sampled', 'sampled', 'complete', 'empty', 'timeout', 'error', 'unavailable'},
    'page_signal': {'challenge_markup', 'captcha_markup', 'access_denied_text',
                    'not_found_text', 'rate_limit_text', 'none', 'unknown'},
}


def public_http_observation(value):
    if not isinstance(value, dict):
        return {}
    result = {key: value[key] if isinstance(value.get(key), str) and value[key] in allowed
              else 'unknown' if 'unknown' in allowed else 'unavailable'
              for key, allowed in HTTP_ENUMS.items()}
    size = value.get('sampled_bytes')
    result['sampled_bytes'] = max(0, min(8192, size)) if type(size) is int else 0
    return result


def public_http_evidence(context, source_sha):
    if (not isinstance(source_sha, str) or not re.fullmatch(r'[0-9a-f]{40}', source_sha)
            or context.get('sourceSha') != source_sha):
        raise ValueError('HTTP evidence does not match the experiment source')
    provider = str(context.get('provider') or '')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}', provider):
        raise ValueError('invalid preflight provider')
    observations = []
    events = context.get('network_evidence')
    for row in (events[:12] if isinstance(events, list) else []):
        if not isinstance(row, dict) or not isinstance(row.get('http_observation'), dict):
            continue
        host, stage, status = row.get('host'), row.get('stage'), row.get('status')
        observations.append({
            'fixture': re.sub(r'[\x00-\x1f\x7f]', '', str(row.get('fixture') or ''))[:120],
            'host': host if isinstance(host, str) and re.fullmatch(r'[a-z0-9.-]{1,160}', host) else '',
            'stage': stage if isinstance(stage, str) and re.fullmatch(r'[a-z_]{1,40}', stage) else '',
            'status': status if type(status) is int and 100 <= status <= 599 else None,
            'http_observation': public_http_observation(row['http_observation']),
        })
    return {'sourceSha': source_sha, 'provider': provider, 'observations': observations,
            'publicationAuthority': False, 'proofAuthority': False}
