"""Repair evidence must cover more than activation's first healthy example."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import evaluate_brain_llm_force_candidates as verifier

original = json.loads((ROOT / 'health-config.json').read_text())
seen = []
def health(**options):
    config = json.loads(options['health_config'].read_text())
    seen.append(config)
    assert config['modes']['deep']['primary_fixture_limit_per_category'] == 2
    assert config['modes']['deep']['probe_streams_adaptively'] is False
    assert config['modes']['deep']['max_streams_to_probe'] == original['modes']['deep']['max_streams_to_probe']
    assert config['fixtures'] == original['fixtures']
    assert config.get('activation') == original.get('activation')
    return {'results': []}

with tempfile.TemporaryDirectory() as directory, patch.object(verifier.deep, 'run_health', side_effect=health):
    root = Path(directory)
    verifier.health_provider(root / 'base-stage', root / 'baseline')
    verifier.health_provider(root / 'candidate-stage', root / 'candidate')
assert seen[0] == seen[1]
assert json.loads((ROOT / 'health-config.json').read_text()) == original

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    def subprocess_health(command, **options):
        assert options['env']['NUVIO_HEALTH_CONFIG'] == str((root / 'config.json').resolve())
        (root / 'health-results.json').write_text('{"results":[]}')
    with patch.object(verifier.deep.subprocess, 'run', side_effect=subprocess_health):
        assert verifier.deep.run_health(stage=root, registry_path=root / 'candidates.json',
            output_dir=root, mode='deep', health_config=root / 'config.json') == {'results': []}

# Execute the production fixture selector. The health CLI otherwise starts its
# network job at import, so expose only this function with deterministic profiles.
source = (ROOT / 'scripts/health_check.mjs').read_text()
selector = source[source.index('function fixturesForCandidate('):source.index('function providerLocale(')]
program = '''
const vm = require('node:vm'), assert = require('node:assert/strict');
const groups = {anime:[1,2,3,4].map(n=>({category:'anime',id:n})),movie:[5,6,7].map(n=>({category:'movie',id:n}))};
const ctx = {requestedMode:'deep', modeConfig:{fixture_limit_per_category:true,fallback_fixture_limit_per_category:3},
 candidateProfile:()=>({requiredCategories:['anime','movie'],fixtureGroups:groups,pool:[...groups.anime,...groups.movie]}),
 fixtureRotationPeriod:()=>1, fixtureKey:f=>f.id};
vm.createContext(ctx);
vm.runInContext(SELECTOR,ctx);
assert.deepEqual(Array.from(ctx.fixturesForCandidate({}).fixtures,x=>x.id),[1,5]);
ctx.modeConfig.primary_fixture_limit_per_category=2;
const repair=ctx.fixturesForCandidate({});
assert.deepEqual(Array.from(repair.fixtures,x=>x.id),[1,2,5,6]);
assert.deepEqual(Array.from(repair.fallbackFixtures,x=>x.id),[3,4,7]);
'''.replace('SELECTOR', json.dumps(selector))
subprocess.run(['node', '-e', program], check=True, capture_output=True, text=True)
print('Repair comparison: two primary titles per category, bounded complete probing, symmetric baseline/candidate config passed')
