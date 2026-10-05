# Native study API

This is the independent reference for `assets/studytools.sty` and `assets/study-tree.tex`. Manuscripts are native LaTeX, not a JSON collection. Rendering is owned by the explicitly installed `bilingual-pdf` dependency.

## Contents

1. Loading, compatibility and trust
2. Concepts, lookup groups, aliases and subentries
3. Local and companion-document references
4. Lookup rendering, navigation and headers
5. Decision questions, methods and typed edges
6. Labels and formatting hooks
7. Minimal complete use
8. Validation and limits

## Loading, compatibility and trust

Load `studytools` before language/manuscript configuration. It loads `xr-hyper` before the shared `paralleltext` package. Make both packages discoverable through `TEXINPUTS` or a portable delivery copy; do not assume the two installed skills are siblings.

`\StudyToolsAPIVersion` is `1`. The package requires native `\ParallelTextAPIVersion` `2`; a missing or incompatible version produces an actionable error. Keep the two skills on a matching tested repository revision. These interface numbers are separate from user-visible document version/status metadata.

The common package owns languages, fonts, styles, alignment, geometry, paragraph continuation, figures, covers and print checks. Consult its independently installed `references/latex.md`, `references/configuration.md` and `references/languages.md`. Do not copy that implementation into this skill.

All native arguments are trusted TeX, not sanitized strings. Disabled shell escape does not prevent arbitrary TeX filesystem access. Use appropriate isolation for untrusted manuscripts.

## Concepts, groups, aliases and subentries

Declare records in the preamble. Study IDs start with an ASCII letter and then use letters, digits, dot, colon, underscore or hyphen. IDs are case-sensitive and unique across concepts, routes and subentries. A displayed term is not an ID.

### Canonical concept

`\StudyDeclareConcept[options]{id}{sort-key}{left-title}{right-title}{notes-label}{body}`

- `id`: stable canonical target ID
- `sort-key`: nonempty literal ordering key; use a consistent policy such as lowercase English keys for an English A–Z sequence
- Titles: full display text in the physical left/right languages
- `notes-label`: label in the selected companion notes source; empty means no notes location
- `body`: authored native content using the shared `ParallelParagraph`, `ParallelText`, equations, figures and other documented commands; it is rendered in the Quick Reference and omitted in the compact index

Options:

| Key | Default | Meaning |
| --- | --- | --- |
| `lookup` | This record's ID | Explicit shared headword-group identity |
| `notes-source` | `notes` | Named companion source used by `notes-label` |
| `context-left`, `context-right` | Empty | Sense/subject qualifiers; both are required when a group contains several canonical concepts |
| `header-left`, `header-right` | Full titles | Short running-header text; printed headings remain full |

Lookup identity and sort order are independent. Equal sort keys do not merge records automatically. Records deliberately sharing one `lookup` must use the same sort key. Canonical concepts precede routes inside a group; IDs break otherwise equal ordering ties. This is deterministic string sorting, not automatic locale-aware collation.

A group with several meanings keeps distinct canonical IDs and paired sense labels. Do not merge different definitions solely because punctuation or spelling normalizes to the same string.

### Route with one or more targets

`\StudyDeclareRoute[options]{id}{sort-key}{left-title}{right-title}` declares a remembered word/task. Its options are the same record metadata above; context/notes fields are useful primarily on canonical targets.

`\StudyRouteTarget{route-id}{target-id}{left-context}{right-context}` adds one target row. Declare the route before its rows. Targets may be declared later in the preamble, but each must resolve to a canonical concept or subentry at document start. A route cannot target another route, so alias chains are rejected.

Context text identifies the relevant sense, condition or task. It may be empty for an unambiguous alias. Rows preserve their authored order. A route needs at least one target. A context-free pointer back to a canonical record in the same explicit lookup group is suppressed because that content is already present there; additional contextual/other targets remain visible.

`\StudyDeclareAlias[options]{id}{sort-key}{left-title}{right-title}{target-id}` is shorthand for a route with one direct, context-free target. It uses the same grouping and sorting rules.

### Subentry

