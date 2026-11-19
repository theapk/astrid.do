#!/usr/bin/env python3
# Astrid gate — reads the plan + the charter. It never asks the model.
# Rule: permission = autonomy L-levels + the operator word; a plan carries
# hints (needs_human, reversible) but holds no authority. stdlib only.
import json, os, re, sys

def domain_for(step: str, domains: dict) -> str:
    s = step.lower()
    if re.search(r"\brm\b|file|directory|path\b|tar\b|archive", s):
        return "filesystem" if "filesystem" in domains else next(iter(domains))
    if re.search(r"ufw|firewall|route|dns|port|ip\b|netplan", s):
        return "network" if "network" in domains else next(iter(domains))
    if re.search(r"apt|pkg|package|install|update\b", s):
        return "packages" if "packages" in domains else next(iter(domains))
    if re.search(r"unit|systemctl|service|daemon|restart|stop\b", s):
        return "services" if "services" in domains else next(iter(domains))
    if re.search(r"key|secret|password|token", s):
        return "secrets" if "secrets" in domains else next(iter(domains))
    return next(iter(domains))

def gate(plan: dict, charter: dict) -> dict:
    doms = charter["autonomy"]["domains"]
    verdict = {"gate": "astrid/contract v1",
               "plan_producer": plan.get("producer"),
               "needs_human": plan.get("needs_human", True),
               "reversible": True,
               "steps": [],
               "apply_word_required": bool(plan.get("needs_human", True)),
               "admissible": True}
    # allowlist: every target the deterministic facts blessed; a step naming a
    # file outside it = a fabricated target → refused (model priors never bless deletes)
    candidates = set()
    for h in plan.get("hints", []):
        for c in h.get("candidates", []):
            candidates.add(c)
    prop = plan.get("proposal")
    if not prop:
        verdict["steps"].append({"step": "(no proposal — report only)", "domain": None,
                                  "L": None, "auto_allowed": True})
        verdict["summary"] = "report-only; nothing to apply"
        return verdict
    verdict["reversible"] = bool(prop.get("reversible", False))
    for step in prop.get("steps", []):
        dom = domain_for(step, doms)
        lvl = doms.get(dom, charter["autonomy"]["default"])
        auto = {"L1": False, "L2": False, "L3": True, "L0": False}[lvl]
        entry = {"step": step, "domain": dom, "L": lvl, "auto_allowed": auto}
        # deterministic cross-check: delete targets must be real, on-box, and in the facts
        if re.search(r"\brm\b|delete|remove", step.lower()):
            m = re.findall(r"(/[^\"'\s]+)", step)
            if not m:
                entry["fabricated"] = True
                entry["auto_allowed"] = False
            for path in m:
                if candidates and path not in candidates:
                    entry["fabricated"] = True
                    entry["refused_reason"] = f"target {path} not in reconcile candidate list (outside facts)"
                    entry["auto_allowed"] = False
                    break
                if not os.path.exists(path):
                    entry["fabricated"] = True
                    entry["refused_reason"] = f"target {path} does not exist on the box"
                    entry["auto_allowed"] = False
                    break
        verdict["steps"].append(entry)
        if not auto:
            verdict["admissible"] = False
    if not verdict["reversible"]:
        verdict["apply_word_required"] = True
        verdict["double_confirm"] = True
    fabric = [s for s in verdict["steps"] if s.get("fabricated")]
    verdict["fabricated_targets_refused"] = len(fabric)
    verdict["summary"] = (
        "no auto-apply path; operator word required"
        if verdict["apply_word_required"] else
        "all steps inside granted autonomy; still logged before apply")
    return verdict

if __name__ == "__main__":
    plan_p = sys.argv[1] if len(sys.argv) > 1 else "/tmp/plan.json"
    charter_p = sys.argv[2] if len(sys.argv) > 2 else "charter/example.json"
    print(json.dumps(gate(json.load(open(plan_p)), json.load(open(charter_p))), indent=2))
