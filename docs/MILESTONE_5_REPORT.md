# Milestone 5 Report

Tags used throughout, per instructions: **Verified / Strongly supported / Hypothesis
/ Rejected**. This milestone closes the one honest gap flagged at the end of
`docs/MILESTONE_4_REPORT.md` section 6: no adversarial countersearch had yet
specifically targeted `baselines/defense_v6_encryptor_fix`'s new SUPPORT
(Encryptor) placement/upgrade behavior under the corrected "High School
Terminal 2026" config. It covers three separate lines of investigation, done
in sequence: (A) three hypothesis-driven opponents targeting SUPPORT
specifically, (B) a "held-out corpus" check — three more opponents built
blind from unimplemented prior-art archetypes, specifically to guard against
having just overfit sections A's opponents to this one champion, and (C) a
direct re-check of the Milestone 3 endgame policy (`all_in_tied_strike` /
`desperation_offense`) under the corrected config's numbers, since that logic
was carried over unchanged from before the config correction and had never
been re-examined against the new stats.

## 0. Headline summary

- **(A) SUPPORT-targeted countersearch: three distinct hypotheses were formed
  by reading `defense_v6_encryptor_fix`'s source directly**, each targeting a
  different angle on the SUPPORT change: (1) SUPPORT is the single most
  fragile structure type (30 HP) at a fixed, detectable location; (2) the
  champion's own lane-choice heuristic has no awareness of the SUPPORT's
  shield radius, so it could in principle be routed around it entirely; (3)
  SUPPORT upgrades strictly last (after all 10 turret anchors and 12 wall
  cells), creating a real timing window where it's unupgraded/weaker even
  though already exposed. Three purpose-built opponents
  (`support_sniper`/`corner_lane_baiter`/`shield_race_rusher`) tested all
  three, real n=10 each seat. **Result: no exploitable weakness found** — see
  section 1-6 below (unchanged from the first pass of this report).
- **(B) Held-out corpus check: three more opponents, built blind from
  archetypes never previously implemented in this repo's opponent corpus**
  (`docs/STRATEGIC_PRIOR_ART_REPORT.md` §3.5 signature detection +
  counter-switching, §3.2 turn-level minimax/recipe-scoring, §3.7
  opponent-move prediction) — specifically to check that (A)'s "no exploit
  found" result wasn't just an artifact of only ever testing opponents shaped
  around this specific champion's known weaknesses. **Result: no exploit
  found here either** — 30/30 games won (10 each), 0 crashes, real and
  sometimes long/varied games (`predictor_opponent`: 18-70 turns) — see
  section 7.
