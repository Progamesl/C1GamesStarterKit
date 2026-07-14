# Milestone 1 Report

Tags used throughout, per instructions: **Verified / Strongly supported / Hypothesis
/ Rejected**. Nothing here is claimed as certain unless tagged Verified with a
citation. This report also covers process interruptions, since several occurred.

## 0. Process note (interruptions)

This session was interrupted by transient tool/auth/billing errors **three times**.
No work was lost: every interruption happened between git commits, and the very
first action on each resume was to check `git log`/`git status` against the actual
repo state (not just trust the recap in the resuming prompt) before continuing. One
resume prompt's recap was stale (it said "no docs/ files... written yet" when
`docs/GAME_SPEC.md` and `docs/COMPLIANCE_REPORT.md` were already committed) — caught
by checking `git log` directly rather than proceeding on unverified assumptions. A
separate, parallel research-only workstream (visible via `git log`, commit `f22d30d`,
authored while this workstream was between turns) independently produced
`docs/STRATEGIC_PRIOR_ART_REPORT.md`; its ranked hypotheses were read and used to
inform baseline design below.

## 1. What's actually verified to work

- **Verified**: `correlation-one/C1GamesStarterKit` clones and its bundled
  `engine.jar` runs real matches end-to-end on this machine, producing a `.replay`
  file and an authoritative `Winner (p1 perspective, 1 = p1 2 = p2): N` stdout line.
  Confirmed by direct `java -jar engine.jar work <run.sh> <run.sh>` invocations, not
  just the (buggy, see below) `scripts/run_match.py`.
- **Verified**: the repo's own `scripts/run_match.py` is broken on this specific
  workspace because it builds an unquoted shell command string and the workspace
  path contains a space (`Citadel Terminel`) — `cd /Users/sidshukla/Citadel &&
  ...` silently fails. Our harness (`experiments/harness.py`) calls `java` directly
  via `subprocess` with an argument list (no shell string), which sidesteps this.
  This is a real, demonstrated bug in the starter kit's own convenience script for
  any path containing a space, not a config/rules issue.
- **Verified**: all 3 of our baseline algos (`baselines/defense`, `baselines/rush`,
  `baselines/hybrid`) are legal, complete, crash-free algos: each independently
  passed `scripts/test_algo_mac` (syntax/semantic smoke test against a replay) and
  each played multiple full real `engine.jar` matches with zero crashes detected
  (see `experiments/results/*.jsonl`, field `*_crashes` is 0 in every summary).
- **Verified**: the packaged submission zip (`submissions/emergency_fallback/defense_baseline.zip`)
  is not just a source-tree copy — it was re-extracted into a clean temp directory
  and played one more real match against `python-algo` from that extracted copy,
  which ran to completion and produced a winner line, confirming the actual artifact
  a human would upload is functional, not just the pre-zip source.

## 2. Game spec — see `docs/GAME_SPEC.md` for the full cited breakdown

Headline Verified findings (all cited to `game-configs.json` and/or decompiled
`engine.jar` bytecode in that doc, not memory):

- Board: 28x28 diamond (`ARENA_SIZE=28`), your territory `y<14`.
- 6 real unit types + Remove/Upgrade meta-actions; full cost/HP/damage/range table
  in `GAME_SPEC.md` section 2.
- Resources: SP starts at 40 + 5/turn flat; MP starts at 5 + 5/turn + ramp, decays
  25%/turn unspent, caps at 150.
- **Turn cap: hard 100 turns**, found only by decompiling `engine.jar` bytecode
  (`GameMain.runLoop`) — not documented in any config file or the Python client.
- **Win tie-break chain** (also only found via decompiled bytecode,
  `GameMain.processEndGame`): higher remaining health wins; if tied, **lower
  cumulative compute time used wins**; if still tied, a literal coin flip
  (`Random.nextBoolean()`).
- Per-turn compute budget: soft 5000ms / hard 35000ms in local ("work") mode.

Open gaps (Hypothesis, not Verified — see `docs/COMPLIANCE_REPORT.md` section 3 for
the full list): SUPPORT's exact shield formula, exact MP-cap ramp formula, exact
crash-loss consequence, whether the tournament runner uses byte-identical
`engine.jar`/config to what's in this clone.

## 3. Benchmark results

**Setup:** `experiments/harness.py` (see file for full implementation) runs matches
via direct `engine.jar` invocation, alternates which algo is p1/p2 across the batch,
parses the engine's own winner line, cross-checks against the replay's final health
fields, and records crash/timeout detection. All matches below used the actual
`engine.jar` and `game-configs.json` shipped in this repo — no simulation.

**Sample size:** **20 games per matchup, 6 matchups, 120 games total.** This is a
small sample by statistical standards — with a true 50/50 matchup, a 20-0 sweep
would be extraordinarily unlikely (probability ≈ 2×20/2^20 ≈ 0.002% two-sided) so a
clean 20-0 result is strong evidence of a real, large skill gap for *that specific
matchup*, not noise. It does **not** prove a near-zero loss rate in general — 20
games cannot rule out, e.g., a 1-in-30 loss rate, and none of these results say
anything about performance against opponent archetypes we haven't tested (this is
explicitly flagged as a gap to close in Milestone 2).

