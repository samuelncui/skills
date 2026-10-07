# Translation handoff

Use this reference when the caller has asked for translation before PDF layout, or supplies a reviewed bilingual-translation exchange v1 file. Supplied native/JSON pairs still use this renderer directly, without a translation dependency.

## Discovery and ownership

Use the host's installed-skill listing to discover `bilingual-translation`. Read its installed SKILL.md for the source-first workflow and its owned contract reference for the optional data exchange. Resolve its actual directory; installations may be unrelated paths. Record both tested skill revisions and exchange version in the project. Use the host's supported installation flow if a dependency is missing, with applicable authorization. The renderer does not download or install it.

Translation owns the canonical paired manuscript, full-source/context review, source revisions and per-unit review state. PDF owns physical columns, supported profiles, layout configuration and visual acceptance. Keep source/target roles separate from physical left/right position.

## Optional v1 import

After the calling agent has completed semantic review, run from the installed PDF skill:

```sh
python3 scripts/import_translation.py paired.json --translation-skill "$TRANSLATION_SKILL" --output pdf-layout.json
python3 scripts/bilingual_pdf.py preflight pdf-layout.json
python3 scripts/bilingual_pdf.py render pdf-layout.json --asset-root "$ORIGINAL_ASSET_ROOT" --output new-pdf-project
```

Set TRANSLATION_SKILL to the discovered installation. Set ORIGINAL_ASSET_ROOT to the original paired.json directory (or the explicitly authorized equivalent assets directory); moving the generated layout file does not move its referenced assets. `--source-side right` reverses only physical columns. It does not change the semantic source/target roles or text.

The importer loads the installed contract validator and requires contract version 1 and current reviewed targets. It writes a new file and preserves the full paired contract, including locators, hashes and stable semantic IDs, under the ignored layout metadata field `translation`. The mapping records generated safe PDF anchors separately. Edit the canonical paired manuscript and reimport; generated layout JSON is a presentation derivative.

The first block must be a reviewed title at heading level 1. Later level-2 headings become sections. Plain paragraphs, unordered lists, rectangular tables with 1–5 columns, optional table captions and shared PNG/JPEG figures use the existing PDF route. Import sets figure `caption_prefix: "none"`, so supplied caption labels are preserved exactly without an additional generated figure label. Lists align by item and tables by row. Figure alternative descriptions remain in metadata; this renderer does not encode tagged-PDF alt text or claim accessibility conformance.

For ordered lists, deeper headings, rich inline text, complex tables or scripts outside the structured profile list, use reviewed pairs in native TeX with the public package API and a separately verified language/font setup. The importer reports these limitations instead of flattening structural content. Native authors can retain the semantic IDs directly where valid as TeX labels; JSON import keeps them in the mapping because the legacy JSON ID grammar is narrower.

The plain-text contract accepts literal strings; the PDF route still applies its stricter text/control/path constraints. Supported profiles remain en, fr, zh-Hans, zh-Hant, ja, ar and he, with the documented mixed-Chinese restriction. Font/glyph preflight and actual PDF inspection remain necessary.

## Editable source and acceptance

Keep the original source, one canonical paired manuscript and the required render outputs/assets. For native manuscripts, the source-first workflow can operate directly on paired commands with a small review record; no JSON conversion is required. Preserve the existing native and JSON rendering routes through the same canonical package.

The importer proves only contract readiness as recorded and supported mapping. Review content against the full source through the translation workflow; then inspect actual PDF pixels through [layout acceptance](acceptance.md). A recorded review state or successful compilation cannot establish semantic equivalence.
