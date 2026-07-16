# Milestone 4 champion submission

**Algo:** `baselines/defense_v6_encryptor_fix` (`defense_v4_tiebreak` +
a corrected-config SUPPORT/Encryptor shield fix).

**Packaged from:** the tagged commit `milestone4-champion` (see `git log
milestone4-champion` / `git show
milestone4-champion:baselines/defense_v6_encryptor_fix/algo_strategy.py` for the
exact source that was zipped).

## Why this replaces `milestone3-champion` (`baselines/defense_v4_tiebreak`)

Milestone 4 discovered that every benchmark through Milestone 3 (including
`milestone3-champion` itself) was run against the wrong `game-configs.json` — the
generic public starter-kit default, not the actual competition's "High School
Terminal 2026" config (`docs/COMPLIANCE_REPORT.md` §0, `docs/GAME_SPEC.md` §2.5).
The single most strategically significant change: SUPPORT ("Encryptor") flips from a
resource-generating unit with a provably-inert shield to a real shield/support unit
with zero economy function.

Re-running `defense_v4_tiebreak` completely unmodified under the corrected config
(tag `m4_v4carry` in `docs/MILESTONE_4_REPORT.md`) still wins 100% of a 14-opponent,
136-game regression suite — but on the three "leak/turtle" style opponents
(`turtle_survivor`, `single_leak_turtle`, `lategame_defector`), every single win is a
bare +10 HP margin (30 vs 20) riding the turn-100 cap to the engine's health
tie-break — a fragile win, not a decisive one.

`defense_v6_encryptor_fix` repositions SUPPORT to a spot that actually benefits from
the now-real shield (`[[13,9],[14,9]]`, verified via a dedicated controlled probe,
`docs/GAME_SPEC.md` §2.5.2) and upgrades it (something no earlier "defense" family
baseline ever did). Result: **same 100% win rate**, but the three fragile matchups
above become decisive wins (3-4x bigger margins, games often ending well before
turn 100). A direct head-to-head round-robin against both `defense_v4_tiebreak` and
a more aggressive rebalance candidate (`defense_v7_range_leverage`) shows
`defense_v6_encryptor_fix` undefeated against both (10-0 each) — see
`docs/MILESTONE_4_REPORT.md` for the full numbers and why `v7range` was tested and
rejected despite also clearing the regression suite at 100%.

## Important compliance finding, confirmed again on Linux: `zipalgo_linux` also strips `run.sh`'s executable bit

Milestone 3 found that the starter kit's official `scripts/zipalgo_mac` tool
produces a zip where `run.sh` loses its executable permission bit
(`docs/COMPLIANCE_REPORT.md` §1.1). This milestone re-ran the same
fresh-extraction test against `scripts/zipalgo_linux` (the correct tool for this
now-Linux workspace) and confirmed **the identical bug is present there too**:
`defense_v6_encryptor_fix.zip` in this folder has `run.sh` at `0o100644`
(non-executable) after a plain `unzip`, verified directly by inspecting the zip's
own permission metadata (not just by observing a crash, though the underlying
engine-side race condition documented in the compliance report still applies and
can cause exactly the crash logged there).

## What's in this folder

- `defense_v6_encryptor_fix.zip` — produced with the starter kit's own official
  packaging tool for this platform:
  ```
  ./scripts/zipalgo_linux baselines/defense_v6_encryptor_fix submissions/milestone4_champion/defense_v6_encryptor_fix.zip
  ```
  **Confirmed to have the non-executable `run.sh` bit** (see above). Kept for
  parity/transparency with the official tool's output, not recommended as the
  primary upload artifact.
- **`defense_v6_encryptor_fix_permfix.zip` (recommended)** — identical contents,
  built with the system `zip` tool instead, which does preserve the executable bit.
  **Verified functional**: re-extracted into a clean temp directory
  (`/tmp/m4_verify_permfix`) with a plain `unzip`, no `chmod` applied manually, `ls
  -la` confirms `run.sh` is `-rwxr-xr-x` (`0o100755`) straight out of the archive,
  and a real local match against `python-algo` ran to completion and won
  (`Winner (p1 perspective, 1 = p1 2 = p2): 1`), 0 crashes.
- `defense_v6_encryptor_fix_algo_folder/` — the same algo, unzipped, with the
  executable bit already set on `run.sh` directly, in case the submission portal
  accepts a raw folder instead of a zip (safest option if available, sidesteps the
  permission question entirely). Also independently fresh-run-verified: won its own
  match against `python-algo`, 0 crashes.

## How to submit

Same caveat as every prior milestone's package: we have no portal/login access, so
the actual upload flow is untested (`docs/COMPLIANCE_REPORT.md`).

1. Go to the Terminal submission portal (https://terminal.c1games.com).
2. **Prefer uploading `defense_v6_encryptor_fix_algo_folder/` directly if the portal
   supports a raw folder.** Otherwise upload `defense_v6_encryptor_fix_permfix.zip`
   (not the plain `defense_v6_encryptor_fix.zip` — see the compliance finding
   above).

## Rollback / provenance

This exact algo is preserved at the `milestone4-champion` git tag. All earlier
champions remain separately preserved and **untouched**: `milestone1-fallback`
(`submissions/emergency_fallback/`), `milestone2-champion`
(`submissions/milestone2_champion/`), and `milestone3-champion`
(`submissions/milestone3_champion/`) — if `defense_v6_encryptor_fix` ever turns out
to regress something not caught by our local benchmark corpus, fall back to any of
those tags.

```bash
git show milestone4-champion:baselines/defense_v6_encryptor_fix/algo_strategy.py
# or, to get the whole tagged tree into a fresh directory:
git archive milestone4-champion -- baselines/defense_v6_encryptor_fix | (cd /tmp/restore && tar -x)
```

## If you need to regenerate this package

```bash
cd /workspace
./scripts/zipalgo_linux baselines/defense_v6_encryptor_fix submissions/milestone4_champion/defense_v6_encryptor_fix.zip
cd baselines
chmod +x defense_v6_encryptor_fix/run.sh
zip -r ../submissions/milestone4_champion/defense_v6_encryptor_fix_permfix.zip defense_v6_encryptor_fix \
  -x '*.git*' 'defense_v6_encryptor_fix/README.md' 'defense_v6_encryptor_fix/*.ps1' '*__pycache__*'
cd ..
```
