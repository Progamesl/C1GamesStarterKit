# Emergency fallback submission

**Algo:** `baselines/defense` ("conservative balanced defense" baseline)
**Packaged:** from the tagged commit `milestone1-fallback` (see `git log
milestone1-fallback` / `git show milestone1-fallback:baselines/defense/algo_strategy.py`
for the exact source that was zipped).

## Why this one

Benchmarked locally (`experiments/results/*.jsonl`, 120 total games, engine
`engine.jar` from this repo, JDK 17): `defense` won **all 60 of its games** across
every matchup we ran it in (20-0 vs the starter algo, 20-0 vs our own `rush`
baseline, 20-0 vs our own `hybrid` baseline). It also had 0 crashes and 0
harness/timeout errors across all 120 games in the full round robin. See
`docs/MILESTONE_1_REPORT.md` for the full numbers and honest caveats (n=20 per
matchup, all one-sided sweeps -- strong signal of a real skill gap among these 4
algos specifically, but not proof of a near-zero loss rate against unseen opponent
archetypes).

## Milestone 3/4 compliance update: `run.sh` executable-bit race condition

**A later milestone found and root-caused a real bug in `defense_baseline.zip`
(and every other zip produced by the official `scripts/zipalgo_mac` tool):**
the zip stores `run.sh` without its executable bit (`0o100644` instead of
`0o100755`). Decompiling `engine.jar`'s `SimpleAlgoPlayer.class` confirms the
engine has a self-healing attempt for exactly this — on non-Windows it runs
`Runtime.getRuntime().exec("chmod u+x " + runPath)` before launching the algo —
**but never calls `.waitFor()` on that chmod process before immediately trying to
execute `run.sh` directly.** This is a genuine, Verified race condition, not a
guaranteed failure: repeated local trials of this exact un-fixed zip mostly boot
successfully (chmod usually wins the race on a fast local disk), but it has been
directly reproduced crashing at least once locally
(`java.io.IOException: error=13, Permission denied`, `AlgoIndex 0 crashed
bootup`). See `docs/COMPLIANCE_REPORT.md` section 1.1 for the full mechanism,
decompiled bytecode evidence, and empirical local crash-rate estimate. The
original "verified locally" claim below reflects a run that happened to win the
race, not proof the race can't be lost.

**Use `defense_baseline_permfix.zip` (added below) instead of
`defense_baseline.zip` where possible** — it sidesteps the race entirely by
shipping `run.sh` already executable, so the async chmod's timing becomes
irrelevant.

## What's in this folder

- `defense_baseline.zip` -- produced with the starter kit's own official
  packaging tool exactly as documented:
  ```
  cd baselines && ../scripts/zipalgo_mac defense ../submissions/emergency_fallback/defense_baseline.zip
  ```
  (`.zipignore` inside the algo excludes `run.ps1`, matching how the starter kit's
  own `python-algo/.zipignore` behaves.) **Carries the race-condition risk above**
  — kept for parity/transparency with the official tool's output, not recommended
  as the primary upload artifact.
- **`defense_baseline_permfix.zip` (recommended)** -- identical contents, built
  with the system `zip` tool instead (preserves the executable bit). Verified via
  fresh extraction with a plain `unzip` (no manual `chmod`) plus a real match
  against `python-algo` -- ran to completion and won, 0 crashes.
- `defense_algo_folder/` -- the same algo, unzipped, with the executable bit
  already set on `run.sh`, in case the submission portal accepts a raw folder
  instead of a zip (safest option if available).

## How to submit

1. Go to the Terminal submission portal (https://terminal.c1games.com) -- we do not
   have login credentials for this and could not test the actual upload end-to-end;
   this is an explicit compliance gap for the user, see `docs/COMPLIANCE_REPORT.md`.
2. **Prefer `defense_algo_folder/` if the portal takes a raw folder, otherwise
   upload `defense_baseline_permfix.zip`** (not the plain `defense_baseline.zip`
   -- see the race-condition finding above).
3. **Verified locally**: re-extracted `defense_baseline_permfix.zip` fresh into a
   clean temp dir with a plain `unzip`, no `chmod` applied manually, and ran a
   real match against `python-algo` with `engine.jar` -- it ran end-to-end and
   won, 0 crashes, with `run.sh` already executable straight off extraction.

## If you need to regenerate this package

```bash
cd "Citadel Terminel"
cd baselines
chmod +x defense/run.sh
zip -r ../submissions/emergency_fallback/defense_baseline_permfix.zip defense \
  -x '*.git*' 'defense/README.md' 'defense/*.ps1'
cd ..
```

## Rollback / provenance

This exact algo is preserved forever at the `milestone1-fallback` git tag,
independent of any later changes to `baselines/defense` on the main branch. If
later work on the main branch ever regresses, you can always recover this exact
known-good version with:

```bash
git show milestone1-fallback:baselines/defense/algo_strategy.py
# or, to get the whole tagged tree into a fresh directory:
git archive milestone1-fallback -- baselines/defense | (cd /tmp/restore && tar -x)
```
