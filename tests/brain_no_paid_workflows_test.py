"""A repository API secret must never activate paid generation automatically."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / '.github/workflows'

# The two legacy paid/hosted entrypoints must remain completely disabled.
for filename in ('brain-multi-provider-repair.yml', 'hosted-api-check.yml'):
    text = (WORKFLOWS / filename).read_text(encoding='utf-8')
    assert re.search(r'\n    if: \$\{\{ false \}\}\n', text), filename
    assert not re.search(r'^\s*(?:NIAKVIO_OPENAI_API_KEY|OPENAI_API_KEY):', text, re.M), filename

# Local Qwen inference is allowed ONLY in an isolated, non-publishing proof job.
filename = 'brain-hosted-repair-check.yml'
text = (WORKFLOWS / filename).read_text(encoding='utf-8')
assert not re.search(r'^\s*(?:NIAKVIO_OPENAI_API_KEY|OPENAI_API_KEY):', text, re.M), filename
assert not re.search(r'https?://api\.openai\.com|api\.anthropic\.com', text, re.I), filename
assert "github.repository == 'niakw/NiakVIO'" in text
assert "github.ref == 'refs/heads/main'" in text
assert 'contents: read' in text
assert '127.0.0.1:8080' in text
assert 'Qwen/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M' in text
assert "NIAKVIO_REQUIRE_DECODE_PROOF: '1'" in text
assert "NIAKVIO_FORCE_CPU_TIGHT_PROMPT: '1'" in text
assert 'publicationAuthority' in text
assert 'materializedMutationObserved' in text
assert 'No strictly decoded, materialized Brain repair proved' in text
print('PAID_MODEL_WORKFLOWS_DISABLED local-Qwen proof main-only read-only strict decode')
