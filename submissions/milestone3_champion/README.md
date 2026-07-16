# Milestone 3 champion submission

**Algo:** `baselines/defense_v4_tiebreak` (`defense_v3_lowcompute` + a fix for a
verified tied-endgame mode-transition bug found this milestone).

**Packaged from:** the tagged commit `milestone3-champion` (see `git log
milestone3-champion` / `git show
milestone3-champion:baselines/defense_v4_tiebreak/algo_strategy.py` for the exact
source that was zipped).

## Why this replaces `milestone2-champion` (`baselines/defense_v3_lowcompute`)

`defense_v3_lowcompute` still lost the large majority of games (3/16, ~19%) to
`opponents/turtle_survivor`. Milestone 3 root-caused this further via turn-by-turn
replay inspection: the champion *does* commit real force (it repeatedly damaged and
sometimes destroyed the opponent's walls), but `ahead = my_health >= enemy_health`
conflated an exact tie with a genuine lead, triggering passive endgame-preserve mode
for the last ~19 turns of every tied game — Verified via replay MP tracking to leave
~55-57 MP sitting completely idle at turn 99 every time.

`defense_v4_tiebreak` fixes this specific bug (splits into a strict `ahead` and a
new `all_in_tied_strike` mode that commits 100% of MP every remaining turn once
genuinely tied near the cap) and passed the full regression suite: **110/110
(100%)** against every opponent `defense_v3_lowcompute` already beat, 0 regressions.
It also won both of this milestone's new adversarial-countersearch matchups
(`opponents/lategame_defector` 10-0, `opponents/single_leak_turtle` no measurable
degradation).

**Stated plainly: this does NOT close the `turtle_survivor` gap.** Win rate stayed
at 3/20 (15%), statistically the same as before. See `docs/MILESTONE_3_REPORT.md`
for the full root-cause trail, why the fix doesn't move that specific number
(structural/economic, not behavioral), and why it was still accepted as champion
regardless (zero regressions + a real, verified bug fix + survives two new targeted
adversarial designs).

## Important newly-discovered compliance finding: the official `zipalgo_mac` tool strips `run.sh`'s executable bit

While doing the standard "fresh-extraction verification" for this package, we found
that the starter kit's own official packaging tool
(`scripts/zipalgo_mac`) **produces a zip where `run.sh` loses its executable
permission bit** (`0o100644` instead of `0o100755`). Re-extracting that zip into a
clean directory and running a real match against `python-algo` reproduces a genuine
engine-level crash:

```
Algo Crashed. Crash: true !processIsAlive: null
...
java.io.IOException: error=13, Permission denied
AlgoIndex 0 crashed bootup: .../defense_v4_tiebreak/run.sh
```

This is **not specific to this algo** — we confirmed the same permission loss in
last milestone's already-submitted `submissions/milestone2_champion/*.zip` too, so
if the actual competition portal does a literal unzip that preserves standard unix
permissions (normal zip behavior, and what our own `unzip` does locally), **any
zip produced by the official `zipalgo_mac` tool used exactly as documented could
fail to boot on submission.** We have no portal access to confirm whether the
server-side upload flow re-applies executable permissions itself (a real
possibility, in which case this is a non-issue) — see
`docs/COMPLIANCE_REPORT.md` for this flagged as an open, unverified risk.

**Mitigation shipped in this package:** `defense_v4_tiebreak_permfix.zip`, built
with the system `zip` tool instead (which preserves unix permission bits by
default), verified via the same fresh-extraction test to boot and run correctly
with **no manual `chmod` needed**.

## What's in this folder

- `defense_v4_tiebreak.zip` — produced with the starter kit's own official
  packaging tool, exactly as prior milestones did:
  ```
  cd baselines && ../scripts/zipalgo_mac defense_v4_tiebreak ../submissions/milestone3_champion/defense_v4_tiebreak.zip
  ```
  **Verified to fail on fresh extraction** (permission bit issue above) unless
  whatever unzips it either preserves/restores the executable bit itself or the
  portal's upload flow fixes permissions server-side. Kept here for parity/
  transparency with the official tool's output, not recommended as the primary
  upload artifact.
- **`defense_v4_tiebreak_permfix.zip` (recommended)** — identical contents, built
  with the system `zip` tool instead, which does preserve the executable bit.
  **Verified functional**: re-extracted into a clean temp directory with a plain
  `unzip`, no `chmod` applied manually, and played a real match against
  `python-algo` — ran to completion and won, 0 crashes.
- `defense_v4_tiebreak_algo_folder/` — the same algo, unzipped, with the
  executable bit already set on `run.sh`, in case the submission portal accepts a
  raw folder instead of a zip (safest option if available, sidesteps the
  permission question entirely).

## How to submit

Same caveat as `submissions/emergency_fallback/README.md` and
`submissions/milestone2_champion/README.md`: we have no portal/login access, so the
actual upload flow is untested (`docs/COMPLIANCE_REPORT.md`).

1. Go to the Terminal submission portal (https://terminal.c1games.com).
2. **Prefer uploading `defense_v4_tiebreak_algo_folder/` directly if the portal
   supports a raw folder.** Otherwise upload `defense_v4_tiebreak_permfix.zip`
   (not the plain `defense_v4_tiebreak.zip` — see the compliance finding above).

## Rollback / provenance

This exact algo is preserved at the `milestone3-champion` git tag. Both earlier
champions remain separately preserved and **untouched**:
`milestone1-fallback` (`submissions/emergency_fallback/`) and `milestone2-champion`
(`submissions/milestone2_champion/`) — if `defense_v4_tiebreak` ever turns out to
regress something not caught by our local benchmark corpus, fall back to either of
those tags.

```bash
git show milestone3-champion:baselines/defense_v4_tiebreak/algo_strategy.py
# or, to get the whole tagged tree into a fresh directory:
git archive milestone3-champion -- baselines/defense_v4_tiebreak | (cd /tmp/restore && tar -x)
```

## If you need to regenerate this package

```bash
cd "Citadel Terminel"
cd baselines
chmod +x defense_v4_tiebreak/run.sh
zip -r ../submissions/milestone3_champion/defense_v4_tiebreak_permfix.zip defense_v4_tiebreak \
  -x '*.git*' 'defense_v4_tiebreak/README.md' 'defense_v4_tiebreak/*.ps1'
cd ..
```
