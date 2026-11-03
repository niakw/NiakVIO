"""Scoped opaque URL correlation, never the private address table."""
import re


def address_scope(value):
    return value if isinstance(value, str) and re.fullmatch(r's[0-9a-f]{16}', value) else ''


def address_ref(value):
    return value if (isinstance(value, str) and re.fullmatch(r'r[1-9][0-9]{0,2}', value)
                     and int(value[1:]) <= 512) else ''


def public_address_fields(value):
    if not isinstance(value, dict) or not address_scope(value.get('address_scope')):
        return {}
    result = {'address_scope': value['address_scope'],
              'address_refs_truncated': value.get('address_refs_truncated') is not False,
              'address_trace_truncated': value.get('address_trace_truncated') is not False}
    for key in ('request_ref', 'response_ref', 'referer_ref'):
        ref = address_ref(value.get(key))
        if ref:
            result[key] = ref
        elif value.get(key):
            result['address_refs_truncated'] = True
    return result


def public_markup_address_refs(value, attributes):
    if not isinstance(value, dict) or not {'address_refs', 'address_refs_truncated'} & value.keys():
        return {}
    raw = value.get('address_refs')
    truncated = value.get('address_refs_truncated') is not False
    result = {}
    if isinstance(raw, dict):
        for key, refs in raw.items():
            if key not in attributes or not isinstance(refs, list):
                truncated = True
                continue
            kept = []
            if len(refs) > 16:
                truncated = True
            for ref in refs[:16]:
                safe = address_ref(ref)
                if safe and safe not in kept:
                    kept.append(safe)
                elif not safe:
                    truncated = True
            if kept:
                result[key] = kept
    elif raw is not None:
        truncated = True
    return {'address_refs': result, 'address_refs_truncated': truncated}
