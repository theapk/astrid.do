# models — what runs on the stem, and how it's pinned

One model family, tiny on purpose. Astrid is the file-server + the gate;
the model is a drafting tier. Smaller is *safer here*: less RAM competition
with the browser face, cheaper to verify, and everything it produces is
decode-pinned and gate-checked anyway. **No outside LLM runs anywhere in
the loop** — conversation, tool-calling, and planning all ride the same
on-box stem.

| piece | what | why this one |
|---|---|---|
| stem model | **LFM3-Omni-2B GGUF, Q4_K_M** (~1.0 GB) + mmproj (~0.5 GB) | fastest CPU decode of the candidates measured (9.99 tok/s vs Qwen3-1.7B's 7.24 at 4 threads); audio-in/text-out makes it the one-model upgrade path for the face's ASR later; coexists with the whisper face in ~4 GB total box RAM |
| text alternates (on disk) | LFM2-1.2B Q8_0 (9.01 tok/s), Qwen3-1.7B Q4_K_M (7.24 tok/s) | kept as swap-candidates; the 4B sibling was tried and retired — it starves the face (OOM-pair proven) |
| inference | **llama.cpp** (`llama-server`, CPU, 4 threads, `--jinja`, FA, KV q8_0, ctx 4096) | one binary; OpenAI-compatible `/v1/chat/completions` with tool calling; `response_format` schemas are its decode-time pin |
| face ASR | **whisper tiny, q8_0 ggml** (~45 MB) | runs in-browser via transformers.js over loopback — audio never leaves the box; ~1.5× faster than the stem's audio path on 2 cores today |
| TTS | kokoro via an on-box loopback relay to the voice host | the assistant's spoken replies; no cloud TTS |

## supply-chain law: bytes on disk, pinned by hash

1. Download the GGUF **on a management box, not the astrid box**.
2. Record `sha256` into the models dir *before* first use:

```
sha256sum LFM3-Omni-2B-Q4_K_M.gguf > /var/lib/astrid-models/LFM3-Omni-2B-Q4_K_M.gguf.sha256
sha256sum -c /var/lib/astrid-models/*.sha256   # after every download/swap
```

3. Serve — the command the demo box runs (weights dir root-owned):

```
/opt/llama/bin/llama-server \
  -m /var/lib/astrid-models/LFM3-Omni-2B-Q4_K_M.gguf \
  --mmproj /var/lib/astrid-models/mmproj-LFM3-Omni-2B-Q8_0.gguf \
  --host 127.0.0.1 --port 8811 -c 4096 -t 4 --jinja --flash-attn on \
  -ctk q8_0 -ctv q8_0
```

4. Keep weights **out of the backed-up home tree** — a GB-scale GGUF in
   `$HOME` turns a nightly home backup into a nightly model transfer.
5. Stage transfers outside `/tmp` on boxes where it is a small tmpfs —
   big model copies there silently truncate and eat RAM.

## decode-time pin (the part that matters)

The stem is never trusted on its own. `tools/plan.py` posts a JSON schema
with the drift facts on every call; llama.cpp turns the schema into a
grammar **before the first token is drawn**, so the model's output is a
fixed-shape JSON with `applies_without_gate` restricted to the literal
`"false"` and `needs_human` to `true` — not by prompt discipline, by
**construction of the language the decoder is allowed to emit**. Whatever
the 2B hallucinates, it cannot express self-exemption.
`assets/grammar.gbnf` documents the same law for the raw completion route.
