#!/usr/bin/env python3
import json
import re
from pathlib import Path

# NuvioTV is the Android TV provider runtime; there is no separate live-TV addon in this repository.
p = Path('automation/nuvio-tv-runtime-contract.json')
data = json.loads(p.read_text(encoding='utf-8'))
data.pop('separate_live_tv_addon', None)
p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

p = Path('scripts/validate_nuvio_tv_runtime_policy.py')
text = p.read_text(encoding='utf-8')
old = '''\n    addon = contract.get("separate_live_tv_addon") or {}\n    if addon.get("enabled") is not True or addon.get("contract") != "stremio-addon-manifest-catalog-meta-stream":\n        errors.append("separate live-TV addon contract missing")\n'''
if old not in text:
    raise SystemExit('obsolete live-TV validator block not found')
text = text.replace(old, '\n')
p.write_text(text, encoding='utf-8')

p = Path('README.md')
text = p.read_text(encoding='utf-8')
text = text.replace(
    '**Écosystème communautaire pour Nuvio regroupant des providers VO, VF et VOSTFR, avec compatibilité Nuvio Mobile, Desktop et NuvioTV, ainsi qu’une intégration TV live séparée.**',
    '**Écosystème communautaire pour Nuvio regroupant des providers VO, VF et VOSTFR, avec compatibilité Nuvio Mobile, Desktop et NuvioTV.**'
)
text = text.replace(
    '[![Type](https://img.shields.io/badge/type-Nuvio%20providers%20%2B%20TV-1f6feb?style=for-the-badge)](#installation)',
    '[![Type](https://img.shields.io/badge/type-Nuvio%20providers-1f6feb?style=for-the-badge)](#installation)'
)

exact_blocks = [
'''\n### TV live\n\nNiakvio possède également une branche TV live séparée, basée sur un addon de type Stremio exposant :\n\n```text\nmanifest\ncatalog/tv\nmeta/tv\nstream/tv\n```\n\nCette branche TV live est distincte de la **compatibilité NuvioTV des providers du manifest principal**. Les deux existent et répondent à deux usages différents.\n''',
'''\n### TV live\n\nL’intégration TV live utilise son propre manifest d’addon et ses ressources `catalog`, `meta` et `stream`. Elle n’est pas une projection de `manifest.json`.\n''',
'''\n### TV live / addon\n\nEn parallèle, l’écosystème Niakvio contient une intégration **TV live** indépendante des providers de films/séries/animes. Elle utilise le contrat addon Stremio `manifest + catalog + meta + stream` pour les chaînes TV.\n\nIl faut donc distinguer :\n\n```text\nNuvioTV + providers Niakvio\n        = compatibilité runtime des providers JS\n\nNuvioTV + TV live Niakvio\n        = addon TV séparé catalog/meta/stream\n```\n'''
]
for block in exact_blocks:
    if block not in text:
        raise SystemExit('expected README live-TV block not found')
    text = text.replace(block, '\n')

text = text.replace('- maintenir en parallèle une intégration TV live au format addon ;\n', '')
text = text.replace('Le manifest de l’addon TV live est volontairement séparé : il appartient à une autre famille d’intégration.\n\n', '')
text = text.replace('8. **La TV live addon ne doit pas être confondue avec la compatibilité provider NuvioTV.**\n', '')
text = text.replace('9. **Une publication doit être reproductible et intègre jusque sur le `main` final.**', '8. **Une publication doit être reproductible et intègre jusque sur le `main` final.**')
text = text.replace('Providers • NuvioTV • TV live • Réparation • Validation • Compatibilité • Intégrité', 'Providers • NuvioTV • Réparation • Validation • Compatibilité • Intégrité')
text = text.replace(
    '**Niakvio ne stocke aucune vidéo.** Le projet publie des manifests, métadonnées, correctifs, bundles de providers et structures d’addon consommés côté client.',
    '**Niakvio ne stocke aucune vidéo.** Le projet publie des manifests, métadonnées, correctifs et bundles de providers consommés côté client.'
)
old_diagram = '''```text
                         Écosystème Niakvio
                                │
             ┌──────────────────┴──────────────────┐
             │                                     │
        Providers JS                           TV live
             │                                     │
 Sources communautaires                    Inventaire TV filtré
             │                                     │
 DNS / hubs / domaines                     Manifest addon Stremio
             │                                     │
 Diagnostic + réparation                   catalog / meta / stream
             │                                     │
 Validation des médias                     Lecture côté NuvioTV
             │
   ┌─────────┴──────────┐
   │                    │
Mobile / Desktop     NuvioTV
QuickJS              Android TV runtime
   │                    │
   └─────────┬──────────┘
             │
 Manifest général + projection VF
             │
 Versions + hashes + intégrité
```'''
new_diagram = '''```text
                         Écosystème Niakvio
                                │
                         Providers JS
                                │
                    Sources communautaires
                                │
                       DNS / hubs / domaines
                                │
                    Diagnostic + réparation
                                │
                     Validation des médias
                                │
                    ┌───────────┴───────────┐
                    │                       │
             Mobile / Desktop           NuvioTV
                  QuickJS            Android TV runtime
                    │                       │
                    └───────────┬───────────┘
                                │
                  Manifest général + projection VF
                                │
                    Versions + hashes + intégrité
```'''
if old_diagram not in text:
    raise SystemExit('README ecosystem diagram not found')
text = text.replace(old_diagram, new_diagram)

if re.search(r'(?i)tv live|live[- ]tv|stremio-addon-manifest-catalog-meta-stream|catalog/tv|stream/tv', text):
    raise SystemExit('stale live-TV wording still present in README')
p.write_text(text, encoding='utf-8')

print('stale live-TV documentation and contract removed')
