# Native decision-graph components

These generic components render a validated decision graph. They do not validate graph reachability, first-match predicate meaning, loop progress or scientific correctness. A downstream structured-data adapter must validate these before emitting native TeX. The graph may converge or cycle; do not run the older acyclic tree validator on it.

## Ownership and reader profile

`studytools.sty` loads `study-graph-components.tex`. Semantic roles map to the installed `paralleltext` roles; `paralleltext` owns physical fonts, colors, spacing and columns. Generate reader fragments with the semantic commands below; put presentation overrides in the preamble using the common renderer's documented configuration/hooks. This keeps one style definition across nodes and language editions. Private course content belongs in downstream projects, never these assets or fixtures.

Call `\StudyGraphReaderProfile` in the preamble for compact number-and-title headings, plain numbered solution steps and ordinary reader-facing labels. It changes no page geometry. Override localized words with `\StudyGraphLabels{key}{left}{right}` after selecting the profile. Register both language titles; references automatically use the current language title and printable page. Render one graph in ordinary left/right paired cells, with each side using its own title and labels.

Use `\StudyGraphLegendItem{question|action|check|warning|result}{description}` inside an ordinary paragraph cell for a reader-facing function legend. It uses the exact function-to-role mapping of graph headings and the current localized label; no downstream color map is needed. Question/check use the concept role, action/result the example role, and warning the caution role.

## Registry and anchors

- `\StudyDeclareGraphNode{opaque-key}{display-number}{decision|procedure}{question|action|check|warning|result}{left-title}{right-title}`
- `\StudyDeclareGraphTerminal{opaque-key}{left-title}{right-title}`
- `\StudyGraphNode{opaque-key}`
- `\StudyGraphReference{opaque-key}`

Keys are stable lowercase ASCII words separated by hyphens. Numbers are positive, unique and derived by the adapter from one explicit display order. The terminal has no artificial node number. Node labels are `graph:<key>`; step labels `graph:<key>:step:<n>`; completion labels `graph:<key>:completion-check`. Resolve actual PDF destinations from the AUX rather than guessing hyperref target names. Reference rendering never changes the current node.

## Rule placement

Call `\StudyGraphRulePlacement{node|intro}` in the preamble. The default `node` preserves automatic first-match paragraphs after decision headings and explicit `\StudyGraphFirstMatch` output. Choose `intro` when the document already provides the full priority/uncertainty rule once in its introductory guide: automatic rule paragraphs are omitted entirely, and explicit `\StudyGraphFirstMatch` calls produce no output. The caller owns that introductory rule; this option does not generate it. It leaves local choices, uncertainty conditions, required facts, warnings and fallback/invariant rules unchanged. Unknown values and document-body changes are errors.

## Choices and uncertainty

- `\StudyGraphInstruction{reader-instruction}`
- `\StudyGraphFirstMatch`
- `\StudyGraphChoice{ordinal}{natural-condition}{target-key}`
- `\StudyGraphFallback{ordinal}{condition}{target-key}`
- `\StudyGraphUncertainty{condition}{needed-facts}{target-key}{invariant-result-rule}`
- `\StudyGraphCombinedFallback{ordinal}{fallback-condition}{uncertainty-condition}{needed-facts}{target-key}{invariant-result-rule}`

Ordinals generate A/B/C in order. First-match means stop at the first true condition. An undecided earlier condition that could affect the requested result must not be treated as false. The adapter may consolidate uncertainty and final fallback only when their destinations match; preserve both triggering conditions and invariant-result scope. Different destinations remain distinct. The combined component does not prove these semantic conditions itself.

## Procedures and fields

- `\StudyGraphOperationChoice{ordinal}{condition}{owner-key}{first-step}` points to the explicit local step, not back to the node heading. An empty fourth argument renders only the lettered condition, without a destination line or arrow; follow it with the source-defined local execution scope. Do not invent a first step. The owner must still be declared. Nonempty steps retain ordinary positive-integer/target validation.
- `\StudyGraphStep{one-based-step}{text}`
- `\StudyGraphCompletionCheck{text}`
- `\StudyGraphField{field-key}{text}`

Field keys: input, output, check, warning, result, operation, limits, context, related, explanation, support. Use lettered operation selectors only for actual alternatives; unconditional procedures go directly to inputs and numbered steps. A valid input contract and a correct solution are authoring responsibilities.

## Reuse, continuation and loops

- `\StudyGraphCall{callee-key}{when}{returned-outputs}{resume-key}{resume-step}`; the step is a positive integer or `completion_check`.
- `\StudyGraphResumeReference{key}{step}`
- `\StudyGraphCalleeExit{ordinary-next-key}`
- `\StudyGraphJump{key}`
- `\StudyGraphLoop{carried-results}{progress}{continue-condition}{exit-condition}`

Emit a reuse instruction immediately after its owning step. The callee must be a procedure. A requested return takes precedence over that procedure's ordinary next link; an ordinary jump does not create a return obligation. Reader labels should say what to use, what result to bring back and where to continue, rather than exposing execution-mode jargon. Cycles need a source-validated progress/exit rule; typesetting is not a termination proof.

## Terminal presentation

Call `\StudyGraphTerminalMode{link|local}` in the preamble. Default `link` preserves the terminal destination and page reference. In `local` mode, `\StudyGraphJump` and the ordinary-next branch of `\StudyGraphCalleeExit` render a terminal target as a local result field with its registered current-language title, without a destination link or page. Nonterminal jumps and genuine call-return/resume references are unchanged. Register an actionable completion title; this setting does not validate or rewrite terminal content. Unknown values and body-time changes are errors.

## Verification

For an installed skill, build the authored native project with the discovered dependency and follow the [rendering checks](rendering.md#check-the-selected-outputs). Test adapter field coverage, source bindings, graph targets and any source-defined loop progress/exit conditions separately. Repository maintainers additionally use `tests/study_graph_components.py` for scoped English, paired, style-hook and negative API cases; its neutral fixture is repository-only and contains no private course data. Inspect current-hash-bound raster pages: passing compilation cannot establish reader usability, semantic correctness or absence of clipped content. Preserve delivered artifacts when producing comparison candidates.
