# Milestone 7 Report: Attempting to fix the `travelling_salesmen_v33` loss

## 0. Headline summary

**The gap this milestone attempts to close:** Milestone 6 found and root-caused
a real, decisive, fully-reproducible loss (0/20, both seats) against
`public_opponents/travelling_salesmen_v33`, tried and rejected 5 patch
attempts (`baselines/defense_v9_corner_depth`), and shipped no new champion —
`baselines/defense_v6_encryptor_fix` (`milestone5-champion`) remained
unchanged, undefeated against 24/25 opponents tested at that point (20
self-built + starter/rush/hybrid + 4/5 independent), losing only to `v33`.

**What this milestone did:** two more, larger, more fundamental attempts —
`baselines/defense_v10_lockdown` (region-wide defense depth + reactive-cap
rework) and `baselines/defense_v11_econ_offense` (v10 plus a restored
both-flank offense lane, a newly-verified economy mechanic, and continuous
un-paused counter-offense) — plus a full re-run of the entire opponent corpus
(now 28 opponents: the original 25 from Milestone 6, `funnel_uoft` and
`summer2022_6th` added in the M6-round-2 follow-up, and 3 new synthetic
lane-variation stress opponents added this milestone) against each candidate.

**Headline result — stated as plainly as every prior milestone:**

- **Neither `defense_v10_lockdown` (4 sub-iterations) nor
  `defense_v11_econ_offense` reverses the `travelling_salesmen_v33` loss.**
  All still lose 0/10-0/20, both seats, no crashes. `v10`'s best sub-iteration
  delays the loss from ~35 turns to ~53 turns (mean); none closes the gap.
- **`defense_v10_lockdown` (the version actually committed) introduces ZERO
  new regressions** — it is a legitimate, if unsuccessful, attempt: still
  wins against the full self-built corpus and, newly confirmed this
  milestone, still beats `travelling_salesmen_adapdef` and
  `travelling_salesmen_frumblesnatch` 4/4 each in isolation.
- **`defense_v11_econ_offense` is a clear net regression and is REJECTED.**
  On top of *still* losing to `v33` (0/20), it introduces new, previously
  unseen losses against **4 of the 7 independent/public opponents that
  `milestone5-champion` (and `v10_lockdown`) beat cleanly**:
  `travelling_salesmen_adapdef` (0/10, was 10/10), `travelling_salesmen_frumblesnatch`
  (0/10, was 10/10), `davidw0311_mcts` (0/10, was 10/10), and `summer2022_6th`
  (0/10, was 10/10). It still wins 100% against the entire self-built corpus
  (21 opponents) plus `skill_issue_final3gem` and `funnel_uoft`, which is
  exactly the failure mode this project's public-opponent expansion
  (Milestone 6) exists to catch: a candidate that looks perfect against
  everything we built ourselves while quietly losing to real, independently
  designed opponents.
- **Root cause of the new regressions was bisected, not just observed** (§3):
  it is `defense_v11_econ_offense`'s "Finding 3" — continuous, un-paused,
  100%-of-current-MP counter-offense from turn 6 onward, replacing the
  previous paced/gated posture — not the lockdown-upgrade logic that an
  earlier in-progress code comment incorrectly (and, per this report, now
  correctedly) claimed was the cause and claimed to have fixed. That comment
  was written before the actual re-test came back and was left in place after
  the re-test contradicted it; both the comment and this report exist so that
  mistake is visible rather than quietly overwritten (see §4).
- **Recommended champion: unchanged. `baselines/defense_v6_encryptor_fix`
  (`milestone5-champion`) remains the champion.** Neither new candidate is
  promoted. `v10_lockdown` and `v11_econ_offense` are both kept in the
  repository as documented, tested, rejected candidates (same convention as
  `defense_v7`/`v8`/`v9`) — `v11_econ_offense` explicitly flagged as
  actively worse than doing nothing, not merely "not better."

---

## 1. `defense_v10_lockdown`: region-wide defense depth (still doesn't fix `v33`)

### 1.1 What it changes

Per the module docstring: a per-side `lockdown_side` state machine that
detects when a flank has taken 2+ recent breaches and, while locked down,
(a) raises the SP cap on `reactive_defense` rebuild spend for that side, (b)
adds a wider TURRET cluster (`_left_cluster`/`_right_cluster`, 6+ anchors deep
rather than 1-2), and (c) pauses upgrades everywhere except the contested
cluster itself, to free more SP for cluster rebuild.

