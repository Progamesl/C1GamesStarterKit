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

## What's in this folder

- `defense_baseline.zip` -- ready to upload as-is. Produced with the starter kit's
  own official packaging tool:
  ```
  cd baselines && ../scripts/zipalgo_mac defense ../submissions/emergency_fallback/defense_baseline.zip
  ```
  (`.zipignore` inside the algo excludes `run.ps1`, matching how the starter kit's
  own `python-algo/.zipignore` behaves.)
- `defense_algo_folder/` -- the same algo, unzipped, in case the submission portal
  wants a folder rather than a zip (`README.md` at the repo root: "Simply select the
  folder of your algo when prompted on the Terminal website... select the specific
  language folder").

## How to submit

1. Go to the Terminal submission portal (https://terminal.c1games.com) -- we do not
   have login credentials for this and could not test the actual upload end-to-end;
   this is an explicit compliance gap for the user, see `docs/COMPLIANCE_REPORT.md`.
2. Upload `defense_baseline.zip` directly, OR select the `defense_algo_folder/`
   directory if the portal wants a raw folder instead of a zip.
3. **Verified locally** (re-extracted the zip fresh into a clean temp dir and ran a
   real match against `python-algo` with `engine.jar` -- it ran end-to-end and won)
   that this exact zip's contents are a legal, complete, crash-free algo: it
   contains `algo_strategy.py` at the top level (platform requirement, see
   `docs/COMPLIANCE_REPORT.md` section 1) plus its own private copy of `gamelib/`.

## If you need to regenerate this package

```bash
cd "Citadel Terminel"
cd baselines && ../scripts/zipalgo_mac defense ../submissions/emergency_fallback/defense_baseline.zip && cd ..
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
