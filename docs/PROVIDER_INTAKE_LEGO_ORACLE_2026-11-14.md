# Brain diagnostic oracle: source-positive → reusable NiakVIO Lego

The first read-only upstream intake, run 43538083385, observed terminal media for **Movix** and **FrenchStream** in France; user wants functioning providers without duplicating region entries. Their sources were historically implemented inside NiakVIO and have retained `provider-old/` bases and provider patch Legos.

This is a deliberately **temporary, non-publishing** A/B oracle. For each positive movie/series fixture from the intake, it compiles a minimal adapter around NiakVIO's *existing local managed Lego*, and executes both that local hypothesis and the immutable upstream under `provider_worker.cjs` and the existing terminal HLS/media probe. Pinned source scripts remain untrusted worker inputs.

Two families:
- `frenchstream` : DLE catalogue → season/episode/player → HLS, local `scripts/provider_patches/frenchstream_exact_runtime_v3.py`.
- `movix` : TMDB API cache → provider video groups → HLS/embed, local `scripts/provider_patches/movix_runtime_v1.py`.

If upstream returns terminal media and local Lego does not, this is a **Brain reconstruction/knowledge/route strategy gap** to solve before promoting a provider. If local does return terminal media, it is **not** a verified Provider v3 publication: clean v3 base, Core identity/season/quality, native client acceptance and region-only projection remain mandatory. No manifest, provider, or override is modified by this job; temporary JS is discarded after it runs. The result contains no URL, token, header value, user data or compiled code.

This is not a license to reintroduce a disabled source (e.g. Videasy) or directly execute foreign JS as a production provider. Following a confirmed positive local oracle, the Brain must generate and persist a V3 candidate from the structured route knowledge, materialize and validate it end-to-end before production activation.


## Résultats observés, pas une réparation proclamée

La version initiale du laboratoire (run [#43539208479](https://github.com/niakw/NiakVIO/actions/runs/43539208479)) prouve :
- **FrenchStream** : upstream `2/2` et Lego historique NiakVIO `2/2` avec HLS terminal, sur *Thor* et *Mr. Robot S01E01*.
- **Movix** : upstream `3/3` avec HLS terminal, ancien Lego `0/3`, chaque tentative locale renvoie uniquement HTTP 403.

Le run [#43539920416](https://github.com/niakw/NiakVIO/actions/runs/43539920416) construit un **ProviderBase NiakVIO v3 propre** (pas de réutilisation des bytes du vieux provider) avec le Lego existant, puis applique les briques Core dispatch et identité en prévisualisation éphémère :
- **FrenchStream v3 preview : 2/2 HLS terminal** (Lego nu 2/2, source 2/2). Le Core v3 de dispatch n'empêche pas l'extraction.
- **Movix v3 preview : 0/3** (Lego nu 0/3, source 3/3), même défaut de transport HTTP 403. La génération du skeleton Core n'est pas la cause immédiate du zéro Movix; il faut faire apprendre au Brain le nouveau parcours source/API.
- Le preview **n'est pas** la composition finale avec *tous* les Core Lego ni une preuve de lecture native; il ne certifie pas une correspondance réelle des épisodes, langues, résolutions ou sous-titres. Aucune entrée de production créée.

La suite qui autorise une promotion : assembler le Provider v3 complet depuis DATA + Lego (sans override résiduel), appliquer et vérifier les bytes, tester film + épisode exact + HLS + identité, vérifier TV/Mobile/Desktop, non-régression et seulement ensuite publier **dans France uniquement**. Le pipeline actuel suppose `vf` sous-ensemble de Global : c'est un **blocage structurel de publication France-only**, à corriger au niveau du catalogue et de la matérialisation, pas par duplication dans Global.

Les détails sont persistés sans URL de média ni secrets dans [l'oracle Brain](../automation/evidence/provider-intake-v3-oracle-2026-11-14.json). Les scripts source historiques `scripts/provider_patches/frenchstream_exact_runtime_v3.py` et `scripts/provider_patches/movix_runtime_v1.py` restent des inputs de connaissance/diagnostic, pas un droit d'activer des providers.
