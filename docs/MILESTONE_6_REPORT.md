# Milestone 6 Report: Genuinely independent (public, black-box) opponents

## 0. Headline summary

**The concern this milestone addresses:** every opponent used in Milestones
1-5 — the full self-built corpus of 20 opponents plus the official starter
bot — was either designed by this project or is the (weak, untouched)
official starter template. A 100% win rate against that corpus is evidence of
robustness against threats *we imagined*, not against real,
independently-designed opponents. This is exactly the overfitting failure
mode the top-level instructions warn against, and the user raised it as a
valid, specific strategic concern.

**What this milestone did:** searched for, vetted, and locally benchmarked
real, publicly-available Terminal python-algo bot code from other teams'
GitHub repos, used strictly as unmodified black-box test opponents (never
copied or adapted into our own code). Found and ran 5 genuinely independent,
substantial, non-stub bots (plus 2 more smoke-tested variants of one of them).

**Headline result — stated as plainly and honestly as every prior milestone:**

- **4 of 5 genuinely independent opponents: `milestone5-champion`
  (`baselines/defense_v6_encryptor_fix`) wins 20/0 (or 19/1), both seats, no
  crashes, against all of them.**
- **1 of 5 genuinely independent opponents (`travelling_salesmen_v33`, a real
  team's self-declared "final version" algo, from a repo claiming a real
  competition win): `milestone5-champion` LOSES 0/20, both seats, no
  crashes.** This is a real, decisive, fully reproducible loss — not noise,
  not a crash, not a fluke of one game.
- **Root cause was found and is well-understood** (§3): a continuous,
  un-paused, 100%-MP-committed Demolisher rush at a single fixed lane grinds
  down our single-layer corner defense faster than it can be rebuilt,
  eventually breaching through to direct player-health damage every turn.
- **Five separate, honestly-attempted patches were built and empirically
  tested (§4).** All five measurably delayed the loss (survival extended from
  ~35 turns to ~38-43 turns, and points conceded dropped somewhat). **None of
  the five actually reversed the result.** This is reported plainly rather
  than forcing an unproven "fix" into the champion slot.
- **Recommended champion: unchanged. `baselines/defense_v6_encryptor_fix`,
  tagged `milestone5-champion`, remains the champion.** No new tag is cut
  this milestone. The full regression suite (§5) confirms zero regressions
  anywhere else — the champion is still undefeated against all 20 self-built
  opponents plus 4 of 5 independent ones. This one genuine, well-documented,
  currently-open loss is the single most important finding of this entire
  project and is flagged prominently, not buried, per §6.

This report distinguishes **self-built opponent corpus results** (Milestones
1-5, `opponents/*` + `baselines/rush`/`hybrid` + `python-algo`) from
**independently-designed opponent results** (`public_opponents/*`, this
milestone) throughout, per the user's explicit instruction.

---

## 1. The search: what was found, and how it was vetted

Full sourcing detail, license notes, and the config-mismatch analysis for
every candidate live in `docs/STRATEGIC_PRIOR_ART_REPORT.md` source-log
entries #21-24 (updated this milestone) — this section summarizes.

### 1.1 Named former winners (Smite/Stanford, QY/Cambridge, Garpuz/UW, Bin
Birds/APAC 2026) — searched specifically per the user's upgraded goal

The user specifically asked to check whether any of the strongest,
highest-profile named winners already identified in
`docs/STRATEGIC_PRIOR_ART_REPORT.md` (Team "Smite," Stanford, 2021 Global
Champions; Team "QY," Cambridge, 2022 Global Champions; Team "Garpuz," UW,
2020 regional winner; Team "Bin Birds," APAC, **April 2026** — the single most
recent data point in the whole prior-art report) have public code.

**Result: no public repo was found for any of the four.** For "Bin Birds"
specifically — the most recent and most likely to still have an active,
findable GitHub presence — the actual named individuals (Lucas Liang, Hugo
Jasmin, Trong Nghia Nguyen) were identified via Lucas Liang's own LinkedIn
post confirming the win, and his linked personal GitHub account
(`lucasisntcoding`) was checked directly: 12 public repos, all quantitative
finance / web projects, zero Terminal or C1Games code. This directly confirms
(rather than just repeats) the "please don't publish complete algos" norm
already documented in `docs/STRATEGIC_PRIOR_ART_REPORT.md` source #7 — this
is a real, checked negative result, not an assumption.