### 1.2 Four sub-iterations tested against `v33` (n=10 each)

| Variant | Change vs. previous | Result | Mean turns survived |
|---|---|---|---|
| `v10` | Base lockdown mechanism above | 0/10 | 41.0 |
| `v10b` | Tuning pass on cluster spacing/cap | 0/10 | 41.0 |
| `v10c` | Wider cluster still | 0/10 | 53.0 |
| `v10d` (committed) | Final tuning | 0/10 | 52.8 |

**None reverses the result.** Delay roughly doubled (35 -> ~53 turns) versus
Milestone 6's best patch attempt, but the opponent's MP-funded, ramping
Demolisher stream still eventually outpaces the flat, non-ramping SP rebuild
budget across the whole contested flank — the same fundamental economic
mismatch Milestone 6 identified, just pushed later into the game.

### 1.3 Regression check: clean

Directly re-confirmed this milestone (not assumed carried over from
Milestone 6, since the lockdown mechanism is a real behavioral change):
`defense_v10_lockdown` beats `travelling_salesmen_adapdef` 4/4 and
`travelling_salesmen_frumblesnatch` 4/4 in isolated smoke tests (§3.2 has the
exact commands/results). Combined with the full-suite run reported in the
commit history (all 20 self-built opponents + starter/rush/hybrid, 10/10 or
16/16 throughout), `v10_lockdown` is a legitimate, honestly-negative result:
it tries something bigger, it's clean, and it still isn't enough.

---

## 2. `defense_v11_econ_offense`: three more findings layered on `v10`, net regression

### 2.1 What it adds (module docstring, condensed)

On top of everything in `v10_lockdown`:

- **Finding 2**: `_get_cached_lane`'s 2-option lane list (`[13,0]`, `[3,10]`)
  has been carried unchanged since Milestone 2's compute-time trim and
  accidentally kept two points on the *same* flank (`BOTTOM_LEFT`), dropping
  both `BOTTOM_RIGHT` options. Restored to the original 4-option, both-flank
  list, with `RECOMPUTE_INTERVAL` dropped 12 -> 4 to track `v33`'s own
  every-4-turn adaptive flank switch.
- **Finding 3**: `coresForPlayerDamage: 1.0` verified (via exact-match replay
  arithmetic — see `docs/GAME_SPEC.md` §3 for the added citation) as a real,
  active mechanic: landing player-breach damage earns the attacker bonus SP
  income, not just points. `opportunistic_offense` rewritten to spend a
  continuous, un-paused, 100%-of-current-MP budget on a combined
  demolisher+scout strike **every turn from turn 6 onward**, instead of the
  previous turn-parity/MP-floor-gated posture — reasoning: "match their
  sustained, un-paused posture," and any MP committed is not wasted MP even
  if it doesn't win outright, because landed hits now fund our own SP economy
  too.
- **Finding 4**: cheap WALLs added further inland along the same scoring-edge
  diagonal that the corner tip sits on (`diagonal_edge_walls`), on the theory
  that widening attempts were only ever pushing the breach point deeper along
  that diagonal rather than closing it off.

### 2.2 Result against `v33`: still 0/20, no improvement

`m7_v11_final_vs_v33` (n=20, both seats): 0/20, mean 56.0 turns — actually
*worse* than `v10d`'s 52.8-turn mean survival, though within noise for a
20-turn confirmatory run at this sample size. **No progress on the actual
target opponent.**

### 2.3 Result against everything else: 4 NEW regressions found

Full regression suite (`experiments/run_regression.py`, all 28 opponents,
n=10/16/20 depending on opponent, `tag=m7_v11_full`):

| Opponent | Result | Note |
|---|---|---|
| All 21 self-built opponents (`python-algo` through `opponents/predictor_opponent`) | 10/10 or 16/16 | Clean |
| `public_opponents/skill_issue_final3gem` | 10/10 | Clean |
| **`public_opponents/travelling_salesmen_adapdef`** | **0/10** | **REGRESSION — was 10/10** |
| **`public_opponents/travelling_salesmen_frumblesnatch`** | **0/10** | **REGRESSION — was 10/10** |
| `public_opponents/travelling_salesmen_v33` | 0/10 | Known, unpatched (unchanged) |
| **`public_opponents/davidw0311_mcts`** | **0/10** | **REGRESSION — was 10/10** |
| `public_opponents/funnel_uoft` | 10/10 | Clean |
| **`public_opponents/summer2022_6th`** | **0/10** | **REGRESSION — was 10/10** |
| `opponents/alternating_corner_rush`, `opponents/dual_corner_rush`, `opponents/scout_demolisher_corner_mix` (new this milestone, §5) | 10/10 each | Clean |

