#!/usr/bin/env python3
"""two-tier-memory -- a queryable long-term memory for AI coding agents.

Tier 1 (INDEX.md): a tiny, always-loaded index -- one line per solved problem.
Tier 2 (memory.db): the full detail in SQLite, queried on demand -- it costs the
agent zero context until it runs a query.

  python3 memory.py init
  python3 memory.py add --title "..." --problem "..." --solution "..." --tags "a,b"
  python3 memory.py query "connection pool timeout"
  python3 memory.py get 3
  python3 memory.py list [--area db]
  python3 memory.py index          # regenerate INDEX.md from the database

Stdlib only. No dependencies beyond Python 3 and its bundled sqlite3.
"""
import argparse
import datetime
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "memory.db")
SCHEMA = os.path.join(HERE, "schema.sql")
INDEX = os.path.join(HERE, "INDEX.md")


def connect():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def cmd_init(args):
    con = connect()
    with open(SCHEMA) as f:
        con.executescript(f.read())
    con.commit()
    print(f"initialized {DB}")


def cmd_add(args):
    row = {
        "created": args.date or datetime.date.today().isoformat(),
        "area": args.area, "title": args.title, "problem": args.problem,
        "root_cause": args.root_cause, "solution": args.solution,
        "gotcha": args.gotcha, "artifacts": args.artifacts, "tags": args.tags,
        "refs": args.refs,
    }
    con = connect()
    cols = ",".join(row)
    ph = ",".join(f":{k}" for k in row)
    cur = con.execute(f"INSERT INTO solutions ({cols}) VALUES ({ph})", row)
    con.commit()
    print(f"added solution #{cur.lastrowid}: {args.title}")


def cmd_query(args):
    match = " OR ".join(args.text.split())   # loose recall; quote the arg for a phrase
    con = connect()
    rows = con.execute(
        "SELECT s.id, s.title, s.area, "
        "  snippet(solutions_fts, -1, '[', ']', ' ... ', 12) AS snip "
        "FROM solutions_fts f JOIN solutions s ON s.id = f.rowid "
        "WHERE solutions_fts MATCH ? ORDER BY rank LIMIT ?",
        (match, args.limit)).fetchall()
    if not rows:
        print("no match -- likely a genuinely new problem. Solve it, then `add` it.")
        return
    for r in rows:
        print(f"#{r['id']}  [{r['area'] or '-'}]  {r['title']}")
        print(f"     {r['snip']}")


def cmd_get(args):
    con = connect()
    r = con.execute("SELECT * FROM solutions WHERE id=?", (args.id,)).fetchone()
    if not r:
        sys.exit(f"no solution #{args.id}")
    for k in r.keys():
        if r[k]:
            print(f"{k:>11}: {r[k]}")


def cmd_list(args):
    con = connect()
    if args.area:
        rows = con.execute("SELECT id,title,area FROM solutions WHERE area=? ORDER BY id", (args.area,))
    else:
        rows = con.execute("SELECT id,title,area FROM solutions ORDER BY id")
    for r in rows:
        print(f"#{r['id']:>3}  [{r['area'] or '-'}]  {r['title']}")


def cmd_index(args):
    con = connect()
    rows = con.execute("SELECT id,title,tags FROM solutions ORDER BY id").fetchall()
    out = ["# Memory index (tier 1)", "",
           "One line per solved problem. Always loaded; the detail lives in the "
           "database -- `python3 memory.py get <id>` or `query <text>`.", ""]
    for r in rows:
        tags = f"  _{r['tags']}_" if r["tags"] else ""
        out.append(f"- **#{r['id']}** {r['title']}{tags}")
    with open(INDEX, "w") as f:
        f.write("\n".join(out) + "\n")
    print(f"wrote {INDEX} ({len(rows)} entries)")


def main():
    ap = argparse.ArgumentParser(description="two-tier memory for AI coding agents")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init").set_defaults(fn=cmd_init)

    a = sub.add_parser("add"); a.set_defaults(fn=cmd_add)
    a.add_argument("--title", required=True)
    a.add_argument("--problem")
    a.add_argument("--root-cause", dest="root_cause")
    a.add_argument("--solution")
    a.add_argument("--gotcha")
    a.add_argument("--area")
    a.add_argument("--tags")
    a.add_argument("--artifacts")
    a.add_argument("--refs")
    a.add_argument("--date")

    q = sub.add_parser("query"); q.set_defaults(fn=cmd_query)
    q.add_argument("text")
    q.add_argument("--limit", type=int, default=8)

    g = sub.add_parser("get"); g.set_defaults(fn=cmd_get)
    g.add_argument("id", type=int)

    ls = sub.add_parser("list"); ls.set_defaults(fn=cmd_list)
    ls.add_argument("--area")

    sub.add_parser("index").set_defaults(fn=cmd_index)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
