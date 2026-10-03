# Acceptance

## Mechanical checks

Build with latexmk to resolve native labels and page references. Treat missing glyphs, overfull boxes, undefined or duplicate references, oversized paired units and missing language patterns as findings to fix. The importer enforces text escaping, stable IDs, paired list/table dimensions and safe relative image paths; native TeX has a different trust boundary.

With optional Python QA dependencies installed:

```sh
python3 scripts/bilingual_pdf.py validate path/to/main.pdf --paired
```

The matching `.aux` and `.log` must be beside the PDF for pair-position and log checks. Add `--covers` for a booklet with outside covers and blank inner faces; omit it for ordinary articles. Use `--margin-mm N` when the project deliberately changes the nominal equal side margin. The checker verifies embedded fonts, pair starts/pages, selected print bounds, log defects and local/relative cross-PDF destinations, including named targets. It is not a generic PDF security auditor or accessibility certification.

Keep source projects complete. A Quick Reference's relative target PDF must stay in the documented bundle location. Browser PDF viewers may handle external-document links differently from desktop viewers; inspect the actual PDF action and verify with an appropriate viewer when needed.

## Personal page review

Render every page to a readable image and look at it. Confirm useful first-page content, meaningful density, corresponding units on the same page, a stable divider, intact equations, properly placed list markers, readable captions and accurate figures/tables. Review both page parities and every intentional cover/blank when present. An image can compile cleanly and still have a wrong scale or label.

Read source and translation independently in context, including English readability when present, then reconcile meaning, names, numbers, negation, qualifications and omissions. Track recurring terminology and deliberate variants; prefer natural sentences over literal word substitutions. Check that every figure mentioned is present or precisely located and explained, and that a worked example includes the inputs and assumptions needed to follow it. Exact vertical starts do not prove a translation. State when review is author-only, when an independent specialist read it, and what remains unverified.

## Delivery

Deliver the PDF and portable editable `.tex`/image/package files, plus structured source if used. Separate transient build logs from the handoff. Preserve user inputs and do not publish private provenance or metadata. Report actual passes, failures and unrun checks rather than describing a planned check as complete.