`\StudyDeclareSubentry{id}{parent-concept-id}{left-title}{right-title}{notes-label}` declares a distinct target owned by a concept. Declare its parent first; the subentry inherits that concept's notes-source selection.

Place `\StudySubentry{id}{body}` inside the parent's body to render the labelled subentry. It uses the common unnumbered `ParallelSubsection*`, so dictionary subentries do not acquire meaningless section numbers such as 0.1. The compact index retains the subentry heading/destination even though it omits explanatory bodies.

A subentry pointer names the owning canonical concept, its sense qualifier when applicable, and the subentry title. Its local page is the subentry's own page, not the beginning of the parent concept. Printing a subentry twice creates duplicate layout IDs and fails; omitting a referenced subentry leaves a broken reference that must fail acceptance.

## Local and companion-document references

`\StudyReference{target-id}` produces a local link with the target's exact title/context and generated page, localized to the active physical side. It is intended inside paired content. Use a concept or subentry ID.

`\StudyDeclareNotesSource{source-id}{left-document-name}{right-document-name}{aux-basename}{pdf-path}` registers and imports a companion document. The source ID must be unique. The AUX basename omits `.aux`; the PDF path is the relative delivery target. Build that companion first and keep its generated AUX available while compiling dependants.

`\StudyNotesSource{aux-basename}{pdf-path}` is the convenience form for source ID `notes`, using the configured notes labels as its document names.

`\StudyNotesReference{target-id}` generates the companion's document identity, section and printed page. It emits no pointer when that source was not registered or the notes label is empty. This allows a selected form to stand alone without linking to omitted companions. The named PDF destination remains distinct from printed folios, including Roman folios.

Import only included companions. Registering a missing file is not the same as omitting it: missing/undefined external references must fail the build/acceptance checks. Different records can use different named notes sources. A downstream collection supplies private document identities, filenames and metadata; none belong in this public example.

## Lookup rendering, navigation and headers

`\StudyPrintQuickReference` renders one sorted headword sequence with substantive concepts, aliases and keyword routes interleaved. It does not create a separate aliases or keywords section.

`\StudyPrintKeywordIndex` renders a compact pointer view from the same registry. Canonical and subentry anchors remain present, while concept bodies are omitted. This is a separately selected product, not an extra required location in the default Quick Reference.

Use one lookup rendering command per PDF: repeated rendering would duplicate stable destinations. Choose collections by building separate requested forms together.

`\StudyAlphabetNavigation` declares the fixed A–Z navigation slots once in the preamble. During lookup rendering, the first character of each sort key selects its letter slot; non-A–Z keys clear that selection. The common package records all letters actually appearing on a page. This does not enable or style tabs by itself: configure `tabs`, `tab-top`, `tab-step`, `tab-height`, `tab-inset` and other native layout keys explicitly. The example uses A4-compatible settings; custom paper needs a geometry check.

`\StudyLookupGroupHook{first-record-id}{lookup-id}{sort-key}` is an initially empty public callback, invoked once before each new displayed group. Redefine it for additional project navigation instead of patching internal macros. It supplements the optional alphabet mechanism.

Use common `ParallelFirstEntry` / `ParallelLastEntry` headers. Record `header-left/right` metadata supplies short display text, while the full body headings stay unchanged. The shared renderer owns continuation cues and header height checks. Configure its `entry-header-width`, `entry-header-max-lines` and `entry-continuation-left/right`; do not truncate or shrink a troublesome heading silently.

## Decision questions, methods and typed edges

Decision IDs use the same letter-led syntax but a separate namespace from lookup records. Declare nodes and edges in the preamble.

