# INTERFACES — astrid

Contracts and routes. The box binds loopback only for its brain; management
rides a private plane (tailnet or mgmt LAN); everything else stays off.

## Ports

| port | bind | protocol | contract |
|---|---|---|---|
| 7731 | 127.0.0.1 | HTTP | assistant daemon: `/health` → 200, `/input`, `/frame?u=`, `/latency.json` |
| 7741 | 127.0.0.1 | ws | daemon ⇄ face |
| 8811 | 127.0.0.1 | HTTP | llama-server (stem): OpenAI-compatible `/completion`, grammar via body |
| 8801 | 127.0.0.1 | HTTP | face asset server (loop page, whisper weights, grammar, clips) |
| 22 | mgmt LAN + tailnet | ssh | management |

## Contracts (one machine)

| flow | shape | enforcement |
|---|---|---|
| charter compile | charter (YAML subset) → compiled JSON | `charter/schema.json` Draft 7; failure = no generation |
| reconcile | stdlib checks on ss/ufw/units/manifests | `tools/reconcile.py`; invariants 1:1 charter |
| drift report | `drift_report` JSON (severity, invariant_broken, confidence, summary, proposal, applies_without_gate:"false", needs_human) | grammar-pinned on the model path; deterministic on the tool path |
| plan | stem `/completion` + GBNF | `applies_without_gate` is a literal; no decode path emits `true` |
| gate | L0–L3 from charter autonomy + target allowlist | fabricated targets refused; reversible:false = double confirm |
| warehouse ship | stdin pipe `ship.py <name> <sha256>` | forced-command key; sha verified on receive; manifest line = proof |
| alerts | bot sendMessage to the operator chat | transition-only: speak on drift, speak on recovery, silent on clean |

## Cross-host

| from | to | mechanism |
|---|---|---|
| box | warehouse host | forced-command ed25519 key (restrict+command), stdin-pipe receiver, keeps 29 files, `manifest.log` |
| box | alerts | on-box alert script, token 0600, sends only |
| operator | box | private-plane ssh; charter + tools under the operator user |

## Cadence

| unit | when | noise policy |
|---|---|---|
| backup timer | daily | log only |
| ship timer | daily | alert on failure + all-clear |
| reconcile timer | hourly | alert on drift transition + all-clear; plan+gate verdict to log |