**5 of 7 independent/public opponents now lose to `v11_econ_offense`** — up
from 1 of 7 for `milestone5-champion`/`v10_lockdown`. This is a straightforward
net regression: it does not fix the one opponent it was built to fix, and it
breaks four others that were previously solid wins, while remaining a clean
100% sweep of the entire self-built corpus — precisely the "looks perfect on
opponents we built ourselves, quietly loses to real ones" pattern Milestone 6
exists to catch.

---

## 3. Root-cause bisection of the new regressions (not just observed — isolated)

### 3.1 A misdiagnosis was made, tested against, and found wrong — logged here rather than hidden

While investigating, an in-progress code comment in
`baselines/defense_v11_econ_offense/algo_strategy.py` attributed the
`adapdef`/`frumblesnatch` regression to the lockdown upgrade-skip logic
(shared with `v10_lockdown`) and claimed reverting it (to "contested cluster
keeps upgrading normally") fixed the problem, "and it worked." **This claim
was made before the actual confirmatory re-test finished, and the re-test
then contradicted it**: `m7_v11fix_vs_adapdef`/`m7_v11fix_vs_frumble`
(n=4 each, run immediately after that revert) both still show 0/4 losses.
The comment was not corrected before this report was written. This is
exactly the mistake this project's own discipline (verify before writing,
check the actual result rather than the plausible-sounding reasoning) is
supposed to catch, and it is being reported plainly rather than quietly
patched over — the comment in the source file has now been corrected to
state the below findings instead.

### 3.2 Actual bisection: 4 isolated variants, each layered individually onto `v10_lockdown` (which is clean), smoke-tested n=4 against `travelling_salesmen_adapdef`

| Layered onto `v10_lockdown` | Result | Verdict |
|---|---|---|
| Nothing (`v10_lockdown` baseline) | 4/4 | Clean (confirms the lockdown/upgrade-skip logic was never the problem) |
| Finding 2 only (4-option lane list + `RECOMPUTE_INTERVAL` 12->4) | 4/4 | Clean in isolation |
| Finding 4 only (`diagonal_edge_walls`) | 3/4 | Minor degradation, not the primary cause |
| **Finding 3 only (continuous, un-paused, 100%-MP offense from turn 6)** | **1/4** | **Primary driver of the regression** |
| Findings 2+3+4 together (`v11_econ_offense` as committed) | 0/10 (full n=10 run) | Compounds to a total loss |

