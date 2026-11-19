#!/usr/bin/env python3
# Astrid on-box reconcile — charter JSON in, drift_report out. stdlib only.
import json, os, socket, subprocess, sys, glob, gzip, time
from urllib.request import Request, urlopen

def sh(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=20)

def check_listeners(port, label, fails, facts):
    # bind truth from ss: the line must exist and be loopback-bound
    out = sh("ss", "-tln").stdout
    line = ""
    for ln in out.splitlines():
        f = ln.split()
        if len(f) >= 4 and f[3].endswith(str(port)) and ":" + str(port) in f[3]:
            line = ln
            break
    if not line:
        fails.append(f"{label}: not listening on {port}")
        facts[label] = "absent"
        return
    addr = line.split()[3]
    ok = addr.startswith("127.0.0.1") or addr.startswith("[::1]")
    facts[label] = addr
    if not ok:
        fails.append(f"{label}: binds {addr}, invariant requires loopback only")

CHECKS = []  # (name, fn) — every charter invariant maps to exactly one check

def run(charter_path):
    with open(charter_path) as f:
        charter = json.load(f)
    fails, facts = [], {}

    # 1-2, 9: loopback binds (7731, 7741, 8811)
    check_listeners(7731, "daemon 7731 binds loopback only", fails, facts)
    check_listeners(7741, "face 7741 binds loopback only", fails, facts)
    check_listeners(8811, "stem 8811 binds loopback only", fails, facts)

    # 3: no container runtime
    bins = [b for b in ("docker", "podman", "containerd", "nerdctl") for found in (sh("sh", "-c", f"command -v {b}"),) if found.returncode == 0 and found.stdout.strip()]
    if bins:
        fails.append(f"container runtime present: {bins}")
    facts["containers"] = "absent" if not bins else "PRESENT"

    # 4: sole user is bot (human range: uid 1000–60000; nobody=65534 is a system uid)
    users = [l.split(":")[0] for l in open("/etc/passwd") if 1000 <= int(l.split(":")[2]) <= 60000]
    if users != ["bot"]:
        fails.append(f"users in human range: {users}")
    facts["users"] = users

    # 5: health 200
    code = 0
    try:
        code = urlopen(Request("http://127.0.0.1:7731/health"), timeout=5).status
    except Exception as e:
        fails.append(f"health check failed: {e}")
    if code != 200:
        fails.append(f"health returned {code}, invariant requires 200")
    facts["health"] = code

    # 6-7: ufw posture (tool runs under sudo for root state reads)
    ufw = sh("ufw", "status", "verbose")
    ut = ufw.stdout
    if ufw.returncode != 0 and not ut:
        fails.append(f"ufw status unreadable (rc={ufw.returncode}, run under sudo)")
    elif "deny (incoming)" not in ut:
        fails.append("ufw default incoming is not deny")
    has_lan_22 = any((_os.environ.get("ASTRID_MGMT_CIDR", "192.0.2.0/24") in ln and "22" in ln) for ln in ut.splitlines())
    has_ts = any("tailscale0" in ln for ln in ut.splitlines())
    if not (has_lan_22 and has_ts):
        fails.append(f"ufw ssh gate rules missing (lan_22={has_lan_22}, ts={has_ts})")
    facts["ufw"] = {"deny_incoming": "deny (incoming)" in ut, "lan_22": has_lan_22, "tailscale": has_ts}

    # 8: backups verify + keep-7
    archs = sorted(glob.glob("/var/backups/astrid/*-*.tar.gz"))
    if len(archs) > 7:
        fails.append(f"backups exceed keep-7: {len(archs)}")
    verify_ok = None
    if archs:
        r = sh("gzip", "-t", archs[-1])
        verify_ok = (r.returncode == 0)
        if not verify_ok:
            fails.append(f"gzip -t failed on {archs[-1]}")
    else:
        fails.append("no backup archives present")
    facts["backups"] = {"count": len(archs), "newest_verify": verify_ok}

    # 10: off-box ship freshness (charter law: warehouse copy ≤48h old)
    sp = "/var/lib/astrid/ship-state.json"
    ship_fresh, ship_age = False, None
    if os.path.exists(sp):
        st = json.load(open(sp))
        ship_age = int(time.time()) - int(st.get("last_success", 0))
        ship_fresh = ship_age <= 48 * 3600
    if not ship_fresh:
        fails.append(f"off-box shipment stale/missing ({ship_age}s since last_success)")
    facts["ship"] = {"age_s": ship_age, "fresh": ship_fresh}

    broken = (len(fails) > 0)
    sev = "high" if broken else "low"
    summary = "; ".join(fails) if broken else "all 10 invariants hold; machine matches charter rev %d" % charter["revision"]
    # hints: deterministic suggestions for known drift classes (the stem finalizes steps)
    hints = []
    if len(archs) > 7:
        excess = len(archs) - 7
        oldest = archs[:excess]
        hints.append({"class": "backups-over-keep-7",
                      "suggest": "delete the %d oldest archive(s) to restore keep-7" % excess,
                      "candidates": oldest})
    report = {
        "kind": "drift_report",
        "severity": sev,
        "invariant_broken": broken,
        "confidence": 1.0 if not broken else round(1.0 - 0.05 * len(fails), 2),
        "summary": summary[:320],
        "proposal": None,
        "applies_without_gate": "false",
        "needs_human": True if broken else False,
        "producer": "reconcile-tool (deterministic)",
        "charter_revision": charter["revision"],
        "hints": hints,
        "facts": facts,
    }
    return report

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "charter/example.json"
    rep = run(path)
    print(json.dumps(rep, indent=2))
    sys.exit(0 if not rep["invariant_broken"] else 1)
