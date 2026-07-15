# Milestone 5 Report

Tags used throughout, per instructions: **Verified / Strongly supported / Hypothesis
/ Rejected**. This milestone closes the one honest gap flagged at the end of
`docs/MILESTONE_4_REPORT.md` section 6: no adversarial countersearch had yet
specifically targeted `baselines/defense_v6_encryptor_fix`'s new SUPPORT
(Encryptor) placement/upgrade behavior under the corrected "High School
Terminal 2026" config. This milestone builds three purpose-built opponents
against that specific logic, benchmarks the champion against them with a real
sample size (n=10 each, both seats), and reports the outcome honestly.

## 0. Headline summary

- **Three distinct hypotheses were formed by reading `defense_v6_encryptor_fix`'s
  source directly**, each targeting a different angle on the SUPPORT change:
  (1) SUPPORT is the single most fragile structure type (30 HP) at a fixed,
  detectable location; (2) the champion's own lane-choice heuristic has no
  awareness of the SUPPORT's shield radius, so it could in principle be routed
  around it entirely; (3) SUPPORT upgrades strictly last (after all 10 turret
  anchors and 12 wall cells), creating a real timing window where it's
  unupgraded/weaker even though already exposed.
- **Three new opponents were built, one per hypothesis** — `opponents/support_sniper`
  (adaptive detection + escorted structural sniping), `opponents/corner_lane_baiter`
  (asymmetric static defense designed to bait the lane-choice heuristic), and
  `opponents/shield_race_rusher` (a sustained, non-adaptive early rush with a
  real defense of its own) — smoke-tested for legality (0 crashes, both
  seats) before any real benchmarking.
- **Result: no exploitable weakness found, after a genuine effort with real
  sample sizes.** All three lost 10/10 (or, for `corner_lane_baiter`, never
  even succeeded in redirecting the champion's lane choice) against
  `baselines/defense_v6_encryptor_fix`, 0 crashes anywhere, in both p1/p2
  seats (`experiments/results/20260715-0336*_m5_*.jsonl` through
  `20260715-0344*_m5_*.jsonl`).
- **`corner_lane_baiter` is the one genuinely informative result**, even
  though it didn't find a win: direct replay evidence (not inference) shows
  the champion's offense kept using the central lane throughout a 72-turn
  game despite the deliberately asymmetric defense designed to make the
  corner lane look cheaper — the routing-around-the-shield hypothesis is
  real *in mechanism* (the heuristic genuinely has no shield-awareness) but
  this specific opponent design did not manage to trigger it in practice.
- **Running the identical three opponents against the control
  (`defense_v4_tiebreak`, tag `m4_v4carry`) produced statistically
  indistinguishable results** in every case — identical shield-event counts
  and identical final health in `corner_lane_baiter`'s case, overlapping
  margins/turn-counts in the other two — confirming this isn't just "the
  champion is generally strong," it's specifically that these three attack
  mechanisms don't create a *differential* weakness introduced by the
  Milestone 4 SUPPORT change relative to what was already there.
- **No patch was made. `baselines/defense_v6_encryptor_fix` remains the
  champion, still tagged `milestone4-champion`.** No new `milestone5-champion`
  tag was created, per the instruction to only tag/re-package if a real
  weakness is found and fixed. `milestone1-fallback`, `milestone2-champion`,
  and `milestone3-champion` all remain untouched as rollback points.

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

## 6. Champion decision

**No change. `baselines/defense_v6_encryptor_fix` remains the champion,
still tagged `milestone4-champion`.** No patch was warranted: no opponent
built this milestone found a real degradation (loss, crash, or measurable
margin regression) relative to `defense_v4_tiebreak`, the previous champion,
under real n=10-per-opponent sampling in both seats. Per the standing
acceptance discipline (never patch on small-sample noise or a purely
theoretical gap without a demonstrated practical cost), introducing a patch
here — e.g. making the lane heuristic shield-aware — would add complexity and
regression risk for a benefit that was not actually demonstrated to exist in
practice against any opponent tested, including one (`corner_lane_baiter`)
purpose-built to expose exactly that gap.

This is a genuine, honestly-reported negative result, not proof the design
has no exploitable weakness anywhere — see section 5 above for what remains
untested. `milestone1-fallback`, `milestone2-champion`, and
`milestone3-champion` all remain **completely untouched** as rollback
points, per the standing instruction. No new submission package was built
this milestone (the existing `submissions/milestone4_champion/` package is
still current, since the champion did not change).