### 1.2 Candidates that WERE found, real and substantial

| Candidate | Real? | Non-stub? | License | Placement claim |
|---|---|---|---|---|
| `satvikmittal638/Terminal-2026-Skill-Issue` | Yes, real named team (Satvik Mittal, Om Gore, Chatanya Maheshwari) | Yes — 235-line `algo_strategy.py`, distinct strategy writeup in-repo | Repo-level `License.md` is the standard Correlation One starter-kit license (governs the starter-kit-derived files only — see §2); **the team's own strategy code additions have no separate license of their own**, so default all-rights-reserved applies to that layer | 3rd/4 shown on own leaderboard image, "Citadel Terminal Competition," Mar 2026 |
| `The-Travelling-Salesmen/terminal-c1` (multiple iterations: `snorkeldink-v1/v2/v3-1/v3-2/v3-3`, `AdapDef`, `frumblesnatch-v1`, `algo-1`, `python-algo`) | Yes, real repo, real (squashed, 1-commit) git history | Yes for the iterations that matter — see §1.3 correction below | Same starter-kit license situation as above | Repo description: "helped us clinch #1 spot at Harvard in Terminal" |
| `davidw0311/c1_terminal` | Yes | Yes — 971-line MCTS bot (`numpy`/`scipy`), enemy-spawn tracking | No LICENSE file at all (defaults to all-rights-reserved) | None (personal/student project) |
| `wllmzhu/alpha-terminal` | Yes | Yes (RL/PPO agent) | Not re-benchmarked this milestone (already documented in `docs/STRATEGIC_PRIOR_ART_REPORT.md` source #8 from prior research; not re-run locally — no clear evidence it out-performs the candidates above, and RL/PPO agents in this domain are self-reported to reach only "strong amateur" level per that same source) |  |
| `vinharish77/TerminalCompetition` | Checked, found to be an essentially-untouched starter-kit fork (no meaningful custom `algo_strategy.py` content beyond the default template) | **No — dud, correctly excluded** | — | — |

Two more repos flagged in earlier research
(`langsonzhang/Terminal-C1-Midwest-2022`, `yip6ga1lok6/C1-Terminal-Summer-2022`)
were confirmed to have real directory structures and non-`NOASSERTION`-only
license files, but were **not** run locally this milestone given the two
Travelling Salesmen iterations already surfaced the most important, decisive
finding of this whole search — deprioritized rather than abandoned; see §7.

### 1.3 Correction made during vetting: which iteration is actually
"the algo that won"?

The Travelling Salesmen repo preserves ~10 iterations of their algo
(`snorkeldink-v1` through `v3-3`, plus a separately-named `AdapDef` and
`frumblesnatch-v1`). An initial pass assumed `AdapDef` — the more
"official-sounding" name — was their strongest/final version, benchmarked
only that one, and recorded a clean 20/0 win for our champion.

**This assumption was wrong, and finding that out required actually reading
more than one file.** Diffing `AdapDef`'s `algo_strategy.py` against
`snorkeldink-v3-3`'s line-by-line found `AdapDef` retains large chunks of
**unmodified starter-kit boilerplate**: the default `"Configuring your custom
algo strategy..."` debug string, the starter kit's own unused
`build_reactive_defense`/`stall_with_scramblers`/`emp_line_strategy` helper
methods verbatim, and comments literally reading "Most of the algo code you
write will be in this file unless you create new modules yourself." Its
`defence.py` also has fewer/commented-out Encryptor placements than the later
iterations, suggesting incomplete economy tuning.

`snorkeldink-v3-3`, by contrast, has its own docstring reading
`"Strategy-code for the final version of Snorkeldink-V69"` (a self-declared
final version) and a real, working `save_cores` resource-discipline gate
(don't spend on secondary defense until the primary destructor wall is fully
built) that `AdapDef` never has. **`snorkeldink-v3-3` is the one that beats
our champion 0/20; `AdapDef` is the one that loses 20/0.** Two more
intermediate iterations were spot-checked to understand when this mechanism
appeared: `snorkeldink-v3-1` loses to us (6/0, smoke-tested), while
`snorkeldink-v3-2` — one version later — already has it and beats us (0/6,
smoke-tested), consistent with `v3-3` inheriting and keeping the same
winning mechanism. This strongly suggests the actual "algo that clinched #1
at Harvard" is `v3-2`, `v3-3`, or something extremely close to them, not
`AdapDef`.

This correction is logged prominently here (and in
`docs/REAL_OPPONENT_RESULTS.md` §6) rather than quietly fixed, because it's a
direct, concrete illustration of exactly the kind of mistake this whole
milestone was designed to catch: assuming instead of checking.

---

## 2. Compliance: sourcing, license, and black-box-only usage

Every candidate above is used **strictly as an unmodified black-box local
test opponent** — dropped into `public_opponents/<name>/` exactly as cloned
(only file-permission fixes for `run.sh`, no logic changes), run through this
project's own harness, never read for the purpose of copying or adapting any
of its logic into `baselines/`. See `docs/COMPLIANCE_REPORT.md` (updated this
milestone) for the full sourcing/license table.

**License situation, stated plainly:** every repo found ships the standard
Correlation One starter-kit `License.md` (a fairly permissive
copy/modify/merge/distribute license, with an explicit no-commercial-use and
no-competing-product clause) — but that license, by its own text, covers "the
Software" as originally distributed by Correlation One, i.e. the starter-kit
boilerplate (`gamelib/`, `engine.jar`, the scripts directory). **None of the
teams added a separate license of their own for their own strategy code**
(no per-team `LICENSE` override, no license header in `algo_strategy.py`
itself). The conservative, correct reading is that each team's own original
strategic code additions default to standard copyright (all rights reserved)
absent an explicit grant — which is exactly why this project only ever runs
this code as a black-box opponent and never copies from it, regardless of
the starter-kit license's own permissiveness.

---

## 3. Root-cause analysis: why `travelling_salesmen_v33` wins

Full turn-by-turn replay evidence (not just aggregate win/loss) is in
`experiments/replays/m6_public_v6fix_vs_v33_n20_*.replay`.

### 3.1 The opponent's mechanism (`snorkeldink-v3-3`, self-named "Snorkeldink-V69")

Read directly from its own (unmodified) code:

1. **Adaptive wall-opening**: every 4 turns, count our own Filter (Wall) and
   Destructor (Turret) units on each half of the board (weighted 1 badness
   point per Wall, 6 per Turret) and open a gap in their own wall toward
   whichever of our halves currently looks weaker.
2. **Continuous, un-paused, 100%-MP Demolisher rush**: from turn 4 onward,
   *every single turn*, spend as many Demolishers as current MP allows
   (`attempt_spawn(EMP, emp_location, 1000)`) at a single fixed lane (`[4,9]`
   or `[23,9]`) tied to the wall-opening decision above. No bursting, no
   pausing, no alternating sides mid-stream — pure sustained pressure.
   Because this spends MP (not SP), it never competes with their own
   defensive rebuild budget.

### 3.2 Why our champion's defense fails to this specific mechanism

Verified directly from replay spawn/death event pairs
(`experiments/replays/m6_public_v6fix_vs_v33_n20_000.replay`):

- Our `core_turret_anchors` places single TURRETs directly at the two
  extreme board corners (`[1,12]`, `[26,12]`) — which, per
  `gamelib.GameMap.get_edge_locations`, **are themselves valid scoring edge
  tiles** (`BOTTOM_LEFT`/`BOTTOM_RIGHT`). A Demolisher merely needs to
  survive to stand on that exact tile to breach for direct player damage; no
  further travel required.
- `build_core_defense` re-attempts to spawn a fresh TURRET there every turn
  after it's destroyed — but a **freshly-spawned, full-HP (75) TURRET is
  killed again within the SAME turn it's rebuilt**, before it can contribute
  meaningfully, because 3+ simultaneous Demolishers converge and fire
  multiple times within one turn's frame window (Verified: e.g. turn 28, unit
  id `'420'` spawns at `[26,12]` and dies at `[26,12]` in the same turn's
  event log).
