# Source

- Repo: https://github.com/langsonzhang/Terminal-C1-Midwest-2022
- Folder: `funnel_INTER/`
- Team: "Murphy's Lawyers" (Langson Zhang, Stan Hua, George/`CardboardTank`), UofT
- Real placement claim: #5 of 24 teams, C1 Midwest Spring 2022 (hosted by
  Citadel), against competitors from CMU, UMich, and UIUC (per repo's own
  README, with a linked certificate of participation).
- License: standard Correlation One starter-kit `License.md` (covers
  starter-kit-derived files only; no separate license found for the team's
  own strategy code additions -- see docs/COMPLIANCE_REPORT.md sec 7).
- 723-line `algo_strategy.py` plus 4 supporting modules (`attack_method.py`,
  `attack_strat.py`, `BoundedBox.py`, `build_alt_defenses.py`) -- real,
  substantial, non-stub code.
- Config mismatch (checked directly): ships an old `seasonCompatibilityMode:
  5`-era config -- Wall `startHealth: 60.0` (vs our `40.0`), Support
  `startHealth: 1.0` completely unshielded pre-upgrade with upgrade
  `shieldPerUnit: 1` (vs our `2.0`/`4`) -- their Support was apparently much
  squishier and less shield-potent than ours under our corrected config.
- Benchmark result vs `milestone5-champion`: WON 10/10, both seats, no
  crashes, decisively (mean 10 turns, 31-0 points_scored observed) -- the
  fastest, most lopsided sweep of any independent opponent tested in this
  project. See docs/REAL_OPPONENT_RESULTS.md sec 7.2.
- Usage: unmodified local black-box test opponent only. Never copied or
  adapted into this project's own baselines.
- `documentation/` (Sphinx build artifacts) stripped before committing, same
  convention as every other `public_opponents/*` folder.
