# Milestone 2 champion submission

**Algo:** `baselines/defense_v3_lowcompute` ("defense" baseline + endgame policy +
a compute-time fix for a real, Verified weakness found this milestone).

**Packaged from:** the tagged commit `milestone2-champion` (see `git log
milestone2-champion` / `git show milestone2-champion:baselines/defense_v3_lowcompute/algo_strategy.py`
for the exact source that was zipped).

## Why this replaces `milestone1-fallback` (`baselines/defense`)

`baselines/defense` (the Milestone 1 champion) won every local match it played
across Milestone 1 (120 games) and the first half of Milestone 2 (75 more games,
195-0 total across 11 distinct opponents) — but this milestone's endgame-policy
investigation found a real weakness: it lost **0-10, every single game**, to
`opponents/turtle_survivor` (a purely passive, zero-offense, maximal-defense test
fixture), always finishing tied 40.0-40.0 on health at turn 99. Root cause,
Verified directly from the replay's `endStats.total_computation_time` field:
`defense` used ~1820-1827ms of cumulative compute per game vs turtle_survivor's
~710-730ms, and the Verified turn-100 tie-break rule (`docs/GAME_SPEC.md` 4.3)
breaks a tied-health game in favor of **lower** cumulative compute time. `defense`
was losing purely on compute, not on any unit-placement weakness.

`defense_v3_lowcompute` patches this (4 concrete changes: caching/throttling the
most expensive per-turn heuristic, hoisting a repeated object construction out of a
hot loop, skipping a redundant JSON re-parse, and a "stalemate breaker" that commits
real force if never breached by turn 40 — see the algo's own docstring for detail)
and was accepted as the new champion only after passing the **full regression
suite**: 110/110 (100%) against every opponent `defense` already beat (0
regressions), plus an improved (not perfect) 3/16 (~19%) win rate against
`turtle_survivor`, up from a Verified 0/10 (0%). See
`docs/MILESTONE_2_REPORT.md` and `docs/COUNTEREXAMPLE_SUITE.md` section 6 for the
full numbers, methodology, and the honest limitation (this is a partial fix, not a
complete one — `turtle_survivor` is a deliberately extreme, unrealistic fixture, and
the champion still loses to it more often than not).

## Milestone 3/4 compliance update: `run.sh` executable-bit race condition

**A later milestone found and root-caused a real bug affecting `defense_v3_lowcompute.zip`
(and every other zip produced by the official `scripts/zipalgo_mac` tool):** the
zip stores `run.sh` without its executable bit (`0o100644` instead of
`0o100755`). Decompiling `engine.jar`'s `SimpleAlgoPlayer.class` shows the engine
has a self-healing attempt for exactly this — it runs `Runtime.getRuntime().exec("chmod
u+x " + runPath)` before launching the algo on non-Windows — **but never calls
`.waitFor()` on it before immediately trying to execute `run.sh` directly.** This
is a genuine, Verified race condition: most local boots win the race, but it has
been directly reproduced losing (crashing) at least once locally
(`java.io.IOException: error=13, Permission denied`). The "Verified functional"
claim below reflects a run that happened to win the race, not proof it can't be
lost. See `docs/COMPLIANCE_REPORT.md` section 1.1 for the full mechanism and
empirical crash-rate estimate.

**Use `defense_v3_lowcompute_permfix.zip` (added below) instead of
`defense_v3_lowcompute.zip` where possible** — it ships `run.sh` already
executable, sidestepping the race entirely.

## What's in this folder

- `defense_v3_lowcompute.zip` — produced with the starter kit's own official
  packaging tool exactly as documented:
  ```
  cd baselines && ../scripts/zipalgo_mac defense_v3_lowcompute ../submissions/milestone2_champion/defense_v3_lowcompute.zip
  ```
  **Carries the race-condition risk above** — kept for parity/transparency with
  the official tool's output, not recommended as the primary upload artifact.
- **`defense_v3_lowcompute_permfix.zip` (recommended)** — identical contents,
  built with the system `zip` tool instead (preserves the executable bit).
  Verified via fresh extraction with a plain `unzip` (no manual `chmod`) plus a
  real match against `python-algo` — ran to completion and won, 0 crashes.
- `defense_v3_lowcompute_algo_folder/` — the same algo, unzipped, with the
  executable bit already set on `run.sh`, in case the submission portal wants a
  folder instead of a zip.

## How to submit

Same caveat as `submissions/emergency_fallback/README.md`: we have no portal/login
access, so the actual upload flow is untested (`docs/COMPLIANCE_REPORT.md`).

1. Go to the Terminal submission portal (https://terminal.c1games.com).
2. **Prefer `defense_v3_lowcompute_algo_folder/` if the portal takes a raw
   folder, otherwise upload `defense_v3_lowcompute_permfix.zip`** (not the plain
   `defense_v3_lowcompute.zip` — see the race-condition finding above).

## Rollback / provenance

This exact algo is preserved at the `milestone2-champion` git tag. The Milestone 1
champion remains separately preserved and **untouched** at `milestone1-fallback`
(`submissions/emergency_fallback/`) — if `defense_v3_lowcompute` ever turns out to
regress something not caught by our local benchmark corpus, fall back to that tag,
which has the simpler, lower-risk (if less complete) `baselines/defense` design.

```bash
git show milestone2-champion:baselines/defense_v3_lowcompute/algo_strategy.py
# or, to get the whole tagged tree into a fresh directory:
git archive milestone2-champion -- baselines/defense_v3_lowcompute | (cd /tmp/restore && tar -x)
```

## If you need to regenerate this package

```bash
cd "Citadel Terminel"
cd baselines
chmod +x defense_v3_lowcompute/run.sh
zip -r ../submissions/milestone2_champion/defense_v3_lowcompute_permfix.zip defense_v3_lowcompute \
  -x '*.git*' 'defense_v3_lowcompute/README.md' 'defense_v3_lowcompute/*.ps1'
cd ..
```
