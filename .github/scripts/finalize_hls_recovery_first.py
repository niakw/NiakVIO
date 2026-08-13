#!/usr/bin/env python3
from pathlib import Path

path = Path('scripts/provider_patches/hls_runtime_integrity_v1.py')
text = path.read_text(encoding='utf-8')

replacements = [
    (
        '    finally{clearTimeout(timer);try{if(controller)controller.abort()}catch(_e){}}',
        '    finally{clearTimeout(timer)}',
        'do not abort response body before bounded reader consumes it',
    ),
    (
        '''    if(referer&&!Object.keys(out).some(function(k){return k.toLowerCase()==="referer"}))out.Referer=referer;\n    if(referer&&!Object.keys(out).some(function(k){return k.toLowerCase()==="origin"})){\n      try{out.Origin=new URL(referer).origin}catch(_e){}\n    }''',
        '''    if(referer){\n      var refKey=Object.keys(out).find(function(k){return k.toLowerCase()==="referer"}),currentRef=refKey?clean(out[refKey]):"";\n      if(!currentRef||currentRef!==clean(referer)){\n        Object.keys(out).forEach(function(k){var lower=k.toLowerCase();if(lower==="referer"||lower==="origin")delete out[k]});\n        out.Referer=referer;try{out.Origin=new URL(referer).origin}catch(_e){}\n      }\n    }''',
        'adapt request context when traversing from catalogue page to player to media',
    ),
    (
        '''    if(referer&&!Object.keys(headers).some(function(k){return k.toLowerCase()==="referer"}))headers.Referer=referer;\n    if(referer&&!Object.keys(headers).some(function(k){return k.toLowerCase()==="origin"}))try{headers.Origin=new URL(referer).origin}catch(_e){}''',
        '''    if(referer){\n      var refKey=Object.keys(headers).find(function(k){return k.toLowerCase()==="referer"}),currentRef=refKey?clean(headers[refKey]):"";\n      if(!currentRef||currentRef!==clean(referer)){\n        Object.keys(headers).forEach(function(k){var lower=k.toLowerCase();if(lower==="referer"||lower==="origin")delete headers[k]});\n        headers.Referer=referer;try{headers.Origin=new URL(referer).origin}catch(_e){}\n      }\n    }''',
        'return recovered stream with the immediate player request context',
    ),
    (
        '''    [stream&&stream.playerUrl,stream&&stream.embedUrl,stream&&stream.pageUrl,stream&&stream.sourceUrl,stream&&stream.referrer,stream&&stream.referer,headerValue(stream,"referer")].forEach(function(u){if(u)enqueue(u,base)});''',
        '''    var outerReferer=headerValue(stream,"referer");\n    [stream&&stream.playerUrl,stream&&stream.embedUrl,stream&&stream.pageUrl,stream&&stream.sourceUrl,stream&&stream.referrer,stream&&stream.referer].forEach(function(u){if(u)enqueue(u,outerReferer||base)});\n    if(outerReferer)enqueue(outerReferer,"");''',
        'treat the original Referer as a recovery page rather than a child of the broken media URL',
    ),
]

for old, new, label in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one match, found {count}')
    text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')
print('HLS recovery-first implementation finalized')