- `reactive_defense`'s neighborhood backfill (one row behind a recent breach,
  capped at 6 SP/turn in the unpatched champion) cannot outpace this, because
  it only adds *more single-layer* TURRETs in the same exposed spot, which
  die the identical way.
- The board's diamond geometry means there is **no tile physically "behind"
  the extreme corner** at the same x-coordinate (Verified via
  `gamelib.GameMap.in_arena_bounds` — `[26,11]`/`[25,10]` are both outside
  the arena), so naive "add a second layer directly behind" is not even
  geometrically possible at the exact corner tip.
- Once that corner's structures are reliably dead every turn, subsequent
  waves walk straight through to deal direct player-health breach damage —
  which is exactly what the observed health trace shows: flat at 30 HP
  through turn ~24 in the best patched attempt (unpatched: breach starts as
  early as turn 4-5), then a steadily *accelerating* decline (22 → 3 HP over
  the final ~10-12 turns) as the opponent's MP economy (which ramps up over
  the game via `bitRampBitCapGrowthRate`) affords ever-larger simultaneous
  waves.
- A secondary contributing factor: our own `_stalemate_breaker` (extra
  Demolisher pressure to break a mutual stalemate) is explicitly gated off
  once `self.ever_breached` is `True` — which happens almost immediately in
  this matchup — so our own counter-offense goes quiet exactly when extra
  pressure on the opponent would help most. Unpatched champion's
  `points_scored` ended the game at **1.0** vs. the opponent's **30.0** — we
  are barely landing any hits back.

