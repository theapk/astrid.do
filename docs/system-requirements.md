# system requirements — what it takes to stand up an AS

No GPU anywhere. Every number below is CPU-only, and the "demo box" row is
**measured**, not estimated — that tier is the hardware the reference box
actually runs on today (a Broadwell-era mini PC, 2 cores / 4 threads,
3.46 GB usable RAM).

| tier | CPU | RAM | disk | what runs |
|---|---|---|---|---|
| minimum — headless AS | 2c / 4t x86_64 | 2 GB | 8 GB | reconcile daemon + timers, plan→gate tools, the stem (LFM3-Omni-2B, smaller context), text-only |
| demo box — full loop | 2c / 4t | 4 GB (3.46 usable) | 16 GB | everything above + chromium face + in-browser whisper + full voice beats. **Proven: 9.99 tok/s decode, 10/10 invariants, warm brain first-token ≈ 3 s** |
| comfortable | 4+ cores | 8 GB | 32 GB | larger context, snappier tok/s, room to colocate the optional TTS leg |

## where the RAM actually goes (demo box, measured)

| piece | resident |
|---|---|
| stem (LFM3-Omni-2B Q4_K_M + mmproj, mmap) | ~1.6–1.9 GB |
| python daemon + tools | ~60 MB |
| chromium face (+ whisper tiny q8_0, 45 MB, in-browser) | ~0.7–1.0 GB |
| OS base (ubuntu server, systemd, ufw) | ~0.3 GB |

The floor is the stem. Below ~2 GB the model plus the OS start swapping and
every budget in this document becomes a lie — headless-with-2 GB is the
honest minimum, not 2 GB with a face.

## software

- Linux + systemd + journald (the units and cadence ship as systemd)
- python ≥ 3.9, stdlib only — no pip on the box
- `llama-server` from llama.cpp — one static binary
- ufw (a charter invariant: deny-in + a management-CIDR gate)
- chromium (any recent) — only for the face tier
- arch note: the shipped build is x86_64; llama.cpp itself builds on arm64
  if you want to compile your own

## network & provisioning

- **Runtime internet: none.** Everything binds loopback; the brain, the
  planning tier, and the gate all run on-box. This is the point.
- Provision-time: fetch OS packages, the binary, and the GGUFs once, from a
  management box — never let the AS pull weights at runtime. The sha-pin
  law lives in [`docs/models.md`](models.md).
- The stem decodes ~10 tok/s at 2c/4t; a 1-core box halves that and starts
  missing the interaction budgets — 2 cores is the honest floor, 1 is a
  toy.

## what won't run

- Anything below 2 GB RAM (swap-thrash; the stem becomes the disk).
- A GPU requirement — there isn't one. If you have one, faster; if you
  don't, exactly as shown above.
