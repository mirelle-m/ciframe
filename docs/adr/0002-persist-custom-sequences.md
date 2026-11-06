# Persist custom chord sequences in a SQLite catalog backed by a named Docker volume

The app could only search six chord sequences hardcoded in `main.py`; there was no way for a
visitor to register a new one, and no persistence layer at all. The music and genre catalog is
loaded from a CSV into memory at startup, and ADR 0001 keeps the deploy as a single local-only
container with no external services. The feature therefore needed a store that fits inside that
container, survives container recreation, and does not migrate the music catalog out of the CSV.

We added a SQLite catalog using the standard-library `sqlite3` module, with the database file at
`/app/instance/deciframe.db` (overridable via `DATABASE_PATH`). The schema keeps the ordered chord
list of each sequence, a precomputed set of matching music IDs, and a small `meta` table with a
dataset version. The six existing sequences are seeded idempotently at startup and new sequences
are inserted through `POST /sequencias`. Matching uses the same rule that reproduces the existing
`SEQ_FAMOSA` tag with zero divergences: the sequence must appear as a contiguous ordered block in
`musica.cifra`, and every chord of the music must belong to the sequence, comparing case-sensitively.
Matches are computed once when a sequence is created (and rebuilt when the dataset version changes),
so search reads a set instead of scanning every chord list, with a small in-memory LRU cache for
popular searches. The catalog is exposed through `GET /sequencias`, `POST /sequencias`, and
`GET /similares?sequencia_id=...`, while the legacy `sequencia=` parameter keeps working. A named
volume mounted at `/app/instance` makes the file survive `docker rm` and container recreation; the
writable container layer alone only survived restarts.

This keeps the deploy model intact: no new Python dependency, no external database service, and no
change to the CSV-backed music catalog. The trade-offs are deliberate. SQLite allows one writer at a
time, which is fine with the current single gunicorn worker but requires WAL and a busy timeout if
workers are added. Precomputed matches must be rebuilt when the CSV changes, which the dataset
version handles on startup. The matching rule is restrictive for user-created sequences and the
case-sensitive identity means `Bm,G,D,A` and `bm,g,d,a` are different sequences; both were accepted
to preserve the existing results and musical meaning (`7M` ≠ `7m`). The in-memory cache is
per-process and not a source of truth. Finally, persistence depends on the documented named volume,
so the run command in the README and the ignore rules for the database files are part of the
deployment change. Editing and deleting sequences remain out of scope because the catalog is
anonymous and has no authentication.
