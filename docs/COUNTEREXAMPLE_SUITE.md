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

## 10. Milestone 4->5: adversarial countersearch specifically against `defense_v6_encryptor_fix`'s SUPPORT logic

`docs/MILESTONE_4_REPORT.md` section 6 flagged an honest gap: the Milestone 4
champion's new SUPPORT (Encryptor) placement/upgrade behavior had never been
adversarially countersearched the way `defense_v4_tiebreak` was in section 8
above. This section closes that gap. Full analysis and numbers in
`docs/MILESTONE_5_REPORT.md`; this section covers the three new opponents in
the same per-attempt format as sections 1-2/5/8.3 above.

| Opponent | Targeted weakness (read directly from `defense_v6_encryptor_fix`'s source) | Result vs `defense_v6_encryptor_fix` |
|---|---|---|
| `opponents/support_sniper` | SUPPORT is the single most fragile structure type in the corrected config (30 HP, vs WALL 40/TURRET 75) and sits at a fixed, adaptively-detectable location. Scans `game_state.game_map` for enemy SUPPORT (same technique as `adaptive_reactive`/`escorted_combined_arms`), then sends escorted scout+demolisher waves at the detected column from turn 3 onward, sustained for the whole game. | **Rejected as an effective counter — 10/10 games lost by the attacker** (`experiments/results/20260715-033657_m5_v6fix_vs_support_sniper.jsonl`), consistently by turn 8-10, 0 crashes. Replay inspection (`m5_v6fix_vs_support_sniper_000.replay`): SUPPORT was present in only 128/835 frames and its recorded health never dropped below its full 30 HP in any frame — not because it survived heavy fire, but because these games resolve so fast (turn 8-10) that the champion's static core defense decides the outcome before the SUPPORT mechanism (or the sniping attempt against it) ever gets meaningfully exercised either way. |
| `opponents/corner_lane_baiter` | The champion's own `_get_cached_lane`/`least_damage_spawn_location` heuristic has **zero awareness of the SUPPORT's shield radius** — it only minimizes projected turret damage along the path. SUPPORT sits at `[[13,9],[14,9]]`; the alternate lane option `[3,10]` is `sqrt(10^2+1^2)≈10.05` tiles away, outside even the upgraded 7-tile shield range. Pure static defense (no offense), deliberately dense across the center columns (x∈[6,21], where `[13,0]`'s path runs) and deliberately weak at the corners (where `[3,10]`'s path runs), to try to bait the heuristic into consistently picking the corner lane and never collecting the shield bonus. | **Rejected as tested — hypothesis about the mechanism is real, but this specific opponent design did not trigger it.** 10/10 games won by the champion, every single one ending at exactly turn 72, health 30.0 vs -2.0 (`experiments/results/20260715-033811_m5_v6fix_vs_corner_lane_baiter.jsonl`). Direct replay evidence (not inference): **936 `shield` events fired over the course of the game**, all from the SUPPORT pair at `[13,9]`/`[14,9]` onto scouts near `[14,2]`/`[15,3]` — i.e. the champion's offense kept using the *central* lane the entire game despite the deliberately asymmetric defense, so the SUPPORT bonus (`6.7` HP/unit, matching the Verified upgraded formula `4.0 + 0.3*9`) was applied continuously, not avoided. Running the identical opponent against the control (`defense_v4_tiebreak`/`m4_v4carry`) produced the **exact same 936 shield events** and the **exact same 30.0/-2.0 result in all 10 games** (`experiments/results/20260715-034234_m5_v4carry_vs_corner_lane_baiter.jsonl`) — confirming `v4carry`'s own (unupgraded, un-relocated) SUPPORT at `[13,3]` also shields the same central-lane scouts, just for less (`2.0` HP/unit, no `shieldBonusPerY` since never upgraded). The champion's lane choice was not redirected by this design; why the denser center didn't score worse than the sparser corner in the heuristic's own path-damage sum was not further isolated (an honest open sub-question, not resolved here). |
| `opponents/shield_race_rusher` | SUPPORT upgrades strictly last in `upgrade_core`, after all 10 turret anchors and 12 wall cells — a real (if unverified until now) upgrade-timing window where it sits at weaker unupgraded stats. A real (not minimal) defense of its own, paired with a *sustained* (not one-off) central-lane rush starting turn 3, to maximize exposure to this window via a non-adaptive, "dumb but persistent" mechanism, as a cross-check on `support_sniper`'s more targeted approach. | **Rejected as an effective counter — 10/10 games lost by the attacker** (`experiments/results/20260715-033953_m5_v6fix_vs_shield_race_rusher.jsonl`), by turn 12-14, 0 crashes. Replay inspection (`m5_v6fix_vs_shield_race_rusher_000.replay`): SUPPORT present in 249/898 frames, health never below full 30, **zero shield events fired all game** — again, the match resolves (via the champion's static core alone) before the SUPPORT mechanism has enough turns to engage in either direction. The control (`v4carry`) produced statistically indistinguishable margins on the same opponent (`experiments/results/20260715-034422_m5_v4carry_vs_shield_race_rusher.jsonl`) — turn counts and health margins overlap within the noise expected from the interceptor-placement randomness both share, no systematic gap either way. |