**This is a genuine, structural weakness, not a fluke or a config-reading
bug**: confirmed at n=20, both seats, 0 crashes, consistent turn count
(34-36 turns) and consistent mechanism across every single loss inspected.

---

## 4. Patch attempts (all tested, all honestly reported — none fully closed the gap)

Five distinct, principled fix attempts were built as `baselines/defense_v9_corner_depth`
(kept in the repo, clearly marked as an insufficient/rejected candidate, same
convention as `defense_v7_range_leverage`/`defense_v8_offense_burst`) and
empirically tested against `travelling_salesmen_v33`:

| # | Change | Result vs. `v33` (win rate / mean turns survived) | Verdict |
|---|---|---|---|
| 1 | Add a 2nd TURRET layer at `[2,11]`/`[25,11]` (one diagonal step from each corner) | 0/20, mean turns 42.9 (up from 34.8 unpatched) | Delayed but didn't fix. **Rejected on inspection**: these tiles are themselves also scoring edge tiles (same failure mode as the original corner) |
| 2 | Corrected: 2nd TURRET layer at `[3,11]`/`[24,11]` (confirmed NOT edge tiles, true depth, within Turret attack range of the corner) | 0/20, mean turns 37.7 | Still didn't fix — worse than attempt #1's delay, despite being the geometrically "more correct" fix |
| 3 | Attempt #2 + raised `max_reactive_spend_per_turn` (6 → 24, from 14) | 0/10, mean turns 37.7 (**identical** to attempt #2) | The SP cap was not the bottleneck — SP *income*, not the self-imposed cap, is the real constraint |
| 4 | Attempt #2 (at cap=14) + new MP-funded counter-offense (`_sustained_pressure_counter`: periodic Demolisher pressure triggered by evidence of sustained incoming damage, independent of the `ever_breached` gate) | 0/12, mean turns 38.2; `points_scored` improved from 1.0 → 5.0 | Real, measurable improvement in our own offense, but still a decisive loss |
| 5 | Replace corner TURRETs with cheaper WALLs (`[1,12]`/`[26,12]`, 1 SP vs. 2 SP, "alive at all" is what blocks pathing) + keep depth TURRETs at `[3,11]`/`[24,11]` for kill power + attempt #4's counter-offense | 0/12, mean turns 38.0 | No further improvement over attempt #4 |

