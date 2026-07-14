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

## What's in this folder

- `defense_v3_lowcompute.zip` — ready to upload as-is, produced with the starter
  kit's own official packaging tool:
  ```
  cd baselines && ../scripts/zipalgo_mac defense_v3_lowcompute ../submissions/milestone2_champion/defense_v3_lowcompute.zip
  ```
- `defense_v3_lowcompute_algo_folder/` — the same algo, unzipped, in case the
  submission portal wants a folder instead of a zip.
- **Verified functional**: re-extracted the zip into a clean temp directory and
  played a real match against `python-algo` with `engine.jar` — ran to completion
  and won, with 0 crashes on either side.

## How to submit

Same caveat as `submissions/emergency_fallback/README.md`: we have no portal/login
access, so the actual upload flow is untested (`docs/COMPLIANCE_REPORT.md`).

1. Go to the Terminal submission portal (https://terminal.c1games.com).
2. Upload `defense_v3_lowcompute.zip` directly, OR select the
   `defense_v3_lowcompute_algo_folder/` directory if the portal wants a raw folder.

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
cd baselines && ../scripts/zipalgo_mac defense_v3_lowcompute ../submissions/milestone2_champion/defense_v3_lowcompute.zip && cd ..
```
