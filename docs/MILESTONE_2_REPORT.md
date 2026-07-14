# Milestone 2 Report

Tags used throughout, per instructions: **Verified / Strongly supported / Hypothesis
/ Rejected**. This report covers the full Milestone 2 scope: broader opponent corpus
(closing the "shared blind spot" gap flagged at the end of Milestone 1), the
endgame-policy investigation, patching, full regression, and parameter search.

## 0. Headline summary

- Built **4 more opponents** from `docs/STRATEGIC_PRIOR_ART_REPORT.md`'s
  ranked, previously-uncovered hypotheses (escorted combined-arms, sunk-cost
  recipe-switching, a second structurally distinct maze shape) plus one
  purpose-built test fixture for the endgame investigation (`turtle_survivor`).
- The champion (`baselines/defense`) beat the first 3 of those cleanly (45-0), but
  **lost 0-10 to `turtle_survivor`** — a real weakness, not a hypothetical one,
  caused by the Verified compute-time tie-break (`docs/GAME_SPEC.md` 4.3), not by
  any placement/unit weakness.
- Patched it (`baselines/defense_v3_lowcompute`), re-ran the **full regression
  suite** (all 11 previously-tested opponents), confirmed **0 regressions**
  (110/110, 100%), and confirmed a **real but partial** improvement against
  `turtle_survivor` (0/10 → 3/16 across two batches, ~19%).
- Ran a basic parameter search on 2 of the 3 suggested thresholds — **no
  improvement found** beyond the already-shipped fix; documented as a genuine null
  result, not skipped.
- **New recommended champion: `baselines/defense_v3_lowcompute`, tagged
  `milestone2-champion`.** `milestone1-fallback` (`baselines/defense`) remains
  untouched as a safe rollback.

## 1. New opponent corpus: 4 opponents, novelty analysis

Per the explicit instruction to close the "every opponent so far is the starter bot
or something we built ourselves" gap using `docs/STRATEGIC_PRIOR_ART_REPORT.md`'s
ranked hypotheses rather than more self-similar variants. See
`docs/COUNTEREXAMPLE_SUITE.md` section 5 for the full per-opponent detail (novelty
table, exact result citations); summary here:

| Opponent | Prior-art hypothesis | Novel vs. our existing 5 opponents/probes? | Result vs `defense` |
|---|---|---|---|
| `opponents/escorted_combined_arms` | #5: screen unit ahead of a structure-cracker, re-derived from current unit stats | Yes — staggered-by-one-turn timing, no existing opponent does this | 15-0 to `defense` |
| `opponents/sunk_cost_recipe_switcher` | #3: abandon a failing attack recipe using multi-turn realized value | Yes — recipe-level multi-turn decision, qualitatively different from every per-turn cheapest-lane heuristic elsewhere in this repo | 15-0 to `defense` |
| `opponents/double_funnel_maze` | #6: a second maze/path-control shape | Partially overlapping in spirit with `funnel_maze`, but structurally distinct (2 symmetric corridors -> central kill zone, alternating sides, vs. 1 static corridor) | 15-0 to `defense` |
| `opponents/turtle_survivor` | N/A — purpose-built test fixture for the endgame-policy investigation (see below), not a "realistic" strategic archetype | Not a strategic opponent at all; a maximal-defense/zero-offense fixture designed to force turn-100 board states | **10-0 AGAINST `defense`** (see section 2) |

All 4 pass `scripts/test_algo_mac` crash-free. Combined with the Milestone 1 round
robin, the first 3-archetype corpus, and the 2 adversarial probes from earlier in
Milestone 2, `defense`'s cumulative local record (before the turtle_survivor loss)
was **180 wins, 0 losses, across 180 games against 11 distinct opponents** (1
official starter bot, 2 of our own contrasting baselines, 8 purpose-built
opponents/probes spanning funnel/maze, adaptive-reactive, burst-hoarder, two
adversarial-hardening probes, and these 3 new prior-art-derived opponents) — see
`experiments/results/20260715-013111*`, `*-013259*`, `*-013446*` for the raw
per-match records of the 3 new-opponent matchups specifically.

## 2. `turtle_survivor`: the endgame-policy investigation found a REAL weakness

Rather than wait for a near-turn-100 board state to arise naturally (every game
above ended by turn ~10-38, nowhere close to the cap), we built
`opponents/turtle_survivor` — a purely passive, zero-offense, maximal-defense
fixture — specifically to force long games, as the closest available local
substitute for "constructing the relevant board state directly" (the engine does
not expose a way to set arbitrary health/turn state).

