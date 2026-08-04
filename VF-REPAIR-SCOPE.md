# Targeted VF repair scope

This branch isolates repair attempts for the following providers:

- Coflix
- DuLourd
- French-Manga
- Frenchstream
- Movix
- Sekai
- StreamZo

A provider is not considered valid for the VF manifest merely because it returns a playable stream. Evidence must match at least one declared category (`movie`, `tv`, or `anime`) and expose French audio or French subtitles for the tested fixture.

The targeted workflow is report-only. It never publishes a repaired candidate automatically. A provider may be promoted only after the candidate improves the verified playable-stream result for its own category.