**Honest overall verdict for this section: no exploitable weakness found.**
All three purpose-built opponents lost 10/10 (or, for `corner_lane_baiter`,
"won" 0/10 in the sense of never even redirecting the champion's lane
choice), 0 crashes anywhere, in both p1/p2 seats. Per the standing acceptance
discipline, this is a genuine negative result, not proof the design is
flawless: it means three specific, reasoned, adaptively-built attack
mechanisms (direct structural sniping, lane-routing baiting, sustained
timing-window pressure) did not find a regression relative to
`defense_v4_tiebreak`, under real n=10-per-opponent sampling in both seats —
see `docs/MILESTONE_5_REPORT.md` section 4 for what remains untested. (This
verdict is about the SUPPORT-targeted countersearch specifically — see
sections 11-12 below for two further checks done in the same milestone, one
of which *did* find and fix something.)

## 11. Milestone 5: held-out corpus check (opponents built blind, not derived from `defense_v6_encryptor_fix`'s code)

Full rationale in `docs/MILESTONE_5_REPORT.md` section 7. Three opponents
were built strictly from unimplemented archetypes in
`docs/STRATEGIC_PRIOR_ART_REPORT.md`, without referencing the champion's
source, specifically to check that section 10's "no exploit found" wasn't an
artifact of only ever testing SUPPORT-shaped attacks against a SUPPORT-shaped
countersearch.

| Opponent | Archetype (never previously implemented in `opponents/`) | Result vs `defense_v6_encryptor_fix` (n=10, both seats) |
|---|---|---|
| `opponents/signature_detector` | §3.5 signature detection + counter-strategy switching: tracks the champion's mobile-spawn pattern; a repeated pattern for `SIGNATURE_THRESHOLD` turns triggers a reinforce-and-counter-attack switch. | **10/10 champion**, 0 crashes, turns 12-34 (`experiments/results/20260715-040040_m5_heldout_v6fix_vs_signature_detector.jsonl`). |
| `opponents/minimax_lookahead` | §3.2 turn-level simulation/minimax lookahead: scores several candidate recipes per turn (MP efficiency, projected path damage, unspent-SP value) and plays the best-scoring one, under an explicit 400ms time budget. | **10/10 champion**, 0 crashes, turns pinned at 18 (deterministic given its fixed recipe set; seat-swap is the only variation) (`experiments/results/20260715-050241_m5_heldout_v6fix_vs_minimax_lookahead.jsonl`). |
| `opponents/predictor_opponent` | §3.7 opponent-move prediction: detects a recurring spawn pattern at a consistent turn-offset (every 2/3/4 turns) and preemptively reinforces the predicted side *before* the champion's move that turn, rather than reacting after the fact. | **10/10 champion**, 0 crashes, turns 18-70 — the widest/most varied matchup in the whole corpus (`experiments/results/20260715-050359_m5_heldout_v6fix_vs_predictor_opponent.jsonl`). |

One implementation bug was caught and fixed before benchmarking:
`signature_detector` and `predictor_opponent` both initially misread
`on_action_frame`'s raw per-unit `player_index` (1-indexed, 1=self/2=opponent
— confirmed against `python-algo/algo_strategy.py`'s own handling of the same
field) as if it used `GameUnit.player_index`'s 0=self/1=enemy convention,
causing both opponents to track their own spawns instead of the champion's.
Fixed to `if player_index != 2: continue` in both files.

**Honest verdict: no exploit found.** All three held-out opponents lost
10/10, 0 crashes, real and sometimes long/varied games (not instant losses
regardless of play) — meaningfully strengthens confidence beyond section 10
alone, since this is a second, methodologically-independent batch that also
failed to find a weakness, though it is still not proof of invulnerability.

## 12. Milestone 5: endgame policy re-check under the corrected config — one real fix found

Full analysis in `docs/MILESTONE_5_REPORT.md` section 8. Unlike sections
10-11, this check **did** find something real, though narrow: the
`all_in_tied_strike`/`desperation_offense`/`ENDGAME_TURN_THRESHOLD` logic was
carried over unchanged from before the config correction and had never been
re-verified against the corrected numbers.

