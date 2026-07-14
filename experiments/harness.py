#!/usr/bin/env python3
"""
Minimal local match-running / benchmarking harness for Terminal algos.

Runs N matches between two algo directories (each must contain a `run.sh`,
per the starter kit convention), parses the engine's own authoritative
winner line, and stores one JSON record per match plus a summary.

Deliberately simple (~a few hundred lines), not a framework. See
docs/GAME_SPEC.md section 4.3 for why we trust the "Winner (p1 perspective...)"
line and the replay's final p1Stats/p2Stats as cross-checks.

Usage:
    python3 experiments/harness.py --algo1 python-algo --algo2 baselines/rush -n 10
    python3 experiments/harness.py --algo1 baselines/defense --algo2 baselines/rush -n 20 --swap
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE_JAR = os.path.join(REPO_ROOT, "engine.jar")
REPLAYS_DIR = os.path.join(REPO_ROOT, "replays")
EXP_REPLAYS_DIR = os.path.join(REPO_ROOT, "experiments", "replays")
EXP_RAW_LOGS_DIR = os.path.join(REPO_ROOT, "experiments", "raw_logs")
EXP_RESULTS_DIR = os.path.join(REPO_ROOT, "experiments", "results")

WINNER_RE = re.compile(r"Winner \(p1 perspective, 1 = p1 2 = p2\):\s*(\d)")
SEED_RE = re.compile(r"Random seed:\s*(\d+)")


def _find_java():
    """Prefer a JAVA_HOME set up by tools/setup_java.sh; fall back to PATH java."""
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        candidate = os.path.join(java_home, "bin", "java")
        if os.path.isfile(candidate):
            return candidate
    return shutil.which("java") or "java"


JAVA_BIN = _find_java()


def _run_path(algo_dir):
    algo_dir = algo_dir.rstrip("/")
    if algo_dir.endswith("run.sh"):
        return algo_dir
    return os.path.join(algo_dir, "run.sh")


def run_single_match(algo1_dir, algo2_dir, match_id, timeout_s=180):
    """Runs one match with algo1 as p1, algo2 as p2. Returns a result dict.

    Does not raise on algo crashes / timeouts within the engine itself (the
    engine handles those and reports them); only raises/records `error` if
    the *engine process itself* fails to run or produce a parseable result
    (e.g. this JVM/tooling is broken), which is a harness-level failure
    distinct from a legal in-game loss.
    """
    algo1_run = _run_path(algo1_dir)
    algo2_run = _run_path(algo2_dir)

    before_replays = set(os.listdir(REPLAYS_DIR)) if os.path.isdir(REPLAYS_DIR) else set()

    start = time.time()
    result = {
        "match_id": match_id,
        "p1_algo": algo1_dir,
        "p2_algo": algo2_dir,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    try:
        proc = subprocess.run(
            [JAVA_BIN, "-jar", ENGINE_JAR, "work", algo1_run, algo2_run],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as e:
        result["error"] = "harness_timeout"
        result["duration_s"] = time.time() - start
        result["detail"] = str(e)
        return result
    except Exception as e:  # pragma: no cover - defensive
        result["error"] = "engine_launch_failed"
        result["detail"] = repr(e)
        result["duration_s"] = time.time() - start
        return result

    result["duration_s"] = round(time.time() - start, 2)
    result["engine_returncode"] = proc.returncode

    combined_log = stdout + "\n" + stderr
    raw_log_path = os.path.join(EXP_RAW_LOGS_DIR, f"{match_id}.log")
    os.makedirs(EXP_RAW_LOGS_DIR, exist_ok=True)
    with open(raw_log_path, "w") as f:
        f.write(combined_log)
    result["raw_log"] = os.path.relpath(raw_log_path, REPO_ROOT)

    winner_match = WINNER_RE.search(combined_log)
    result["winner"] = int(winner_match.group(1)) if winner_match else None

    seeds = SEED_RE.findall(combined_log)
    result["random_seeds_seen"] = seeds  # both algos' printed seeds, if any

    result["p1_crashed"] = bool(re.search(r"crashed bootup", combined_log, re.I)) and "AlgoIndex 0" in combined_log
    result["p2_crashed"] = bool(re.search(r"crashed bootup", combined_log, re.I)) and "AlgoIndex 1" in combined_log
    result["any_crash_detected"] = bool(re.search(r"crashed bootup", combined_log, re.I))

    turn_matches = re.findall(r"Performing turn (\d+) of your custom algo strategy", combined_log)
    result["last_turn_seen"] = max((int(t) for t in turn_matches), default=None)

    after_replays = set(os.listdir(REPLAYS_DIR)) if os.path.isdir(REPLAYS_DIR) else set()
    new_replays = list(after_replays - before_replays)
    if new_replays:
        src = os.path.join(REPLAYS_DIR, new_replays[0])
        dst = os.path.join(EXP_REPLAYS_DIR, f"{match_id}.replay")
        os.makedirs(EXP_REPLAYS_DIR, exist_ok=True)
        try:
            shutil.move(src, dst)
            result["replay"] = os.path.relpath(dst, REPO_ROOT)
            _augment_from_replay(dst, result)
        except Exception as e:  # pragma: no cover - defensive
            result["replay_move_error"] = repr(e)
    else:
        result["replay"] = None

    if result.get("winner") is None and not result["any_crash_detected"]:
        result["error"] = result.get("error") or "no_winner_line_found"

    return result


def _augment_from_replay(replay_path, result):
    """Cross-check winner via the replay's final health line (best-effort)."""
    try:
        with open(replay_path) as f:
            lines = [l for l in f if l.strip()]
        if len(lines) < 2:
            return
        last = json.loads(lines[-1])
        turn_info = last.get("turnInfo")
        p1_stats = last.get("p1Stats")
        p2_stats = last.get("p2Stats")
        result["final_turn_number"] = turn_info[1] if turn_info else None
        result["final_p1_health"] = p1_stats[0] if p1_stats else None
        result["final_p2_health"] = p2_stats[0] if p2_stats else None
    except Exception as e:  # pragma: no cover - defensive, replay parsing is best-effort
        result["replay_parse_error"] = repr(e)


