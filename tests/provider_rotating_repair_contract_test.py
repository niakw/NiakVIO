from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sequential = (ROOT/'scripts/validate_provider_v3_routes_sequential.py').read_text()
reconstruct = (ROOT/'scripts/reconstruct_provider_v3_sequential_live.py').read_text()
desktop = (ROOT/'.github/workflows/native-desktop-reader-acceptance.yml').read_text()
android = (ROOT/'.github/workflows/native-mobile-android-reader.yml').read_text()
ios = (ROOT/'scripts/prepare_native_ios_reader_acceptance.py').read_text()
prep = (ROOT/'scripts/prepare_native_corpus_validation.py').read_text()
assert 'PROVIDER_V3_ROTATING_CATALOGUE_SAMPLE_V1' in sequential
assert 'evaluation.get("playableChainValidatedTypes")' in reconstruct
assert 'FIELD_PROVIDER_RESAMPLE_REQUIRED' in reconstruct
assert 'completion_state = "resample-required"' in reconstruct
assert '"resample-required"' in sequential
assert 'rotating_corpus.py" select --lane all --count-per-lane 1' in desktop
assert 'FIELD_ROTATING_CORPUS client=tv' in android
assert 'FIELD_ROTATING_CORPUS client=mobile' in android
assert 'from rotating_corpus import select_fixtures' in ios
assert 'rotating_fixture_by_slug' in prep
print('provider rotating Repair/Lab integration contract tests passed')
