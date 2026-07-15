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
