# Counterexample Suite — Adversarial Hardening Against `baselines/defense`

Per Milestone 2 step: deliberately try to build counters/exploits against our own
current champion (`baselines/defense`), document each attempt (mechanism, result,
realism), and only patch if a real weakness is found. Tags: **Verified / Strongly
supported / Hypothesis / Rejected**, consistent with all other docs in this repo.

**Honesty note up front:** both attempts below **failed to beat `defense`** (15-0 to
defense in both cases). That is itself the finding — it does **not** mean `defense`
is unbeatable, only that these two specific, plausible attack vectors did not work
against it locally, with this engine/config, in the time available. See section 3
for what this does and doesn't prove.

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

## 3. What this does and does not prove

- **Strongly supported:** across everything tested so far — the Milestone 1 round
  robin (120 games), the 3-archetype opponent corpus (45 games), and these two
  targeted adversarial probes (30 games) — `defense` has a **135-0 record across
  135 total local games against 8 distinct opponents** (1 official starter bot, 2 of
  our own contrasting baselines, 3 diverse archetypes, 2 hand-built adversarial
  probes), 0 crashes, 0 harness errors throughout. This is a real, repeatedly
  corroborated result, not a fluke of one lucky matchup.
- **Explicitly not proven:** that `defense` is unbeatable, or that no counter
  exists. All 8 opponents were built by this same workstream (or are the one
  official starter bot); none are an independently-written, actively-competitive
  human team's algo. **This is the same class of gap already flagged in
  `docs/MILESTONE_1_REPORT.md` section 7** — a shared blind spot between our
  opponent-design instincts and our own baseline's actual weaknesses cannot be
  fully ruled out just by us failing to find a counter ourselves, especially with
  only ~2 focused hardening attempts (limited by time, not by these being the only
  ideas worth trying).
- **Ideas not yet tried** (explicitly deferred, not rejected): a DEMOLISHER-focused
  (not SCOUT-focused) middle rush; an attack specifically timed to hit before
  `defense`'s turret upgrades complete (its `upgrade_core` call has no explicit
  early-game gating, but upgrades cost SP that's also being spent on width, so
  there may be a real early-turn window); a maze that specifically routes around
  `defense`'s exact known turret coordinates rather than going straight up the
  middle; and simply feeding `defense`'s own replay data into a scripted opponent
  that has "seen" its layout in advance (which would be a fair test of
  "sustained ladder play against a memorized opponent," not tested here since we
  only ever play fresh matches).

## 4. Outcome

No patch was made to `baselines/defense` as a result of this pass, because no
working counter was found to patch against. Per the standing instruction to never
overwrite the last known-good submission without a benchmarked improvement, the
`milestone1-fallback` tag and `submissions/emergency_fallback/` package are
unchanged. This section should be revisited if/when a real counter is found in a
future hardening pass.
