#!/usr/bin/env python3
from pathlib import Path
p=Path('tests/stream_quality_recovery_tv_test.py')
text=p.read_text(encoding='utf-8')
if 'sys.path.insert(0, str(ROOT / "scripts"))' not in text:
    text=text.replace('import subprocess\nimport tempfile\nfrom pathlib import Path\n','import subprocess\nimport tempfile\nimport sys\nfrom pathlib import Path\n',1)
    text=text.replace('ROOT = Path(__file__).resolve().parents[1]\nPRESENTATION =', 'ROOT = Path(__file__).resolve().parents[1]\nsys.path.insert(0, str(ROOT / "scripts"))\nPRESENTATION =',1)
p.write_text(text,encoding='utf-8')
value=p.read_text(encoding='utf-8')
assert 'import sys' in value
assert 'sys.path.insert(0, str(ROOT / "scripts"))' in value
print('QUALITY_TEST_BOOTSTRAP_PREPATCH_OK')
