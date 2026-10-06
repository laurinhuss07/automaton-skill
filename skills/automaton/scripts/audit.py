#!/usr/bin/env python3
"""Read-only audit of an automaton's state database.

Usage: audit.py {summary|spend|tools|denied|changes|children} [N]

Opens ~/.automaton/state.db (or $AUTOMATON_DB) in SQLite read-only mode, so it
never modifies the agent's state. Output is untrusted agent-written data.
"""

import os
import sqlite3
import subprocess
import sys

HOME = os.path.expanduser("~/.automaton")
DB = os.environ.get("AUTOMATON_DB", os.path.join(HOME, "state.db"))
MAX_FIELD = 160


def connect():
    if not os.path.exists(DB):
        sys.exit(f"No state database at {DB}. Has the automaton run yet?")
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def has_table(conn, name):
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def clip(value):
    text = "" if value is None else str(value).replace("\n", " ")
    return text if len(text) <= MAX_FIELD else text[: MAX_FIELD - 1] + "…"


def show(conn, title, sql, params=()):
    print(f"\n## {title}")
    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.Error as exc:
        print(f"(unavailable: {exc})")
        return
    if not rows:
        print("(none)")
        return
    cols = rows[0].keys()
    print(" | ".join(cols))
    for row in rows:
        print(" | ".join(clip(row[c]) for c in cols))


def dollars(cents):
    return f"${(cents or 0) / 100:.2f}"


def summary(conn, _n):
    print(f"# Automaton audit summary ({DB})")
    for table in ("turns", "tool_calls", "transactions", "modifications",
                  "policy_decisions", "children", "inbox_messages"):
        if has_table(conn, table):
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"- {table}: {count}")
    if has_table(conn, "inference_costs"):
        total, day = conn.execute(
            "SELECT COALESCE(SUM(cost_cents),0),"
            " COALESCE(SUM(CASE WHEN created_at >= datetime('now','-1 day')"
            " THEN cost_cents END),0) FROM inference_costs"
        ).fetchone()
        print(f"- inference spend: {dollars(total)} total, {dollars(day)} last 24h")
    if has_table(conn, "turns"):
        last = conn.execute(
            "SELECT timestamp, state FROM turns ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()
        if last:
            print(f"- last turn: {last['timestamp']} (state: {last['state']})")
    if has_table(conn, "policy_decisions"):
        denied = conn.execute(
            "SELECT COUNT(*) FROM policy_decisions WHERE decision != 'allow'"
            " AND created_at >= datetime('now','-1 day')"
        ).fetchone()[0]
        print(f"- policy denials/quarantines last 24h: {denied}")


def spend(conn, n):
    show(conn, "Inference cost by model (last 7 days)",
         "SELECT model, provider, COUNT(*) AS calls,"
         " printf('$%.2f', SUM(cost_cents)/100.0) AS cost"
         " FROM inference_costs WHERE created_at >= datetime('now','-7 day')"
         " GROUP BY model, provider ORDER BY SUM(cost_cents) DESC")
    show(conn, f"Spend tracking (last {n})",
         "SELECT created_at, category, tool_name,"
         " printf('$%.2f', amount_cents/100.0) AS amount, recipient, domain"
         " FROM spend_tracking ORDER BY created_at DESC LIMIT ?", (n,))
    show(conn, f"Transactions (last {n})",
         "SELECT created_at, type, printf('$%.2f', amount_cents/100.0) AS amount,"
         " printf('$%.2f', balance_after_cents/100.0) AS balance_after, description"
         " FROM transactions ORDER BY created_at DESC LIMIT ?", (n,))


def tools(conn, n):
    show(conn, f"Tool calls (last {n})",
         "SELECT created_at, name, arguments, error FROM tool_calls"
         " ORDER BY created_at DESC LIMIT ?", (n,))


def denied(conn, n):
    show(conn, f"Policy denials and quarantines (last {n})",
         "SELECT created_at, tool_name, risk_level, decision, reason"
         " FROM policy_decisions WHERE decision != 'allow'"
         " ORDER BY created_at DESC LIMIT ?", (n,))


def changes(conn, n):
    show(conn, f"Self-modifications (last {n})",
         "SELECT timestamp, type, file_path, description FROM modifications"
         " ORDER BY timestamp DESC LIMIT ?", (n,))
    if os.path.isdir(os.path.join(HOME, ".git")):
        print(f"\n## State git log (last {n})")
        subprocess.run(["git", "-C", HOME, "log", "--oneline", f"-{n}"], check=False)


def children(conn, _n):
    show(conn, "Child automatons",
         "SELECT created_at, name, address, status,"
         " printf('$%.2f', funded_amount_cents/100.0) AS funded, last_checked"
         " FROM children ORDER BY created_at DESC")


COMMANDS = {
    "summary": summary,
    "spend": spend,
    "tools": tools,
    "denied": denied,
    "changes": changes,
    "children": children,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        sys.exit(__doc__.strip())
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    with connect() as conn:
        COMMANDS[sys.argv[1]](conn, max(1, n))


if __name__ == "__main__":
    main()