def run_batch(algo1_dir, algo2_dir, n, swap=True, timeout_s=180, tag=None):
    """Runs n matches. If swap=True, alternates who is p1/p2 across matches
    (roughly half/half) since p1 vs p2 may not be perfectly symmetric (map
    orientation, and the processing-order/time tie-break noted in
    GAME_SPEC.md 4.3). Returns (results list, summary dict) and writes a
    .jsonl file with one line per match plus a summary line.
    """
    os.makedirs(EXP_RESULTS_DIR, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    safe = lambda s: s.replace("/", "_")
    tag = tag or f"{safe(algo1_dir)}__vs__{safe(algo2_dir)}"
    out_path = os.path.join(EXP_RESULTS_DIR, f"{ts}_{tag}.jsonl")

    results = []
    with open(out_path, "w") as f:
        for i in range(n):
            do_swap = swap and (i % 2 == 1)
            a1, a2 = (algo2_dir, algo1_dir) if do_swap else (algo1_dir, algo2_dir)
            match_id = f"{tag}_{i:03d}"
            r = run_single_match(a1, a2, match_id, timeout_s=timeout_s)
            r["swapped"] = do_swap
            # Normalize winner to "did algo1_dir win" regardless of p1/p2 seat
            if r.get("winner") is not None:
                winner_seat = r["winner"]  # 1 or 2
                r["algo1_won"] = (winner_seat == 1 and not do_swap) or (winner_seat == 2 and do_swap)
            else:
                r["algo1_won"] = None
            results.append(r)
            f.write(json.dumps(r) + "\n")
            f.flush()
            status = "?" if r.get("winner") is None else ("algo1" if r["algo1_won"] else "algo2")
            print(f"[{i+1}/{n}] seat(p1={a1}, p2={a2}) winner_seat={r.get('winner')} "
                  f"-> {status} won | turns~{r.get('last_turn_seen')} | {r.get('duration_s')}s"
                  f"{' | ERROR: ' + r['error'] if r.get('error') else ''}")

        summary = summarize(results, algo1_dir, algo2_dir)
        f.write(json.dumps({"summary": summary}) + "\n")

    print(f"\nResults written to {os.path.relpath(out_path, REPO_ROOT)}")
    print(json.dumps(summary, indent=2))
    return results, summary


def summarize(results, algo1_dir, algo2_dir):
    n = len(results)
    decided = [r for r in results if r.get("algo1_won") is not None]
    algo1_wins = sum(1 for r in decided if r["algo1_won"])
    algo2_wins = sum(1 for r in decided if not r["algo1_won"])
    errors = [r for r in results if r.get("error")]
    crashes_algo1 = sum(1 for r in results if r.get("p1_crashed") and not r.get("swapped")
                        or r.get("p2_crashed") and r.get("swapped"))
    crashes_algo2 = sum(1 for r in results if r.get("p2_crashed") and not r.get("swapped")
                        or r.get("p1_crashed") and r.get("swapped"))
    turns = [r["last_turn_seen"] for r in results if r.get("last_turn_seen") is not None]
    durations = [r["duration_s"] for r in results if r.get("duration_s") is not None]
    return {
        "algo1": algo1_dir,
        "algo2": algo2_dir,
        "n_requested": n,
        "n_decided": len(decided),
        "algo1_win_rate": round(algo1_wins / len(decided), 3) if decided else None,
        "algo2_win_rate": round(algo2_wins / len(decided), 3) if decided else None,
        "algo1_wins": algo1_wins,
        "algo2_wins": algo2_wins,
        "n_errors_or_undecided": len(errors),
        "algo1_crashes": crashes_algo1,
        "algo2_crashes": crashes_algo2,
        "mean_turns": round(sum(turns) / len(turns), 1) if turns else None,
        "min_turns": min(turns) if turns else None,
        "max_turns": max(turns) if turns else None,
        "mean_duration_s": round(sum(durations) / len(durations), 1) if durations else None,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--algo1", required=True)
    ap.add_argument("--algo2", required=True)
    ap.add_argument("-n", "--num-matches", type=int, default=10)
    ap.add_argument("--no-swap", action="store_true", help="Don't alternate p1/p2 seats")
    ap.add_argument("--timeout", type=int, default=180, help="Per-match subprocess timeout (s)")
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()

    run_batch(
        args.algo1, args.algo2, args.num_matches,
        swap=not args.no_swap, timeout_s=args.timeout, tag=args.tag,
    )


if __name__ == "__main__":
    main()
