# Bilingual HTML

Render already paired text into a portable offline page. Every passage keeps its two languages together: columns on desktop, source then target on mobile. Native tables, lists, one shared image and paired captions remain meaningful structures.

Requires Python 3.11+. No third-party Python package or translation skill is needed for paired input.

```sh
python3 scripts/bilingual_html.py render examples/tutorial/layout.json --output page
```

Run from this skill's directory. Choose a new output directory whose parent exists. Open `page/index.html`; deliver the whole directory.

- [Complete tutorial input](examples/tutorial/layout.json) and [generated page](examples/tutorial/site/index.html)
- [Format, styling, fonts, assets and review](references/rendering.md)
- [Rendering schema](schemas/layout.schema.json)
- [Agent workflow](SKILL.md)

Version 1 renders literal text and local PNG/JPEG images. It does not interpret HTML, Markdown or TeX. Configure fonts per language and inspect actual glyphs; font names do not guarantee coverage. Structural checks are separate from translation, visual and accessibility review.

For raw source, discover the separately installed `bilingual-translation` skill. Its reviewed v1 pairs can be imported through an explicit `--translation-skill` path. No dependency is installed automatically. [Import and revision pinning](references/rendering.md#optional-translation-import).

Code, documentation and original example assets use the [MIT license](LICENSE).
