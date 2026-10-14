# Design provenance

The workflow, exchange, validator and example are original implementations.

Design research consulted:
- [nature-reader's output specification](https://github.com/Yuan1z0825/nature-skills/blob/main/skills/nature-reader/references/output-spec.md), in Apache-2.0-licensed [nature-skills](https://github.com/Yuan1z0825/nature-skills): stable anchors and typed source maps informed the inventory/structure distinction.
- [baoyu-translate](https://github.com/JimLiu/baoyu-skills/blob/main/skills/baoyu-translate/SKILL.md), in MIT-licensed [baoyu-skills](https://github.com/JimLiu/baoyu-skills): shared context and terminology informed concise master-level context.

No upstream source code, workflow text, templates or examples are bundled. Neither project is a runtime dependency. The single-master, full-source-first and independently reviewed per-unit procedure is this skill's own workflow. Referenced concepts do not establish semantic accuracy or replace the caller's language, scope and format.

The skill's [MIT license](../LICENSE) covers its authored files.

## Command composition

Independent commands and stdin-JSONL batches use one command registry, parameter definition and handler per operation. This keeps the two entry routes aligned without maintaining a second mutation implementation. Each action carries its own reference and the process fixes one master; an atomic batch does not create implicit reference substitution or cross-task access.

Save and next are separate operations so a mutation acknowledgment stays small and the caller explicitly controls when another body is returned. A batch permits at most one body-reading action, last. Exact adjacent split anchors retain the agent's semantic choice while moving unique-location resolution and codepoint counting into deterministic code. Exact old/new review patches avoid retransmitting unchanged targets, while a subsequent comparison read preserves the review boundary. Local repair and a full review restart serve different scopes; unresolved todos and current-review checks govern export.

These are interface and integrity choices, not measured performance claims. Compare token, call and elapsed-time costs with the maintained benchmarks before claiming an improvement.

## Review-instruction validation scope

A scoped cold-context translation trial reached structural readiness with all 88 units recorded as reviewed. Independent language inspection nevertheless found two meaning failures: a negation/modal-scope error survived the review, and a review correction introduced a more specific actor unsupported by the source context. The actor also omitted some progress updates that the tool had emitted. Structural completion therefore did not establish semantic accuracy or reporting compliance.

The resulting instruction change teaches proposition/scope comparison, source-evidenced actor resolution before corrections, semantic comparison on the existing post-patch read, and inspection of every JSONL progress receipt. It does not add a routine full-document pass or embed trial answers. These are targeted responses to observed failures; effectiveness requires a fresh-context retest on the failed phenomena and nearby variants, and no instruction or passing structural gate guarantees translation accuracy. Detailed prompts, source material, trial identities and language-review evidence remain private.

A subsequent focused language check passed its 32 semantic cases, while the actor still omitted five of 26 emitted progress updates. The next scoped change renders each public progress value as one directly forwardable string, replacing its public object representation, and reduces the actor's step to forwarding it before the next tool call. A small cold-context progress check is required to evaluate that change; the earlier language result does not establish reporting compliance.