- **(C) Endgame policy re-check: found and fixed one real, if narrow,
  inconsistency.** `desperation_offense` (the "behind on health near the turn
  cap" branch, carried over unchanged since before the config correction)
  hardcoded "spawn exactly 2 demolishers" instead of budgeting a *fraction* of
  available MP the way its sibling `all_in_tied_strike` does — and the
  corrected config's cheaper DEMOLISHER (MP cost 3->2) makes that hardcoded
  count an even smaller, more arbitrary fraction of a real late-game MP pool
  than before. This branch has **never once triggered in any recorded game
  across 5 milestones** (the champion's defense is strong enough that real
  losses are always decided well before turn 78), so there is no real-match
  before/after to show — verified instead via a synthetic mocked-`GameState`
  probe, and fixed for consistency with `all_in_tied_strike`. Full 20-opponent
  regression after the fix: **172/172 games won, 0 crashes** — see section 8.
- **Champion updated: `baselines/defense_v6_encryptor_fix` (patched) is now
  tagged `milestone5-champion`.** Same algo as `milestone4-champion` in every
  respect except the `desperation_offense` fix in (C). `milestone1-fallback`,
  `milestone2-champion`, `milestone3-champion`, and `milestone4-champion` all
  remain untouched as rollback points — see section 9.

## 1. Hypotheses, read directly from `defense_v6_encryptor_fix/algo_strategy.py`

| # | Hypothesis | Source evidence |
|---|---|---|
| 1 | SUPPORT (30 HP — the most fragile structure type in the corrected config: WALL 40/120, TURRET 75) sits at a **fixed** pair of coordinates (`[[13,9],[14,9]]`), spawned once `SP>10`, and is re-buildable (not a permanent kill) — so sustained, adaptively-targeted pressure could keep it perpetually destroyed/unupgraded. | `build_core_defense`, `core_support_anchors` |
| 2 | The offense-lane heuristic (`_get_cached_lane` -> `least_damage_spawn_location`) picks between `[13,0]` and `[3,10]` purely by projected turret damage, with **zero awareness of the SUPPORT's shield radius**. `dist([3,10], [13,9]) ≈ 10.05`, outside even the upgraded 7-tile range. If a defense could make `[3,10]` look cheaper, the champion's own offense would never collect the shield bonus it was specifically redesigned to use. | `_get_cached_lane`, `core_support_anchors`, Milestone 4 shield-probe formula |
| 3 | `upgrade_core` upgrades SUPPORT **strictly last**, after all 10 `core_turret_anchors` and all 12 `core_wall_front` cells. With finite per-turn SP, this could leave SUPPORT at its weaker unupgraded stats (`shieldRange` 2.5, `shieldPerUnit` 2.0, no `shieldBonusPerY`) for a large fraction of the game even though it's already spawned and exposed. | `upgrade_core`'s call order |

## 2. Opponents built (one per hypothesis, plus a non-adaptive cross-check)

- **`opponents/support_sniper`** (hypothesis 1): minimal own defense (4 corner
  turrets, same design choice as `opponents/middle_rush_exploit`), scans
  `game_state.game_map` every turn for enemy SUPPORT structures (the same
  enemy-unit-scanning technique already used by `opponents/adaptive_reactive`
  and `opponents/escorted_combined_arms`), and sends a scout-screen-then-
  demolisher-escort wave (the `escorted_combined_arms` staggering idea) at
  the detected column every 4 turns from turn 2 onward, falling back to the
  known central lane if SUPPORT hasn't spawned yet.
- **`opponents/corner_lane_baiter`** (hypothesis 2): pure static defense, zero
  offense (isolating the routing question cleanly, same rationale as
  `opponents/turtle_survivor`), deliberately dense (full wall+turret
  coverage, all upgraded) across x∈[6,21] — exactly where the `[13,0]` lane
  runs — and deliberately weak (a single turret per side) at the corners,
  where `[3,10]`'s lane runs.
- **`opponents/shield_race_rusher`** (hypothesis 3, plus a non-adaptive
  cross-check on hypothesis 1): a real defense of its own (corner turrets +
  partial wall, upgraded opportunistically, not a glass cannon), paired with
  a *sustained* (not one-off) central-lane scout+demolisher rush from turn 3
  onward — testing whether "dumb but persistent" pressure alone, without
  adaptive detection, is enough to matter.

All three were smoke-tested in both p1/p2 seats before real benchmarking:
0 crashes, 0 harness errors, sane/distinct turn counts (`corner_lane_baiter`
reaching turn 72 in the smoke test alone, confirming it's a real long game,
not an instant loss).

## 3. Benchmark results (n=10 each, alternating seats)

| Opponent | Result vs `defense_v6_encryptor_fix` | Result vs `defense_v4_tiebreak` (control) |
|---|---|---|
| `support_sniper` | **10/10 lost by attacker**, turn 8-10, margins ~26-38 HP (`experiments/results/20260715-033657_m5_v6fix_vs_support_sniper.jsonl`) | **10/10 lost by attacker**, turn 10, comparable margins (`...034119_m5_v4carry_vs_support_sniper.jsonl`) |
| `corner_lane_baiter` | **10/10 lost by attacker**, every game turn 72, health exactly 30.0/-2.0 (`...033811_m5_v6fix_vs_corner_lane_baiter.jsonl`) | **10/10 lost by attacker**, every game turn 72, health exactly 30.0/-2.0 (`...034234_m5_v4carry_vs_corner_lane_baiter.jsonl`) — byte-for-byte identical outcome pattern |
| `shield_race_rusher` | **10/10 lost by attacker**, turn 12-14, margins ~30-37 HP (`...033953_m5_v6fix_vs_shield_race_rusher.jsonl`) | **10/10 lost by attacker**, turn 12-14, overlapping margins (`...034422_m5_v4carry_vs_shield_race_rusher.jsonl`) |

0 crashes, 0 harness errors, across all 60 games (30 for the champion, 30 for
the control), both seats.

## 4. Turn-by-turn / replay-level evidence (not just aggregates)

### 4.1 `support_sniper` and `shield_race_rusher`: games resolve too fast for the mechanism to be exercised either way

Direct inspection of `experiments/replays/m5_v6fix_vs_support_sniper_000.replay`
and `m5_v6fix_vs_shield_race_rusher_000.replay` (frame-by-frame `p1Units[1]`,
the SUPPORT slot, and `events.shield`):

- vs `support_sniper`: SUPPORT present in only 128/835 frames, health never
  recorded below its full 30 HP in any frame it existed.
- vs `shield_race_rusher`: SUPPORT present in 249/898 frames, health never
  below full 30, **zero `shield` events fired in the entire game**.

**Verified, not hypothesis:** in both matchups, the champion's static core
defense (10 turret anchors + wall front, present from turn 0) decides the
outcome outright by turn 8-14 — well before SUPPORT (gated on `SP>10`, then
low-priority in the upgrade order) has enough turns to either take
meaningful sniping damage or apply a meaningful shield bonus. The sniping and
sustained-rush mechanisms were both real, legal, and functioning as designed
(confirmed via the smoke tests and the `escorted_combined_arms`-derived
staggering firing on schedule) — they simply didn't get enough turns of
runway to matter, because neither opponent's own defense was strong enough to
extend the game past the point where the champion's core alone already wins.

### 4.2 `corner_lane_baiter`: the routing hypothesis is real in mechanism, but this design didn't trigger it

This is the one result worth double-clicking into, because the aggregate
number (10/10, 30.0 vs -2.0 every game) could otherwise be misread as "the
bait had no effect at all."

Direct `events.shield` inspection of
`experiments/replays/m5_v6fix_vs_corner_lane_baiter_000.replay` shows **936
shield events over the course of the 72-turn game**, structured like:

```
[[14, 9], [14, 2], 6.7, 1, '157', '168', 1]
```

— i.e. the SUPPORT at `[14,9]` repeatedly shielding units arriving near
`[14,2]`/`[15,3]` for `6.7` HP each, exactly matching the Verified upgraded
formula `shieldPerUnit + shieldBonusPerY * support_y = 4.0 + 0.3*9 = 6.7`
(`docs/GAME_SPEC.md` 2.5.2). This location is at distance exactly `7` from
the SUPPORT — the edge of its upgraded shield range — meaning the champion's
scout swarms are launching up the **central** `[13,0]`/`[14,0]` lane and
picking up the shield almost immediately, every single wave, for the entire
game. The corner_lane_baiter's deliberately asymmetric defense (dense center,
weak corners) did **not** redirect `_get_cached_lane`'s choice to `[3,10]` as
hypothesized.

