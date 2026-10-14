# Complete example and review scope

[guide/source.txt](../examples/guide/source.txt) is an original English source about a fictional community seed shelf. [guide/translation.json](../examples/guide/translation.json) is its complete French paired master. It exercises title, heading, paragraphs, two list items, a two-column table with distinct cell units, table/figure captions and descriptive alt text. The shared [diagram](../examples/guide/assets/shelf.png) contains no language-dependent text.

This is an illustration, not horticultural advice. Its source includes authored alt text; a real source without it requires an identified authoring decision rather than invented source quotation. The [manifest](../examples/guide/MANIFEST.json) records source/asset hashes, provenance and exact source-unit byte locations. Source units are separated by blank lines in the plain-text snapshot; the master supplies their explicit structural types.

The example pairs were read against the full source for quantities, conditions, negation, terminology and boundaries. The reviewed state demonstrates this process; validation alone does not perform semantic review or guarantee publication-quality French or other language pairs.

## Inspect the exchange and review scope

This is a supplied semantic exchange example, not an alternate authoring command sequence. Read [source.txt](../examples/guide/source.txt) completely, then compare its exact inventory with [translation.json](../examples/guide/translation.json). The [exchange reference](semantic-exchange.md) defines fields, structural blocks and the read-only consumer validator.

For a new translation supported by the Markdown importer, use [workflow.py](workflow.md): read and initialize complete source units in preparation batches, split oversized units within their current batch, translate the bounded active groups and review all pairs in a separate pass. Save and next are explicit separate actions. Keep rich content that the importer cannot represent in an explicit lossless native route. Export the reviewed master only when a consumer needs semantic exchange JSON.

## Compare a complete paragraph

The `intro` source states that the shelf contains 12 packets, each has one label, and the register records their contents. Its French counterpart is:

> L’étagère commune contient 12 sachets. Chaque sachet porte une étiquette, et le registre indique son contenu.

Compare the quantity, one-label-per-packet relation, pronoun reference and natural French. Review the exact complete source and target with the already-read global context. A reviewed field records an attestation; neither that field nor a passing validator demonstrates semantic judgment.

## Preserve table-cell identities

Each cell keeps its own stable ID and target. Read a row together with its headers: `Crop / Packets` gives the context for `Bean / 3`. The target row `Haricot / 3` preserves both crop and count. Inspect both pairs, including the literal number, without collapsing their separate IDs. In the JSONL workflow, submit only the active group's IDs and return its references unchanged; use the separate review stage to attest to the comparison.

## Native TeX equivalent

Create the editable source-first manuscript with stable pair IDs and explicit empty target arguments; execute that save and inspect the file before writing translated prose:

```tex
% Source snapshot retained separately; intro target is pending.
\ParallelParagraph{intro}
  {The community shelf holds 12 packets. Each packet has one label, and the register records its contents.}
  {}
```

Then read this complete source paragraph in context, author and proofread its French counterpart, and update only intro's second argument in the same manuscript. Save and confirm that scoped edit before working on the next pair. Keep source IDs and source arguments unchanged. For a short native table row or coherent list, inspect all its source fields with their headers/context, review the separate target fields together and save that scoped row/list once. A brief native comment/progress record can record completed review; JSON exchange is not required. Fill all requested target slots before rendering the deliverable.

For source changes, preserve the previous target and mark that pair for review. For a JSONL task, use the documented workflow and recovery boundaries; do not edit an exchange or master directly to bypass review. Use an extra checkpoint only when it serves a real revision need. When rendering this demonstration outside the installed example directory, stage its one shared figure beside the working master or pass the renderer's supported asset-root option.
