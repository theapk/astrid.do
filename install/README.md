# quickstart — run astrid's contract on your box

No package manager, no Docker, no database: everything is Python ≥ 3.9
stdlib + ssh + systemd. Linux with systemd is the target; anything else you
adapt the timers yourself.

## 0 · what you already have

```
python3 --version        # ≥ 3.9, stdlib only — pip is never invoked
systemctl --user --no-pager --version
```

## 1 · serve the stem (the plan leg — optional until you want it)

The stem is llama.cpp's `llama-server` on loopback. Get the binary however
you like (`llama.cpp` release build), pick a GGUF (see
[`docs/models.md`](../docs/models.md) for the ones the demo box runs and
the sha-pinning procedure), then:

```
/path/to/llama-server -m /var/lib/astrid-models/Qwen3-1.7B-Q4_K_M.gguf \
    --host 127.0.0.1 --port 8811 -c 1024 -t 4
```

Loopback only, by charter. `tools/plan.py` posts the drift facts + the
GBNF grammar (`assets/grammar.gbnf`) to it; the decode-time pin is the
grammar itself.

## 2 · compile + reconcile once, by hand

```
git clone <this repo>
python3 tools/charter_compile.py charter/example.yaml charter/example.json
python3 tools/reconcile.py charter/example.json
```

`reconcile.py` audits *your* box against your compiled charter and writes
the drift report to stdout — redirect it wherever you keep state
(`... > /var/lib/astrid/drift.json`, creating the dir first).

## 3 · wire the hourly loop

```
sudo cp install/units/*.service install/units/*.timer /etc/systemd/system/
sudo cp install/astrid-cadence.sh /usr/local/bin/astrid-cadence.sh
sudo chmod +x /usr/local/bin/astrid-cadence.sh
sudo systemctl daemon-reload
sudo systemctl enable --now astrid-reconcile.timer astrid-ship.timer
```

The wrapper reads its wiring from env (defaults shown):

| var | meaning | default |
|---|---|---|
| `ASTRID_TOOLS` | repo's `tools/` dir | `$HOME/tools` |
| `ASTRID_CHARTER` | compiled charter path | `$HOME/charter/example.json` |
| `ASTRID_GRAMMAR` | GBNF for the plan leg | `assets/grammar.gbnf` |
| `ASTRID_ALERT_CHAT` / `ASTRID_ALERT_TOKEN` | drift alert destination (Telegram-style HTTP POST) | *must set the chat*; token file `/etc/astrid/tg-token` |
| `ASTRID_WAREHOUSE_HOST` | off-box backup target for the ship leg | `warehouse.example.invalid` |

Alert wiring is a plain `curl` to a chat API — swap in any webhook or drop
a no-op and you still get the drift report file.

## 4 · the apply word

Gate an admissible plan like the examples show:

```
python3 tools/plan.py /var/lib/astrid/drift.json /var/lib/astrid/plan.json
python3 tools/gate.py /var/lib/astrid/plan.json charter/example.json
```

Nothing in this repo mutates your machine on its own; `apply` runs only
when a human types the word, and irreversible changes want the word twice.
