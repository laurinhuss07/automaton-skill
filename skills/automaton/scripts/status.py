#!/usr/bin/env python3
"""Redacted automaton status: config (secrets removed), runtime status, process.

Usage: status.py [--runtime-dir DIR]

Never prints wallet.json, api-key, or API key values from automaton.json.
"""

import json
import os
import re
import subprocess
import sys

HOME = os.path.expanduser("~/.automaton")
CONFIG = os.path.join(HOME, "automaton.json")
SECRET_KEY = re.compile(r"(key|secret|token|private|password)", re.IGNORECASE)


def redact(value):
    if isinstance(value, dict):
        return {
            k: ("<redacted>" if SECRET_KEY.search(k) and v else redact(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def runtime_dir():
    if "--runtime-dir" in sys.argv:
        return os.path.expanduser(sys.argv[sys.argv.index("--runtime-dir") + 1])
    for candidate in (os.environ.get("AUTOMATON_DIR"), "~/automaton",
                      "/opt/automaton", "~/.automaton/runtime"):
        if candidate:
            path = os.path.expanduser(candidate)
            if os.path.exists(os.path.join(path, "dist", "index.js")):
                return path
    return None


def main():
    print("## Config (redacted)")
    if os.path.exists(CONFIG):
        with open(CONFIG, encoding="utf-8") as fh:
            cfg = json.load(fh)
        if cfg.pop("genesisPrompt", None):
            print("(genesisPrompt omitted; see automaton.json)")
        print(json.dumps(redact(cfg), indent=2))
    else:
        print(f"No config at {CONFIG}. Run setup first.")

    print("\n## Process")
    proc = subprocess.run(["pgrep", "-af", "dist/index.js"],
                          capture_output=True, text=True, check=False)
    lines = [l for l in proc.stdout.splitlines() if "--run" in l or "index.js" in l]
    print("\n".join(lines) if lines else "Not running (no dist/index.js process found).")

    print("\n## Runtime status")
    rdir = runtime_dir()
    if not rdir:
        print("Runtime not found. Pass --runtime-dir or set AUTOMATON_DIR.")
        return
    out = subprocess.run(["node", os.path.join(rdir, "dist", "index.js"), "--status"],
                         capture_output=True, text=True, check=False, cwd=rdir)
    text = (out.stdout or "") + (out.stderr or "")
    print(re.sub(r"(cnwy_k_|sk-ant-|sk-)[A-Za-z0-9_\-]+", r"\1<redacted>", text).strip())


if __name__ == "__main__":
    main()
