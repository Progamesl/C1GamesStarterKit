# Tournament Strategy Brief

**Read this first if you're at the competition and need to understand or
defend our algo's behavior quickly.** This is a practical synthesis of 7
milestones of work, not a benchmark log — for the full evidence behind any
claim here, follow the doc references, but you shouldn't need to.

**Current champion: `baselines/defense_v6_encryptor_fix`, tagged
`milestone5-champion`.** This has been the champion since Milestone 4 and
remains so after two further milestones of dedicated attempts to improve it
(Milestones 6-7) found nothing that beats it without introducing new risk.
**Submit this one unless section 6 tells you otherwise.**

---

## 1. Central mechanism, in one paragraph

A static, corner-weighted TURRET/WALL defensive core (built once, upgraded
opportunistically) plus a lightweight reactive-rebuild system that watches
for breaches and reinforces exactly where we got hit, capped so a feint
can't bait us into overspending. Offense is deliberately conservative and
opportunistic — spend only MP we can genuinely spare, probe the
currently-cheapest lane, never touch the SP set aside for defense. Two
special-case endgame modes (a hard tie fix and a genuine "behind, all-in"
mode) exist specifically because of a Verified turn-100 tie-break rule (see
§5). This is a **turtle-and-punish, not a race**, design — it is built to
grind out a long game and win on structural integrity + a small compute-time
edge, not to out-rush anyone.

## 2. Opening behavior (turns ~1-6)

- Turns 1-6: **pure defense, zero offense.** `build_core_defense` places 10
  TURRET anchors in a diagonal staircase from each corner inward
  (`[1,12]→[4,12]→[7,11]→[10,10]→[13,10]/[14,10]`) plus a WALL row along the
  front (`y=13`, spanning both corners) — all at once, budget-permitting, not
  gradually.
- MP is *not* idle during this window: `stall_with_interceptors` spends up
  to 2 MP/turn on cheap INTERCEPTORs at our own edge, a pure defensive
  supplement that doesn't compete with SP.
- Once turn 6 hits and MP allows, `opportunistic_offense` starts probing —
  gated on turn-parity + MP ≥ 9, so it fires roughly every other turn once
  we can afford it, not continuously.

## 3. Defensive logic (the core of the strategy)

- **Static core** (`build_core_defense`): 10 TURRET anchors + wall front row,
  rebuilt every turn via `attempt_spawn` (a no-op if already present/full).
- **SUPPORT ("Encryptor") pair** at `[13,9]`/`[14,9]`, one row behind the
  turret line, on our own central attack lane — shields OUR mobile units
  passing through (real mechanic, see §4), gated on SP > 10 so it never
  jumps the queue ahead of core defense.
- **Reactive rebuild** (`reactive_defense`): tracks every breach location
  with a decaying weight (×0.6/turn), and each turn reinforces the
  highest-weighted breach neighborhoods with fresh TURRETs — **capped at 6
  SP/turn** (raised to 10 in the two endgame-preserve/all-in-tied modes)
  specifically so a repeated feint can't bait us into overspending on a
  decoy lane.
- **Upgrades** (`upgrade_core`): TURRET upgrade is a big damage jump (5→16)
  for a real range tradeoff (4.5→3.5) — worth it since our anchors are close
  enough together that the range loss rarely opens a gap. WALL and SUPPORT
  are also upgraded once they exist (WALL: 40→120 HP; SUPPORT: shield
  roughly doubles and its range nearly triples — see §4).

## 4. Offensive logic

- **`opportunistic_offense`** (normal play): every other turn, if MP ≥ 9,
  dump everything into SCOUTs at whichever of 2 cached lane options
  (`[13,0]` middle, `[3,10]` near-corner) currently looks cheapest by a
  turret-damage-along-path heuristic. Lane choice is cached and only
  recomputed every 12 turns — a deliberate compute-time tradeoff, not a
  bug.
- **`_stalemate_breaker`**: if we've never once been breached by turn 40,
  periodically (every 10 turns) commit 2 DEMOLISHERs + a full SCOUT wave —
  because a passive 40-40 tie at turn 100 is a **loss** for us under the
  tie-break rule (§5) unless we're strictly faster, so a truly passive
  mutual stalemate must be actively broken.
