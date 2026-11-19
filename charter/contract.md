# Reconciliation contract (artifact 2, page 2)

The machine reconciles to its charter forever. This page is the loop and its gate.

```
 charter/*.yaml          compiled *.json           the box
 ─────────────           ───────────────           ───────
   edit + diff     ──►   schema-check     ──►    reconcile()           (loop, on-box)
        diff = review surface                invariants checked live
        gate                                 drift  = state != charter
        ║                                    report = drift_report JSON
        ║                                              │
        ▼                                              ▼
   operator word ◄──────── signed plan ◄────── grammar-governed stem output
   (apply only on                              (applies_without_gate: false —
    explicit go,                                pinned inside the GBNF; no decode
    L-level checked)                            path can emit a self-exempting plan)
        │
        ▼
   apply → re-freeze → new revision + commit (rollback = generation pointer)
```

## The loop

| stage | who | contract |
|---|---|---|
| compile | operator side | YAML subset → JSON; schema-validated or the generation is invalid |
| reconcile | the box, any time | read charter JSON; run every invariant; diff state; emit `drift_report` |
| plan | the stem only | grammar-governed JSON (see below); no other path may write a plan |
| gate | fixed | apply requires: L-level permits + needs_human honored + operator word |
| apply | operator side | the plan's steps run verbatim; nothing else |
| re-freeze | operator side | applied changes land as a charter revision with evidence |

## The plan shape (the stem's only output vocabulary)

```json
{ "kind": "drift_report",
  "severity": "low | medium | high",
  "invariant_broken": true | false,
  "confidence": 0.0-1.0,
  "summary": "≤ 320 chars, states the drift in facts",
  "proposal": null | { "title": "...", "steps": ["..."],
                       "reversible": true | false },
  "applies_without_gate": "false",
  "needs_human": true | false }
```

- `applies_without_gate` is the literal string `"false"` — written **inside the
  grammar** (`grammar.gbnf`), not as a model habit. A decode path that cannot
  emit `true` cannot ask for self-exemption.
- `needs_human` is the box's voice, the gate's hint — **the gate never reads a
  model field as permission.** Permission is autonomy L-levels + the operator's
  word; the plan just carries what the reader needs.
- `reversible: false` plans require the operator word twice (once to see it,
  once to run it).

## Rollback

The generation pointer (git HEAD of the charter). `checkout` the earlier
generation → re-apply its compiled files by the same apply step. Nothing in the
format invents a second rollback mechanism; git is the mechanism.

## Drift classes

| class | example | first move |
|---|---|---|
| invariant broken | a loopback bind became 0.0.0.0 | report immediately, severity high, reversible=false steps only after go |
| state skew | backup timer disabled | report + plan (L1) |
| state ahead | operator fix landed with no revision | re-freeze (operator side) |
| stale goal | G4 done by hand | goal status update, next revision |
