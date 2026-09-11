#!/usr/bin/env python3
from pathlib import Path

p = Path('tests/overrides_test.py')
s = p.read_text(encoding='utf-8')
old = '''    output, records = apply_overrides("movix", source, phase="runtime")
    assert b"NUVIO_FIXED_ENDPOINT:https://api.movix.fun" in output
    assert b"NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1" in output
    assert b"fetch(DOMAINS_URL)" not in output
    assert b"raw.githubusercontent.com" not in output
    assert any(row.get("type") == "fixed_endpoint" for row in records)
    assert any(row.get("type") == "runtime_domain_overrides" for row in records)
    second, second_records = apply_overrides("movix", output, phase="runtime")
    assert second == output
    assert not any(row.get("type") in {"fixed_endpoint", "runtime_domain_overrides"} for row in second_records)
    with tempfile.TemporaryDirectory(prefix="niakvio-overrides-") as tmp:
        target = Path(tmp) / "provider.js"
        target.write_bytes(output)
        subprocess.run(["node", "--check", str(target)], check=True)
        subprocess.run(
            ["node", str(ROOT / "scripts" / "validate_provider_artifact.cjs"), str(target)],
            check=True,
        )
'''
new = '''    output, records = apply_overrides("movix", source, phase="runtime")
    # The fixed endpoint is the executable authority. A runtime-domain shim is
    # optional: once detectApi() is replaced, no registry lookup is required and
    # forcing a legacy fetch wrapper would test implementation history rather than
    # runtime behavior.
    assert b"NUVIO_FIXED_ENDPOINT:https://api.movix.fun" in output
    assert b"fetch(DOMAINS_URL)" not in output
    assert b"raw.githubusercontent.com" not in output
    assert any(row.get("type") == "fixed_endpoint" for row in records)
    has_runtime_record = any(row.get("type") == "runtime_domain_overrides" for row in records)
    has_runtime_marker = b"NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1" in output
    assert has_runtime_record == has_runtime_marker

    second, second_records = apply_overrides("movix", output, phase="runtime")
    assert second == output
    assert not any(row.get("type") in {"fixed_endpoint", "runtime_domain_overrides"} for row in second_records)
    with tempfile.TemporaryDirectory(prefix="niakvio-overrides-") as tmp:
        target = Path(tmp) / "provider.js"
        target.write_bytes(output)
        subprocess.run(["node", "--check", str(target)], check=True)
        subprocess.run(
            ["node", str(ROOT / "scripts" / "validate_provider_artifact.cjs"), str(target)],
            check=True,
        )
        # Behavioral proof: the rewritten resolver must make the provider request
        # directly against api.movix.fun and must never consult DOMAINS_URL.
        probe = Path(tmp) / "probe.cjs"
        probe.write_text(
            "const p=require(process.argv[2]);"
            "const seen=[];"
            "global.fetch=async u=>{seen.push(String(u));return {ok:true,status:200,text:async()=>'',json:async()=>({})};};"
            "Promise.resolve(p.getStreams()).then(()=>{"
            "if(seen.length!==1||!seen[0].startsWith('https://api.movix.fun/')){console.error(JSON.stringify(seen));process.exit(2);}" 
            "console.log('MOVIX_FIXED_ENDPOINT_RUNTIME_OK '+seen[0]);"
            "}).catch(e=>{console.error(e);process.exit(3);});",
            encoding="utf-8",
        )
        subprocess.run(["node", str(probe), str(target)], check=True)
'''
assert old in s, 'Movix stale runtime-domain assertion block not found'
s = s.replace(old, new, 1)

old_shim = '''def test_runtime_domain_override_rewrites_polyfilled_urls_without_mutating_hostname() -> None:
    source = b'''module.exports={getStreams:async function(){await fetch("https://api.movix.cash/stream");return []}};'''
    output, records = apply_overrides("movix", source, phase="runtime")
    text = output.decode("utf-8")
    assert "NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1" in text
    assert "url.hostname=replacement" in text
    assert any(row.get("type") == "runtime_domain_overrides" for row in records)
'''
new_shim = '''def test_runtime_domain_override_rewrites_polyfilled_urls_without_mutating_hostname() -> None:
    # Test the generic runtime-domain primitive with an explicit synthetic config.
    # Do not couple this Core primitive to Movix, whose fixed-endpoint authority may
    # legitimately make the shim unnecessary.
    source = b'''module.exports={getStreams:async function(){await fetch("https://api.old.invalid/stream");return []}};'''
    with tempfile.TemporaryDirectory(prefix="niakvio-runtime-domain-") as tmp:
        config_path = Path(tmp) / "overrides.json"
        config_path.write_text(json.dumps({
            "provider_patches": {
                "synthetic": {
                    "runtime_domain_replacements": {
                        "api.old.invalid": "api.new.invalid"
                    }
                }
            }
        }), encoding="utf-8")
        output, records = apply_overrides(
            "synthetic",
            source,
            phase="runtime",
            config_path=config_path,
        )
    text = output.decode("utf-8")
    assert "NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1" in text
    assert "url.hostname=replacement" in text
    assert any(row.get("type") == "runtime_domain_overrides" for row in records)
'''
assert old_shim in s, 'generic runtime-domain shim fixture not found'
s = s.replace(old_shim, new_shim, 1)
p.write_text(s, encoding='utf-8')
print('MOVIX_OVERRIDE_BEHAVIOR_TEST_PATCHED generic_runtime_shim=synthetic')
