# BEP upload timeout

## Problem

`upload_test_logs_from_bep()` runs on a background thread concurrent with
`bazel test`, following the BEP JSON file until it sees a `lastMessage` event
and then uploading it (and any failed/flaky test logs) via `bazelci-agent
artifact upload`. `bazelci.py:1671` (`future.result()`) waits on that thread
unconditionally.

The exact hang mechanism inside `bazelci-agent` is **not confirmed** — flagging
this explicitly since an earlier version of this doc overstated it as settled.

What's actually verified (rules_scala build 6444, logs from all four
platforms): `bazel test` fails instantly on an unrecognized flag
(`--local_extra_resources=bazel_instance=1`, from an experimental
"do not merge" branch), and the very next line launches `bazelci-agent
artifact upload`, which then produces no further output for the full 8-hour
step timeout (`bazelci.py:3104`) before being killed externally.

The obvious theory — bazel dies before writing `lastMessage` to the BEP file,
so `follow()` (`agent/src/utils/follow.rs:36-39`) polls forever waiting for
bytes that never arrive — does **not** hold up under direct reproduction.
Running the same bazel 9.2.0 + bazelci-agent 0.2.7 binaries with the same
flag and the same file-creation race as `bazelci.py`, `bazel` exits in under
a second, but the BEP file still ends with a proper `lastMessage:true` line,
and the agent reaches `buildkite-agent artifact upload <bep file>` within a
second too — the opposite of what the theory predicts. Whatever the real
production job actually gets stuck on remains open; something differs
between the repro and the real hang that hasn't been identified.

Two follow-up theories were also tested and ruled out, rather than left
unexamined:
- **Output buffering hiding a real hang**: maybe the agent does reach
  `buildkite-agent artifact upload <bep file>` in production and hangs
  there, but Rust's stdout is block-buffered when piped to a non-tty, so the
  print never surfaces before the process is killed. Reproduced with the
  real 0.2.7 binary, a stub `buildkite-agent` that sleeps forever, and the
  pipe read directly (not via a blocking `readline()`): the upload-call print
  reaches the pipe in under a second, well before the process is still
  hanging 5+ seconds later. If the same thing happened in production, the
  print should have shown up in the Buildkite log — it didn't. Ruled out.
- **`buildkite-agent`/network broadly down on that machine**: in the same
  hung job, a separate `buildkite-agent artifact upload` call for `java.log`
  (issued directly from `bazelci.py`, not through the Rust agent) succeeded
  around the same time — so the CLI and network were working on that
  machine at that moment. Weakens a generic "infra was down" explanation.

This is exactly why the fix below doesn't try to address a specific
mechanism inside the agent: it bounds the wait from the outside, which works
regardless of what turns out to be the actual cause.

## Non-goals

- Fixing the agent itself (`agent/src/artifact/upload.rs`,
  `agent/src/utils/follow.rs`) to detect that the writer process died. Real
  root-cause fix, but needs a new agent release and version bump
  (`bazelci.py:1939` pins `0.2.7`). Mention as a follow-up in the PR, don't
  implement now.
- Per-project/per-task timeout overrides. `bazelci.py` is shared by every
  project on this Buildkite fleet; a configurable override is a reasonable
  future improvement but out of scope here.

## Design

Bound the one subprocess call that can hang, using `subprocess.run`'s own
`timeout` kwarg — no new mechanism needed:

- `execute_command()` gets a new `timeout=None` parameter, passed through to
  `subprocess.run(..., timeout=timeout)`.
- `upload_test_logs_from_bep()` wraps only the `bazelci-agent artifact
  upload` call (not `download_bazelci_agent`, which is an unrelated short
  binary download) with a new module constant:
  `_BEP_UPLOAD_TIMEOUT_SECONDS = 2 * 60 * 60` (2 hours).
- On `subprocess.TimeoutExpired`, log via `eprint` and return normally
  (don't re-raise).

`subprocess.run(timeout=N)` kills the child process itself on expiry, so no
change is needed to the `with ThreadPoolExecutor(): ... future.result()`
block at `bazelci.py:1629-1671` — the thread function now always returns
within 2 hours, so the executor's `shutdown(wait=True)` and `future.result()`
resolve promptly.

`upload_log_file()` also gets the same `timeout` passthrough, applied only
at its `java.log` call site (`bazelci.py:1654`, same function, same
`buildkite-agent artifact upload` defect class as the fix above, already
wrapped in its own `try/except`). Other `upload_log_file()` callers are
unaffected (default `timeout=None`).

### Timeout value

2 hours, picked as a margin over normal runtime versus the existing global
8-hour step timeout (`bazelci.py:3104`) — the only number that applies
uniformly to every project on this shared fleet, since a killed upload here
doesn't fail the build (bazel's pass/fail verdict is already decided before
this step runs; only debug artifacts are lost). Not validated against other
projects' normal runtimes — call this out to the repo maintainers when
posting the fix.

### Error visibility

Log-only (`eprint`), no Buildkite annotation. Less code; matches the low
severity of the failure (lost debug artifacts, not a build failure).

## Testing

Two unit tests in `bazelci_test.py`:
1. `execute_command` with a real hanging subprocess and a short timeout
   raises `TimeoutExpired`.
2. `upload_test_logs_from_bep`, with `execute_command` mocked to raise
   `TimeoutExpired`, does not propagate the exception.

## Rollout

Post the fix to `bazelbuild/continuous-integration`. Mention in the PR:
that the exact hang mechanism inside `bazelci-agent` is still unverified
(the leading theory was tested by direct reproduction and didn't hold up —
see Problem section), that the fix is deliberately symptom-level because of
that, the 2-hour value as a starting point pending confirmation from
maintainers about other projects' normal runtimes, and an agent-side
investigation/fix as a possible follow-up once the real mechanism is found.
