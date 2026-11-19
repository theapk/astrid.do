# models — what runs on the stem, and how it's pinned

The demo box runs one model, tiny on purpose. Astrid is the file-server +
the gate; the model is a drafting tier. Smaller is *safer here*: less RAM
competition with the browser face, cheaper to verify, and everything it
produces is grammar-governed and gate-checked anyway.

| piece | what | why this one |
|---|---|---|
| stem model | **Qwen3-1.7B-Instruct GGUF, Q4_K_M** (~1.1 GB) | fits beside the whisper face in ~4 GB total box RAM; ~8–9 tok/s on 4 cores; the 4B sibling was tried and retired — it starved the face |
| inference | **llama.cpp** (`llama-server`, CPU, 4 threads) | one static binary; `--grammar-file` grammar support is the whole mechanism |
| face ASR | **whisper tiny, q8_0 ggml** (~45 MB) | runs in-browser via transformers.js over loopback — audio never leaves the box |

## supply-chain law: bytes on disk, pinned by hash

1. Download the GGUF **on a management box, not the astrid box**.
2. Record `sha256` into the models dir *before* first use:

```
sha256sum Qwen3-1.7B-Q4_K_M.gguf | awk '{print $1}' > /var/lib/astrid-models/model-1.7b.sha256
sha256sum -c /var/lib/astrid-models/model-1.7b.sha256   # after every download/swap
```

3. Serve — the command the demo box runs (weights dir root-owned, 0600 shas):

```
/opt/llama/bin/llama-server \
  -m /var/lib/astrid-models/Qwen3-1.7B-Q4_K_M.gguf \
  --host 127.0.0.1 --port 8811 -c 1024 -t 4
```

4. Keep weights **out of the backed-up home tree** — a 1.1 GB GGUF in
   `$HOME` turns a nightly home backup into a nightly model transfer.

## decode-time pin (the part that matters)

The stem is never trusted on its own. `tools/plan.py` passes
`assets/grammar.gbnf` as the completion grammar every call: the model's
output is a fixed-shape JSON with `applies_without_gate` restricted to the
literal `"false"` — not by prompt discipline, by **construction of the
language the decoder is allowed to emit**. Whatever the 1.7B hallucinates,
it cannot express self-exemption.
