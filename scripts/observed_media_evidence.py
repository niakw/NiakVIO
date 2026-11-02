"""Project a diagnostic of a previously unrequested observed media address."""
if __package__:
    from .address_reference_evidence import address_ref
    from .http_response_evidence import public_http_observation
else:
    from address_reference_evidence import address_ref
    from http_response_evidence import public_http_observation


def public_observed_media_probe(value):
    if (not isinstance(value, dict) or type(value.get('attempted')) is not bool
            or not address_ref(value.get('source_ref')) or not address_ref(value.get('template_ref'))):
        return None
    attempted, outcome = value['attempted'], value.get('outcome')
    if not attempted and outcome != 'budget_exhausted':
        return None
    if attempted and (not isinstance(outcome, str) or outcome not in {'response', 'timeout', 'error'}):
        outcome = 'error'
    status = value.get('status')
    raw = value.get('media_observation')
    media = raw if isinstance(raw, dict) else {}
    def enum(key, allowed, default):
        return media[key] if isinstance(media.get(key), str) and media[key] in allowed else default
    def count(key, maximum):
        return max(0, min(maximum, media[key])) if type(media.get(key)) is int else 0
    return {
        'attempted': attempted, 'source_ref': value['source_ref'], 'template_ref': value['template_ref'],
        'outcome': outcome,
        'status': status if attempted and outcome == 'response' and type(status) is int and 100 <= status <= 599 else None,
        'media_observation': {
            'signature': enum('signature', {'unknown', 'mp4', 'ebml', 'mpegts', 'hls', 'html'}, 'unknown'),
            'durationSeconds': count('durationSeconds', 1209600) if type(media.get('durationSeconds')) is int else None,
            'bytesSampled': count('bytesSampled', 32768),
            'readState': enum('readState', {'not_read', 'data', 'empty', 'complete', 'error'}, 'not_read'),
            'cancelState': enum('cancelState', {'not_requested', 'requested', 'complete', 'error'}, 'not_requested'),
        },
        'http_observation': public_http_observation(value.get('http_observation')
            if isinstance(value.get('http_observation'), dict) else {}),
    }