**Honest conclusion on the patch attempts**: this is a real, structural,
economic problem — the opponent's MP-funded rush economy compounds over the
game (via `bitRampBitCapGrowthRate`) while our SP-funded defensive rebuild
budget does not compound at a comparable rate, and no combination of "add
more/cheaper static structure at the exact choke point" tested here closes
that gap. A fix that actually reverses this result likely requires a more
fundamental rebalancing of our SP/MP allocation strategy (e.g., a much more
aggressive counter-race posture, or fundamentally rethinking corner defense
depth across the whole board rather than two tiles) — a larger change than
is responsible to make and ship as the new champion without much more
extensive validation than this milestone's timeline allowed. Per this
project's standing discipline (never force an unproven change just to "have
fixed something"), **none of these five attempts is adopted.**
`baselines/defense_v9_corner_depth` is kept in the repository as a documented,
tested, rejected candidate for future reference — not deleted, not shipped.

---

## 5. Full regression suite — confirming no regressions elsewhere

`experiments/run_regression.py`'s `DEFAULT_OPPONENTS` was permanently extended
with the 5 genuinely independent opponents (see file comments distinguishing
self-built vs. independent). Full regression run for
`baselines/defense_v6_encryptor_fix` (`milestone5-champion`, unchanged) against
**all 25 opponents** (20 self-built/starter + 5 independent):

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
| `opponents/lategame_defector` | 10/10 |
| `opponents/middle_rush_exploit` | 10/10 |
| `opponents/multi_lane_saturation` | 10/10 |
| `opponents/single_leak_turtle` | 10/10 |
| `opponents/sunk_cost_recipe_switcher` | 10/10 |
| `opponents/turtle_survivor` | 16/16 |
| `opponents/support_sniper` | 10/10 |
| `opponents/corner_lane_baiter` | 10/10 |
| `opponents/shield_race_rusher` | 10/10 |
| `opponents/signature_detector` | 10/10 |
| `opponents/minimax_lookahead` | 10/10 |
| `opponents/predictor_opponent` | 10/10 |
| **`public_opponents/skill_issue_final3gem`** (independent) | **10/10** |
| **`public_opponents/travelling_salesmen_adapdef`** (independent) | **10/10** |
| **`public_opponents/travelling_salesmen_frumblesnatch`** (independent) | **10/10** |
| **`public_opponents/travelling_salesmen_v33`** (independent) | **0/10 — the known, unpatched loss** |
| **`public_opponents/davidw0311_mcts`** (independent) | **10/10** |

**Zero regressions against anything in the self-built corpus** (all still
100%, matching Milestones 1-5's standing results exactly) — this milestone's
work did not touch `baselines/defense_v6_encryptor_fix` itself, so this was
expected, but is confirmed rather than assumed. Full run log:
`/tmp/m6_full_regression.log` and `experiments/results/20260715-*_m6_full_regression_*.jsonl`.

---

## 6. Champion decision

**`baselines/defense_v6_encryptor_fix`, tagged `milestone5-champion`, remains
the champion.** No new tag is cut this milestone.

This is a deliberate decision, not a default: a real, decisive,
fully-reproducible loss against a genuinely independent opponent was found
and could not be closed despite five honest patch attempts. The champion is
kept unchanged rather than shipping any of the five partial-mitigation
patches, because:

1. None of the five patches actually reversed the loss — shipping one would
   trade "the same known loss, slightly slower" for the risk of unknown new
   regressions, for no proven benefit.
2. The champion remains undefeated against every other opponent tested across
   6 milestones (20 self-built + 4 of 5 independent), a large and now
   genuinely diverse evidence base.
3. Per this project's standing acceptance discipline (carried since
   Milestone 1): never force a change on partial/unproven evidence, and
   report an honest gap plainly rather than paper over it with an unproven
   fix.

**This is, honestly, the single most important open finding in this entire
project.** A real opponent — sourced from a team that plausibly used
something very close to this exact code to win a real Terminal event — beats
our champion cleanly and repeatably, and we do not yet have a working fix.
This should be treated as the top flagged risk in any tournament strategy
brief, not a footnote: if our actual competition opponent pool contains
anything resembling a continuous, un-paused, single-lane Demolisher rush
that doesn't over-commit early enough for us to punish it first, our current
champion is vulnerable to exactly that pattern. See §7 for recommended next
steps.

