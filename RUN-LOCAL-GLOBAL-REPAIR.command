#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p local-output
LOG="local-output/global-provider-repair-run.log"
: > "$LOG"
exec > >(tee -a "$LOG") 2>&1

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 est absent. Installe Python 3 puis relance." >&2
  exit 1
fi

mkdir -p .local-bin
cat > .local-bin/python <<'PYSHIM'
#!/bin/sh
exec python3 "$@"
PYSHIM
chmod +x .local-bin/python
export PATH="$PWD/.local-bin:$PATH"

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js est absent. Installe Node 24 puis relance." >&2
  exit 1
fi
major="$(node -p 'process.versions.node.split(".")[0]')"
if [ "$major" -lt 24 ]; then
  echo "Node.js 24 minimum requis (version détectée: $(node -v))." >&2
  exit 1
fi

if [ ! -d node_modules ]; then
  echo "Installation locale des dépendances (scripts lifecycle désactivés)…"
  npm install --registry=https://registry.npmjs.org --ignore-scripts --no-audit --no-fund --package-lock=false
fi

printf '\n[1/2] Tests ciblés du nouveau moteur global\n'
python3 -m py_compile \
  scripts/build_provider_runtime_profiles.py \
  scripts/deep_repair_loop.py \
  scripts/local/test_global_provider_repair.py
python3 tests/adaptive_runtime_repair_test.py
python3 tests/global_local_repair_pipeline_test.py
node --check scripts/health_check.mjs
python3 tests/overrides_test.py
python3 tests/runtime_repair_test.py
python3 tests/ci_preservation_policy_test.py
python3 tests/no_inconclusive_reenable_test.py

printf '\n[2/2] Test global local — variantes upstream, DNS, accès, qualité et réparation\n'
python3 scripts/local/test_global_provider_repair.py --scope all

mkdir -p local-output/global-provider-repair
cp "$LOG" local-output/global-provider-repair/run.log

printf '\nTERMINÉ. Aucune publication GitHub.\n'
printf 'Résumé : local-output/global-provider-repair/SUMMARY.json\n'
printf 'Matrice générale : local-output/global-provider-repair/provider-matrix.csv\n'
printf 'Matrice VF : local-output/global-provider-repair/vf-provider-matrix.csv\n'
printf 'Matrice VF movie : local-output/global-provider-repair/vf-movie-matrix.csv\n'
printf 'Matrice variantes : local-output/global-provider-repair/variant-matrix.csv\n'
printf 'Plan activation : local-output/global-provider-repair/activation-plan.json\n'
read -r -p 'Appuie sur Entrée pour fermer…' _
