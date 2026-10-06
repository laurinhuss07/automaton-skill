#!/bin/sh
# Check prerequisites for running a Conway Automaton. Changes nothing.
ok=1

if command -v node >/dev/null 2>&1; then
  major=$(node -e "process.stdout.write(process.versions.node.split('.')[0])")
  if [ "$major" -ge 20 ]; then
    echo "[ok]   node $(node -v)"
  else
    echo "[fail] node $(node -v) found, need >= 20"; ok=0
  fi
else
  echo "[fail] node not found (need >= 20)"; ok=0
fi

if command -v git >/dev/null 2>&1; then echo "[ok]   git"; else echo "[fail] git not found"; ok=0; fi

if command -v pnpm >/dev/null 2>&1; then
  echo "[ok]   pnpm $(pnpm -v)"
else
  echo "[warn] pnpm not found; enable with: corepack enable pnpm"
fi

if command -v python3 >/dev/null 2>&1; then echo "[ok]   python3 (for status/audit helpers)"; else echo "[warn] python3 not found; status/audit helpers unavailable"; fi

if [ -d "$HOME/.automaton" ]; then
  echo "[info] existing automaton state at $HOME/.automaton"
fi

# Heuristic: ephemeral CI/cloud containers are unsuitable for a long-running agent.
if [ -n "$CI" ] || [ -n "$CODESPACES" ] || [ -n "$CLAUDE_CODE_REMOTE" ]; then
  echo "[warn] this looks like an ephemeral environment; run the automaton on a machine that stays on"
fi

[ "$ok" = 1 ] && exit 0 || exit 2
