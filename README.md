# astrid — a requirements-file server

Machines like this are **AS — an Astrid Server, not an OS**. One charter file
declares the whole box; the machine reconciles to it forever; the brain holds
zero root.

A charter is an honest text file: every line is a true statement about the
machine *today* — network, services, firewall, backups, even the small models
that live on disk with their sha256s pinned into the file. It compiles to
schema-validated JSON; anything that can't map onto a real mechanism that
exists today gets cut (the compile-today law). A stdlib-only reconciler checks
every invariant against the live machine on a timer. When drift is caught, an
on-box model drafts a repair plan — pinned at decode time so it can never
exempt itself from the review gate, and checked by a deterministic gate that
only admits steps whose targets the reconciler actually observed.

## Artifacts

| artifact | file | what it is |
|---|---|---|
| worked example charter | `charter/example.yaml` | a generic machine, TEST-NET values — mirror it against real facts |
| schema | `charter/schema.json` | Draft 7; the compiler enforces it |
| format rules | `charter/format.md` | the whole YAML subset, one page |
| reconciliation contract | `charter/contract.md` | the loop: compile → reconcile → plan → gate → apply → re-freeze |
| compiler | `tools/charter_compile.py` | YAML → schema-validated JSON (operator side) |
| reconcile | `tools/reconcile.py` | stdlib-only invariant checks on the box |
| plan | `tools/plan.py` | drafts drift-repair plans via a loopback llama-server, GBNF-pinned |
| gate | `tools/gate.py` | autonomy L-levels + fabrication cross-check; never asks the model |
| ship | `tools/ship.py` | nightly off-box copy, sha-verified on the receive side |
| cadence | `tools/cadence.sh` | timer glue: hourly reconcile, daily ship, transition-only alerts |

## Why the gate exists

On run #2 of the reference box, the small model confidently proposed deleting a
backup file that did not exist — a plausible-looking filename pattern-matched
into reality. The gate is the layer between the model and the filesystem: a
delete target must exist AND appear in the reconciler's own candidate list.
The model can word the plan; it cannot decide what is true.

## Getting started

1. Write a charter of a machine you control, mirroring `charter/example.yaml`
   (every line true *today*, placeholders replaced, secrets as file pointers
   only).
2. Compile: `python3 tools/charter_compile.py` → schema-validated JSON.
3. Put the compiled charter and `tools/reconcile.py` on the box; run the
   reconciler (hourly timer works well) and wire its output to your own alert
   lane.
4. If you want the plan leg: serve a small model on loopback, feed the
   reconciler's hints through `tools/plan.py`, and keep the gate between the
   model and anything it touches.

## Repo map

```
charter/   example.yaml (worked example) · schema.json · format.md · contract.md
tools/     charter_compile · reconcile · plan · gate · ship · cadence
```

## Laws worth restating

- **Compile-today** — no field may express a mechanism that doesn't exist on the box.
- **Secrets are pointers, not payloads** — on-box key material appears as
  path + mode + owner; values live outside the file.
- **A git diff of the charter IS the review surface** — one commit = one
  generation; the pointer is the rollback.
- **Autonomy is granted per domain** (L0 watch → L3 self-apply), and L3 is
  never granted in the worked example.

License: MIT.
