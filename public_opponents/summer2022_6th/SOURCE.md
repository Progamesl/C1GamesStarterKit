# Source

- Repo: https://github.com/yip6ga1lok6/C1-Terminal-Summer-2022
- Folder: `python-algo/` (repo also ships `rust-algo/` and `java-algo/`
  variants of unclear relative finality/strength -- the README does not say
  which language was the actual final submission, only that "this repo is
  the algo of the final submission of this competition." `python-algo` is
  the one run here since it drops directly into this project's harness; this
  ambiguity is logged honestly, not resolved.)
- Team: yip6ga1lok6 (individual GitHub account; team name not further
  identified in-repo)
- Real placement claim: 6th of 91 participating teams, Correlation One
  Terminal Summer Invitational 2022 (per repo's own README).
- License: standard Correlation One starter-kit `License.md` (covers
  starter-kit-derived files only; no separate license found for the team's
  own strategy code additions -- see docs/COMPLIANCE_REPORT.md sec 7).
- 752-line `algo_strategy.py` -- real, substantial, non-stub code.
- Config mismatch (checked directly): ships an old `seasonCompatibilityMode:
  5`-era config -- Wall `startHealth: 12.0` (vs our `40.0`, much squishier),
  Turret `attackDamageWalker: 16.0`/`cost1: 6.0` (vs our base `5.0`/`2.0` --
  their base Turret hit much harder but cost 3x more).
- Benchmark result vs `milestone5-champion`: WON 10/10, both seats, no
  crashes (mean 56 turns -- a real, drawn-out engagement, unlike
  `funnel_uoft`, but still a clean sweep). See
  docs/REAL_OPPONENT_RESULTS.md sec 7.2.
- Usage: unmodified local black-box test opponent only. Never copied or
  adapted into this project's own baselines.
- `documentation/` (Sphinx build artifacts) stripped before committing, same
  convention as every other `public_opponents/*` folder.