Running the exact same opponent against the control, `defense_v4_tiebreak`
(`experiments/replays/m5_v4carry_vs_corner_lane_baiter_000.replay`), shows
the **identical 936 shield events**, same locations, but at `2.0` HP each
(`shieldPerUnit=2.0`, `shieldBonusPerY=0` — `v4carry`'s SUPPORT, at
`[13,3]`/`[14,3]`, was never relocated or upgraded) — confirming `v4carry`'s
own SUPPORT is *also* on the central lane and *also* fires, just for a
smaller, flat amount. Since `corner_lane_baiter` mounts zero offense of its
own, the champion's core alone wins by the same 30.0-vs--2.0 blowout margin
regardless of which SUPPORT bonus size applied — the differential (6.7 vs
2.0 HP/unit) never gets to matter in this specific matchup because the fight
was never close to begin with.

**Rejected as tested, honestly stated:** the hypothesis that a defense could
be shaped to bait the champion's lane choice away from the SUPPORT's shield
radius was not confirmed by this design. **Not fully isolated (an open
sub-question, deferred rather than resolved):** why the deliberately denser
center didn't score worse than the deliberately sparser corner in the
heuristic's own path-damage sum — plausibly the corner lane's path geometry
routes through more total path tiles or a different exposure pattern than
intuition suggests, but this was not traced further given time constraints.

