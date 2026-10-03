# Repository instructions

Read the relevant skill and its references before editing. Keep every user-facing instruction and repository document in English; demonstration content may use its declared languages.

- Maintain one owner per implementation. The canonical shared runtime is in skills/bilingual-pdf; regenerate the course skill copy with tools/sync_renderer.py.
- Keep each installed skill self-contained. Run tests from a fresh directory containing only that skill, without access to the source checkout.
- Preserve original user inputs. Do not overwrite or silently change supplied translations.
- Keep private source material, account data, operational reports, credentials and machine-specific paths out of published files and history.
- Use original examples and retain dependency licenses. A public repository is not automatically freely reusable.
- Read source text and inspect actual PDF pixels. Compiler success and rules cannot substitute for semantic, factual or language review.
- Report passes, failures and unrun checks separately. Never claim all languages or accessibility conformance based on a small sample matrix.
- Run schema/security tests, sync freshness, applicable render/visual tests, clean installation and privacy checks before publication. Keep generated review evidence in a private build directory; publish only sanitized test summaries and authorized examples.
- Do not weaken a validation gate merely to make a test pass. Fix the canonical code and rerun affected outputs.

## Curated example artifacts

Track six curated PDFs and six previews beside their sources under `skills/bilingual-pdf/examples/<language-pair>/` and `skills/course-guide-quick-reference/examples/`. Keep both course PDFs flat as `notes.pdf` and `quick-reference.pdf`. Regenerate them with `tests/README.md`, inspect content and metadata, and refresh each skill's local `examples/MANIFEST.json`. Never duplicate installed examples in a root examples directory. All article pairs must translate the same complete source and exercise the same features; recurring languages must remain text-identical. Keep compact compatibility fixtures in `tests/fixtures/`. Transient builds, logs, private inputs and full matrices stay ignored; do not substitute Actions artifacts for these directly browsable examples.

Keep native LaTeX and structured content as equal entry routes through the one canonical package. After editing article fixtures, run tools/export_native_examples.py and tools/sync_renderer.py; native example projects remain directly editable and buildable without Python. Test actual agent authoring from raw sources as well as compilation.

Keep defaults usable without setup. New visual behavior belongs in the canonical package's documented native configuration or standard package hooks, never in per-example hardcoded variants. Test meaningful sparse overrides, invalid inputs, both print parities and native/structured equivalence. Use skill-level references and licenses; do not add repeated per-example README/license files. Language-pair folders are useful project boundaries, while the single learning set stays directly under examples/.