| Command | Arguments and effect |
| --- | --- |
| `\StudyDeclareQuestion{id}{left-question}{right-question}` | Adds a natural question with a visible stable ID |
| `\StudyChoice{question-id}{letter}{left-choice}{right-choice}{target-id}` | Adds a forward edge; `letter` is one uppercase A–Z character and is unique within that question |
| `\StudyUnknown{question-id}{left-choice}{right-choice}{target-id}` | Adds the explicit `?` route; empty texts use the configured unknown labels |
| `\StudyDeclareLeaf{id}{left-title}{right-title}{body}` | Adds a method or terminal outcome with nonempty native body content |
| `\StudyContinue{leaf-id}{target-id}{left-context}{right-context}` | Adds one required forward continuation after a method leaf |
| `\StudyDeclareClarification{id}{left-title}{right-title}{body}{return-question-id}` | Adds an information-gathering node with a typed conditional return to a question |
| `\StudyDecisionID{id}` | Robust literal formatting for a visible decision ID, including underscores; safe in running-header records |
| `\StudyDecisionReference{id}` | Links to a node's visible ID, title and generated local page |
| `\StudyPrintDecisionTree{start-id}` | Prints an entry link, then all declared nodes in declaration order; each node is printed once |

Declare a question before adding its choices, and a method leaf before adding its continuation. Targets may be forward references. Every question needs at least two ordinary choices plus exactly one unknown route. Ordinary choices and required continuations must form an acyclic forward graph and terminate. Unknown targets, duplicate node IDs, duplicate choice letters, empty method bodies and accidental forward cycles are errors.

A clarification return is different from a forward edge. Its target must be a declared question. It is followed only after the stated missing information has been obtained; it is not an unconditional retry loop. The validator allows that typed return without treating it as an ordinary graph cycle. A method without a continuation is terminal. A clarification cannot also masquerade as a method continuation.

The start ID selects the entry point, not a filter that hides other declared nodes. All nodes remain in the document so conditional return targets are available. The tool validates graph structure, not whether a question is sensible or a method is factually correct. The author must check branch exclusivity, observability, return conditions and leaf usefulness.

## Labels and formatting hooks

`\StudySetup{key=value,...}` is preamble-only. Its native text keys are:

- `page-label-left/right`: `p.` by default
- `notes-label-left/right`: `Notes`
- `section-label-left/right`: `section`
- `unknown-label-left/right`: `Unknown / insufficient information`
- `return-label-left/right`: `After obtaining the missing information, return to`
- `continue-label-left/right`: `Required next step`

Values are TeX tokens, not a fixed list of translated strings. Supply the requested languages explicitly.

For languages whose word order cannot be represented by prefix labels, redefine these standard native hooks:

- `\StudyLocalReferenceLeft{title}{page}` and `\StudyLocalReferenceRight{title}{page}` format the clickable local reference, including decision references
- `\StudyNotesLocationLeft{document-name}{section}{page}` and `\StudyNotesLocationRight{document-name}{section}{page}` format a clickable companion location

The default hooks use the configured labels in English order. The example's Chinese hook places section/page numbers before their Chinese suffixes. Do not hardcode another project's publication-number pattern or language pair into the shared package.

Document version and review status are independent optional strings in the common native renderer. A project can populate its `document-version` and `document-status` keys from build metadata and choose how to display them; the study layer imposes no format.

## Minimal complete use

```tex
\documentclass{article}
\usepackage{studytools}
\StudyDeclareConcept{method}{method}{Method}{Method}{}{
  \ParallelParagraph{method-body}{Explain the method.}{Explain the method.}
}
\StudyDeclareAlias{procedure}{procedure}{Procedure}{Procedure}{method}
\begin{document}
\StudyPrintQuickReference
\end{document}
```

Supply appropriate language/font declarations for a non-English pair. A fresh example project shows all four products, companion imports, subentries and a clarification return. No repository helper is required to compile native manuscripts.

## Validation and limits

The build must fail on structural errors; acceptance also checks actual links, fonts, glyphs, aligned positions, printable insets and intended blank pages. Tabs intentionally occupy part of the body margin: validate their configured minimum physical inset as well as the live body-column geometry, rather than disabling margin checks. The example's tabs are inset 6 mm and its minimum ink check is 5 mm; body columns retain their separately recorded geometry.

Read the [build guide](rendering.md) and [review checklist](review-release.md). Native declarations do not establish source rights, source coverage, semantic equivalence, factual correctness, universal language support or accessibility conformance. Keep these judgments separate from executable package checks.
