#!/usr/bin/env python3
# Astrid plan leg — deterministic drift facts in, decode-pinned report out.
# Runs on the box; talks to the on-box stem (llama.cpp, loopback 8811). stdlib only.
#
# The trust law lives at DECODE TIME: the model cannot emit any
# applies_without_gate other than the string "false", and cannot set
# needs_human to anything but true. The chat route declares this as a JSON
# schema whose consts/enum llama.cpp converts to a GBNF grammar internally,
# before the first token is drawn. assets/grammar.gbnf documents the same
# law for the raw /completion route; the chat route is what actually runs,
# because some stem models wedge in whitespace loops under raw
# completion + grammar (observed on LFM3).
import json, os, sys, urllib.request

STEM = "http://127.0.0.1:8811/v1/chat/completions"

SCHEMA = {
    "type": "object",
    "properties": {
        "kind": {"const": "drift_report"},
        "severity": {"enum": ["low", "medium", "high"]},
        "invariant_broken": {"type": "boolean"},
        "confidence": {"type": "number"},
        "summary": {"type": "string"},
        "proposal": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "steps": {"type": "array", "items": {"type": "string"}},
                "reversible": {"type": "boolean"},
            },
            "required": ["title", "steps", "reversible"],
            "additionalProperties": False,
        },
        "applies_without_gate": {"const": "false"},
        "needs_human": {"const": True},
    },
    "required": ["kind", "severity", "invariant_broken", "confidence",
                 "summary", "proposal", "applies_without_gate", "needs_human"],
    "additionalProperties": False,
}


def extract_json_object(s: str) -> str:
    """Cut the first complete JSON object out of model output, string-aware.

    Models may echo prompt prefixes or trail chat-template tokens after the
    pinned object; a suffix parse breaks on those, depth-scan never does.
    """
    start = s.find("{")
    if start < 0:
        raise SystemExit(f"PLAN-FAILED no JSON in stem output: {s[:200]!r}")
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return s[start:i + 1]
    raise SystemExit("PLAN-FAILED unbalanced JSON in stem output")


def plan(drift_facts_path: str) -> dict:
    drift = json.load(open(drift_facts_path))
    facts_compact = json.dumps(
        {k: drift[k] for k in ("severity", "summary", "facts", "hints", "charter_revision")},
        separators=(",", ":"))
    hint_txt = ""
    if drift.get("hints"):
        hint_txt = (" The deterministic tool suggests: " + "; ".join(
            h["suggest"] + " (candidates: " + ", ".join(h["candidates"]) + ")"
            for h in drift["hints"]))
    messages = [
        {"role": "system", "content": (
            "You are the planning tier of machine astrid, a requirements-file server. "
            "Emit exactly one drift_report JSON object matching the response schema. "
            "Rules: summary restates the concrete numbers from the facts; steps are "
            "concrete and reversible; no placeholder text.")},
        {"role": "user", "content": (
            facts_compact + (" Finalize that proposal: use the suggested candidates "
            "as steps, written as concrete actions on the named files." if hint_txt
            else " If action is needed, draft a minimal reversible proposal naming "
            "real objects from the facts."))},
    ]
    body = json.dumps({
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 600,
        "response_format": {"type": "json_schema",
                            "json_schema": {"name": "drift_report", "schema": SCHEMA}},
    }).encode()
    req = urllib.request.Request(STEM, data=body,
                                 headers={"Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=180).read())
    content = r["choices"][0]["message"].get("content", "") or ""
    report = json.loads(extract_json_object(content))
    # identity + provenance from the machine, never from the model
    report["kind"] = "drift_report"
    report["applies_without_gate"] = "false"
    report["producer"] = "stem (decode-pinned) from reconcile facts"
    report["facts"] = drift.get("facts", {})
    report["hints"] = drift.get("hints", [])
    report["charter_revision"] = drift.get("charter_revision")
    return report


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "/tmp/drift.json"
    dest = sys.argv[2] if len(sys.argv) > 2 else "/tmp/plan.json"
    rep = plan(src)
    out = json.dumps(rep, indent=2)
    print(out)
    with open(dest, "w") as f:
        f.write(out + "\n")
