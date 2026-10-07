# Complete example and review scope

[guide/source.txt](../examples/guide/source.txt) is an original English source about a fictional community seed shelf. [guide/translation.json](../examples/guide/translation.json) is its complete French paired master. It exercises title, heading, paragraphs, two list items, a two-column table with distinct cell units, table/figure captions and descriptive alt text. The shared [diagram](../examples/guide/assets/shelf.png) contains no language-dependent text.

This is an illustration, not horticultural advice. Its source includes authored alt text; a real source without it requires an identified authoring decision rather than invented source quotation. The [manifest](../examples/guide/MANIFEST.json) records source/asset hashes, provenance and exact source-unit byte locations. Source units are separated by blank lines in the plain-text snapshot; the master supplies their explicit structural types.

The example pairs were read against the full source for quantities, conditions, negation, terminology and boundaries. The reviewed state demonstrates this process; validation alone does not perform semantic review or guarantee publication-quality French or other language pairs.

## Execute preparation before target authoring

Read [source.txt](../examples/guide/source.txt) completely. The example [preparation script](../examples/guide/prepare_master.py) reads only original source bytes, source locations and the declared structure. Run it to create a new working master:

```sh
python3 -B examples/guide/prepare_master.py --output master.json
python3 -B scripts/translation_contract.py validate master.json --untranslated
```

Let this preparation execution finish. Inspect its readback and compare the saved source inventory with the original. All target slots are empty at this checkpoint. The completed translation.json is a separate worked result for comparison, not an input to preparation. Original source and figure bytes remain unchanged.

## Later, author and persist one full unit

Resume from master.json. Display the active full paragraph and shared context:

```sh
python3 -B scripts/translation_contract.py view master.json --unit intro --context
```

The source states that the shelf contains 12 packets, each has one label, and the register records their contents. Translate that complete paragraph, then compare the two texts for the quantity, one-label-per-packet relation, pronoun reference and natural French. After that review, record only this unit:

```sh
python3 -B scripts/translation_contract.py record-review master.json --unit intro --source-hash c48177efad2dcb7919a381690649094fe089bd1bfb2a5de8e82db72ea4e5699d --target "L’étagère commune contient 12 sachets. Chaque sachet porte une étiquette, et le registre indique son contenu."
```

The command saves the same master and returns the next pending source unit. Confirm that result before authoring its target. Use the returned complete source, already-read global context and only necessary neighbors for the next cycle. The example selects intro to demonstrate a full paragraph; normal work may proceed in the master's source order with `view --next`. Reuse the session and keep one mutable paired master. The helper records the caller's review; its output and timestamps cannot demonstrate semantic judgment.

For direct Python use, load the persisted master, call `unit_view` for one active ID, author/review its target, then `record_review` and `save_document`. A compact update should concern the current unit. Deterministic whole-document checks can run after a useful group of completed updates.

## One short row, one atomic save

IDs remain per cell; a short row can be one working block. Read the row with its headers before authoring its targets. In this example, `Crop / Packets` gives the context for the row `Bean / 3`. Review the two target cells together: `Haricot / 3` preserves both the crop and its count. That single review does not require a separate remote operation for the literal number.

Load the current master once. After reviewing this row, apply its two explicit source-hash attestations in memory and save once:

```python
master = json.loads(master_path.read_text(encoding="utf-8"))
reviewed_row = [
    ("bean-name", "Haricot",
     "1d086001c6e5975be0172586a6cfe53a03781ff43a15881ebd5e68a863402e27"),
    ("bean-count", "3",
     "4e07408562bedb8b60ce05c1decfe3ad16b72230967de01f640b7e4729b49fce"),
]
pending = master
for unit_id, target, reviewed_hash in reviewed_row:
    pending = record_review(pending, unit_id, target,
                            reviewed_source_hash=reviewed_hash)
save_document(master_path, pending)
```

If either source changed, its hash check raises before the save, leaving the file untouched. Read back only these two IDs and target slots, then advance to the next block. A short header row or coherent short list uses the same pattern, with a separate ID/target for each field. This recipe batches persistence of an already-reviewed semantic block; each prose paragraph still gets its own translate-review-save cycle. Use the existing module-loading method for the discovered skill; no new helper or fragment file is needed.

## Native TeX equivalent

Create the editable source-first manuscript with stable pair IDs and explicit empty target arguments; execute that save and inspect the file before writing translated prose:

```tex
% Source snapshot retained separately; intro target is pending.
\ParallelParagraph{intro}
  {The community shelf holds 12 packets. Each packet has one label, and the register records its contents.}
  {}
```

Then read this complete source paragraph in context, author and proofread its French counterpart, and update only intro's second argument in the same manuscript. Save and confirm that scoped edit before working on the next pair. Keep source IDs and source arguments unchanged. For a short native table row or coherent list, inspect all its source fields with their headers/context, review the separate target fields together and save that scoped row/list once. A brief native comment/progress record can record completed review; the optional JSON helpers are not required. Fill all requested target slots before rendering the deliverable.

For source changes, preserve the previous target and mark that pair for review. JSON users can run `sync master.json --in-place`; readiness fails until the changed pair is read and reviewed. Use an extra checkpoint only when it serves a real revision need. When rendering this demonstration outside the installed example directory, stage its one shared figure beside the working master or pass the renderer's supported asset-root option.