- **Endgame offense** (`all_in_tied_strike` / `desperation_offense`, only
  past turn 80): commit a fraction of current MP to DEMOLISHERs + the rest
  to SCOUTs, every remaining turn, no pacing — because there's nothing left
  to conserve MP for. `desperation_offense` has **never been observed to
  trigger in any recorded game across 7 milestones** — our defense has never
  let a real game reach turn 80 while we're behind — so treat it as a
  theoretically-sound but empirically-untested safety net, not a
  battle-proven mechanism.
- **SUPPORT's real mechanic** (Verified via a purpose-built probe,
  `docs/MILESTONE_4_REPORT.md`): shields ONLY mobile units passing within
  range, never stationary structures, stacking across multiple SUPPORTs,
  bonus = `shieldPerUnit + shieldBonusPerY * support_y`. This is why our
  offense gets a real, measurable HP bonus on the central lane specifically
  — it's not decorative.

## 5. The turn-100 rule you must not forget

**Verified from engine bytecode** (`GameMain.runLoop`, `docs/GAME_SPEC.md`
§4.3): if turn 100 is reached, the winner is decided by (1) remaining
health, then (2) **less cumulative compute time used**, then (3) a coin
flip. This is why: (a) a huge amount of Milestone 2 effort went into
compute-time reduction (caching pathfinding, hoisting object construction
out of hot loops), and (b) the endgame modes exist at all — an exact health
tie near the cap used to be silently treated as "safe" by an off-by-one
(`>=` instead of `>`) bug, which we found and fixed (Milestone 3). If you
ever see us sitting on a long tied game past turn 80 doing nothing, that
would be the bug's symptom — it should not happen in the current champion.

## 6. Known weaknesses — stated plainly, this is the most important section

### 6.1 THE headline weakness: a continuous, single-lane, un-paused Demolisher rush

**Impact: 0/20 (0%) against `public_opponents/travelling_salesmen_v33`, both
seats, fully reproducible, zero crashes.** This is the single most important
fact in this document. Everything else we test, we win; this one pattern,
we lose to cleanly and repeatably.

- **The pattern**: every turn from turn 4 onward, spend 100% of current MP
  on DEMOLISHERs at one lane, re-targeted every 4 turns toward whichever of
  our two corners currently looks structurally weaker (by counting our own
  WALL/TURRET density). No bursting, no pausing, no early over-commitment we
  can punish — pure sustained pressure that never lets up and never
  competes with the opponent's own SP-funded defense.
- **Why we lose to it**: our corner TURRET anchors (`[1,12]`/`[26,12]`) sit
  ON scoring-edge tiles themselves — once 3+ simultaneous Demolishers land
  enough damage in one combat frame to kill even a freshly-rebuilt 75-HP
  TURRET (they do), the tile is open and a Demolisher just walks onto it and
  scores directly, no further breach needed. Our flat, non-ramping SP
  income (`coresPerRound: 5.0`) cannot keep rebuilding fast enough against
  an MP economy that ramps up over the game.
- **What was tried, and genuinely didn't work (12 tested variants across 2
  milestones)**: 5 patch attempts in Milestone 6 (extra structural layers at
  various tile combinations, raised SP caps, MP-funded counter-offense,
  cheaper walls) — all delayed the loss (35→~38-43 turns survived) but none
  reversed it. 4 more attempts in Milestone 7 (`defense_v10_lockdown`'s
  region-wide depth rework, delayed to ~53 turns) — still didn't reverse it.
  A 5th, larger attempt (`defense_v11_econ_offense`, adding a restored
  offense lane + continuous un-paused counter-offense) not only failed to
  fix this but **introduced 4 new losses** against previously-solid
  opponents (see §6.2) — REJECTED as a net regression, not shipped. One
  final, narrowly-scoped, depth-only retry (`defense_v12_corner_box`, zero
  offense/MP changes) — see `docs/MILESTONE_7_REPORT.md` §4 for the result;
  check there for the current status if you need the latest word on this.
