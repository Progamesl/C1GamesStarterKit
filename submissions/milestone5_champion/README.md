# Milestone 5 champion submission

**Algo:** `baselines/defense_v6_encryptor_fix` (`defense_v4_tiebreak` + the
Milestone 4 SUPPORT/Encryptor shield fix + one Milestone 5 endgame-policy
consistency fix).

**Packaged from:** the tagged commit `milestone5-champion` (see `git log
milestone5-champion` / `git show
milestone5-champion:baselines/defense_v6_encryptor_fix/algo_strategy.py` for
the exact source that was zipped).

## What changed vs `milestone4-champion`

Exactly one method. `desperation_offense` (the "behind on health near the
turn-100 cap" branch) used to hardcode "spawn exactly 2 demolishers, dump the
rest of the MP on scouts," while its sibling `all_in_tied_strike` (identical
"spend everything, every remaining turn" intent, just triggered by an exact
tie instead of being strictly behind) budgets a *fraction* of current MP for
demolishers instead. The corrected config's cheaper `DEMOLISHER` (MP cost
3 -> 2) made the old hardcoded count an even smaller, more arbitrary share of
a real late-game MP pool than before. Fixed to use the same
fraction-of-current-MP budget as `all_in_tied_strike`.

This branch has **never triggered in any recorded game across 5 milestones**
of benchmarking — the champion's defense has never actually let a game reach
turn 78 while behind on health — so this fix was verified via a synthetic
mocked-`GameState` probe (constructing a `turnInfo`/`p1Stats` JSON payload
directly and calling the method), not a real-match before/after. See
`docs/MILESTONE_5_REPORT.md` section 8 for the full investigation, including
a direct mirror-match test proving the broader ahead/tied/behind endgame
framework *is* real and reachable under the corrected config (just not by
this specific opponent corpus), and `docs/COUNTEREXAMPLE_SUITE.md` section 12
for the equivalent per-finding writeup.

Also folded into this milestone: a full adversarial countersearch
specifically against the Milestone 4 SUPPORT fix (3 opponents,
`docs/MILESTONE_5_REPORT.md` sections 1-6) and a held-out corpus check (3
more opponents built blind from unimplemented prior-art archetypes, sections
7) — both found **no exploitable weakness**, so neither contributed a code
change, only additional regression coverage (all 6 new opponents are now
permanently in `experiments/run_regression.py`'s `DEFAULT_OPPONENTS`).

**Full regression after the fix: 172/172 games won across 20 distinct
opponents (the original 14-opponent corpus plus all 6 new Milestone 5
opponents), 0 crashes, 0 errors.**

## Important compliance finding, reconfirmed again on Linux: `zipalgo_linux` also strips `run.sh`'s executable bit

Same finding as Milestones 3 and 4 (`docs/COMPLIANCE_REPORT.md` §1.1),
reconfirmed for this package: `defense_v6_encryptor_fix.zip` in this folder
has `run.sh` at `0o100644` (non-executable) after a plain `unzip`, verified
directly by inspecting the zip's own permission metadata.

## What's in this folder

- `defense_v6_encryptor_fix.zip` — produced with the starter kit's own
  official packaging tool for this platform:
  ```
  ./scripts/zipalgo_linux baselines/defense_v6_encryptor_fix submissions/milestone5_champion/defense_v6_encryptor_fix.zip
  ```
  **Confirmed to have the non-executable `run.sh` bit** (see above). Kept for
  parity/transparency with the official tool's output, not recommended as the
  primary upload artifact.
- `defense_v6_encryptor_fix_permfix.zip` (recommended) — identical contents,
  built with the system `zip` tool instead, which does preserve the
  executable bit. **Verified functional**: re-extracted into a clean temp
  directory (`/tmp/m5_verify_permfix`) with a plain `unzip`, no `chmod`
  applied manually, `ls -la` confirms `run.sh` is `-rwxr-xr-x` (`0o100755`)
  straight out of the archive, and a real local match against `python-algo`
  ran to completion and won (`Winner (p1 perspective, 1 = p1 2 = p2): 1`), 0
  crashes.
- `defense_v6_encryptor_fix_algo_folder/` — the same algo, unzipped, with the
  executable bit already set on `run.sh` directly, in case the submission
  portal accepts a raw folder instead of a zip (safest option if available,
  sidesteps the permission question entirely).

## How to submit

Same caveat as every prior milestone's package: we have no portal/login
access, so the actual upload flow is untested (`docs/COMPLIANCE_REPORT.md`).

1. Go to the Terminal submission portal (https://terminal.c1games.com).
2. **Prefer uploading `defense_v6_encryptor_fix_algo_folder/` directly if the
   portal supports a raw folder.** Otherwise upload
   `defense_v6_encryptor_fix_permfix.zip` (not the plain
   `defense_v6_encryptor_fix.zip` — see the compliance finding above).

## Rollback / provenance

This exact algo is preserved at the `milestone5-champion` git tag. All
earlier champions remain separately preserved and **untouched**:
`milestone1-fallback` (`submissions/emergency_fallback/`),
`milestone2-champion` (`submissions/milestone2_champion/`),
`milestone3-champion` (`submissions/milestone3_champion/`), and
`milestone4-champion` (`submissions/milestone4_champion/`) — if
`defense_v6_encryptor_fix` (patched) ever turns out to regress something not
caught by our local benchmark corpus, fall back to any of those tags.

```bash
git show milestone5-champion:baselines/defense_v6_encryptor_fix/algo_strategy.py
# or, to get the whole tagged tree into a fresh directory:
git archive milestone5-champion -- baselines/defense_v6_encryptor_fix | (cd /tmp/restore && tar -x)
```

## If you need to regenerate this package

```bash
cd /workspace
find baselines/defense_v6_encryptor_fix -name "__pycache__" -exec rm -rf {} +
./scripts/zipalgo_linux baselines/defense_v6_encryptor_fix submissions/milestone5_champion/defense_v6_encryptor_fix.zip
cd baselines
zip -r ../submissions/milestone5_champion/defense_v6_encryptor_fix_permfix.zip defense_v6_encryptor_fix \
  -x '*.git*' 'defense_v6_encryptor_fix/README.md' 'defense_v6_encryptor_fix/*.ps1' '*__pycache__*'
cd ..
```