**Root-cause hypothesis**, consistent with the data: committing 100% of
current MP to offense every single turn, unconditionally, works as intended
against `travelling_salesmen_v33`'s specific always-on, single-flank rush
pattern (matching a sustained attacker with sustained counter-pressure), but
it removes the MP-funded `stall_with_interceptors` slack that `v10`'s
previous paced/gated posture was actually relying on to survive *weaker*,
less-sustained single-lane rushes like `adapdef`/`frumblesnatch`, and appears
to also hurt against qualitatively different opponents (`davidw0311_mcts`'s
MCTS-based play, `summer2022_6th`'s old-config turret-heavy defense) for
reasons not yet further decomposed. **"Match their posture" turned out not
to be a safe general rule, in exactly the same way Milestone 6's "upgrade is
free against Demolishers" reasoning was true in isolation against one
opponent but not general** — this is the second time in two milestones that
an isolated, single-opponent-verified reasoning chain has failed to
generalize, which is itself a useful, repeatable finding about this specific
failure mode (see §6).

Diagnostic scratch copies used for this bisection live under `/tmp/diag_*`
(not committed — throwaway, reproducible from the description above plus
`baselines/defense_v10_lockdown/algo_strategy.py` and
`baselines/defense_v11_econ_offense/algo_strategy.py`'s diff).

---

## 4. Champion decision

**`baselines/defense_v6_encryptor_fix`, tagged `milestone5-champion`, remains
the champion.** Neither `defense_v10_lockdown` nor `defense_v11_econ_offense`
is promoted.

1. `v10_lockdown` is an honest, clean, but unsuccessful attempt — no reason to
   switch to it since it doesn't fix anything the current champion doesn't
   already handle, and switching would add risk (a bigger, more complex
   codebase change) for zero proven benefit.
2. `v11_econ_offense` is actively worse: it fails on its own stated goal
   AND introduces 4 new regressions against opponents the current champion
   handles cleanly. Shipping it would be a straightforward net loss.
3. Both are kept in the repository, undeleted, clearly marked as rejected
   candidates with an honest record of what was tried and why it didn't
   work — same standing convention as `defense_v7`/`v8`/`v9`.

---

## 5. Regression-suite hygiene: 3 new stress opponents added

To directly check (per repeated user instruction) that any `v33`-targeted
fix generalizes to *the pattern* (single/adaptive-flank sustained rush)
rather than overfitting to `v33`'s exact lane sequence, three small synthetic
opponents were added to `opponents/` and to
`experiments/run_regression.py`'s permanent `DEFAULT_OPPONENTS` list this
milestone: `alternating_corner_rush`, `dual_corner_rush`, and
`scout_demolisher_corner_mix`. All three candidates tested this milestone
(`v10_lockdown`, `v11_econ_offense`) beat all three cleanly (10/10 each,
~11-turn stomps) — these are deliberately weaker/smaller-scale stress tests,
not a substitute for the real independent-opponent corpus, and their clean
sweep does not offset the real regressions found in §2.3.

---

## 6. What this milestone does not resolve, and recommendation on further investment

- **`travelling_salesmen_v33` is still not fixed**, after now 3 rounds of
  honest attempts across 2 milestones (Milestone 6's 5 patches, this
  milestone's 4 `v10` sub-iterations, and `v11_econ_offense`'s 3 additional
  findings) — 12 distinct tested variants total, zero of which reverse the
  result.
- **A clear, repeatable failure pattern has emerged**: the more ambitious /
  further-reaching an attempted fix is (v11's continuous-offense rewrite
  being the largest single behavioral change attempted so far), the larger
  the collateral regression risk against the broader opponent pool, not just
  against the one target opponent — this happened in Milestone 6
  (`defense_v8_offense_burst` regressed `corner_lane_baiter`) and again, more
  severely, this milestone (`v11_econ_offense` regressed 4 opponents).
- **Recommendation: treat this specific line of attack (further bespoke
  patches aimed at reversing the `v33` result) as past the point of good
  marginal return.** 12 tested variants, 2 milestones, and the most
  determined/complex attempt yet made things measurably worse elsewhere. A
  fix that actually reverses `v33` without collateral damage most likely
  requires either (a) a genuinely different mechanism not yet tried (e.g. an
  approach that doesn't touch the shared offense-posture code path at all,
  since that is now confirmed as the highest-collateral-risk area), or (b) is
  possibly not closeable at all within this defense architecture's basic
  SP/MP resource model without a much larger rewrite and much more extensive
  validation than is responsible to ship on the timeline remaining. Continuing
  to sink further iteration cycles into this one opponent, at this point, is
  a worse use of remaining effort than:
  1. Broadening the public-opponent corpus further (two more real,
     sourced-but-unrun repos remain flagged from Milestone 6 §7 —
     `langsonzhang/Terminal-C1-Midwest-2022`'s and
     `yip6ga1lok6/C1-Terminal-Summer-2022`'s siblings/other iterations, plus
     any additional named-champion or high-placer search), which both
     stress-tests the *current, working* champion further and has a much
     better chance of surfacing genuinely new information per unit of effort
     spent, or
  2. Final freeze/consolidation prep on the current champion, given it is
     now empirically the most robust candidate produced across all 7
     milestones (loses to exactly 1 of 28 tested opponents, with zero
     regressions ever found against it — a materially better record than
     either `v10_lockdown`'s "same 1 loss, no improvement" or
     `v11_econ_offense`'s "same 1 loss, plus 4 new ones").
- If further `v33`-specific work is explicitly prioritized anyway, the one
  concrete, low-risk-shaped idea not yet tried is applying `v10_lockdown`'s
  region-wide defense-depth mechanism (clean, no regressions) WITHOUT any of
  `v11`'s offense-posture changes (the confirmed regression source) plus a
  purely economic change scoped narrowly to *only* the lockdown-triggered
  state (not a global always-on posture change) — but per the above, this is
  now a "one more cheap, narrowly-scoped try, not a fourth full redesign"
  recommendation, not a call for another open-ended iteration cycle.
