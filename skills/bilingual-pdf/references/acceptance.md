# Rendering acceptance

This checklist concerns layout and output integrity. The caller supplies paired content and owns its semantic choices. The renderer does not translate, establish source coverage, fact-check prose or certify accessibility.

## Before compiling

- Preserve the supplied input. Work in a fresh output directory.
- For JSON, validate against `schemas/document.schema.json`, then run `scripts/bilingual_pdf.py preflight`. Preflight also checks cross-field relationships, IDs, targets, tools and supported fonts/glyphs. Then export or render the document to resolve, decode and stage figure assets; preflight alone does not check their contents.
- For native LaTeX, resolve the installed package, declare languages/fonts and choose the paragraph-flow policy. Native TeX is executable; use trusted source or appropriate isolation.
- Verify that referenced images are authorized and available. Do not substitute fonts or download resources silently.

## Mechanical gates

1. Compile to stable references with XeLaTeX/latexmk. Reject missing glyphs, overfull boxes, undefined or multiply defined references, missing hyphenation data and explicit package errors.
2. Run `scripts/bilingual_pdf.py validate document.pdf --paired` for paired output, or omit `--paired` for a selected-language edition. Supply `--covers` only when booklet covers are used. Keep matching AUX/LOG files with the PDF during validation.
3. Confirm page dimensions, embedded fonts and intended blank pages. Booklet parity follows physical pages even if printed folios reset or use Roman numbers.
4. Check matching unit starts and table-row/list-item positions. For flowing paragraphs, verify that both sides can continue, the shorter side is not padded with invented content, and the next pair resynchronizes after both have finished.
5. Check links against their actual target pages and named destinations. A printed page label may differ from the physical PDF page. Keep relative cross-document targets together.

The validator is a set of mechanical checks, not a universal layout proof. Table rows align individually, but the JSON table is an unbreakable `ParallelKeep` group. Native paired rows can be authored outside that group to break between rows. Neither route splits an individual table row automatically.

## Inspect actual pages

Inspect every changed final page at readable resolution, not just a contact sheet or first-page preview. Check paragraph/table alignment, heading attachment, continuation boundaries, column order, divider endpoints, clipping, whitespace, images and captions. Inspect both binding parities when relevant.

For RTL/CJK, check shaping, punctuation, mixed-script numbers/identifiers, formula placement, list markers and reference suffixes. The physical left/right order must match the requested order independently of language direction. Font availability alone does not establish correct rendering.

Keep-together content that exceeds a page must produce an actionable error. Do not truncate, shrink individual content or bypass validation to obtain a nominal pass. Select breakable prose where appropriate or let the caller choose a different structure.

## Delivery record

Deliver the PDF and portable native project, including necessary images/package/license files; include the JSON source when used. State which mechanical and visual checks passed, failed or were not run. Distinguish current results from historical example/CI evidence. Do not claim universal language support, printer certification or PDF/UA conformance.
