# Structured decision graphs, contract v1

Use this optional route when the input is a structured decision graph. Keep one versioned JSON graph as the authoritative content and edge source; regenerate TeX after every edit. Native notes, quick references, indexes and manually authored graphs remain supported. The importer emits the existing studytools semantic commands, not another renderer or reader graph. `bilingual-pdf` owns typography, escaping, restricted math and image resolution.

## Installed workflow

1. Discover installed `study-notes` and `bilingual-pdf` through the host's skill listing. Read both SKILL.md files. Set `STUDY_NOTES_SKILL` and `BILINGUAL_PDF_SKILL` to those discovered directories. The importer requires bilingual-pdf renderer API 1 and the studytools helper-call API shipped with this revision. Pin both skills to the tested repository revision in downstream projects; do not infer paths from sibling directories.
2. Use Python 3.10+ in a project environment. Install `study-notes/requirements.txt` and the discovered bilingual-pdf requirements. Native-only manuscripts do not require Python. No script fetches a skill or installs packages automatically.
3. Start from [the complete paired parcel example](../examples/structured-graph.json), or author the standard [JSON Schema](../schemas/graph-v1.schema.json). Read the actual sources first. Supplied pairs need no translation service or model review workflow. Preserve their wording; content review is separate from compilation.
4. Validate, order and generate into a new output directory. The command rejects an existing output directory to avoid overwriting user work.

```sh
python "$STUDY_NOTES_SKILL/scripts/structured_graph.py" graph.json \
  --bilingual-pdf-skill "$BILINGUAL_PDF_SKILL" --output generated
```

Omit `--output` for validation and ordering only. Use `--asset-root ./approved-assets` only when figures are present. The output is `graph-declarations.tex`, `graph-body.tex`, `graph-report.json`, and content-addressed image copies under `assets/` if needed. Paths in the fragments are relative to this generated project directory.

5. Use an existing trusted native project's preamble/layout, or copy [the minimal driver](../examples/structured-graph.tex) into `generated/main.tex`. Put the declaration fragment in the preamble and the body fragment in the document. Select `\StudyGraphReaderProfile` so every visible node receives its generated N identity; the optional hierarchy profile changes only presentation. Localize labels through `\StudyGraphLabels` when needed. Keep native customization outside generated fragments.

```sh
cp "$STUDY_NOTES_SKILL/examples/structured-graph.tex" generated/main.tex
cd generated
export TEXINPUTS="$STUDY_NOTES_SKILL/assets//:$BILINGUAL_PDF_SKILL/assets//:${TEXINPUTS:-}:"
xelatex -no-shell-escape -halt-on-error -interaction=nonstopmode main.tex
xelatex -no-shell-escape -halt-on-error -interaction=nonstopmode main.tex
```

The sample driver is English/French. Configure other language profiles, fonts, directionality and paired/left/right selection with the discovered bilingual-pdf native language/layout references. Languages in JSON describe the supplied fields; they do not silently reconfigure an unrelated native preamble. Inspect the resulting PDF pixels, text, destinations and reader paths. Deliver the authoritative JSON, driver/customization, pinned dependency identities, generated report and reviewed PDF. Generated TeX remains a disposable derived artifact.

## Data model

All objects reject unknown properties. The CLI rejects duplicate object member names and non-finite JSON numbers before validation. Schema validation uses JSON Schema draft 2020-12 and is followed by semantic validation. The schema alone cannot establish valid target relationships or flow.

Required root properties:

- `schema_version`: integer `1`.
- `languages`: exactly two installed renderer profile IDs. Repeating a language is allowed for same-language parallel variants. Edition selection never changes node order. The renderer's mixed simplified/traditional Chinese limitation applies.
- `title`: exactly two nonempty plain strings.
- `entry`: stable semantic node key.
- `seed_order`: every node key exactly once; supplies deterministic tie rank and baseline.
- `nodes`: one to 2,000 visible nodes. Every visible decision, procedure and solution receives an Nx identity. A finishing procedure uses a local `stop` field, not an extra invisible/sentinel node.

