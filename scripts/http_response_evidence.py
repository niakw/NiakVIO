"""Project HTTP diagnostics to fixed categories, never headers or body text."""
import re

HTTP_ENUMS = {
    'content_kind': {'html', 'json', 'text', 'media', 'binary', 'unknown'},
    'url_relation': {'same_url', 'same_origin', 'cross_origin', 'unknown'},
    'body_state': {'not_sampled', 'sampled', 'complete', 'empty', 'timeout', 'error', 'unavailable'},
    'page_signal': {'challenge_markup', 'captcha_markup', 'access_denied_text',
                    'not_found_text', 'rate_limit_text', 'none', 'unknown'},
}

NETWORK_ERROR_CODES = {'ENOTFOUND', 'EAI_AGAIN', 'ECONNREFUSED', 'ECONNRESET', 'ETIMEDOUT',
    'UND_ERR_CONNECT_TIMEOUT', 'UND_ERR_HEADERS_TIMEOUT', 'UND_ERR_SOCKET', 'CERT_HAS_EXPIRED',
    'ERR_TLS_CERT_ALTNAME_INVALID', 'UNABLE_TO_VERIFY_LEAF_SIGNATURE', 'DEPTH_ZERO_SELF_SIGNED_CERT',
    'NUVIO_FETCH_TIMEOUT'}


def public_network_error_code(value):
    return value if isinstance(value, str) and value in NETWORK_ERROR_CODES else None


def public_http_observation(value):
    if not isinstance(value, dict):
        return {}
    result = {key: value[key] if isinstance(value.get(key), str) and value[key] in allowed
              else 'unknown' if 'unknown' in allowed else 'unavailable'
              for key, allowed in HTTP_ENUMS.items()}
    size = value.get('sampled_bytes')
    result['sampled_bytes'] = max(0, min(8192, size)) if type(size) is int else 0
    return result


def public_reader_probe(value):
    if not isinstance(value, dict) or not value:
        return {}
    attempted = value.get('attempted') is True
    outcome = value.get('outcome') if isinstance(value.get('outcome'), str) and value['outcome'] in {
        'response', 'timeout', 'error'} else 'error'
    if not attempted:
        outcome = 'budget_exhausted' if value.get('outcome') == 'budget_exhausted' else 'missing_profile'
    status = value.get('status')
    return {
        'attempted': attempted,
        'profile_source': 'prior_successful_html', 'changed_header': 'user-agent',
        'status': status if attempted and outcome == 'response' and type(status) is int and 100 <= status <= 599 else None,
        'outcome': outcome,
        'http_observation': public_http_observation(value.get('http_observation')
            if isinstance(value.get('http_observation'), dict) else {}),
    }


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
        if isinstance(row.get('reader_user_agent_probe'), dict):
            observations[-1]['reader_user_agent_probe'] = public_reader_probe(row['reader_user_agent_probe'])
    return {'sourceSha': source_sha, 'provider': provider, 'observations': observations,
            'publicationAuthority': False, 'proofAuthority': False}