- **The ahead/tied/behind framework and `ALL_IN_TIED` mode are Verified still
  functional and reachable** under the corrected config — direct proof via a
  controlled mirror-match test (`defense_v6_encryptor_fix` vs itself, n=6,
  `experiments/results/20260715-050822_m5_endgame_mirror_match.jsonl`): 6/6
  games reached an exact 14.0-vs-14.0 tie at turn 100, `ALL_IN_TIED` engaged
  for all 19 endgame turns on both sides, 0 crashes, decided by the
  compute-time tie-break (p1 376ms vs p2 500ms cumulative) — consistent with
  section 6.2's tie-break finding, now reconfirmed under the new config.
- **But against every actual opponent in the corpus (5 distinct long-game
  opponents, dozens of games across all milestones), only `NORMAL` and
  `PRESERVE` ever appear near the cap — never `ALL_IN_TIED`, never
  `DESPERATE`.** This is a real, config-driven change from Milestone 3's
  finding (exact ties were the *dominant* outcome against `turtle_survivor`
  under the old config); under the corrected config the champion instead
  ends up strictly and heavily ahead in the same matchups. Not a bug — a
  change in which matchups actually produce a tie.
- **The real finding:** `desperation_offense` hardcoded "spawn exactly 2
  demolishers, dump the rest on scouts," while its sibling
  `all_in_tied_strike` (identical "spend everything" intent, different
  trigger condition) budgets a *fraction* of current MP
  (`ALL_IN_DEMOLISHER_MP_FRACTION=0.4`) for demolishers instead. The
  corrected config's cheaper `DEMOLISHER` (MP cost 3->2) makes the hardcoded
  count an even smaller, more arbitrary share of a realistic late-game MP
  pool than before (4 MP out of a sampled 35 MP budget = 11%, vs
  `all_in_tied_strike`'s 40% at the same budget). **This branch has never
  triggered in any recorded game across 5 milestones** (0 real losses have
  ever reached turn 78), so verification was done via a synthetic
  mocked-`GameState` probe rather than a real-match before/after: before the
  fix, `MP=35` produced `{'EI': 2, 'PI': 31}`; after, `{'EI': 7, 'PI': 21}` —
  identical to `all_in_tied_strike`'s own output at the same MP total.
- **`PRESERVE` mode's conservatism was checked and found still appropriate**:
  every observed `PRESERVE` engagement has `my_hp` pinned at the full 30 HP
  starting value against an opponent already near-dead — an already-maximal,
  secured lead, not a marginal one a more aggressive policy might improve.
- **Patch applied** (commit `520345b`): `desperation_offense` now uses the
  same fraction-of-MP demolisher budget as `all_in_tied_strike`. **Full
  20-opponent regression re-run after the fix (the original 14 plus all 6
  new opponents from sections 10-11, now folded permanently into
  `experiments/run_regression.py`'s `DEFAULT_OPPONENTS`): 172/172 games won,
  0 crashes** (`experiments/results/20260715-05*_m5_final_regression_*.jsonl`).

**Honest open gap:** `DESPERATE` mode (the "behind" counterpart to
`ALL_IN_TIED`) remains **entirely unverified in real play** — 0 occurrences
in any recorded game ever, because the champion has never actually lost a
game reaching turn 78. The fix above is sound by code-review and the
synthetic probe, not by real-match evidence, since no real match exercises
this branch.

**Champion updated as a result of this section: `baselines/defense_v6_encryptor_fix`
(patched) is now tagged `milestone5-champion`.** `milestone1-fallback`,
`milestone2-champion`, `milestone3-champion`, and `milestone4-champion` all
remain **completely unchanged** as safe rollback points.

## 13. Milestone 6: genuinely independent, publicly-sourced opponents — a REAL, currently-unpatched loss found

Everything in sections 1-12 above, however methodologically varied, is
**self-built**: every opponent was designed, written, and tuned by this same
project. Full detail (sourcing, vetting, root-cause, patch attempts) is in
`docs/MILESTONE_6_REPORT.md`; this section is the counterexample-suite-style
summary, kept consistent with the format of sections 1-12.

**5 real, substantial, non-stub Terminal python-algo bots were found on
public GitHub repos, vetted, and run unmodified as local black-box test
opponents** (never copied/adapted into our own code — see
`docs/COMPLIANCE_REPORT.md` §7 for sourcing/license notes):

| Opponent | Source | Result vs. `milestone5-champion` |
|---|---|---|
| `public_opponents/skill_issue_final3gem` | Real team, 3rd-place claim, "Citadel Terminal Competition" Mar 2026 | WON 20/0 |
| `public_opponents/travelling_salesmen_adapdef` | Real team, "#1 spot at Harvard" repo claim (this specific iteration is mostly unmodified starter-kit boilerplate — see correction below) | WON 20/0 |
| `public_opponents/travelling_salesmen_frumblesnatch` | Same repo, different iteration | WON 19/20 |
| **`public_opponents/travelling_salesmen_v33`** (self-declared "Snorkeldink-V69") | Same repo — this is the actual most-evolved iteration, and the one whose mechanism (continuous, un-paused, single-lane Demolisher rush) plausibly *is* what won at Harvard | **LOST 0/20, both seats, no crashes** |
| `public_opponents/davidw0311_mcts` | Real 971-line MCTS bot, no placement claim | WON 20/0 |

**Correction made and logged transparently, not buried**: an initial pass
assumed `AdapDef` (the more official-sounding folder name) was this team's
strongest/final algo and benchmarked only that one, recording a clean win.
Deeper inspection (reading — not just naming — every iteration) found
`AdapDef` actually retains large amounts of unmodified starter-kit
boilerplate and never fixed a resource-discipline bug present in earlier
iterations. `snorkeldink-v3-3` (renamed `travelling_salesmen_v33` in this
repo), whose own docstring self-declares `"the final version of
Snorkeldink-V69,"` is the actual strongest iteration — and it is the one
that beats us.

### 13.1 Root cause (Verified, turn-by-turn replay evidence)

`travelling_salesmen_v33`'s mechanism: adaptively pick whichever of our two
halves looks weaker (Wall+Turret count), then commit **100% of MP to
Demolishers at that one lane, every single turn from turn 4 onward, forever
— no bursting, no pausing.** Our `core_turret_anchors` places single TURRETs
directly on the two extreme board corners, which are themselves valid
scoring edge tiles (`gamelib.GameMap.get_edge_locations`). A freshly
rebuilt, full-HP TURRET there is killed again in the *same turn* it's
rebuilt by 3+ simultaneous Demolishers converging (Verified: matching
spawn/death unit IDs within one turn's event log), and the diamond board's
geometry means there is no tile physically "behind" the extreme corner to
retreat to (Verified via `gamelib.GameMap.in_arena_bounds`). Once that
corner is reliably undefended, every subsequent wave breaches directly for
player-health damage — accelerating as the opponent's MP economy ramps up
over the game (`bitRampBitCapGrowthRate`), while our SP-funded rebuild
budget does not compound at a comparable rate.

### 13.2 Patch attempts: 5 tried, all honestly reported, none fully closed the gap

Unlike every prior section in this document, **this is a case where a real
weakness was found and root-caused, but could not be fixed within this
milestone's effort** — reported here exactly that plainly, per this
project's standing discipline of never forcing an unproven fix just to avoid
reporting an open gap:

1. 2nd TURRET layer at `[2,11]`/`[25,11]` — delayed to turn ~43, still 0/20.
   Rejected on inspection: those tiles are themselves also scoring edges.
2. 2nd TURRET layer at `[3,11]`/`[24,11]` (confirmed true depth, off the
   scoring edge) — delayed to turn ~38, still 0/20.
3. Attempt 2 + reactive-defense SP cap raised 6→24 — **identical** result to
   attempt 2 (SP cap was not the actual bottleneck).
4. Attempt 2 (cap=14) + new MP-funded counter-offense triggered by evidence
   of sustained incoming damage — `points_scored` improved 1.0→5.0, still a
   decisive 0/12 loss.
5. Corner TURRETs replaced with cheaper WALLs (absorb hits more cheaply) +
   depth TURRETs for kill power + attempt 4's counter-offense — no further
   improvement, still 0/12.

Kept in the repo as `baselines/defense_v9_corner_depth`, clearly documented
as a tested-and-rejected candidate (same convention as
`defense_v7_range_leverage`/`defense_v8_offense_burst`) — **not adopted, not
deleted.**

### 13.3 Full regression (no regressions found anywhere else)

`experiments/run_regression.py`'s `DEFAULT_OPPONENTS` permanently extended
with all 5 independent opponents. Full run for
`baselines/defense_v6_encryptor_fix`: **all 20 self-built opponents still
100% (no change from Milestone 5), 4/5 independent opponents 100%, 1/5
(`travelling_salesmen_v33`) 0% — the one known, open loss, kept permanently
in the suite rather than silently excluded.** Full log:
`/tmp/m6_full_regression.log`.

### 13.4 Outcome (Milestone 6)

**Champion unchanged: `baselines/defense_v6_encryptor_fix`, tagged
`milestone5-champion`, remains the champion.** No new tag cut. This is the
single most important open finding in this project — a real, publicly
sourced, plausibly-competition-relevant opponent beats our champion cleanly
and repeatably, and we do not yet have a working fix. Flagged prominently in
`docs/MILESTONE_6_REPORT.md` §6 as the top risk for the tournament strategy
brief, not buried as a footnote.
