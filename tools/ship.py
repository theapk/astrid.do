#!/usr/bin/env python3
# Astrid warehouse ship — push /var/backups/astrid archives to the warehouse host
# over a forced-command ssh key (stdin pipes only; no shell on the other end).
# Writes ship-state.json as the machine-checkable freshness proof.
import hashlib, json, os, subprocess, glob, time

KEY = "/etc/astrid/warehouse_key"
import os as _os
USER = _os.environ.get("ASTRID_SHIP_USER", "operator")
HOST = _os.environ.get("ASTRID_WAREHOUSE_HOST", "warehouse.example.invalid")
STATE = "/var/lib/astrid/ship-state.json"

def ship() -> dict:
    archs = sorted(glob.glob("/var/backups/astrid/*-*.tar.gz"))
    state = {"last_success": 0, "files": {}}
    if os.path.exists(STATE):
        state = json.load(open(STATE))
    now = int(time.time())
    results = []
    for a in archs:
        name = os.path.basename(a)
        prev = state["files"].get(name, {})
        data = open(a, "rb").read()
        sha = hashlib.sha256(data).hexdigest()
        if prev.get("sha") == sha and now - prev.get("shipped_at", 0) < 7 * 86400:
            results.append({"name": name, "sha": sha, "status": "already", "age_s": now - prev["shipped_at"]})
            state["files"][name] = {**prev, "seen_now": True}
            continue
        r = subprocess.run(
            ["ssh", "-i", KEY, "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
             "-o", "StrictHostKeyChecking=accept-new", "-T", USER + "@" + HOST,
             "astrid-ship " + name + " " + sha],
            input=data, capture_output=True, timeout=120)
        out = (r.stdout.decode() or "").strip().splitlines()
        verdict = out[-1] if out else (r.stderr.decode().strip())[:80]
        ok = verdict.startswith("OK ")
        if ok:
            state["files"][name] = {"sha": sha, "shipped_at": now}
            state["last_success"] = now
        results.append({"name": name, "sha": sha, "status": "ok" if ok else "FAILED",
                        "reply": verdict[:80]})
    state["last_run"] = now
    json.dump(state, open(STATE, "w"), indent=2)
    summary = {"shipped": sum(1 for r in results if r["status"] in ("ok", "already")),
               "failed": sum(1 for r in results if r["status"] == "FAILED"),
               "results": results, "state_epoch": now}
    return summary

if __name__ == "__main__":
    s = ship()
    print(json.dumps(s, indent=2))
    raise SystemExit(0 if s["failed"] == 0 and s["shipped"] > 0 else 1)
