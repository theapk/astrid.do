# example run — captured artifacts

Real output from a live astrid box (the demo machine), captured 2026-11-19,
redacted of nothing but real hostnames — there were none to remove: every
address below is loopback on purpose.

- **`drift.json`** — what the deterministic reconcile tool wrote when all 10
  invariants held. Note `producer: reconcile-tool (deterministic)`,
  `applies_without_gate: "false"`, and that "silent on clean" still means
  this file gets rewritten every hour with fresh facts.
- **`plan.json`** — the same facts handed to the on-box stem, whose output
  was *forced through the GBNF grammar* (`assets/grammar.gbnf`). The model
  can word the summary and steps; it cannot emit another schema, and it
  cannot emit `applies_without_gate: true` — the grammar simply has no such
  token sequence available.
- **`gate-verdict.json`** — the deterministic gate reading that plan back
  against the charter. Verdict: `admissible: false`,
  `apply_word_required: true` — even a fully-reversible, zero-fabrication
  plan gets no auto-apply path. `fabricated_targets_refused: 0` because the
  stem named only real objects from the facts; in the recorded run #2 the
  stem invented a backup file that did not exist as a reconcile fact and the
  gate refused it (`fabricated_targets_refused: 1`).
