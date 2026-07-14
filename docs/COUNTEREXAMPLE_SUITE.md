# Counterexample Suite — Adversarial Hardening Against `baselines/defense`

Per Milestone 2 step: deliberately try to build counters/exploits against our own
current champion, document each attempt (mechanism, result, realism), and only patch
if a real weakness is found. Tags: **Verified / Strongly supported / Hypothesis /
Rejected**, consistent with all other docs in this repo.

**Honesty note up front (updated after the second Milestone 2 pass):** the two
adversarial *offense* attempts in sections 1-2 below both **failed to beat
`baselines/defense`** (15-0 in both cases). Three more prior-art-derived opponents in
section 5 below *also* failed to beat it (15-0 each). But section 6
(`opponents/turtle_survivor`) **did** find a real weakness — `defense` lost **0-10**,
every single game, to a purely passive opponent, purely on the Verified compute-time
tie-break. That weakness was patched (partially — see section 6.3) and is the reason
this doc now also covers a champion change; see `docs/MILESTONE_2_REPORT.md` for the
full narrative.

## 1. Attempt 1: `opponents/middle_rush_exploit`

**Hypothesis:** `baselines/defense`'s `core_wall_front` only covers x∈[0-5] and
x∈[22-27] at y=13 (read directly from the source,
`baselines/defense/algo_strategy.py`) — the middle columns x∈[6-21] have no wall at
the front row, only a turret line set back at y=10/11/12. A mobile unit spawned in
the middle might path almost straight up with much less exposure time than one
forced along a wall corridor, similar to the "funnel/maze" mechanism our own
`opponents/funnel_maze` uses defensively (prior-art hypothesis, see
`docs/STRATEGIC_PRIOR_ART_REPORT.md` 3.4) — here applied offensively, against the
*absence* of a funnel.

**Implementation:** `opponents/middle_rush_exploit` — near-zero defense (2 corner
turrets only), spawns a SCOUT swarm straight up x≈13/14 every single turn from
turn 0, picking whichever of 4 near-middle spawn points the standard
least-damage-path heuristic currently rates cheapest.

