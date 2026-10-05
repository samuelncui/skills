# Coverage and review: choosing a study set

This original self-hosted example teaches how to choose and build study forms. Its scope is the seven sections of [source.md](source.md); it does not claim coverage of an external subject. [source-map.json](source-map.json) records provenance and native target IDs, not a second manuscript input format.

This document records source-level coverage and the example review below. Earlier example page counts and review results do not establish acceptance of these sources.

## Authored forms

- [Notes](notes.tex), with explanations in [notes-content.tex](notes-content.tex)
- [Unified Quick Reference](quick-reference.tex), with substantive concepts and direct routes interleaved in one sorted sequence
- [Optional Keyword Index](keyword-index.tex), a separately selected compact view of the same [entries.tex](entries.tex) registry
- [Decision Tree](decision-tree.tex), with questions, methods and typed edges in [decisions.tex](decisions.tex)

English is the physical left language and Simplified Chinese the right. [common.tex](common.tex) and [languages.tex](languages.tex) hold common presentation choices; the [Makefile](Makefile) selects products and builds included notes first. The default pair is notes plus Quick Reference. An index or tree can also stand alone without importing omitted companions.

The lookup registry contains five canonical concepts, three subentries and twelve alias/keyword route records. One route deliberately shares the Decision Tree headword, avoiding a duplicate lookup location. The decision graph contains two questions, five method/outcome leaves and two clarification nodes. These are source inventories, not PDF page counts.

## Coverage map

| Source section | Explanation in notes | Lookup coverage | Decision coverage |
| --- | --- | --- | --- |
| S1: Select the reader's task | notes, quick, index, tree | The four canonical form entries | choose-goal and choose-lookup |
| S2: Preserve evidence and scope | notes-evidence | evidence subentry; Coverage and Source map routes | review-set |
| S3: Use one native implementation | build | Build and portable delivery; Portable project points directly to it | The four make-* methods |
| S4: Make lookup paths direct | quick | Quick Reference; Aliases, Find a word and QR routes | make-quick and make-index |
| S5: Choose a paragraph-flow policy | notes-flow | Long paragraphs subentry; Page breaks route | make-notes |
| S6: Make decision paths explicit | tree-clarification | Unknown information subentry; Missing information and Unknown routes | clarify-goal, clarify-lookup and review-set |
| S7: Check and deliver | review | Scope and evidence subentry | review-set |

Coverage is distributed across the selected forms. A compact lookup route need not repeat the entire source section. The standalone index intentionally omits explanatory bodies; the tree includes method instructions so that it remains useful alone.

## Retrieval exercises

Use the final rendered product to establish these outcomes:

1. **QR** → Quick Reference. Reach the substantive canonical entry directly, then its notes section when notes are included.
2. **Find a word** → two clearly labeled targets: Quick Reference for a compact answer, Keyword Index for pointers only.
3. **Page breaks** → Explanatory notes / Long paragraphs. Reach the subentry's own page, not merely the first page of its parent concept.
4. **Coverage** or **Source map** → Explanatory notes / Scope and evidence. Confirm the explanation distinguishes provenance from manuscript input.
5. **Missing information** or **Unknown** → Decision Tree / Unknown information. Distinguish a conditional clarification return from a required continuation.
6. **Decision Tree** → one deliberately grouped headword with its substantive entry. A context-free route to that same entry must not create a second visible lookup location.
7. In the standalone Keyword Index, follow each local concept/subentry pointer. When notes are omitted, no external notes pointer may remain.

Check generated titles, sense qualifiers where present, local pages and actual PDF destinations. Test printed lookup as well as clicking: a clickable title alone does not establish a usable printed pointer.

## Decision exercises

- choose-goal A → make-notes → review-set
- choose-goal B → choose-lookup A → make-quick → review-set
- choose-goal B → choose-lookup B → make-index → review-set
- choose-goal C → make-tree → review-set
- choose-goal ? → clarify-goal; obtain one real reader task before returning to choose-goal
- choose-lookup ? → clarify-lookup; establish whether an answer or location is wanted before returning to choose-lookup

The four make-* leaves require continuation to review-set. The review-set outcome is terminal. Clarification returns are conditional, not unconditional retries. Review whether the questions are observable and methods useful; an acyclic graph alone cannot establish this.

## Current example review

Reviewed on 2026-10-05. The current native examples produce Notes (3 pages), Unified Quick Reference (2), Keyword Index (2) and Decision Tree (2). All nine pages passed the selected-form integration checks and readable-resolution visual review. Checks cover embedded fonts, aligned positions, intended margins/tabs, generated local/subentry destinations and included named companion links. The clarification-return label spacing was corrected and checked in the actual PDF text and page image.

Source reading verified the self-hosted seven-section scope, the unified lookup organization, the direct Build/portable-delivery target and the explicit clarification/required-continuation paths. These are assistant reviews of this original example, not external translation, domain or accessibility certification. The local artifact manifest binds the delivered files and their source/dependency hashes. Repository-wide profile results are recorded separately.

## Rendered acceptance and limits

For the exact source/output revision being delivered, record the selected products, build and validator results, link checks and actual page review. Follow the [build guide](../references/rendering.md) and [review checklist](../references/review-release.md):

- Rebuild selected forms and regenerate their previews and artifact manifest. Do not reuse older artifacts as current evidence.
- Check every local/subentry destination and included companion's document identity, section, printed page and named PDF target.
- Inspect every final page for aligned starts, paragraph continuation, glyphs, clipping, headings, alphabet tabs, folios and references.
- Read both languages independently and reconcile claims and qualifications.
- For portable delivery, rebuild the selected native sources with the explicitly discovered bilingual dependency and necessary package files/licenses.

Report passed, failed, blocked, incomplete and unrun checks separately. Source inspection is not a rendered, independent translation or accessibility audit. This small example does not demonstrate every language, printer or viewer's handling of cross-document links.