- **Bottom line for the competition**: if you face an opponent that
  sustains a single-lane rush without over-committing early and without
  pausing, **assume we lose that specific matchup** unless a future patch
  changes this. There is currently no in-repo fix. This is a known,
  accepted risk, not an oversight.

### 6.2 Second-order lesson: our own attempted fixes are a source of risk too

`defense_v11_econ_offense`'s "match their sustained posture" offense change
looked reasonable in isolation against the target opponent, but broke 4
other previously-100%-win opponents
(`travelling_salesmen_adapdef`/`frumblesnatch`/`davidw0311_mcts`/`summer2022_6th`)
that the unmodified champion still beats cleanly. **Lesson for anyone
tempted to patch this further under time pressure: any change to
offense/MP-spending posture is now a confirmed high-collateral-risk area.**
Prefer not touching it at all unless you can run the full regression suite
(`experiments/run_regression.py`) before shipping.

### 6.3 Everything else: no known weakness found

Across 28 distinct opponents tested (20 self-built archetypes covering
rushes/turtles/funnels/signature-detection/minimax/prediction, the official
starter bot, 2 self-built baselines, and 6 genuinely independent
publicly-sourced bots — 4 with real competition placement claims), the
current champion is **undefeated except for the one pattern in §6.1**. Zero
crashes, zero timeouts, in any recorded game across 7 milestones.

## 7. Expected counterstrategies at the actual event

Ranked by how much of our own testing already covers them:

1. **Single/adaptive-flank sustained rush (§6.1's pattern)** — the one
   opponent style we know we lose to. If you can scout or infer this before
   a match, there's no in-repo counter-adjustment available live; this is a
   pre-match risk to accept.
2. **Turtle/passive/no-offense opponents** — well covered, `_stalemate_breaker`
   exists specifically for this, tested against multiple self-built
   turtle archetypes plus one real independent one (`Captain`, per the
   user's manual practice-sandbox testing, `docs/REAL_OPPONENT_RESULTS.md`
   §2) with a decisive win.
3. **Burst/feint-heavy opponents trying to bait overspending** — the
   reactive-defense SP cap exists specifically for this; tested against
   self-built feint/decoy archetypes with no exploit found.
4. **SUPPORT/shield-targeted counters, minimax lookahead, move-prediction
   opponents** — a full adversarial countersearch (Milestone 5) targeted our
   own SUPPORT logic specifically and found no exploit; a held-out corpus
   built blind from unimplemented prior-art archetypes also found nothing.
5. **Anything not resembling the above** — no specific evidence either way,
   but the breadth of the 28-opponent corpus (deliberately including several
   independently-designed, real-competition-placed bots, not just
   self-built ones) is the best available proxy for "an opponent we didn't
   specifically design for."

## 8. Endgame behavior summary (turns 80-100)

| Condition (checked every turn, turn > 80) | Mode | Behavior |
|---|---|---|
| Strictly ahead on health | `PRESERVE` | Zero offense; stall with up to 3 MP/turn on defensive INTERCEPTORs only; raised reactive-defense cap (10, from 6) |
| Exactly tied on health | `ALL_IN_TIED` | Commit a fraction of current MP to DEMOLISHERs + rest to SCOUTs, every remaining turn, no pacing; same raised reactive cap |
| Behind on health | `DESPERATE` | Same all-in offensive commitment as `ALL_IN_TIED` (never observed to trigger in 7 milestones of testing) |
| (turn ≤ 80) | `NORMAL` | Standard opportunistic offense + reactive defense described in §§3-4 |

**Why a tie near the cap is treated as dangerous, not safe**: per §5's
tie-break rule, an exact health tie is decided by compute-time efficiency
next — we don't know our margin there for certain against every possible
opponent, so `ALL_IN_TIED` tries to actually win outright rather than
coast on an assumed tie-break advantage.

---

## 9. Emergency rollback procedure

**If something goes wrong with the current champion right before or during
the event, here is exactly how to get back to any previous, known-good,
already-validated version.**

### 9.1 Quick reference: every tagged champion, oldest to newest

| Tag | Algo | `submissions/` folder | Headline result at the time |
|---|---|---|---|
| `milestone1-fallback` | `baselines/defense` | `submissions/emergency_fallback/` | 60/60 (100%) vs. starter bot + our own rush/hybrid baselines |
| `milestone2-champion` | `baselines/defense_v3_lowcompute` | `submissions/milestone2_champion/` | Fixed `turtle_survivor` weakness + compute-time cuts |
| `milestone3-champion` | `baselines/defense_v4_tiebreak` | `submissions/milestone3_champion/` | Fixed tied-endgame mode-transition bug |
| `milestone4-champion` | `baselines/defense_v6_encryptor_fix` | `submissions/milestone4_champion/` | Re-benchmarked + fixed for the corrected "High School Terminal 2026" config |
| **`milestone5-champion` (CURRENT CHAMPION)** | `baselines/defense_v6_encryptor_fix` (one more small fix) | `submissions/milestone5_champion/` | 172/172 across 20 opponents at the time; now 28-opponent-tested, loses only to §6.1's pattern |

`defense_v10_lockdown`, `defense_v11_econ_offense`, and
`defense_v12_corner_box` (Milestone 7 candidates) are **not tagged and not
packaged** — all three were tested and rejected, never promoted to
champion. Do not use them as a rollback target.

### 9.2 How to actually roll back (exact commands)

**If you just need to look at or extract an old version's code (no repo
changes):**