---

## 7. What this milestone does not resolve, and recommended next steps

- **The `travelling_salesmen_v33` loss is not fixed.** This is the headline
  gap. A more fundamental rebalancing of SP/MP allocation (not just
  more/cheaper static structure at one choke point) is the most promising
  untried direction, per §4's conclusion — but this needs a full milestone's
  worth of careful, incrementally-tested design, not a same-day patch bolted
  on to avoid reporting a loss.
- **Two more sourced-but-not-yet-run repos** (`langsonzhang/Terminal-C1-Midwest-2022`,
  `yip6ga1lok6/C1-Terminal-Summer-2022`) were vetted as real/non-stub but not
  benchmarked this milestone — deprioritized once the Travelling Salesmen
  loss surfaced as clearly the highest-value finding, not exhausted as an
  avenue. **Update: both were actually run in the same-day follow-up (§8) and
  again re-confirmed in Milestone 7 — this bullet is stale as of that
  follow-up, kept here only for the historical record of what this
  milestone itself did and didn't cover.**
- **No former Global Championship winner's actual code was found** (§1.1) —
  this remains, as flagged in `docs/STRATEGIC_PRIOR_ART_REPORT.md`, a hard
  ceiling on how far local black-box testing can go; the organizer norm of
  not publishing complete winning algos held up even for the most recent
  (April 2026) named winner checked directly.
- **`docs/REAL_OPPONENT_RESULTS.md`'s §§1-4 (the user's manual
  `terminal.c1games.com/playgroundlive` testing) remains separately thin,
  single-sourced, and unreproducible by this agent** — unaffected by this
  milestone's work, still an open gap in its own right.

---

## 8. Follow-up (same day, "round 2"): the two deprioritized repos, actually run

Both repos flagged as deprioritized-not-exhausted in §7 were sourced, vetted,
and benchmarked in a same-day follow-up round:

| Local name | Source repo | Real placement claim | Result vs. `milestone5-champion` (n=10, both seats) |
|---|---|---|---|
| `public_opponents/funnel_uoft` | [`langsonzhang/Terminal-C1-Midwest-2022`](https://github.com/langsonzhang/Terminal-C1-Midwest-2022) ("Murphy's Lawyers," UofT) | #5 of 24 teams, C1 Midwest Spring 2022 | **WON 10/10**, both seats, no crashes — fastest, most lopsided sweep of any independent opponent tested (mean 10 turns) |
| `public_opponents/summer2022_6th` | [`yip6ga1lok6/C1-Terminal-Summer-2022`](https://github.com/yip6ga1lok6/C1-Terminal-Summer-2022) | 6th of 91 teams, Summer Invitational 2022 | **WON 10/10**, both seats, no crashes (mean 56 turns — a real, drawn-out engagement) |

Full detail (config-mismatch caveats, license/sourcing) in
`docs/STRATEGIC_PRIOR_ART_REPORT.md` source-log #15/#16,
`docs/COMPLIANCE_REPORT.md`, and `docs/REAL_OPPONENT_RESULTS.md` §7.

**Milestone 7 re-confirmation (per the user's explicit follow-up request):**
before doing any further sourcing work, both GitHub accounts
(`langsonzhang`, `yip6ga1lok6`) were checked directly for any *other*
Terminal-related repos that might represent a later/different iteration
(the exact mistake Milestone 6 §1.3 caught and corrected for the Travelling
Salesmen repo, checked for here too rather than assumed not to apply). Both
accounts have **exactly one** Terminal repo each (10 and 11 public repos
respectively, the rest unrelated coursework/personal projects) — there is no
other iteration to find. **`funnel_uoft` and `summer2022_6th` are the
complete, exhaustive coverage of both named sources; no further benchmarking
of these two specific repos is possible or needed.** Both results (10/10
each) stand unchanged and are re-confirmed by the champion's continued clean
performance against them throughout Milestone 7's full regression re-runs.