Optional `ordering` holds `exact_limit` (integer 1–9, default 9) and `budget` (integer 1–1,000,000, default 60,000). Optional `sources` is a catalog of unique `{key, sha256, title}` records. The SHA-256 is the caller-verified immutable source identity; the importer checks binding consistency, not the existence, authenticity, licensing or factual truth of that source. Catalog titles are paired plain strings. Unused catalog entries are metadata, not hidden reader content.

Keys are lowercase ASCII words separated by hyphens, at most 80 characters. Choose meaningful semantic keys that survive translation, title editing and reordering. Never derive keys from page numbers or Nx identities.

Every node has `key`, `kind` (`decision` or `procedure`), `function` (`question`, `action`, `check`, `warning`, `result`) and paired plain `title`. A result/leaf is a procedure with function `result` and remains numbered. Optional common fields:

- `prerequisites`: paired content printed inline as context at the node needing it.
- `fields`: ordered `{key, role, text}` records. Field keys are unique within the node. Roles map directly to native `input`, `output`, `check`, `warning`, `result`, `operation`, `limits`, `context`, `related`, `explanation`, or `support`.
- `completion_check`: paired content, with a native completion-check anchor.
- `loop`: paired `carried`, `progress`, `continue_when`, `exit_when` fields.
- `figures`: ordered `{path, caption}` records, with paired captions.

A decision requires nonempty ordered `choices`, each `{condition, target}`. Their array position generates A/B/C; the importer never sorts, merges or rewrites alternatives. The first true condition wins. Resolve an earlier unknown condition before treating a later condition as applicable. An uncertainty/inspection task is optional: represent it as a source-supported explicit choice and node only when needed. A decision cannot have steps, next or stop. Its prerequisite facts stay inline.

A procedure may have ordered `steps`, each with paired `text` and an optional `call`. It finishes through exactly one `next` target or local paired `stop`, except that a declared helper return exit may have no ordinary route. Empty/zero-step result procedures are permitted when their fields/stop provide the answer. Ordinary routes may converge. Every node must be reachable through the declared executable edges.

## Optional helper calls and precise limits

A call belongs immediately after a procedure step. It has:

```json
{
  "target": "choose-material",
  "when": ["Before closing the box.", "Avant de fermer la boîte."],
  "outputs": ["Selected material.", "Matériau choisi."],
  "resume": {"node": "pack-parcel", "step": 2},
  "return_exits": ["use-paper", "use-padding"]
}
```

`target` may be a decision or procedure. All return exits must be reachable procedures. `resume.node` must be the owning procedure; `resume.step` must be a later actual step or `completion_check` with that field present. The region stops at declared return exits. Every region node must have a structural path to a declared exit. Nested/recursive calls and overlapping regions with incompatible return exits are rejected in v1. A return-only exit cannot be reached in ordinary entry flow; give it an ordinary `next` when ordinary access is intended. Calls are never silently converted into jumps.

The motivating reader task in the neutral example is selecting one material through an optional question helper, bringing that result back, and finishing the existing packing procedure. This does not require a separate reader graph, inspection stage, uncertainty topology or call for ordinary solutions. Native `StudyGraphCall` keeps its old procedure-only contract. The importer uses `StudyGraphHelperCall` for decision-entry helpers and `StudyGraphReturnExit` only for return-only exits.

Loop annotation is a structural obligation: removing annotated nodes must leave the ordinary-flow graph acyclic. Calls and their synthetic return edges are excluded from that ordinary-cycle test. The validator does not prove predicate exclusivity, progress, termination, factual validity or natural-language quality. Review those claims against the source.

## Paired rich content and source binding

A paired content field contains exactly two entries. Each entry is either a nonempty plain string or `{ "runs": [...] }`. Plain text is escaped once through bilingual-pdf, including TeX-looking text. Runs are explicit and ordered:

- `{ "kind": "text", "text": "Literal text" }`
- `{ "kind": "math", "text": "\\frac{1}{2}" }`: inline restricted math, validated by bilingual-pdf's canonical equation policy, plus balanced braces. No separate graph math allowlist.
- `{ "kind": "reference", "source": "guide", "sha256": "<64 lowercase hex digits>", "locator": "Section 2" }`: binds the exact source identity; emits the current-language source title and literal locator. Unknown/stale bindings fail. These are textual citations, not invented PDF links or externally fetched content.
- `{ "kind": "node", "target": "finish" }`: native generated node/page reference, excluded from executable ordering edges.
- `{ "kind": "native", "text": "\\emph{Trusted native text}" }`: rejected unless the caller explicitly passes `--trusted-native`.

Nonempty fields, bounded string lengths, control/direction characters, identifiers and references are validated. Embedded bidi control characters are rejected; use the native renderer's documented language configuration. Arbitrary paragraph/list/table/span or directional-run encodings from other contracts are not accepted by accident. Represent supported text/math/reference runs explicitly, or retain a trusted native route where necessary. The separate bilingual-translation plain-text exchange remains unchanged; do not flatten rich graph fields into it. Translation/review state is not generated or certified by this importer.

For every paired content field the report records its JSON pointer, SHA-256 of canonical paired content and emission coverage. Structural fields (keys, edge targets, roles, configuration) are validated, never treated as text. Source catalog titles are consumed by bound reference runs. A successful coverage check proves mapping, not equivalence of two languages or correctness of prose.

## Trust and assets

Native TeX is executable input. The explicit flag acknowledges that route; it is not a sanitizer. Structural guarantees cover declared JSON edges only. Native runs are uninspected executable content: keep routing in structured properties and use this route only for trusted content constructs; macros that redefine flow or declarations invalidate the graph-only semantic guarantee. Use trusted inputs or suitable isolation for both native runs and the surrounding native driver. Disabled shell escape alone is insufficient. Plain strings and restricted math do not enable arbitrary preamble commands.

Figures require an explicit asset root. Paths must be relative PNG/JPEG names accepted by bilingual-pdf, with no traversal, absolute paths, URLs or symlink escape. Files must exist, be regular, be at most 10 MiB each and at most 40 million pixels, and pass Pillow verification. The importer copies only validated images with content-addressed names. It performs no network fetch, source-derived path lookup or credential access. The caller owns permission to process/share each source and asset.

## Ordering evidence and bounds

Objective: sum of absolute ordinal distances over distinct directed executable transitions, with unit weight. Reverse directions count separately; duplicate conditions with the same transition do not imply traffic weights. Include choices, ordinary next, calls and declared returns. Exclude same-node transitions, local stop text and optional node citations. Preserve each node as a whole and preserve every field/choice/step order.

Entry is fixed first. At or below `exact_limit`, enumerate every remaining-node permutation (at most 8! = 40,320 scores); this is an exact optimum only for that constrained ordinal objective. This bounded exhaustive search ignores the heuristic budget. Larger graphs use deterministic rank-tie-broken swaps/relocations, at most `budget` candidate scores including the baseline, and retain a result no worse than baseline. There is no approximation ratio or global-optimum claim for that branch. Page distances are measured after rendering, never certified by ordinal ordering.

The report records algorithm/API/schema versions, effective settings, seed/baseline/final order, exact edges, scores, evaluations, certification flag, source/output hashes and key-number-anchor crosswalk. Hashes use UTF-8 canonical JSON (sorted keys, compact separators, Unicode preserved) for structured values and exact UTF-8 bytes for output files. The report does not independently certify its own optimality claim; maintained independent tiny-graph oracle tests check the exact algorithm.

## Maintainer verification

From a clean checkout, install root requirements and run `python -m unittest discover -s tests -p 'test_*graph*.py' -v`. These maintained tests include independent small-graph optimum checks, deterministic bounded larger cases, invalid graph/text/math/path data, complete field coverage, native-command equivalence and separately installed dependencies. Run the scoped native helper/component and structured-import render profiles documented in the repository test guide. Inspect current generated PDF pixels, visible Nx identities, links and source-defined reader paths before publishing. Do not publish private inputs, machine paths or migration receipts.
