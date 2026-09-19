#!/usr/bin/env python3
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
validator=ROOT/"scripts"/"validate_provider_artifact.cjs"

# Reproduce the publication failure shape: one very long physical line with a
# syntax error near the end. The diagnostic must stay compact and still expose
# a parser-level summary without executing provider code.
bad="const a=1;" + ("const filler=0;"*12000) + "const broken = ;\n"
with tempfile.NamedTemporaryFile("w",suffix=".js",encoding="utf-8",delete=False,dir=ROOT) as handle:
    handle.write(bad)
    tmp=Path(handle.name)
try:
    proc=subprocess.run(
        ["node",str(validator),str(tmp)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )
finally:
    tmp.unlink(missing_ok=True)

assert proc.returncode != 0
detail=(proc.stdout+"\n"+proc.stderr).strip()
assert "syntax_summary=SyntaxError:" in detail, detail
assert "provider-source-omitted" in detail, detail
assert "const filler=0;" not in detail, "giant provider source leaked into diagnostics"
assert len(detail) < 10000, len(detail)
print("provider syntax diagnostics compact-summary contract passed")