## 5. What this milestone does and does not resolve

- **Resolved:** three specific, source-derived hypotheses about
  `defense_v6_encryptor_fix`'s SUPPORT logic were each turned into a real,
  legal, adaptively-built (where applicable) opponent and tested with a real
  sample size in both seats — not just argued about. All three failed to
  find a regression relative to the already-accepted champion, confirmed via
  replay-level evidence (shield events, structure health), not just win/loss
  aggregates.
- **Not resolved / explicitly deferred:** *why* `corner_lane_baiter`'s
  specific density asymmetry didn't redirect the lane-choice heuristic (see
  4.2) — a natural next probe would be to log `least_damage_spawn_location`'s
  actual computed damage value for both `[13,0]` and `[3,10]` directly (a
  one-line instrumentation change) rather than inferring routing from shield
  events after the fact. Also not attempted: a version of `support_sniper`
  or `shield_race_rusher` paired with a *much* stronger own defense
  specifically tuned to survive past turn 30-40, so the SUPPORT
  upgrade-timing window (hypothesis 3) gets a real chance to be exercised
  under sustained pressure rather than the game resolving too fast either
  way — the two timing-focused opponents built this milestone both had
  their own defense overwhelmed (or overwhelmed the target) well before that
  window would have become observable.
- **Still an open gap, unchanged from Milestone 3 §7 / Milestone 4 §6:** the
  exact MP-cap ramp formula, timeout-damage-per-ms formula, and crash-loss
  mechanics remain unverified from engine bytecode; none of this milestone's
  work required resolving them.

## 6. Champion decision (SUPPORT-targeted countersearch, part A only)

**No change from this specific investigation.** No opponent built for
hypotheses 1-3 found a real degradation (loss, crash, or measurable margin
regression) relative to `defense_v4_tiebreak`, the previous champion, under
real n=10-per-opponent sampling in both seats. Per the standing acceptance
discipline (never patch on small-sample noise or a purely theoretical gap
without a demonstrated practical cost), introducing a patch here — e.g.
making the lane heuristic shield-aware — would add complexity and regression
risk for a benefit that was not actually demonstrated to exist in practice
against any opponent tested, including one (`corner_lane_baiter`)
purpose-built to expose exactly that gap.

This is a genuine, honestly-reported negative result for this specific
question, not proof the design has no exploitable weakness anywhere — see
section 5 above for what remains untested on the SUPPORT-targeting front
specifically. (The overall milestone decision, incorporating parts B and C
below, is in section 9.)

## 7. Held-out corpus check: guarding against overfitting the countersearch itself

**Motivation.** Every opponent in section 1-6 was designed by directly
reading `defense_v6_encryptor_fix`'s own source and reasoning backward from
its specific implementation choices. That is a legitimate adversarial
methodology, but it has a blind spot: if the champion happens to have a real
weakness that doesn't look like "attack the SUPPORT specifically," a
countersearch that only ever looks at the SUPPORT logic will never find it.
To partially guard against this, three more opponents were built using a
different methodology: pick a strategic archetype from
`docs/STRATEGIC_PRIOR_ART_REPORT.md` that had **never previously been
implemented** anywhere in `opponents/`, and implement it faithfully to the
archetype description, without referencing `defense_v6_encryptor_fix`'s code
at all during design.

- **`opponents/signature_detector`** (§3.5): tracks the champion's own
  mobile-unit spawn pattern (side + unit type) turn-by-turn; if the same
  pattern repeats for `SIGNATURE_THRESHOLD` consecutive turns, switches into a
  counter-mode that reinforces the detected side and counter-attacks the
  opposite side.
