#!/usr/bin/env python3
# Astrid plan leg — deterministic drift facts in, grammar-governed report out.
# Runs on the box; talks to the on-box stem (loopback 8811) with the GBNF that
# pins applies_without_gate=false. stdlib only.
import json, sys, urllib.request

STEM = "http://127.0.0.1:8811/completion"
GRAMMAR = os.environ.get("ASTRID_GRAMMAR", "assets/grammar.gbnf")

def plan(drift_facts_path: str) -> dict:
    drift = json.load(open(drift_facts_path))
    grammar = open(GRAMMAR).read()
    facts_compact = json.dumps(
        {k: drift[k] for k in ("severity", "summary", "facts", "hints", "charter_revision")},
        separators=(",", ":"))
    hint_txt = ""
    if drift.get("hints"):
        hint_txt = (" The deterministic tool suggests: " + "; ".join(
            h["suggest"] + " (candidates: " + ", ".join(h["candidates"]) + ")"
            for h in drift["hints"]) + ".")
    prompt = (
        "You are the planning tier of machine astrid, a requirements-file server.\n"
        "A deterministic reconcile tool produced these facts:\n" + facts_compact + "\n"
        + (" Finalize that proposal: use the suggested candidates as steps, written"
           " as concrete actions on the named files." if hint_txt else " If action is needed, draft a minimal reversible proposal naming real objects from the facts.") + "\n"
        "Rules: summary restates the concrete numbers from the facts; steps are "
        "concrete and reversible; no placeholder text. needs_human true; the gate "
        "requires the operator word for any apply. kind=drift_report, "
        "applies_without_gate=false.\n"
        "drift_report: "
    )
    body = json.dumps({
        "prompt": prompt,
        "grammar": grammar,
        "temperature": 0.0,
        "n_predict": 600,
        "cache_prompt": True,
    }).encode()
    req = urllib.request.Request(STEM, data=body,
                                 headers={"Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=180).read())
    content = r.get("content", "")
    start = content.find("{")
    if start < 0:
        raise SystemExit(f"PLAN-FAILED no JSON in stem output: {content[:200]!r}")
    report = json.loads(content[start:])
    # identity + provenance from the machine, never from the model
    report["kind"] = "drift_report"
    report["applies_without_gate"] = "false"
    report["producer"] = "stem (grammar-governed) from reconcile facts"
    report["facts"] = drift.get("facts", {})
    report["hints"] = drift.get("hints", [])
    report["charter_revision"] = drift.get("charter_revision")
    return report

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "/tmp/drift.json"
    rep = plan(src)
    out = json.dumps(rep, indent=2)
    print(out)
    dest = sys.argv[2] if len(sys.argv) > 2 else "/tmp/plan.json"
    with open(dest, "w") as f:
        f.write(out + "\n")
