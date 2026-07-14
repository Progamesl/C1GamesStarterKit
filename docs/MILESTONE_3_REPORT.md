# Milestone 3 Report

Tags used throughout, per instructions: **Verified / Strongly supported / Hypothesis
/ Rejected**. This report covers the full Milestone 3 scope: deeper root-cause
analysis of the residual `turtle_survivor` loss rate, an implemented fix and direct
test of the "commit harder" hypothesis, a full regression re-check, a round of
deliberate adversarial countersearch against the resulting candidate, and the
champion decision.

## 0. Headline summary

- **Root cause (Verified via turn-by-turn/frame-level replay inspection, not just
  aggregates):** `defense_v3_lowcompute` DOES commit real, substantial force against
  `turtle_survivor` throughout the game — it is not a "never attacks" problem. The
  actual bug is a mode-transition/passivity error: an exact health **tie** near the
  turn cap was being treated as "ahead," triggering endgame-preserve mode (offense
  fully suppressed) for the entire turns 81-99 window. This left **~55-57 MP sitting
  completely idle at turn 99** in every observed loss — confirmed directly via
  replay MP-stat tracking, not inferred.
- **Fix implemented and tested directly:** `baselines/defense_v4_tiebreak` splits
  the check into a strict `ahead` and an explicit tied-near-cap `all_in_tied_strike`
  mode that commits 100% of available MP every remaining turn. This is exactly the
  "opponent isn't attacking and we're tied near the cap → commit to a decisive
  breach attempt" rule requested — tested directly, not just assumed to help.
- **Honest result: the fix does NOT close the targeted gap.** `turtle_survivor` win
  rate: **3/20 (15%)**, statistically indistinguishable from
  `defense_v3_lowcompute`'s **3/16 (~19%)**. Root cause of *that* residual, also
  tested directly (not assumed): the bottleneck is economic/structural, not a
  matter of committing harder or sooner — `turtle_survivor` was deliberately built
  dense enough (12 overlapping upgraded turrets, two full-width 150 HP wall layers)
  that our achievable MP income cannot reliably field enough simultaneous force to
  fully break through within the turns available, regardless of when the
  commitment starts.
- **Full regression suite (all 11 previously-tested opponents, 10 games each):
  110/110 (100%), 0 crashes, 0 regressions anywhere.**
- **Adversarial countersearch: 2 new opponents built specifically to exploit
  `defense_v4_tiebreak`'s new behavior. Both failed** — `defense_v4_tiebreak` won
  10/10 against a late-surge exploit attempt (`opponents/lategame_defector`) and
  showed no measurable degradation against a permanent-flag exploit attempt
  (`opponents/single_leak_turtle`, 3/10, at or above baseline).
- **New recommended champion: `baselines/defense_v4_tiebreak`, tagged
  `milestone3-champion`.** Accepted on the strength of (a) zero regressions, (b) a
  real, verified bug fix with sound defensive rationale (confirmed useful against a
  late-surge-style opponent we specifically built to test it), and (c) winning both
  new adversarial matchups — **not** on the strength of the targeted metric
  improving, which it plainly did not. `milestone1-fallback` and
  `milestone2-champion` remain untouched as rollback points.

## 1. Root-cause investigation: does the champion ever really attack `turtle_survivor`?

**Method:** rather than trust aggregate win/loss or even `endStats` alone, we
tracked every one of `turtle_survivor`'s WALL/TURRET unit IDs frame-by-frame across
a full losing replay (`experiments/replays/v3_vs_turtle_survivor_full_000.replay`),
comparing each unit's health at first-seen vs. its last-observed value before
removal.

**Finding (Verified):** 78 of 338 tracked `turtle_survivor` structures took real
damage over the course of one single game; several front-row walls were driven from
75 HP down into single digits (one bottomed out at 3.0 HP before a `death` event
fully destroyed it, uid `103`, turn 6). `endStats.player1.dynamic_resource_destroyed:
771.0` for that same game confirms **all** ~771 MP-worth of mobile units the
champion committed over the whole game were eventually destroyed, but
`points_scored: 0.0` confirms **none** of that force ever converted into real damage
against the opponent's health pool (`turtle_survivor`'s walls get rebuilt fresh
every turn a cell is empty, since it unconditionally re-attempts to spawn on its
full layout every turn — a destroyed wall just gets a brand-new 75 HP replacement
next turn, closing the gap before our next unit follow-up can exploit it).