- **`opponents/minimax_lookahead`** (§3.2): every turn, scores several
  candidate "recipes" (defend-only, scout-rush left/center/right,
  demolisher-center) by projected MP efficiency, projected incoming damage
  along paths, and unspent-SP defensive value, and plays the highest-scoring
  one. Runs under an explicit `TIME_BUDGET_TARGET_MS` (400ms) with real
  timing instrumentation, since this is the most compute-heavy opponent in
  the corpus.
- **`opponents/predictor_opponent`** (§3.7): tracks the champion's mobile-unit
  spawn history and looks for a recurring pattern at a consistent
  turn-offset (every 2/3/4 turns); when confident, preemptively reinforces
  the predicted side *before* the champion's move is revealed that turn,
  rather than reacting after the fact.

All three were smoke-tested in both seats (0 crashes) before real
benchmarking. One implementation bug was caught and fixed during this phase:
`signature_detector` and `predictor_opponent` both initially read
`on_action_frame`'s raw per-unit `player_index` field as if it used the same
0=self/1=enemy convention as `GameUnit.player_index` elsewhere in the
codebase — but the raw action-frame JSON events are actually 1-indexed with
1=self, 2=opponent (confirmed directly in `python-algo/algo_strategy.py`'s
own reference handling of this same field). The original code was
effectively tracking its own spawns instead of the champion's. Fixed in both
files (`if player_index != 2: continue`) before any benchmarking.

**Results (n=10 each, both seats, `experiments/results/20260715-04*_m5_heldout_*.jsonl`,
`...050241_*minimax_lookahead.jsonl`, `...050359_*predictor_opponent.jsonl`):**

| Held-out opponent | Result vs champion | Turn range | Crashes |
|---|---|---|---|
| `signature_detector` | 10/10 champion | 12-34 | 0 |
| `minimax_lookahead` | 10/10 champion | 18 (deterministic given its own fixed recipe set; only seat-swap varies) | 0 |
| `predictor_opponent` | 10/10 champion | 18-70 (widest/most varied matchup in the corpus) | 0 |

**Verified, not just aggregate win/loss:** margins were decisive in every
game (no near-misses) — e.g. `predictor_opponent`'s losses for the champion's
opponent were by margins of 5-7 HP but the champion itself never dropped
below a clear structural win in any of the 20 games, and turns ranged widely
(18-70) confirming this is a real, non-trivial matchup rather than a token
opponent that loses instantly regardless of what it does.

**Conclusion:** the held-out corpus check found no exploit either. Combined
with part A, this is now two independently-designed batches of adversarial
opponents (six total, built by two different methodologies) that both failed
to find a weakness — meaningfully stronger evidence of robustness than either
batch alone, though still not proof of invulnerability (see section 9's
caveats).

## 8. Endgame policy re-check under the corrected config

**Motivation.** `defense_v6_encryptor_fix`'s endgame logic
(`ENDGAME_TURN_THRESHOLD=80`, the ahead/tied/behind three-way split, and the
`all_in_tied_strike`/`desperation_offense` handlers) was carried over
**unchanged** from `defense_v4_tiebreak`, which was built and tuned entirely
under the *old*, incorrect config (`startingHP: 40`, `DEMOLISHER` MP cost 3,
etc. — see `docs/GAME_SPEC.md` §2.5). The module docstring explicitly asserts
this logic "did not need to change" because it's about compute-time/turn-cap
mechanics that the config correction didn't touch — a reasonable claim, but
one that had never actually been re-verified empirically against the new
numbers. This milestone did that verification directly rather than taking
the claim on faith.

### 8.1 Is `ALL_IN_TIED` mode still reachable at all under the corrected config?

Grepping `mode=` debug output across every recorded long-game (turn>=78) log
for `defense_v6_encryptor_fix` across **all 5 milestones** (turtle_survivor,
single_leak_turtle, lategame_defector, corner_lane_baiter, predictor_opponent
— every "long game" opponent in the entire corpus, dozens of games) shows:

