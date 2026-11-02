"""A repository API secret must never activate paid generation automatically."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
for filename in ('brain-multi-provider-repair.yml', 'brain-hosted-repair-check.yml', 'hosted-api-check.yml'):
    text = (ROOT / '.github/workflows' / filename).read_text()
    assert re.search(r'\n    if: \$\{\{ false \}\}\n', text), filename
    assert not re.search(r'^\s*(?:NIAKVIO_OPENAI_API_KEY|OPENAI_API_KEY):', text, re.M), filename
print('Paid model workflows disabled; API credentials are not bound to their jobs')