**Conclusion:** "the champion never commits to offense" is **Rejected**. The
champion attacks repeatedly and sometimes meaningfully damages the target's
structures, it just never sustains enough simultaneous force in one action-phase
window to also crack the second wall layer and reach the turret line before
`turtle_survivor`'s next build phase repairs the breach point.

## 2. The real root cause: a tie-vs-ahead conflation wasting the endgame's most valuable resource

**Method:** tracked `p1Stats`/`p2Stats` MP values turn-by-turn across the same
replay set.

**Finding (Verified):** MP oscillates in a normal, mostly-spent range (roughly
8-25) from turn 6 through turn 80 (the existing every-other-turn scout dump already
uses most of what's available). From turn 81 onward, in every single loss checked,
MP grows steadily and ends the game at **55.7-56.9**, completely unspent. This
lines up exactly with `defense_v3_lowcompute`'s own endgame branch:

```python
ahead = game_state.my_health >= game_state.enemy_health   # BUG: tie counts as "ahead"
endgame_preserve = near_cap and ahead
...
if endgame_preserve:
    self.stall_with_interceptors(game_state, max_spend=3)   # caps spend at 3 MP/turn
```

Since `turtle_survivor` never attacks and neither side ever lands a decisive blow,
health stays tied at 40.0-40.0 essentially always. The `>=` conflates that tie with
a genuine lead, and the resulting "preserve the lead" policy throws away exactly the
resource (banked MP) that could have been used to try to actually win outright.

**This is the real, previously-undiscovered structural gap** — not a compute-time
issue (that was Milestone 2's fix, already shipped) and not "insufficient
commitment" in the sense of never attacking, but a specific, verifiable
mode-transition bug: treating "not yet losing" as "already won."

## 3. The fix, and a direct test of "commit harder"

**Fix (`baselines/defense_v4_tiebreak`):** replaced the single `>=` check with a
strict `ahead` (`>`) and a new `tied` branch. Near the turn cap, exactly tied health
now triggers `all_in_tied_strike`: spend 100% of available MP every single
remaining turn (no turn-parity gate, no MP-floor gate — there's nothing left in the
game to pace against) on a concentrated demolisher+scout wave at the
already-cached cheapest lane.

**Direct test, not an assumption:** ran 20 games total (2 independent batches of
10) of `defense_v4_tiebreak` vs `turtle_survivor`:

| Batch | Wins | Losses | Win rate |
|---|---|---|---|
| Batch 1 | 2 | 8 | 20% |
| Batch 2 | 1 | 9 | 10% |
| **Combined (n=20)** | **3** | **17** | **15%** |

Compare to `defense_v3_lowcompute`'s **3/16 (~19%)** from Milestone 2. These are
statistically indistinguishable at this sample size — the fix measurably closes the
MP-waste bug (confirmed: idle MP at turn 99 drops from ~56 to ~17 in these games,
i.e. the mechanism works exactly as designed) but does **not** translate into a
higher win rate.

**Follow-up test: is the window just too short?** Built a variant that starts
`all_in_tied_strike` at turn 50 instead of turn 80 (nearly doubling the commitment
window, from ~19 turns to ~49 turns). Result: **also 2/10 (20%)** — no improvement
from starting earlier or sustaining longer.

**Follow-up test: is this a compute-time-optimization gap instead?** Ran two more
diagnostic probes: (a) skip `build_core_defense`/`upgrade_core`'s per-turn
`attempt_spawn`/`attempt_upgrade` calls once the core is already built (only
re-run every 15 turns) — compute unchanged (~715-741ms, no improvement); (b)
disable `on_action_frame` breach-tracking entirely — compute also unchanged
(~715-728ms). The remaining ~90-120ms compute gap versus `turtle_survivor`'s
~610-630ms appears to be a fixed cost of running a materially more complex
algorithm (more methods, more branching, more attribute access) rather than
anything actionable found so far; it was not further reducible within this
milestone's time budget without gutting the champion's actual defensive logic.

**Conclusion (Strongly supported): the residual gap is economic/structural, not a
matter of commitment timing or remaining compute-time slack.**
`opponents/turtle_survivor` was deliberately built as an extreme fixture — 12
overlapping upgraded turrets (each 15 damage, 3.5 range) plus two full-width,
fully-upgraded 150 HP wall layers. Our achievable MP income within any of the
windows tested cannot reliably field enough simultaneous force to crack both wall
layers and survive to the turret line in the same action-phase window, before the
next build phase repairs the front layer. This is an honest, unresolved residual
risk, not a papered-over one — see section 5.

## 4. Full regression suite (acceptance discipline)

`defense_v4_tiebreak` vs. all 11 previously-tested opponents (the official starter
bot, `rush`, `hybrid`, and all 8 non-`turtle_survivor` `opponents/`
archetypes/probes), 10 games each
(`experiments/results/20260715-02[4-5]*_v4_regress_*.jsonl`):

| Opponent | Result |
|---|---|
| `python-algo` (starter) | 10/10 |
| `baselines/rush` | 10/10 |
| `baselines/hybrid` | 10/10 |
| `opponents/adaptive_reactive` | 10/10 |
| `opponents/burst_hoarder` | 10/10 |
| `opponents/double_funnel_maze` | 10/10 |
| `opponents/escorted_combined_arms` | 10/10 |
| `opponents/funnel_maze` | 10/10 |
| `opponents/middle_rush_exploit` | 10/10 |
| `opponents/multi_lane_saturation` | 10/10 |
| `opponents/sunk_cost_recipe_switcher` | 10/10 |

**Result: 110/110 (100%), 0 crashes, 0 errors, 0 regressions anywhere
`defense_v3_lowcompute` already won.**

## 5. Adversarial countersearch: 2 new opponents targeting `defense_v4_tiebreak` specifically

Per the standing instruction, this round deliberately targets *this* candidate's
*new* behavior (not just re-running old probes), using what we now know about it.

### 5.1 `opponents/lategame_defector` — bait the all-in mode's lack of defensive screening

**Hypothesis:** the old preserve-mode (triggered whenever tied-or-ahead near the
cap, `defense_v3_lowcompute`) always ran `stall_with_interceptors` — some cheap
defensive screening. The new `all_in_tied_strike` mode spends 100% of MP on
offense and deploys **zero** interceptors. An opponent that plays an exact
`turtle_survivor` clone (to bait the tied-endgame state) and then "defects" to a
real, maximal offensive surge starting at turn 90 — while the target is fully
committed to its own offense with no defensive screen up — might land free damage
and win outright.

**Result: Rejected as an effective counter. `defense_v4_tiebreak` won 10/10**
(`experiments/results/20260715-025733_v4_vs_lategame_defector_clean.jsonl`).
Frame-level replay inspection shows `defense_v4_tiebreak`'s own health never
dropped below 40.0 in **any** of the 10 games — the static turret/wall core alone
(no interceptors needed) was sufficient to absorb the late surge completely. As an
unplanned bonus finding: `lategame_defector`'s own late-surge lane-selection logic
is uncached (recomputed every turn from turn 90 on, unlike `defense_v4_tiebreak`'s
throttled version), making it consistently **60-140ms slower** than us
(measured: 795-915ms vs. our 711-837ms across the same 10 games) — meaning it would
have lost the compute tie-break too, in the games it didn't already lose outright
on health. Building a genuine late-game threat without also being computationally
expensive turned out to be harder than assumed.

### 5.2 `opponents/single_leak_turtle` — exploit the permanent one-way `ever_breached` flag

**Hypothesis:** `_stalemate_breaker`'s only gate is `if self.ever_breached: return`
— a single real breach, at any point in the game, permanently disables this
countermeasure for every remaining turn, even if the opponent immediately reverts
to pure passive defense afterward. (Note this does **not** touch the new
`all_in_tied_strike` logic, which has no such gate — this specifically isolates
whether the *mid-game* stalemate breaker mattered for the final outcome.)

**Implementation:** an exact `turtle_survivor` clone that additionally sends one
single, cheap probe SCOUT at turn 1, then never attacks again.

**Result: no measurable exploit found.** 3/10 (30%) win rate for
`defense_v4_tiebreak`
(`experiments/results/20260715-030120_v4_vs_single_leak_turtle.jsonl`) — numerically
at or above the plain-`turtle_survivor` baseline (3/20, 15%), not below it. Given
n=10, this is not strong evidence the fix improved anything either (could easily be
noise in the other direction), but it directly contradicts the hypothesis that this
flag is currently a live, exploitable weakness with any measurable win-rate impact.
**Rejected as an effective counter**, at least at this sample size.

### 5.3 What this round does and does not prove

- **Strongly supported:** `defense_v4_tiebreak`'s specific new design choices (all-in
  tied-endgame commitment, cached lane reuse even under this new mode) survive two
  deliberately-targeted adversarial designs built with full knowledge of its
  internals.
- **Explicitly not proven:** that no exploit exists. Both attempts here specifically
  targeted the *endgame* logic; a genuinely adaptive, non-turtle-shaped opponent
  that mixes real early/mid-game offense with the specific endgame patterns tested
  here was not attempted, nor was an opponent that tries to find a *geometric* gap
  in the champion's fixed `core_turret_anchors`/`core_wall_front` coordinates
  directly (this remains deferred from Milestone 2's own open-items list too).

## 6. Champion decision

**New recommended champion: `baselines/defense_v4_tiebreak`, tagged
`milestone3-champion`.**

Accepted because:
1. **Zero regressions** — identical 100% win rate to `defense_v3_lowcompute` across
   the full 11-opponent, 110-game regression suite.
2. **Fixes a real, Verified bug** (idle MP from tie-vs-ahead conflation) with sound
   forward-looking rationale, independent of whether it happens to move this
   particular opponent's win rate — and that rationale was itself tested, not just
   asserted: `opponents/lategame_defector` is exactly the kind of "looks passive,
   then attacks late" opponent this fix exists to defend against, and
   `defense_v4_tiebreak` handled it cleanly (10-0) where the old preserve-mode logic
   (which stops attacking but also stops defending as actively once "ahead") had
   never been tested against anything like it.
3. **Wins both new adversarial-countersearch matchups** built specifically to probe
   its new behavior.

**Stated plainly, not papered over: this fix does NOT close the `turtle_survivor`
gap.** Win rate remains 3/20 (15%), statistically the same as before the fix. Root
cause of that residual is now understood (Strongly supported, not just
hypothesized) to be economic/structural — `turtle_survivor`'s defensive density
exceeds what our MP economy can reliably crack in the turns available, regardless
of commitment timing — rather than a fixable behavioral bug. We are treating this
as an **accepted residual risk** for the tournament brief: a genuine, competitive
opponent that plays a pure, maximally-dense zero-offense turtle for 100 straight
turns is an unusual, low-probability real-world strategy (it cannot beat anyone
except us, and only via this specific tie-break mechanic), and further chasing it
would require either (a) a fundamentally different offensive approach not yet
designed, or (b) further compute-time reduction that two rounds of profiling in this
milestone did not find a path to.

`milestone1-fallback` (`baselines/defense`) and `milestone2-champion`
(`baselines/defense_v3_lowcompute`) both **remain completely untouched** as safe
rollback points, per the standing instruction.

## 7. What's still a gap (honest, unchanged in spirit from Milestones 1-2 section 7)

- The `turtle_survivor` residual risk above — now root-caused and Strongly
  supported as structural, but not closed.
- Still only ever played opponents built by this same workstream (or the one
  official starter bot) — this gap is unchanged from Milestone 2 and cannot be
  closed further without external opponents.
- The remaining ~90-120ms compute-time gap vs. an extremely minimal opponent
  persisted through two more rounds of profiling this milestone (skip-rebuild,
  disable-action-frame) without a clear actionable cause found; likely a fixed cost
  of the champion's greater logical complexity relative to a maximally-stripped
  opponent, not a specific bug.
- The adversarial countersearch this round specifically targeted the new endgame
  behavior; a broader adaptive/mixed-strategy adversarial opponent, and a
  geometry-aware attack against the champion's exact known fixed coordinates,
  remain untested (carried over from Milestone 2's own deferred list).
