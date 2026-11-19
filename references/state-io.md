# State, persistence, I/O and serialization

Load when: writing files, config, databases, queues, caches, serde types,
or anything that must survive a crash or a second process. These bugs pass
unit tests and lose data in production: test them with real files/DBs in a
temp dir, and with two writers.

## One owner per piece of state (single source of truth)

- Name the owner of every piece of state (a DB table, a file, one task).
  Everything else holds ids/handles and asks the owner — no second copy
  that can drift. Caches are explicitly derived, with an invalidation rule.
- Read-modify-write from two places loses updates. Serialise through the
  owner (one task, one transaction, one lock), or compare-and-swap with a
  version column.
- Config precedence is a documented order (defaults < file < env < flags);
  test that a saved choice survives a restart.

## Files

- **Atomic write**: write a temp file in the same directory → `flush` →
  `sync_all` → `rename` over the target (→ fsync the dir for durability).
  Readers never see half a file; a crash leaves old or new, never torn.
- Buffered I/O for many small reads/writes: `BufReader`/`BufWriter`; call
  `flush()` explicitly and handle its error (drop swallows it). [perf-io-buffering]
- Paths from users or data: never join raw. Map names through an allow
  list or a validated newtype (no `/`, `\`, `..`, NUL, leading `.`);
  canonicalise and check the result stays under the root (security.md).
- Restrictive permissions for secrets/state (`0o600`/`0o700`).

## SQLite / databases

- Transactions for every multi-statement change. In SQLite, writers start
  with `BEGIN IMMEDIATE` so two processes can't both read-then-write.
- WAL mode for concurrent readers; one writer connection or a busy timeout.
- Schema migrations are versioned, forward-only, tested from the previous
  version's real DB file.
- Constraints in the DB (`UNIQUE`, `CHECK`, `FOREIGN KEY`) over app checks.
- Partial indexes for "runnable" queries (`WHERE status = 'queued'`).

## Queues, jobs and at-least-once work

- Durable first: the item is committed before anyone is woken.
- Claim with a **lease** (`lease_until`), renew by heartbeat, a reaper
  requeues expired leases. Count an attempt at claim time; `max_attempts`
  = how many runs, then dead-letter with the last error.
- Consumers are idempotent; dedupe by a caller-chosen unique key.
- Every state change appends an event row (audit + debugging).
- Restart recovery: items that were running when the process died are
  requeued immediately.

## Serde

- Match the wire's naming once: `#[serde(rename_all = "camelCase")]`. [serde-rename-all]
- Evolve formats compatibly: new fields `#[serde(default)]`; omit empty
  with `skip_serializing_if = "Option::is_none"`. [serde-default-compat] [serde-skip-empty]
- Inputs you own the schema of: `#[serde(deny_unknown_fields)]` catches
  typos; don't use it on inputs from newer peers. [serde-deny-unknown-fields]
- Choose enum tagging on purpose (`tag = "type"` internally tagged is the
  readable default for JSON; `untagged` gives the worst errors). [serde-enum-representation]
- `#[serde(flatten)]` to inline or to capture extra keys into a map. [serde-flatten]
- Validate while deserialising: `#[serde(try_from = "Raw")]` produces only
  valid domain types (parse, don't validate). [serde-try-from-validate]
- Custom field formats with `with`/`serialize_with`/`deserialize_with`
  (durations, timestamps, hex). [serde-custom-with]
- Round-trip test every persisted type, and keep a fixture of the **old**
  format to prove new code still reads it.
- `serde_json` with `float_roundtrip` when floats must survive exactly.

## External processes and protocols

- `std::process::Command` with args as separate values — never a shell
  string built from data (security.md).
- Check exit status *and* parse output defensively; capture stderr for the
  error message; set a timeout; close stdin if the child might wait on it.
- Pin the version of external CLIs/APIs you depend on and test against a
  recorded or fake peer (tdd.md: fakes). A field rename upstream should
  fail a test, not silently change behaviour.