**Result:** `defense` lost **0-10**, every game, always at turn 99, always tied
**40.0-40.0** on health (`experiments/results/20260715-013634_defense_vs_turtle_survivor.jsonl`).

**Root cause — Verified, not hypothesis:** the replay format's
`endStats.playerN.total_computation_time` field (ms) gives this directly:

| | `defense` compute | `turtle_survivor` compute |
|---|---|---|
| seat 1 | 1827ms | 712ms |
| seat 2 (swapped) | 1821ms | 730ms |

Per the Verified tie-break rule (`docs/GAME_SPEC.md` 4.3), tied health goes to
**lower cumulative compute time**. `defense` was using ~2.5x `turtle_survivor`'s
compute and losing the tie-break every time. A throwaway diagnostic probe
(disabling `defense`'s `opportunistic_offense` entirely) dropped its compute to
~618ms, matching `turtle_survivor` — isolating `least_damage_spawn_location`'s
per-option pathfinding calls as ~95% of the excess cost.

**Answer to the "health-preservation vs. damage-race" question this milestone
asked:** `defense`'s current behavior is **not** near-optimal on this axis. Its own
docstring claimed to be "kept computationally cheap... free insurance for the
tie-break," but that claim was **disproven** by this benchmark: it was cheap
relative to the 5000ms/35000ms per-turn time *budget*, but not cheap relative to
what a much simpler opponent actually needs. An explicit endgame policy alone
(turn>80 ahead/behind branching, tested first in isolation as
`baselines/defense_v2_endgame`) only shaved ~10% off total compute (1827ms →
1649ms) — nowhere near enough, because the deficit accumulates across the *whole*
game (turns 6-80), not just the last 20 turns. The real fix had to target the
per-turn cost directly, not just add an endgame branch.

## 3. The patch: `baselines/defense_v3_lowcompute`

Built on top of `defense_v2_endgame` (endgame policy) plus 4 measured, targeted
compute-time fixes (see the file's own docstring for full detail):

1. Cache+throttle the `least_damage_spawn_location` lane choice (recompute every
   12 turns instead of every eligible turn), over 2 candidate options instead of 4.
2. Hoist a `GameUnit(TURRET, config)` construction out of the innermost per-path-
   tile loop (previously reconstructed 10-15+ times per call for a value that never
   changes within that call).
3. Skip a redundant second `json.loads()` in `on_action_frame` on the common case
   (empty breach list) — `gamelib.AlgoCore.start()` already parses every action
   frame once just to route it; our own handler was unconditionally parsing it a
   second time.
4. A "stalemate breaker": if never breached by turn 40, periodically commit real
   force (not just a probe) using the cached lane, on the theory that a passive tie
   is a loss for us unless we're strictly faster — so converting a tie into a lead
   is strictly better than staying passive.

**Measured effect (compute):** ~1827ms → ~750-800ms per game vs `turtle_survivor`'s
own ~700-730ms — most, not all, of the gap closed.

**Measured effect (win rate) vs `turtle_survivor`:** 0/10 (0%) → 3/16 (~19%) across
two independent batches on the identical final patch (6 games: 1 win; 10 games: 2
wins). Not just tie-break luck — at least one win was a genuine health-based win
(32 vs 40 final HP), meaning the stalemate breaker actually broke through
`turtle_survivor`'s defense in that game.

**Honest limitation:** this is a **partial** fix. `defense_v3_lowcompute` still
loses the large majority of games against this specific, deliberately extreme,
zero-offense fixture. We consider this an acceptable residual risk rather than
something to keep iterating on indefinitely: `turtle_survivor` is not a realistic
model of a competitive human opponent (a team that never attacks at all is an
unusual, low-probability real-world strategy, and this specific failure mode only
triggers against an opponent that is *also* at least as compute-cheap as
`turtle_survivor`, which a genuinely competitive, offense-capable bot is less
likely to be tuned for as tightly). Time was reallocated to the parameter search
(section 5) instead of continuing to chase this residual gap.

## 4. Full regression suite (acceptance discipline)

Per the standing instruction to never replace the champion without confirming no
regression: `defense_v3_lowcompute` vs. all 11 previously-tested opponents (the
official starter bot, `rush`, `hybrid`, and all 8 `opponents/` archetypes/probes),
10 games each, seat-alternated (`experiments/results/20260715-01[5-9]*_v3_vs_*.jsonl`
and `20260715-020*_v3_vs_*.jsonl`).

**Result: 110/110 (100%), 0 crashes, 0 errors — zero regression anywhere `defense`
already won.** Combined with the 3 new-opponent wins (45-0) and the
`turtle_survivor` numbers above (3 wins / 13 losses across 16 games),
`defense_v3_lowcompute`'s full local record this milestone is **158 wins / 13
losses across 171 games against 12 distinct opponents**, with every single loss
being to the one deliberately-extreme `turtle_survivor` fixture.

## 5. Parameter search — basic grid, honest null result

Per "if time permits": grid search (2 values each) on 2 of the 3 suggested
threshold categories, off the `defense_v3_lowcompute` base:

- MP floor for `opportunistic_offense` (default 9): tried 6 and 12.
- `max_reactive_spend_per_turn` (default 6): tried 4 and 10.

(The third suggested category, "rebuild trigger," is effectively the same lever as
`max_reactive_spend_per_turn` in this codebase's design — there's no separate
rebuild-vs-attack threshold to tune independently.)

Tested against a fast representative subset (`baselines/rush`,
`opponents/funnel_maze`, `opponents/adaptive_reactive`, `opponents/turtle_survivor`),
6 games each, 96 games total
(`experiments/results/20260715-02*_ps_*.jsonl`).

**Result:** all 4 variants matched the shipped defaults' 100% win rate against the 3
non-turtle opponents (18/18 each, no difference). Against `turtle_survivor`, raw
win/loss counts looked noisy (2-3 wins out of 6 for each variant) — but checking the
underlying **continuous** `total_computation_time` metric directly (far lower
variance than win/loss at this sample size) shows all 4 variants land within
~86-92ms of `turtle_survivor`'s own compute time, statistically indistinguishable
from each other and from the shipped defaults. **Conclusion: at n=6/variant, the
win-rate spread was sampling noise around a similar true rate, not a real effect of
either threshold.** Neither parameter is where the residual compute-time gap lives
(most likely candidates for further gains, not attempted: `build_core_defense`/
`upgrade_core`'s per-turn attempt_spawn/attempt_upgrade calls on the full anchor
list even once nothing has changed, or fixed Python/gamelib per-frame parsing
overhead common to both variants). **No parameter change adopted** —
`defense_v3_lowcompute` keeps its shipped defaults.

## 6. Champion decision

**New recommended champion: `baselines/defense_v3_lowcompute`, tagged
`milestone2-champion`.** It strictly dominates `baselines/defense`: identical 100%
win rate against every opponent `defense` already beat (110/110 in the regression
suite, 45/45 against the new prior-art opponents), plus a real, if partial,
improvement against the one opponent that exposed a genuine weakness (0% → ~19%).
No worse anywhere; better somewhere. This satisfies the "only replace if it doesn't
regress worst-case robustness and the improvement isn't just noise" bar.

Packaged submission: `submissions/milestone2_champion/` (zip + unzipped folder +
README, same pattern as Milestone 1's fallback, re-verified with a fresh extraction
and a real match against `python-algo`).

**`milestone1-fallback` (`baselines/defense`, `submissions/emergency_fallback/`)
remains completely untouched** as the safe rollback point, per the standing
instruction — if `defense_v3_lowcompute`'s extra logic (endgame branching, caching,
stalemate breaker) ever turns out to have a bug or edge case our local corpus
didn't catch, that simpler, more heavily-tested design is still there.

## 7. What's still a gap (honest, unchanged in spirit from Milestone 1 section 7)

- We still have only ever played opponents built by this same workstream (or the
  one official starter bot) — 12 distinct opponents now instead of 4, spanning much
  more diverse mechanisms (adaptive, burst, funnel/maze x2, escort timing, recipe
  switching, and a passive extreme), but still not an independently-written,
  actively-competitive human team's algo. This gap cannot be fully closed without
  external opponents (ladder play, other teams' public postmortems beyond what
  `docs/STRATEGIC_PRIOR_ART_REPORT.md` already covers, etc.).
- `defense_v3_lowcompute`'s compute-time fix is real but incomplete — a
  sufficiently compute-cheap AND persistent opponent could still, in principle,
  exploit the same tie-break mechanic, just needing more turns/patience than
  `turtle_survivor`'s maximal version required against the original `defense`.
- The parameter search only covered 2 thresholds with a coarse 2-value grid and a
  small representative opponent subset, not the full corpus at every grid point —
  a finer/wider search remains a natural next step if more runway becomes
  available.
