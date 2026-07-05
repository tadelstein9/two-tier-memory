-- two-tier-memory :: tier 2, the queried-on-demand store.
-- A catalog of solved problems. Boring on purpose: plain columns + full-text search.

CREATE TABLE IF NOT EXISTS solutions (
  id         INTEGER PRIMARY KEY,
  created    TEXT NOT NULL,   -- ISO date the problem was solved
  area       TEXT,            -- domain: build | db | api | infra | ...
  title      TEXT NOT NULL,   -- short name
  problem    TEXT,            -- the concrete problem
  root_cause TEXT,            -- why it happened
  solution   TEXT,            -- what actually worked
  gotcha     TEXT,            -- the non-obvious trap / the lesson
  artifacts  TEXT,            -- files / commits produced
  tags       TEXT,            -- comma-separated
  refs       TEXT             -- related ids / links
);

-- Full-text index over the searchable columns (the exact-match retrieval tier).
CREATE VIRTUAL TABLE IF NOT EXISTS solutions_fts USING fts5(
  title, problem, root_cause, solution, gotcha, tags,
  content='solutions', content_rowid='id'
);

-- Keep the FTS index in lockstep with the table.
CREATE TRIGGER IF NOT EXISTS solutions_ai AFTER INSERT ON solutions BEGIN
  INSERT INTO solutions_fts(rowid, title, problem, root_cause, solution, gotcha, tags)
  VALUES (new.id, new.title, new.problem, new.root_cause, new.solution, new.gotcha, new.tags);
END;
CREATE TRIGGER IF NOT EXISTS solutions_ad AFTER DELETE ON solutions BEGIN
  INSERT INTO solutions_fts(solutions_fts, rowid, title, problem, root_cause, solution, gotcha, tags)
  VALUES ('delete', old.id, old.title, old.problem, old.root_cause, old.solution, old.gotcha, old.tags);
END;
CREATE TRIGGER IF NOT EXISTS solutions_au AFTER UPDATE ON solutions BEGIN
  INSERT INTO solutions_fts(solutions_fts, rowid, title, problem, root_cause, solution, gotcha, tags)
  VALUES ('delete', old.id, old.title, old.problem, old.root_cause, old.solution, old.gotcha, old.tags);
  INSERT INTO solutions_fts(rowid, title, problem, root_cause, solution, gotcha, tags)
  VALUES (new.id, new.title, new.problem, new.root_cause, new.solution, new.gotcha, new.tags);
END;