```
0 files contain mode=DESPERATE
26 files contain mode=ALL_IN_TIED   (all from a dedicated mirror-match test, see below)
```

Every one of those long games shows **only `NORMAL` and `PRESERVE`** modes —
never `ALL_IN_TIED`, never `DESPERATE`. This is a genuine change from
Milestone 3's finding under the *old* config, where an exact 40-40 tie
against `turtle_survivor` was the dominant near-cap outcome, every single
game (the entire reason `all_in_tied_strike` was built in the first place).
Under the corrected config, the same matchups instead resolve to the
champion being **strictly and heavily ahead** (health pinned at the full 30
HP starting value, opponent reduced to single digits) well before turn 80 —
plausibly because the Milestone 4 SUPPORT fix's extra effective HP is enough
to convert what used to be an exact tie into a clear lead in exactly these
matchups (a Hypothesis, not independently isolated from the lower
`startingHP` change also in effect).

**This raised a real question: is `ALL_IN_TIED`/`DESPERATE` now simply dead,
untestable code, or just under-exercised by this specific opponent corpus?**
Answered directly with a controlled test rather than left as a guess:

**Mirror-match test** (`baselines/defense_v6_encryptor_fix` vs itself, n=6,
`experiments/results/20260715-050822_m5_endgame_mirror_match.jsonl`): since
both sides run byte-identical code, a mirror match is the single most
natural real scenario for producing exact health ties. Result: **6/6 games
reached an exact tie, 14.0 vs 14.0, at turn 100** — confirming
`ALL_IN_TIED` is real, reachable code, not a dead branch; it engaged for all
19 endgame turns (turns 81-99) on both sides in every game (`grep -o
"mode=[A-Z_]*" ... | sort | uniq -c` → `38 mode=ALL_IN_TIED` per log, since
both players' debug output is interleaved in the shared log = 19 turns × 2
players), with legal spawn attempts every turn, 0 crashes. Player 1 won all
6 games via the compute-time tie-break (`total_computation_time`: p1=376ms
vs p2=500ms in the sampled replay) — consistent with the compute-time
tie-break dynamic already documented in `docs/COUNTEREXAMPLE_SUITE.md` §6.2
from Milestone 2, now reconfirmed under the corrected config's numbers too.

**Conclusion for 8.1:** the ahead/tied/behind framework and `ALL_IN_TIED`
handler are Verified functional and reachable under the corrected config.
The reason they never appear against the existing opponent corpus is a
change in how those *specific* matchups resolve (champion ends up ahead, not
tied), not a bug in the endgame logic itself. `DESPERATE` mode, however,
remains **entirely unverified in real play** — it has never triggered in any
recorded game in the project's history, because the champion has never
actually lost a game that reached turn 78. This is flagged honestly as an
open gap in section 9, not glossed over.

### 8.2 Is `PRESERVE` mode's conservatism (no offense, cap MP spend at 3) still appropriate?

Checked the margin at the moment `PRESERVE` first engages (turn 81) across
every sampled long game: in every case, `my_hp` is pinned at the **full 30
HP starting value** (untouched all game) against an opponent already reduced
to single digits. This is not a marginal/contested lead where a more
aggressive policy might plausibly matter — it's already a maximal, secured
blowout by the time `PRESERVE` ever engages in any tested matchup. No
evidence found that `PRESERVE`'s conservatism is currently costing anything
measurable. `ENDGAME_TURN_THRESHOLD=80` itself was also re-examined: games
that don't reach it resolve outright under `NORMAL` mode, and every
long-game opponent tested reaches either a clean breakthrough (turn ~78-80)
or continues to turn 99-100 — no evidence the threshold itself needs to move
under the corrected config's numbers.

### 8.3 The real finding: `desperation_offense`'s hardcoded demolisher count

Direct code comparison of the two "spend everything, we're out of time"
handlers:

```179:196:baselines/defense_v6_encryptor_fix/algo_strategy.py
    def all_in_tied_strike(self, game_state):
        ...
        best = self._get_cached_lane(game_state)
        mp = game_state.get_resource(MP)
        demolisher_cost = game_state.type_cost(DEMOLISHER)[MP]
        demolisher_budget = mp * ALL_IN_DEMOLISHER_MP_FRACTION
        num_demolishers = int(demolisher_budget // demolisher_cost)
        if num_demolishers > 0:
            game_state.attempt_spawn(DEMOLISHER, best, num_demolishers)
        game_state.attempt_spawn(SCOUT, best, 1000)
```

vs. (before this milestone's fix) `desperation_offense`, which hardcoded
`game_state.attempt_spawn(DEMOLISHER, best, 2)` regardless of how much MP was
actually on hand, dumping the entire remainder into scouts. Both branches
share the identical *intent* ("we're out of time to conserve, spend
everything this turn and every remaining turn") — they differ only in
*which* health relationship triggers them — so there is no principled reason
for them to use a different offensive-mix policy.

**Why the corrected config makes this worse than it already was:**
`DEMOLISHER`'s MP cost dropped from 3 to 2 in the corrected config
(`docs/GAME_SPEC.md` §2.5 table). 2 demolishers is therefore only 4 MP —
at a realistic late-game MP pool (e.g. 35 MP, a plausible turn-85 total given
`bitsPerRound + bitGrowthRate*floor(turn/10)` ramping, §3 of `GAME_SPEC.md`),
that's just 11% of the budget going to demolishers no matter how much is
actually available, versus `all_in_tied_strike`'s `ALL_IN_DEMOLISHER_MP_FRACTION=0.4`
(40%) at the same budget.

**Verified via a synthetic probe** (not a real match — this branch has never
triggered in any recorded game, so there is nothing to A/B in real play): a
mocked `gamelib.GameState` built from a hand-constructed `turnInfo`/`p1Stats`
JSON payload (turn 85, `my_hp=5 < enemy_hp=20`, `MP=35`) was fed directly into
`desperation_offense`. Before the fix: `{'EI': 2, 'PI': 31}` (2 demolishers,
31 scouts — 4 MP on demolishers). After the fix: `{'EI': 7, 'PI': 21}` (7
demolishers, 21 scouts — 14 MP on demolishers), **identical to
`all_in_tied_strike`'s own output at the same MP total**, confirmed via the
same probe run against `all_in_tied_strike` directly.

**Patch applied** (`baselines/defense_v6_encryptor_fix/algo_strategy.py`,
commit `520345b`): `desperation_offense` now uses the same
fraction-of-current-MP demolisher budget as `all_in_tied_strike`, instead of
a hardcoded count.

### 8.4 Regression after the fix

Since `desperation_offense` has never triggered in any existing benchmark,
there is no real-match regression risk from this specific change by
construction — but the **full** regression suite was still re-run
end-to-end, per the standing acceptance discipline, both to confirm nothing
else broke and to fold the two new opponent batches (SUPPORT-targeted +
held-out) into the permanent suite going forward
(`experiments/run_regression.py`'s `DEFAULT_OPPONENTS` now includes all 6 new
opponents alongside the original 14):

```
FULL REGRESSION SUMMARY for baselines/defense_v6_encryptor_fix (patched)
  python-algo                              8/8   win_rate=1.0
  baselines/rush                           8/8   win_rate=1.0
  baselines/hybrid                         8/8   win_rate=1.0
  opponents/adaptive_reactive               8/8   win_rate=1.0
  opponents/burst_hoarder                   8/8   win_rate=1.0
  opponents/double_funnel_maze              8/8   win_rate=1.0
  opponents/escorted_combined_arms          8/8   win_rate=1.0
  opponents/funnel_maze                     8/8   win_rate=1.0
  opponents/lategame_defector               8/8   win_rate=1.0
  opponents/middle_rush_exploit              8/8   win_rate=1.0
  opponents/multi_lane_saturation            8/8   win_rate=1.0
  opponents/single_leak_turtle               8/8   win_rate=1.0
  opponents/sunk_cost_recipe_switcher        8/8   win_rate=1.0
  opponents/turtle_survivor                  12/12 win_rate=1.0
  opponents/support_sniper                   8/8   win_rate=1.0
  opponents/corner_lane_baiter               8/8   win_rate=1.0
  opponents/shield_race_rusher                8/8   win_rate=1.0
  opponents/signature_detector                8/8   win_rate=1.0
  opponents/minimax_lookahead                 8/8   win_rate=1.0
  opponents/predictor_opponent                8/8   win_rate=1.0
```

**172/172 games won across 20 distinct opponents, 0 crashes, 0 errors**
(`experiments/results/20260715-05*_m5_final_regression_*.jsonl`). No
regression from the patch, as expected.

## 9. Overall milestone decision and open gaps

**`baselines/defense_v6_encryptor_fix` (patched) is the new champion, tagged
`milestone5-champion`.** The patch is narrowly scoped (one method, aligning
an inconsistent hardcoded value with its sibling's already-established
fractional approach), passed the full regression suite with zero
regressions, and is honestly reported as **verified-by-code-review-and-
synthetic-probe rather than by a real-match before/after**, since no existing
or newly-built opponent in the corpus has ever driven the champion into the
health-behind-near-cap state this code handles. If a future opponent is ever
built that manages to do so, this is the first real-match data point that
would exercise `desperation_offense` at all.

**Packaged and verified the same way as Milestone 4**
(`submissions/milestone5_champion/`): `defense_v6_encryptor_fix.zip` (via the
official `scripts/zipalgo_linux`, which again strips `run.sh`'s executable
bit — the same compliance finding as Milestone 3/4, reconfirmed, not a new
bug), `defense_v6_encryptor_fix_permfix.zip` (built with system `zip`,
executable bit preserved, verified via extraction to a clean temp dir plus a
real local match against `python-algo` that ran to completion and won, 0
crashes — recommended upload artifact), and
`defense_v6_encryptor_fix_algo_folder/` (raw folder, executable bit set
directly, for portals that accept a folder instead of a zip).

**What this milestone resolved:**
- Three SUPPORT-specific hypotheses (part A) — no exploit found.
- A methodologically-independent held-out corpus of three more opponents
  (part B) — no exploit found either, meaningfully strengthening confidence
  beyond part A alone.
- The endgame policy's core ahead/tied/behind framework (part C, §8.1-8.2) —
  confirmed still functional and reachable under the corrected config via a
  direct mirror-match test, not just re-read and assumed unchanged.
- One real (if never-yet-observed-in-practice) inconsistency in
  `desperation_offense`'s offensive mix (part C, §8.3) — found via code
  review prompted by the re-check, verified via synthetic probe, fixed, and
  regression-tested.

**What remains an open gap, stated honestly:**
- `DESPERATE` mode is **entirely unverified in real play** — 0 occurrences in
  any recorded game across 5 milestones. The fix in §8.3 is sound by
  construction and by the synthetic probe, but has no real-match validation
  because the champion has never actually been in the state this code
  handles. A natural next step (not attempted this milestone, given
  diminishing returns — see the check-in response for the reasoning) would
  be to deliberately build a stronger opponent capable of putting the
  champion behind in a long game, specifically to get real-match coverage of
  this branch — but that opponent would need to be substantially better than
  anything in the current 20-opponent corpus, which is a materially bigger
  undertaking than the fix itself.
- Section 5's deferred items from part A (why `corner_lane_baiter`'s density
  asymmetry didn't redirect the lane-choice heuristic; a stronger
  SUPPORT-upgrade-timing-window opponent) remain open, unchanged.
- The standing open gaps from Milestones 3/4 (exact MP-cap ramp formula,
  timeout-damage-per-ms formula, crash-loss mechanics, all unverified from
  engine bytecode) remain open, unchanged; none of this milestone's work
  required resolving them.

`milestone1-fallback`, `milestone2-champion`, `milestone3-champion`, and
`milestone4-champion` all remain **completely untouched** as rollback
points, per the standing instruction.
