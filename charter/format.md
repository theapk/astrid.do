# Charter format — rules (artifact 2, page 1)

One charter file declares the whole box. The machine reconciles to it forever.
The brain holds zero root. This page is the law for every `charter/*.yaml`.

## What a charter is

```
charter file (*.yaml)                machine
─────────────────────                ───────
identity + substrate      reconcile   ← live state (ss, ufw, units, files)
disks + network + services  ══════►   drift = any line that stops being true
brain (stem/face/architect)  gate     drift_report JSON (grammar-governed)
autonomy (L0–L3) + invariants         plan → review gate → apply → re-freeze
goals (prose, review-gated)
```

- **YAML is the interface; JSON is the compile.** The strict YAML subset below
  compiles to `*.json` (schema: `charter/schema.json`). The on-box reconcile
  reads the compiled JSON only — no YAML parser on the machine, stdlib only
  (compile-today law, satisfied with `python3` + nothing else).
- **A git diff of the charter IS the review surface.** One commit = one
  generation; the generation pointer is the rollback.

## The subset (the whole grammar)

| allowed | shape | example |
|---|---|---|
| comments | `#` lines | every version bump |
| scalars | strings / ints / bools | `tailscale: 203.0.113.10` |
| flat map | one level `{k: v}` | `policy: { incoming: deny }` |
| sequence | list of maps or strings | `invariants:` |
| block scalar | `>-` folded text | evidence notes |
| nested map | exactly **two** levels deep, no more | `services:` |

**Cut on sight:** anchors, tags, flow collections beyond one level, multi-doc,
three-plus nesting depth, regex/glob anywhere, secrets anywhere (keys live at
the operator; the box stores the minimum — see `secrets.principle`).

## Field classes

| class | keys | rule |
|---|---|---|
| **state** (what is) | identity, substrate, disks, network, services, packages_extra, backups, brain | every line must be true *today* or the file is invalid |
| **invariants** (what must stay) | list, machine-checkable | failure = the machine's first job; never auto-edited |
| **autonomy** | L0 watch · L1 propose · L2 apply-with-review · L3 self-apply | granted per domain; the gate reads this |
| **goals** (what next) | prose, id'd | never auto-applied; apply on the operator's explicit go, then re-freeze |

## Laws

1. **Compile-today.** A field may express only what an existing mechanism on the
   box consumes: systemd units, netplan yaml, ufw rules, files with owner/mode,
   llama-server flags. No primitive, no feature — a field that compiles to a
   plan for a mechanism that does not exist is cut.
2. **Typed invariants.** Invariants are checkable strings with a check id in
   the reconcile tool; prose invariants don't compile and don't ship.
3. **Secrets are pointers, not payloads.** On-box key material appears as
   path + mode + owner; values live outside the file.
4. **Evidence lives in `notes/`, never merged into the charter.** The charter
   carries measured one-liners (numbers, shas); the notes carry procedure.
5. **Version bump = header line + `revision:` + live evidence for every
   changed line.** No silent edits.
