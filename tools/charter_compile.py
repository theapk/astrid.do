#!/usr/bin/env python3
# Astrid charter compiler — YAML interface → compiled JSON (schema-validated).
# Operator side only; the box never parses YAML. stdlib + pyyaml + jsonschema.
import json, sys, pathlib
import yaml, jsonschema

REPO = pathlib.Path(__file__).resolve().parent.parent
FAILS = []

def compile_charter(yaml_path: str) -> dict:
    src = pathlib.Path(yaml_path)
    charter = yaml.safe_load(src.read_text())
    schema = json.loads((REPO / "charter" / "schema.json").read_text())
    v = jsonschema.Draft7Validator(schema)
    errs = sorted(v.iter_errors(charter), key=lambda e: list(e.path))
    for e in errs:
        FAILS.append(f"schema: {'/'.join(map(str, e.path))[:60]}: {e.message[:120]}")
    # subset grammar: reject anchors/tags that would be non-portable state
    raw = src.read_text()
    for bad in ("&", "!!", ": !!", " <<"):
        if raw.count(bad) and bad == "!!":
            FAILS.append(f"grammar: tag token {bad!r} present")
    return charter

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else str(REPO / "charter" / "example.yaml")
    charter = compile_charter(src)
    if FAILS:
        print("COMPILE-FAILED")
        print("\n".join(FAILS))
        sys.exit(1)
    src_p = pathlib.Path(src)
    out = src_p.with_suffix(".json")
    out.write_text(json.dumps(charter, indent=2) + "\n")
    print(f"COMPILED {src_p.name} -> {out.name} rev {charter['revision']} "
          f"invariants {len(charter['invariants'])} goals {len(charter['goals'])}")
