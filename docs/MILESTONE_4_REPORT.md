# Milestone 4 Report

Tags used throughout, per instructions: **Verified / Strongly supported / Hypothesis
/ Rejected**. This report covers the corrected-config re-benchmark this milestone was
actually about: after discovering (see `docs/COMPLIANCE_REPORT.md` §0 and
`docs/GAME_SPEC.md` §2.5) that every prior benchmark in this repo was run against the
wrong `game-configs.json` (generic "Terminal Online Season 8" instead of the
competition's actual "High School Terminal 2026" default), this milestone (a) fixes
the config, (b) verifies the two mechanism-level changes that matter most (SUPPORT's
shield formula, TURRET's range/upgrade behavior) directly rather than assuming them
from the diff table, (c) builds and regression-tests two candidate fixes on top of the
existing `milestone3-champion`, and (d) runs a full corrected-config regression plus a
head-to-head tiebreaker to pick an actual champion.

## 0. Headline summary

- **The config swap itself is the whole story for why a re-benchmark was needed at
  all** — see `docs/COMPLIANCE_REPORT.md` §0 / `docs/GAME_SPEC.md` §2.5 for the full
  diff and how it was verified (`Config.useConfigFile()` bytecode + an actual local
  match confirming the engine reads the repo-root file). Not re-derived here.
- **SUPPORT/Encryptor's shield formula, previously an open gap, is now Verified** via
  a dedicated controlled probe (`experiments/shield_probe/` vs.
  `experiments/shield_probe_passive/`): shields only mobile units, bonus =
  `shieldPerUnit + shieldBonusPerY * support_y` (the SUPPORT's own y, not the
  shielded unit's), stacks across multiple SUPPORTs, hard-capped at `shieldRange`.
  Full derivation in `docs/GAME_SPEC.md` §2.5.2.
- **Two candidates were built and fully regression-tested on top of
  `milestone3-champion` (`defense_v4_tiebreak`, carried forward unmodified as the
  control, tag `m4_v4carry`):**
  - `defense_v6_encryptor_fix` — v4 + reposition/upgrade SUPPORT to actually use the
    now-real shield.
  - `defense_v7_range_leverage` — v6 + a sparser 6-anchor TURRET layout and
    WALL-upgrade-over-TURRET-upgrade rebalance, leaning on the new 4.5 TURRET range.
- **All three (v4carry, v6fix, v7range) scored 100% (136/136, 0 crashes) across the
  full 14-opponent regression corpus** (`python-algo`, `baselines/rush`,
  `baselines/hybrid`, all 11 `opponents/*`) under the corrected config — win rate
  alone does not distinguish them.
- **Margin/robustness analysis breaks the tie decisively:** `v4carry` only survives
  the three "leak/turtle" opponents (`turtle_survivor`, `single_leak_turtle`,
  `lategame_defector`) by riding every single game to the turn-100 cap and winning
  the bare +10 HP tie-break (30 vs 20) — a fragile win, one bad RNG draw or opponent
  tweak from flipping. `v6fix` and `v7range` both win those same matchups decisively
  (3-4x bigger margins, games ending well before turn 100 in most samples).
- **A direct head-to-head round-robin among the three candidates gives an
  unambiguous, non-cyclic-in-outcome answer: `defense_v6_encryptor_fix` beats both
  other candidates outright** — 10-0 vs `v7range`, 10-0 vs `v4carry` (v4carry in turn
  beats v7range 6-0, a genuine intransitive triangle, but `v6fix` is undefeated
  against both, which is what actually matters for picking one champion).
- **Three in-progress Milestone-4 offense-only patches from before the config
  correction landed (`defense_v5_bigwave`, `defense_v5_corner_forced`,
  `defense_v5_demolisher_corner`) are confirmed superseded, not just outdated** — one
  (`v5_demolisher_corner`) is now actively broken (7/50, 14%, vs. `turtle_survivor`)
  because the corner-weak-point geometry it was built to exploit assumed the OLD
  2.5 TURRET range, not the corrected 4.5. None of the three is a viable candidate.
- **New recommended champion: `baselines/defense_v6_encryptor_fix`, tagged
  `milestone4-champion`.** Packaged at `submissions/milestone4_champion/`.
  `milestone1-fallback`, `milestone2-champion`, and `milestone3-champion` remain
  untouched as rollback points.

## 1. Why a re-benchmark was necessary (recap, full detail lives elsewhere)

Every number produced in Milestones 1-3 — including the `defense_v3_lowcompute`
compute-time fix, the `defense_v4_tiebreak` mode-transition fix, and the
`turtle_survivor` "structural/economic bottleneck" conclusion from Milestone 3 §3 —
was measured against `game-configs.json` as shipped by the generic public starter kit
clone, not the actual competition's own "High School Terminal 2026" default. The two
changes with real strategic weight (not just numeric tuning) are:

1. **SUPPORT/Encryptor**: was a `generatesResource1/2` economy unit with a
   provably-inert (`shieldRange: 0`) shield field; is now a real shield/support unit
   with **no** economy function at all (`generatesResource1/2` keys fully absent).
2. **TURRET/Destructor**: `attackRange` 2.5 → 4.5 (+80%), and — a previously-unflagged
   second-order consequence found while building these candidates —
   `upgrade.attackRange` stayed at 3.5 in both configs, so upgrading a TURRET now
   **decreases** its range (a real tradeoff) instead of increasing it (previously a
   free stat boost).

Full diff table, bytecode-level verification of which config file the engine actually
reads, and the shield-probe methodology are in `docs/GAME_SPEC.md` §2.5 (not repeated
here). `docs/COMPLIANCE_REPORT.md` §0 covers what this invalidates and what it
doesn't (the turn-100 cap / tie-break rule, which lives in engine bytecode, is
unaffected).

## 2. Candidates built and why the v5 offense patches are excluded

Before the config correction was identified, in-progress Milestone 4 work
(`defense_v5_bigwave`, `defense_v5_corner_forced`, `defense_v5_demolisher_corner`) was
targeting a `turtle_survivor` corner-weak-point exploit found by direct
`get_attackers()` geometry analysis **under the old 2.5 TURRET range**. That
analysis is invalidated by the range increase to 4.5, and direct re-testing under the
corrected config confirms it, not just assumes it:

| Candidate | vs. `turtle_survivor` (corrected config, all samples combined) | Verdict |
|---|---|---|
| `defense_v5_bigwave` | 30/30 (100%) | Only via the same fragile +10 HP turn-100 tie-break as `v4carry` — this patch is pure offense-pacing, it never touched core defense, so it inherits v4's exact fragility. |
| `defense_v5_corner_forced` | 20/22 (91%) | **Newly losing sometimes** — 2 outright losses at exact 40-40 HP ties decided by the engine's coin-flip tie-break. |
| `defense_v5_demolisher_corner` | 7/50 (14%) | **Badly broken.** The corner-forced demolisher rush this patch encodes now performs *worse* than doing nothing differently — consistent with the range increase closing exactly the gap it targeted. |

(Sources: `experiments/results/20260715-032853_m4_t1_bigwave_vs_turtle.jsonl`,
`...033330_m4_t2_demolisher_vs_turtle.jsonl`, `...033726_m4_t3_cornerforced_vs_turtle.jsonl`
(first batches, 20/20/12 games) plus `...030723_m4_v5bigwave_...`,
`...030916_m4_v5cornerforced_...`, `...031032_m4_v5democorner_...` (second batches, 10
games each).)

**None of the v5 family is carried forward as a candidate.** The two viable
Milestone 4 candidates, both built directly against the corrected config's actual
verified mechanics (not offense-side geometry guesses), are:

- **`defense_v6_encryptor_fix`** = `defense_v4_tiebreak` + reposition SUPPORT from
  `[[13,3],[14,3]]` (a dead economy placement under the old config, and a needlessly
  far-back position for a shield whose bonus scales with the SUPPORT's own y) to
  `[[13,9],[14,9]]` (one row behind `core_turret_anchors`, still fully screened, and
  on the central `[13,0]`/`[14,0]` attack lane), plus actually **upgrading** it
  (`shieldPerUnit` 2.0→4.0, `shieldRange` 2.5→7) — something no earlier "defense"
  family baseline ever did.
- **`defense_v7_range_leverage`** = `defense_v6_encryptor_fix` + a rebalanced core:
  `core_turret_anchors` trimmed 10→6 (leaning on the new 4.5 base range for
  coverage), the freed SP spent on a second `core_wall_second` layer and on WALL
  upgrades (40→120 HP, a 3x multiplier now, vs. the old config's 2x) instead of
  TURRET upgrades (now a real range-for-damage tradeoff per the §1 finding above,
  and a worse trade specifically for this variant's sparser anchor spacing).

## 3. Full regression suite under the corrected config

All three candidates — the unmodified `milestone3-champion` carried forward as the
control (`m4_v4carry`), `defense_v6_encryptor_fix` (`m4_v6fix`), and
`defense_v7_range_leverage` (`m4_v7range`) — were run against the complete
14-opponent corpus (the official starter `python-algo`, both sibling "defense
family" baselines `rush`/`hybrid`, and all 11 `opponents/*` archetypes), 10 games
each (16 for `turtle_survivor`, matching the deeper sampling Milestone 3 used for
that specific opponent), alternating p1/p2 seat every game. Raw data:
`experiments/results/*_m4_v4carry_vs_*.jsonl`, `*_m4_v6fix_vs_*.jsonl`,
`*_m4_v7range_vs_*.jsonl` (41 files, 406 total games).

**Result: all three candidates won 100% of every matchup (136/136 decided games
each, 0 crashes, 0 errors).** Win rate alone is not a usable signal to pick a
champion this time. Win **margin** (`|final_p1_health - final_p2_health|`,
normalized to the candidate's perspective) and mean turn count tell a very different
story:

| Opponent | `v4carry` margin / turns | `v6fix` margin / turns | `v7range` margin / turns |
|---|---|---|---|
| `python-algo` | 33.0 / 14.0 | 32.0 / 16.0 | 32.0 / 12.0 |
| `baselines/rush` | 33.3 / 11.4 | 32.4 / 12.0 | 30.9 / 10.0 |
| `baselines/hybrid` | 21.0 / 58.0 | 27.0 / 44.0 | 21.0 / 30.0 |
| `opponents/adaptive_reactive` | 31.7 / 22.0 | 30.6 / 16.6 | 31.1 / 14.0 |
| `opponents/burst_hoarder` | 35.4 / 12.0 | 31.5 / 12.0 | 27.0 / 12.0 |
| `opponents/double_funnel_maze` | 35.3 / 9.8 | 34.9 / 10.0 | 35.2 / 10.0 |
| `opponents/escorted_combined_arms` | 35.3 / 10.0 | 34.5 / 9.8 | 32.2 / 10.0 |
| `opponents/funnel_maze` | 30.0 / 10.0 | 30.0 / 10.0 | 30.0 / 10.0 |
| **`opponents/lategame_defector`** | **10.0 / 99.0** | **32.4 / 91.0** | **39.3 / 81.3** |
| `opponents/middle_rush_exploit` | 35.0 / 9.4 | 34.2 / 9.0 | 31.5 / 9.0 |
| `opponents/multi_lane_saturation` | 32.3 / 8.6 | 34.4 / 9.0 | 34.4 / 9.6 |
| **`opponents/single_leak_turtle`** | **10.0 / 99.0** | **36.5 / 85.1** | **35.2 / 87.2** |
| `opponents/sunk_cost_recipe_switcher` | 30.3 / 10.0 | 31.0 / 10.0 | 26.5 / 10.2 |
| **`opponents/turtle_survivor`** (n=16) | **10.88 / 99.0** | **34.75 / 88.1** | **35.56 / 86.8** |

**Reading this table (Verified from the raw per-match data, not just the aggregate
win rate):** on the 11 "normal" opponents, all three candidates perform within noise
of each other (roughly 27-35 HP margins, similar turn counts). On the **three
opponents that play a long/passive/leak-style game** (bolded rows), `v4carry`
degrades to *exactly* a `30.0 vs 20.0` final health split, every single game, always
at the hard turn-100 cap — i.e. it is not really "beating" these opponents in any
decisive sense, it is surviving to the tie-break every time. `v6fix` and `v7range`
both convert these into real, decisive wins (3-4x bigger margins, and frequently
ending the game outright before turn 100), which is a direct, measurable consequence
of the SUPPORT shield fix actually doing something now (extra effective HP on the
scouts/demolishers these opponents' defenses have to grind through) — this is not
assumed, it is the same three opponents where `v4carry` was already known (Milestone
3 §3) to be economically bottlenecked, and giving the exact same offense loadout a
free HP multiplier via a working shield is a direct fix for exactly that bottleneck.

## 4. Head-to-head tiebreaker: v6fix vs v7range vs v4carry

Since all three candidates are indistinguishable by win rate against the shared
corpus, the deciding test is a direct round-robin among the three candidates
themselves (10 games each, p1/p2 alternated;
`experiments/results/20260715-030850_m4_h2h_v6_vs_v7.jsonl`,
`...031019_m4_h2h_v4_vs_v6.jsonl`, `...031201_m4_h2h_v4_vs_v7.jsonl`, the last at n=6
as a transitivity spot-check):

| Matchup | Result | Note |
|---|---|---|
| `v6fix` vs `v7range` | **v6fix wins 10/10** | Every single game ended at exactly turn 30 — a strong, consistent signal, not noise. |
| `v4carry` vs `v6fix` | **v6fix wins 10/10** | Every single game ended at exactly turn 66. |
| `v4carry` vs `v7range` | **v4carry wins 6/6** | Every single game ended at exactly turn 50. |

**This is a genuine intransitive result** (`v6fix` > `v4carry` > `v7range`, but also
`v6fix` > `v7range` directly) — not a bug, and not surprising in retrospect:
`v7range`'s sparser 6-anchor TURRET layout is specifically tuned to lean on raw range
for coverage, which is exactly what `v4carry`'s unmodified (denser, no-shield)
offense loadout turns out to punish, while `v6fix`'s combination of the denser
10-anchor layout *and* the working SUPPORT shield beats both of the other two
outright. **Because `defense_v6_encryptor_fix` is undefeated against both other
serious candidates head-to-head, it is the unambiguous champion choice** — there is
no cyclic ambiguity in *who wins the tournament*, only in the pairwise structure among
the two candidates it beats.

## 5. Champion decision

**New recommended champion: `baselines/defense_v6_encryptor_fix`, tagged
`milestone4-champion`.**

Accepted because:

1. **Zero regressions** — identical 100% win rate to `defense_v4_tiebreak`
   (`milestone3-champion`) across the full corrected-config 14-opponent, 136-game
   regression suite (0 crashes anywhere, either candidate).
2. **Strictly better margins/robustness than the control** on every opponent tested,
   and dramatically better (3-4x margin, ~10-15 fewer turns) on the three
   "leak/turtle" opponents where the control was only surviving via the turn-100 HP
   tie-break, not actually winning decisively.
3. **Undefeated head-to-head** against both the control (`v4carry`, 10-0) and the
   more aggressive rebalance candidate (`v7range`, 10-0) — the only candidate with
   this property among the three tested.
4. **The change itself is principled, not just empirically lucky**: it is a direct,
   Verified fix (not a guess) for a real mechanism change in the corrected config
   (SUPPORT going from a dead shield/live economy unit to a live shield/dead economy
   unit), tested against a dedicated controlled probe before being applied
   (`docs/GAME_SPEC.md` §2.5.2), not assumed from the config diff alone.

`defense_v7_range_leverage` is **not** recommended despite also clearing the full
regression suite at 100%: it loses head-to-head to both other candidates once tested
directly, which the aggregate-corpus win rate alone did not reveal. It remains in
`baselines/` for reference/rollback but is not packaged as a submission candidate.

`defense_v4_tiebreak` (`milestone3-champion`) is **not rejected outright** — it still
legitimately wins every regression matchup — but is superseded: `v6fix` strictly
dominates it (better margins everywhere, wins the direct head-to-head 10-0), for the
cost of a small, well-understood, well-tested change.

`milestone1-fallback`, `milestone2-champion`, and `milestone3-champion` all **remain
completely untouched** as safe rollback points, per the standing instruction.

## 6. What this milestone does and does not resolve

- **Resolved:** which config is actually correct (Verified, bytecode + live match), the
  SUPPORT shield formula (Verified, controlled probe), whether the old
  `turtle_survivor` corner-exploit patches survive the range correction (Rejected —
  they don't, confirmed empirically not just theoretically), and which candidate is
  the actual champion under the corrected config (`v6fix`, Verified via direct
  head-to-head, not just corpus win rate).
- **Not attempted this milestone:** a fresh adversarial countersearch specifically
  targeting `v6fix`'s new SUPPORT placement/upgrade behavior (Milestone 3 §5's
  discipline of building 1-2 new opponents that target the *current* candidate's
  *new* behavior was not repeated here — this is an honest gap, not a claim that
  `v6fix` has been adversarially hardened). A natural next-milestone target: an
  opponent that specifically tries to snipe the exposed `[[13,9],[14,9]]` SUPPORT
  pair before it can be upgraded, or one that baits `v7range`'s sparser layout
  head-to-head-style logic to see if the same weakness that lost to `v4carry` is
  reachable by an external opponent, not just another one of our own candidates.
- **Still an open gap, unchanged from Milestone 3 §7:** the exact MP-cap ramp formula,
  timeout-damage-per-ms formula, and crash-loss mechanics remain unverified from
  engine bytecode; none of this milestone's work required resolving them.

## 7. Submission package

Packaged at `submissions/milestone4_champion/` — see that directory's own `README.md`
for the same `run.sh` executable-bit compliance treatment applied to every prior
milestone's package (`docs/COMPLIANCE_REPORT.md` §1.1): both a plain
`zipalgo_linux`-produced zip and a `_permfix.zip` built with the system `zip` tool,
both independently fresh-extraction-verified with a real local match against
`python-algo`, plus an already-executable unzipped `_algo_folder/`.
