#!/usr/bin/env python3
"""
Milestone 4 regression driver: runs one candidate against the full opponent
corpus (all opponents/*, the other baselines, and the starter python-algo),
under whatever game-configs.json is currently active (the corrected
"High School Terminal 2026" config as of Milestone 4).

Usage:
    python3 experiments/run_regression.py --candidate baselines/defense_v6_encryptor_fix \
        --tag m4_v6 -n 10 [--turtle-n 20] [--opponents-file opponents_list.txt]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness  # noqa: E402

REPO_ROOT = harness.REPO_ROOT

DEFAULT_OPPONENTS = [
    "python-algo",
    "baselines/rush",
    "baselines/hybrid",
    "opponents/adaptive_reactive",
    "opponents/burst_hoarder",
    "opponents/double_funnel_maze",
    "opponents/escorted_combined_arms",
    "opponents/funnel_maze",
    "opponents/lategame_defector",
    "opponents/middle_rush_exploit",
    "opponents/multi_lane_saturation",
    "opponents/single_leak_turtle",
    "opponents/sunk_cost_recipe_switcher",
    "opponents/turtle_survivor",
    # Milestone 5 additions: SUPPORT-targeting adversarial opponents (built
    # against defense_v6_encryptor_fix's specific placement/upgrade logic)
    # plus a held-out corpus built blind from unimplemented prior-art
    # archetypes (docs/STRATEGIC_PRIOR_ART_REPORT.md) -- see
    # docs/MILESTONE_5_REPORT.md.
    "opponents/support_sniper",
    "opponents/corner_lane_baiter",
    "opponents/shield_race_rusher",
    "opponents/signature_detector",
    "opponents/minimax_lookahead",
    "opponents/predictor_opponent",
    # Milestone 6 additions: everything above this line is SELF-BUILT (either by
    # us or, for python-algo, the official starter template) -- a 100% win rate
    # against it is evidence of robustness against threats we imagined, not
    # against genuinely independent design. The opponents below are real,
    # substantial, publicly-sourced Terminal python-algo code from other teams'
    # GitHub repos, vetted as complete/runnable (not empty starter forks) and
    # used strictly as unmodified black-box test opponents (never copied into
    # our own code) -- see docs/COMPLIANCE_REPORT.md for sourcing/license notes
    # and docs/MILESTONE_6_REPORT.md for the full vetting + benchmark record.
    # IMPORTANT: `travelling_salesmen_v33` is a REAL, CURRENTLY-UNRESOLVED LOSS
    # for milestone5-champion (0/20, both seats) -- this is intentionally kept
    # in the permanent suite so this is never silently hidden by only counting
    # wins. See docs/MILESTONE_6_REPORT.md for full root-cause + patch-attempt
    # writeup (multiple honest fix attempts made, none fully closed the gap).
    "public_opponents/skill_issue_final3gem",
    "public_opponents/travelling_salesmen_adapdef",
    "public_opponents/travelling_salesmen_frumblesnatch",
    "public_opponents/travelling_salesmen_v33",
    "public_opponents/davidw0311_mcts",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("-n", type=int, default=10)
    ap.add_argument("--turtle-n", type=int, default=None,
                     help="Override sample size specifically for opponents/turtle_survivor")
    ap.add_argument("--opponents", nargs="*", default=None,
                     help="Override the opponent list (defaults to DEFAULT_OPPONENTS)")
    ap.add_argument("--timeout", type=int, default=180)
    args = ap.parse_args()

    opponents = args.opponents if args.opponents else DEFAULT_OPPONENTS

    overall = []
    for opp in opponents:
        n = args.n
        if args.turtle_n is not None and opp == "opponents/turtle_survivor":
            n = args.turtle_n
        safe_opp = opp.replace("/", "_")
        tag = f"{args.tag}_vs_{safe_opp}"
        print(f"\n{'='*70}\n{args.candidate} vs {opp} (n={n})\n{'='*70}")
        results, summary = harness.run_batch(
            args.candidate, opp, n, swap=True, timeout_s=args.timeout, tag=tag,
        )
        overall.append((opp, summary))

    print(f"\n\n{'#'*70}\nFULL REGRESSION SUMMARY for {args.candidate}\n{'#'*70}")
    for opp, summary in overall:
        wr = summary.get("algo1_win_rate")
        wins = summary.get("algo1_wins")
        n_decided = summary.get("n_decided")
        print(f"  {opp:40s} {wins}/{n_decided}  (win_rate={wr})")


if __name__ == "__main__":
    main()