```bash
# See the exact source at any tag:
git show milestone4-champion:baselines/defense_v6_encryptor_fix/algo_strategy.py

# Extract a full tagged tree into a fresh directory for inspection/diffing:
git archive milestone3-champion -- baselines/defense_v4_tiebreak | (mkdir -p /tmp/restore && tar -x -C /tmp/restore)
```

**If you need to actually revert the working tree to an old tag** (only do
this if the current `main`/active branch is genuinely broken and you need
to submit *something* immediately):

```bash
# Safest: create a new branch from the good tag, don't touch history
git checkout -b emergency-rollback milestone5-champion

# Then re-package directly from that branch (see 9.3) and submit.
```

**Do not** `git reset --hard` a shared/pushed branch to an old tag under
time pressure unless you fully understand the consequences for anyone else
with a checkout — prefer the new-branch approach above.

### 9.3 Which folder to actually upload, right now

**Primary: `submissions/milestone5_champion/`.** Inside it:

- **Prefer `defense_v6_encryptor_fix_algo_folder/` if the submission portal
  accepts a raw folder upload** — this sidesteps a known packaging bug
  entirely (§9.4).
- **Otherwise upload `defense_v6_encryptor_fix_permfix.zip`.**
- **Do NOT upload the plain `defense_v6_encryptor_fix.zip`** in that same
  folder — it has a confirmed packaging bug (§9.4). It's kept only for
  transparency/parity with the official tool's output.

**If `milestone5-champion` itself is somehow unusable and you need to fall
back further**, the folders are, in order of preference (newest known-good
first): `submissions/milestone4_champion/`, `submissions/milestone3_champion/`,
`submissions/milestone2_champion/`, `submissions/emergency_fallback/`. Same
rule applies in every one of them: prefer the `_algo_folder/` directory or
the `_permfix.zip`, never the plain `.zip`.

### 9.4 The one packaging gotcha you must know about

The official `scripts/zipalgo_mac`/`zipalgo_linux` tools strip `run.sh`'s
executable bit (produces `0o100644` instead of `0o100755`). The engine
*tries* to self-heal this (`chmod u+x` before launching) but does so
**asynchronously, without waiting for it to finish** — a real, reproduced
race condition (~6% local crash rate in our testing, plausibly worse on a
slower/containerized tournament runner). Every `_permfix.zip` and
`_algo_folder/` in every `submissions/` folder already has this fixed and
independently re-verified. Full detail: `docs/COMPLIANCE_REPORT.md` §1.1,
and the complete pre-submission checklist: `docs/SUBMISSION_CHECKLIST.md`.