| Matchup (algo1 vs algo2) | Result | Crashes | Errors/timeouts |
|---|---|---|---|
| `baselines/defense` vs `python-algo` (starter) | **20-0** to defense | 0 / 0 | 0 |
| `baselines/rush` vs `python-algo` (starter) | **0-20** (starter wins every game) | 0 / 0 | 0 |
| `baselines/hybrid` vs `python-algo` (starter) | **0-20** (starter wins every game) | 0 / 0 | 0 |
| `baselines/defense` vs `baselines/rush` | **20-0** to defense | 0 / 0 | 0 |
| `baselines/defense` vs `baselines/hybrid` | **20-0** to defense | 0 / 0 | 0 |
| `baselines/rush` vs `baselines/hybrid` | **0-20** (hybrid wins every game) | 0 / 0 | 0 |

Raw per-match records: `experiments/results/20260715-*.jsonl` (one JSON object per
game plus a trailing summary line each).

**Verified**: `defense` beat every other algo we tested it against, 100% of the
time, across 60 total games, with zero crashes across the entire 120-game round
robin. **Strongly supported** (not exhaustively proven): `defense`'s full-width
corner-weighted turret core plus capped-spend neighborhood-reactive defense is
simply a much sturdier wall than either `rush`'s deliberately minimal 2-turret
defense or `hybrid`'s smaller 6-anchor core — consistent with `rush` and `hybrid`
both also losing every game to the starter algo's own (moderate) defense, and with
`hybrid` beating `rush` (hybrid's core, while weaker than defense's, is still
stronger than rush's near-absent one). We have **not** isolated exactly which
component (turret count, upgrade timing, reactive-defense cap) is most responsible —
that decomposition is deferred to Milestone 2's parameter search.

## 4. Champion / fallback selection

**Selected: `baselines/defense`.** Rationale, per the instructions to weigh
robustness over raw average win rate: it is not just the highest-win-rate baseline
(100% across all 60 of its games, the best of the three), it is also the one with
the simplest, lowest-variance turn logic (no banked-attack timers, no endgame-mode
branching, no reliance on detecting enemy unit counts before deciding to attack) and
the cheapest per-turn compute (no simulation/lookahead) — minimizing crash surface
and keeping us far under the Verified 5000ms/35000ms per-turn budget, which per
`GAME_SPEC.md` 4.3 is also literally a tie-break input. It never intentionally
under-defends the way `rush` does, so its worst case (loss to an opponent we haven't
seen) is bounded by "our defense wasn't good enough," not "we gambled on tempo and
lost outright" — a more conservative failure mode for a fallback whose entire job is
to not be embarrassing if nothing else is ready in time.

## 5. Fallback archive: exact location and submission steps

- Zip (ready to upload): `submissions/emergency_fallback/defense_baseline.zip`
- Unzipped folder (in case the portal wants a folder): `submissions/emergency_fallback/defense_algo_folder/`
- Instructions: `submissions/emergency_fallback/README.md`
- Immutable snapshot: git tag `milestone1-fallback` (see below) — recoverable even
  if `baselines/defense` on `main` is later changed by Milestone 2 work.
- **Verified** functional: re-extracted into a clean temp dir and played a real
  match against `python-algo`; it ran to completion and won.
- **Gap (cannot verify)**: we have no portal/login access, so the actual upload
  flow itself (file size limits, portal-side validation) is untested — flagged in
  `docs/COMPLIANCE_REPORT.md`. The user needs to do the actual upload.

## 6. Compliance gaps needing user/organizer input (unchanged from `docs/COMPLIANCE_REPORT.md`)

Summary (full detail in that file): no portal access; unverified memory limits;
unverified whether the tournament's live `engine.jar`/config exactly matches this
clone; SUPPORT's shield formula and MP-cap ramp formula not fully traced in
bytecode; exact crash-loss consequence assumed (Hypothesis), not directly Verified.

## 7. Single most important remaining uncertainty

**We have only benchmarked against 4 algos total (3 of our own design + the one
official starter bot), all sharing a similar "moderate structural defense +
opportunistic offense" flavor.** We have not yet tested `defense` (or anything else)
against a rush-heavy, funnel/maze, delayed-burst, or adaptive/opponent-modeling
archetype meaningfully different from what we built ourselves — precisely the
broader corpus Milestone 2 calls for. A 100% local win rate against a narrow,
self-similar opponent pool is a real but limited signal; it is the single biggest
gap between "verified locally" and "confident about the actual tournament."

## 8. Next steps (Milestone 2, time permitting)

1. Build a broader, more diverse opponent corpus (funnel/maze, aggressive
   left/right-biased rush distinct from our own `rush`, delayed-burst hoarder,
   simple adaptive/reactive opponent, mutated variants of our own `defense`) and
   re-benchmark `defense` against all of them before trusting the current 100% win
   rate more broadly.
2. Parameter search (grid/random first) over `defense`'s turret anchor layout,
   upgrade ordering, and reactive-defense spend cap.
3. Adversarial hardening: deliberately try to build a counter to `defense`'s exact
   layout (e.g. a maze that avoids its turret coverage, or a burst timed to exceed
   its reactive-spend cap in one turn) and patch if found, logged in a new
   `docs/COUNTEREXAMPLE_SUITE.md`.
4. Explicit, directly-tested endgame policy (ahead/behind/tied near turn 100),
   building on `hybrid`'s crude turn>80 threshold as a starting point, but validated
   with constructed board states rather than only naturally-arising ones.
5. Only if 1-4 plateau: revisit the explicitly-deferred idea of light opponent-type
   classification (prior-art hypothesis, not attempted in Milestone 1). Full RL
   remains **Rejected** for this timeline per the original task brief and
   `docs/STRATEGIC_PRIOR_ART_REPORT.md` section 6 (no top-placing historical team
   found to have used it as their core mechanism; per-turn compute budget is also a
   poor fit).
