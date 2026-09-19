#!/usr/bin/env python3
"""Make the Mobile native player Lab target the instrumented production package."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'scripts/native_player_diagnostics_codegen.py'
OLD='''            val intent = Intent().setClassName(\n                "com.nuviodebug.com",\n                MainActivity::class.java.name,\n            )'''
NEW='''            val intent = Intent().setClassName(\n                context.packageName,\n                MainActivity::class.java.name,\n            )'''

def main():
    text=PATH.read_text(encoding='utf-8')
    if NEW in text:
        print('NATIVE_MOBILE_PLAYER_LAUNCH_V36 already-applied')
        return 0
    if OLD not in text:
        raise SystemExit('expected hard-coded mobile player launch block not found')
    text=text.replace(OLD,NEW,1)
    text=text.replace(
        '// Start the official production MainActivity explicitly. The package launcher\n            // currently points to an icon-alias subclass; the Lab must observe the actual\n            // player host, not depend on launcher-alias resolution in instrumentation.',
        '// Start the official production MainActivity explicitly inside the exact package\n            // under instrumentation. applicationId can differ between official client\n            // revisions/build variants, so the Lab must not hard-code a debug package.'
    )
    PATH.write_text(text,encoding='utf-8')
    print('NATIVE_MOBILE_PLAYER_LAUNCH_V36 applied')
    return 0
if __name__=='__main__': raise SystemExit(main())
