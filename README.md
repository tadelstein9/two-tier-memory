# two-tier-memory

A queryable long-term memory for AI coding agents — the **two-tier fix** for the context-window wall.

> Companion essay: *"Your AI's Memory Breaks on Real Work. The Fix Is Fifty Years Old."*

## The problem

An AI coding agent's default long-term memory is a stack of markdown files it loads into context at the start of every session. That works at ten files. It fails at a hundred and forty: everything competes for one finite context window, and past the edge the memory silently truncates — the agent quietly forgets, re-solves solved problems, contradicts last week's decisions. You blame the model. The filing system is the problem.

It's an old problem. Loading a whole file and scanning it is the pre-relational habit that databases were invented, in 1970, to kill: store it structured, index it, fetch only the row you need.

## The fix: two tiers

**Tier 1 — an index, always loaded.** One line per solved problem: a title and a pointer. Cheap to carry every session. It tells the agent *what exists*, never the detail. (`INDEX.md`, generated from tier 2 so it never drifts.)

**Tier 2 — a database, queried on demand.** Every hard problem becomes a row in a plain SQLite file — problem, root cause, what worked, the gotcha, the artifacts. A thousand rows cost the agent nothing until it runs a query. When something smells familiar, it asks the table instead of rummaging through prose.

Stop loading the library. Keep an index you can hold, and a database you can question.

## Use it

```sh
python3 memory.py init

python3 memory.py add \
  --area db --title "SQLite can't persist a view over an ATTACH-ed database" \
  --problem "CREATE VIEW over an attached db vanished on the next connection" \
  --root-cause "the view binds to the attach alias, not the file" \
  --solution "materialize into the main db, or re-ATTACH and re-create the view on open" \
  --gotcha "no error is raised — the view simply isn't there next session" \
  --tags "sqlite,attach,view"

python3 memory.py query "attach view disappears"
python3 memory.py get 1
python3 memory.py index      # regenerate INDEX.md from the database
```

## The part that isn't the database

The tool alone is a trap. It earns its keep only with a habit and a little hygiene:

- **Query before you rebuild.** An agent's reflex is to solve, not to look up. Make "search the memory first" a standing rule, or the database becomes dead weight.
- **Keep rows honest.** Write them the day you solve the thing; delete them the day they turn out wrong. A stale row misleads worse than an empty table.
- **Retrieval has a ceiling.** Full-text search (built in here, via FTS5) finds the words you match, not the row you *meant*. When you outgrow it, bolt semantic search / embeddings onto this same relational base — don't start there.

## Wiring it into an agent

Point your agent's project instructions at two rules:

1. On a new hard problem, **`query` first**; act on a hit.
2. On solving something novel, **`add` a row**, then **`index`**.

The always-loaded `INDEX.md` primes the agent on what it already knows; the database holds the rest, for free.

## Files

| File | Role |
|---|---|
| `schema.sql` | the `solutions` table + an FTS5 full-text index kept in sync by triggers |
| `memory.py` | stdlib-only CLI: `init` / `add` / `query` / `get` / `list` / `index` |
| `INDEX.md` | tier-1 index, generated from the database (git-ignored) |
| `memory.db` | tier-2 store — your data (git-ignored) |

No dependencies. Python 3 and its bundled `sqlite3`.

## Credit

Built in the open by Tom Adelstein. The pattern came out of a working session with Claude Code, Anthropic's coding agent: I pitched the relational approach; the agent built, tested, and hardened this implementation. The human–AI collaboration is the point — and, fittingly, the subject of the companion essay.

## License

MIT © 2026 Tom Adelstein