**Result:** **Rejected as an effective counter.** 15/15 games lost to `defense`
(`experiments/results/*_defense_vs_middle_rush_exploit.jsonl`), consistently by
turn 10, 0 crashes either side. `defense`'s middle turret line (`[10,10], [13,10],
[14,10], [17,10]`, from `core_turret_anchors`) evidently provides enough overlapping
range/damage to shred a SCOUT swarm (SCOUT: 15 HP, per `docs/GAME_SPEC.md`) before
it reaches the back edge even without a wall-guided longer path — the turret count
and upgrade path apparently matter more than corridor length for this specific unit
matchup. **Hypothesis for why, not fully isolated:** several turrets simultaneously
in range of a straight-up-the-middle path likely deals more cumulative damage per
turn than the SCOUT's HP pool, regardless of exposure-time-per-tile; testing this
against a lower-HP defense or a DEMOLISHER-led version (DEMOLISHER: 5 HP, so far
more fragile per-shot, but hits back harder) was not attempted due to time and is a
natural next probe.

## 2. Attempt 2: `opponents/multi_lane_saturation`

**Hypothesis:** `defense`'s reactive-defense logic caps itself at 6 SP of rebuilding
per turn (`max_reactive_spend_per_turn`, read directly from the source). Breaching
at 3+ well-separated points in the *same* turn should force it to only partially
repair each breach location, letting damage compound turn-over-turn faster than a
single-lane attack would.

**Implementation:** `opponents/multi_lane_saturation` — near-zero defense (2 corner
turrets only), splits nearly all its MP three ways every turn from turn 2 onward
(near-left x=5, middle x=13, near-right x=22), escalating SCOUT count with available
MP, switching to a 3-way DEMOLISHER strike every 4th turn if it can afford one per
lane.

**Result:** **Rejected as an effective counter.** 15/15 games lost to `defense`
(`experiments/results/*_defense_vs_multi_lane_saturation.jsonl`), also consistently
by turn 10, 0 crashes either side. The reactive-cap hypothesis was never even
meaningfully tested in practice: `defense`'s *static* core (turrets already placed
before any breach occurs) appears to already handle a 3-way split well enough that
the reactive-rebuild layer's cap was not the bottleneck — splitting weakened this
opponent's own per-lane MP (mirroring the classic "spread thin" failure mode) more
than it stressed `defense`'s repair budget.

## 3. What sections 1-2 do and do not prove

- **Strongly supported:** across everything tested in the first Milestone 2 pass —
  the Milestone 1 round robin (120 games), the 3-archetype opponent corpus
  (45 games), and these two targeted adversarial probes (30 games) — `defense` had a
  **135-0 record across 135 total local games against 8 distinct opponents**, 0
  crashes, 0 harness errors throughout.
- **Explicitly not proven:** that `defense` is unbeatable, or that no counter
  exists. All 8 opponents were built by this same workstream (or are the one
  official starter bot); none are an independently-written, actively-competitive
  human team's algo — the same class of gap flagged in `docs/MILESTONE_1_REPORT.md`
  section 7. Sections 5-6 below close part of that gap using
  `docs/STRATEGIC_PRIOR_ART_REPORT.md`'s ranked hypotheses instead of more
  self-designed variants, and section 6 shows the gap was real: a genuinely
  different (if deliberately extreme) opponent design *did* find a weakness that 8
  self-built-or-official opponents had missed.
- **Ideas not yet tried** (explicitly deferred, not rejected): a DEMOLISHER-focused
  (not SCOUT-focused) middle rush; an attack specifically timed to hit before
  `defense`'s turret upgrades complete; a maze that specifically routes around
  `defense`'s exact known turret coordinates; and feeding `defense`'s own replay
  data into a scripted opponent that has "seen" its layout in advance.

## 5. Second pass: 3 more opponents from `docs/STRATEGIC_PRIOR_ART_REPORT.md`

Per the explicit follow-up instruction, these three specifically target prior-art
hypotheses **not** covered by the first 3-archetype corpus (`funnel_maze`,
`adaptive_reactive`, `burst_hoarder`) or the two adversarial probes above. Novelty
analysis (in our own words, as requested) and result for each:

| Opponent | Prior-art hypothesis re-derived | Genuinely novel attack surface? | Result vs `defense` |
|---|---|---|---|
| `opponents/escorted_combined_arms` | #5: cheap screen + DEMOLISHER structure-cracker, re-derived from *current* Verified unit stats (`docs/GAME_SPEC.md` 2.2), not historical ones | **Yes** — none of our other opponents stagger a screen wave one full turn ahead of a following strike group on the same lane, or pair it with a SUPPORT placement. Distinct timing mechanism from `burst_hoarder` (simultaneous burst) and `multi_lane_saturation` (simultaneous spread). | **Rejected as an effective counter.** 15/15 games lost (`experiments/results/*_defense_vs_escorted_combined_arms.jsonl`), turn ~10, 0 crashes. |
| `opponents/sunk_cost_recipe_switcher` | #3: abort a failing attack recipe instead of repeating it, using multi-turn realized-value tracking | **Yes** — this is a recipe-*level*, multi-turn decision (track breach credit over an evaluation window, switch after repeated failure), qualitatively different from the per-turn cheapest-lane heuristic every other opponent/baseline in this repo uses instead. Confirmed working as designed in a smoke test (observed it actually switch recipes after 2 consecutive failures). | **Rejected as an effective counter.** 15/15 games lost (`experiments/results/*_defense_vs_sunk_cost_recipe_switcher.jsonl`), turn ~10, 0 crashes. |
| `opponents/double_funnel_maze` | #6: a second, structurally distinct maze/path-control shape | **Partially overlapping** with `opponents/funnel_maze` in spirit (both are static wall corridors), but **structurally different**: two symmetric corridors from both flanks converging on a shared *central* kill zone, with alternating attack sides, versus one static corridor on one side only. Tests a center-of-board blind spot and lane-alternation specifically, which the single-corridor version cannot. | **Rejected as an effective counter.** 15/15 games lost (`experiments/results/*_defense_vs_double_funnel_maze.jsonl`), turn ~10-12, 0 crashes. |

All three: 0 crashes either side, consistent ~turn-10-12 losses for the attacker,
matching the pattern from section 1-2's probes — `defense`'s static core plus
reactive layer handles all of these within the first ~10 turns before any of the
new opponents' more elaborate multi-turn mechanisms (escort timing, recipe
switching, dual corridors) have a chance to matter.

## 6. `opponents/turtle_survivor` — the endgame-policy investigation found a REAL weakness

Per the Milestone 2 "health-preservation vs. damage-race" investigation: rather than
wait for a near-turn-cap board state to arise naturally (none of the ~10-20-turn
games above get anywhere close to turn 100), we built a purely passive,
zero-offense, maximal-defense test fixture (`opponents/turtle_survivor`) specifically
to force long games, as the closest available local substitute for "constructing the
relevant board state directly."

### 6.1 Result: `defense` lost 0-10, every game, at turn 99, tied 40.0-40.0 on health

`experiments/results/20260715-013634_defense_vs_turtle_survivor.jsonl` — 10/10 games
run to the Verified turn-100 cap, both players finishing with **identical** health
(40.0-40.0, i.e. neither side ever meaningfully damaged the other), and
`turtle_survivor` won *every single one*, regardless of which seat (p1/p2) it played.

### 6.2 Root cause: **Verified**, not hypothesis — the compute-time tie-break

The replay format's `endStats.playerN.total_computation_time` field (ms) gives this
directly, no inference needed:

| Match | `defense` compute (ms) | `turtle_survivor` compute (ms) |
|---|---|---|
| seat 1 | 1827 | 712 |
| seat 2 (swapped) | 1821 | 730 |

Per the Verified tie-break rule (`docs/GAME_SPEC.md` 4.3): tied health is broken by
**lower cumulative compute time**. `defense` was using ~2.5x `turtle_survivor`'s
compute across a full game and lost the tie-break every time. A throwaway diagnostic
probe (disabling `opportunistic_offense` entirely) dropped `defense`'s compute to
~618ms, matching `turtle_survivor` almost exactly — isolating
`least_damage_spawn_location`'s per-option pathfinding calls as ~95% of the excess
cost. This is a genuine weakness in `defense`'s own claimed design intent (its
docstring already claimed to be "kept computationally cheap... free insurance for
the tie-break" — this benchmark **disproves that claim** as stated; it was cheap
relative to the *time budget*, not cheap relative to *what a much simpler passive
opponent needs*.)

### 6.3 Patch: `baselines/defense_v3_lowcompute` — a real, partial fix

See the `baselines/defense_v3_lowcompute/algo_strategy.py` docstring for the full
list of 4 concrete changes (cache+throttle the lane-choice heuristic over fewer
options, hoist a repeated object construction out of a hot loop, skip a redundant
second JSON parse on the common empty-breach case, and a "stalemate breaker" that
commits real force if never breached by turn 40). Measured effect:

- Compute time vs `turtle_survivor`: **~1827ms → ~750-800ms** (turtle_survivor
  itself runs ~700-730ms) — most, not all, of the gap closed.
- Win rate vs `turtle_survivor`: **0/10 (0%) → 3/16 (~19%)** across two independent
  batches run with the identical final patch (6 games: 1 win; 10 games: 2 wins) —
  small-sample, stated honestly, but the wins are not just tie-break luck: at least
  one win was a genuine health-based win (32 vs 40 final HP) where the
  "stalemate breaker" mechanism actually broke through `turtle_survivor`'s defense.
- **Full regression check (the acceptance-discipline step): 0 regressions.**
  `defense_v3_lowcompute` still won **110/110 (100%)** across all 11 previously-
  tested opponents (the official starter bot, `rush`, `hybrid`, and all 8
  `opponents/` archetypes/probes, 10 games each) — see
  `experiments/results/20260715-0[15-20]*_v3_vs_*.jsonl`. 0 crashes anywhere.
- **Honest limitation:** this is a **partial** fix, not a complete one.
  `defense_v3_lowcompute` still loses the large majority of games against this
  specific, deliberately-extreme, zero-offense turtle fixture. We consider this an
  acceptable residual risk (see `docs/MILESTONE_2_REPORT.md` section on why) rather
  than something to keep iterating on indefinitely, given `turtle_survivor` is not a
  realistic model of a competitive human opponent (any team that never attacks
  cannot win against most opponents either, only against ours specifically, via this
  one specific tie-break quirk).

## 7. Outcome (Milestone 2)

`baselines/defense_v3_lowcompute` was **accepted as the new champion** and tagged
`milestone2-champion` (see `docs/MILESTONE_2_REPORT.md`), because it strictly
dominates `baselines/defense`: identical 100% win rate against every opponent
`defense` already beat, plus a real (if partial) improvement against the one
opponent that exposed a genuine weakness. Per the standing instruction, the
`milestone1-fallback` tag and `submissions/emergency_fallback/` package remain
**unchanged** as a safe rollback point regardless.

## 8. Milestone 3: root-causing the residual `turtle_survivor` loss rate further

Full narrative and numbers in `docs/MILESTONE_3_REPORT.md`; this section covers the
adversarial-countersearch piece specifically, in the same format as sections 1-2/5
above.

### 8.1 Root cause (Verified, turn-by-turn evidence, not just aggregates)

Direct replay inspection (frame-level unit-health tracking by `unit_id`, not just
`endStats` aggregates) of `defense_v3_lowcompute` vs `turtle_survivor` losses shows
the champion **does** mount real, substantial attacks throughout the game — several
of `turtle_survivor`'s front-row WALLs were tracked from 75 HP down into single
digits, and some were fully destroyed and rebuilt more than once
(`baselines/defense_v3_lowcompute/algo_strategy.py`'s `dynamic_resource_destroyed:
771.0` in one traced game — every bit of that 771 MP-worth of committed force was
eventually destroyed, but plenty of it did real damage first). So "never commits to
offense" is **Rejected** as the root cause.

The **Verified** root cause instead: `on_turn`'s `ahead = my_health >=
enemy_health` treats an exact tie as "ahead," entering endgame-preserve mode (all
offense suppressed, MP spent only 3/turn on interceptors) for the entire turns
81-99 window even when the game is merely tied, not won. Replay MP-stat tracking
across every checked loss shows **~55-57 MP sitting completely idle at turn 99** as
a direct result — a large, wasted resource at exactly the point where it would
matter most.

### 8.2 Fix and direct test of the "commit harder" hypothesis

`baselines/defense_v4_tiebreak` splits the check into strict `ahead` (`>`) and an
explicit tied-near-cap `all_in_tied_strike` mode (commits 100% of available MP,
every turn, no gating) — directly testing the requested hypothesis: "opponent isn't
attacking and we're tied near the cap → commit to a decisive breach attempt."

**Result: the hypothesis is Rejected as sufficient, even though the mechanism it
targets is real.** Confirmed via replay MP tracking that the fix works exactly as
designed (idle MP at turn 99 drops from ~56 to ~17 when this mode engages), and
confirmed via two further variants (moving the all-in threshold from turn 80 to
turn 50, i.e. nearly doubling the commitment window) that win rate against
`turtle_survivor` does **not** improve with more turns of commitment either (2/10
at turn-80 threshold, 2/10 at turn-50 threshold — same rate). The bottleneck is
economic/structural, not a matter of committing sooner or harder: `turtle_survivor`
was deliberately built with 12 overlapping upgraded turrets plus two full-width
150 HP wall layers, and our MP income within any realistic window cannot reliably
field enough simultaneous force to punch all the way through that specific,
deliberately-extreme density. See `docs/MILESTONE_3_REPORT.md` section 2 for the
full numeric trail.

### 8.3 Adversarial countersearch: 2 new opponents built to exploit `defense_v4_tiebreak` specifically

| Opponent | Targeted weakness | Result vs `defense_v4_tiebreak` |
|---|---|---|
| `opponents/lategame_defector` | The new `all_in_tied_strike` mode spends 100% of MP on offense and **zero** on defensive interceptors — unlike the old preserve-mode it replaced. Plays an exact `turtle_survivor` clone to bait this mode, then defects to a real maximal scout/demolisher surge from turn 90 onward, aiming to land free damage while we're not screening. | **Rejected as an effective counter — 10/10 lost by the attacker (0-10 for `lategame_defector`, `experiments/results/*_v4_vs_lategame_defector_clean.jsonl`).** `defense_v4_tiebreak`'s own health never dropped below 40.0 in any of the 10 games — the static turret/wall core alone was sufficient without interceptor screening. As a bonus, `lategame_defector`'s late-surge pathfinding is uncached (unlike ours), making it 60-140ms *slower* than us in every single game measured — it loses the compute tie-break too, in the ties it didn't lose outright on health. |
| `opponents/single_leak_turtle` | `ever_breached` is a permanent, one-way flag; a single real breach anywhere, anytime, disables the `_stalemate_breaker` (turns 40-80) for the rest of the game, forever, even if the opponent immediately reverts to pure turtle play. | **No measurable exploit found.** A single cheap probe SCOUT at turn 1, then an exact `turtle_survivor` clone for the rest of the game: **3/10 (30%)** win rate for us — numerically at or above the plain-`turtle_survivor` baseline (3/20, 15%), not below it, though n=10 is too small to call this a real improvement rather than noise. Directionally, no evidence this specific flag is currently exploitable. |

Both countersearch attempts **failed** to find a new exploitable regression in
`defense_v4_tiebreak`. This is an honest negative result for the adversarial round,
not a claim that no exploit exists anywhere in the design — see
`docs/MILESTONE_3_REPORT.md` section 4 for what remains untested.

## 9. Outcome (Milestone 3)

`baselines/defense_v4_tiebreak` is **accepted as the new champion** and tagged
`milestone3-champion`: 0 regressions across the full 11-opponent suite (110/110),
plus it wins both new adversarial-countersearch matchups built specifically against
it. It fixes a real, verified bug (idle MP from a tie-vs-ahead conflation) with
sound defensive rationale even though — stated plainly, not papered over — it does
**not** close the targeted `turtle_survivor` gap: win rate stayed at 3/20 (15%),
statistically indistinguishable from `defense_v3_lowcompute`'s 3/16 (~19%).
`milestone1-fallback` and `milestone2-champion` both remain **unchanged** as safe
rollback points.
