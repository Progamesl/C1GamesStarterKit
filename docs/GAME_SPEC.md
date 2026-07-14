# Terminal Game Spec — Reconstructed From Source

This document reconstructs the current (Season/compat-mode 5) ruleset **only from files
actually present in the cloned `correlation-one/C1GamesStarterKit` repo** (commit
`72b7589`, "feat/entrypoint (#150)") plus **decompiled bytecode of the bundled
`engine.jar`** (the authoritative Java game engine that actually adjudicates matches).
No values are taken from memory/training data. Every fact below is tagged:

- **Verified** — read directly from a config/source file, or confirmed by decompiling
  the actual `engine.jar` bytecode and/or by observing it in an actual local match run.
- **Strongly supported** — from the official Python `gamelib` reference client shipped
  in the same repo (written by C1, used by every Python algo), but not independently
  cross-checked against the Java engine's own source.
- **Hypothesis** — inferred/likely but not directly confirmed.
- **Rejected** — considered and ruled out.

Do not trust any historical "Terminal"/"C1Games" knowledge not re-derived here — unit
costs/stats and mechanics are known to change between seasons.

## 0. Sources

| Source | What it gives us |
|---|---|
| `game-configs.json` (repo root) | Canonical numeric config: unit stats/costs, resource growth, timing limits. Loaded by the engine at startup (`Config.useConfigFile`). |
| `python-algo/gamelib/*.py` | Official reference client. Encodes board geometry, targeting heuristics, resource plumbing exactly as C1 wrote it, in a form simple enough to fully read. |
| `engine.jar` (28.6MB, unobfuscated compiled Java) | The actual authoritative engine. We decompiled bytecode with `javap` (JDK 17, Temurin) for `com.c1games.terminal.game.GameMain`, `.Game`, `.Config$ConfigVariables`, `.PlayerStats`, `.player.PlayerManager`. Package layout confirms this is a from-scratch C1 engine, not a wrapper around something else. |
| One real local match (`java -jar engine.jar work python-algo/run.sh python-algo/run.sh`) | Confirms the engine actually runs, produces a `.replay`, and prints a `Winner (p1 perspective, 1 = p1 2 = p2): N` line. |

We do **not** have access to `engine.jar`'s original `.java` source, so bytecode-derived
claims are as good as `javap` disassembly makes them — sufficient to read field names,
string constants, and integer/float comparisons, but we did not trace every branch of
every method exhaustively (see open gaps in `COMPLIANCE_REPORT.md`).

## 1. Board Geometry — **Verified**

Source: `python-algo/gamelib/game_state.py` lines 84-85, `game_map.py` lines 32-37.

- `ARENA_SIZE = 28`, `HALF_ARENA = 14`.
- The board is a **diamond** (Union of two 14-row triangles), not a full 28×28 square.
  `GameMap.in_arena_bounds` (`game_map.py:81-104`) computes, for each row `y`, a
  shrinking valid x-range as you move away from the middle rows (y=13/14) — classic
  Terminal diamond shape.
- Your territory is `y < 14` (`HALF_ARENA`), opponent's is `y >= 14`
  (`game_state.py:335`, `attempt_upgrade`/`attempt_remove` checks).
- Four "edges" where mobile units can be deployed and where they path toward:
  `TOP_RIGHT=0, TOP_LEFT=1, BOTTOM_LEFT=2, BOTTOM_RIGHT=3` — each edge is a list of the
  14 border coordinates of that side (`game_map.py:106-150`).
- Mobile units are only spawnable on your own two bottom edges
  (`BOTTOM_LEFT`/`BOTTOM_RIGHT`), and only on unblocked edge cells
  (`game_state.py:307-353`, `can_spawn`).

## 2. Unit Types — **Verified** (values from `game-configs.json:13-143`)

The shipped config still uses Season-3-era internal names/icons (`filter`,
`encryptor`, `destructor`, `ping`, `emp`, `scrambler`), but the **current** Python
starter algo (`python-algo/algo_strategy.py:36-41`) maps these same 8 array slots to
today's names via `shorthand`. Mapping is positional (array index in
`unitInformation`), confirmed by reading both files side by side:

| Idx | Old display name (config) | Current name (algo_strategy.py) | Shorthand | Category |
|---|---|---|---|---|
| 0 | filter | **WALL** | FF | Structure (stationary) |
| 1 | encryptor | **SUPPORT** | EF | Structure |
| 2 | destructor | **TURRET** | DF | Structure |
| 3 | ping | **SCOUT** | PI | Mobile |
| 4 | emp | **DEMOLISHER** | EI | Mobile |
| 5 | scrambler | **INTERCEPTOR** | SI | Mobile |
| 6 | Remove | REMOVE | RM | (meta-action) |
| 7 | Upgrade | UPGRADE | UP | (meta-action) |

`unitCategory: 0` = stationary/structure, `unitCategory: 1` = mobile
(`gamelib/unit.py:52`). Cost tuple is always `[cost1 (SP), cost2 (MP)]`
(`unit.py:61`; `game_state.py` `SP=0`, `MP=1`).

### 2.1 Structures (SP cost)

| Unit | SP cost | Start HP | Attack (vs mobile / vs structure) | Range | Notes | Upgrade effect |
|---|---|---|---|---|---|---|
| WALL | 1.0 | 75 | — | — | pure blocker | `startHealth -> 150` |
| SUPPORT | 7.0 | 30 | — | — | `generatesResource1: 1` (shields nearby mobile units — mechanism read from field name only, see gap below) | `generatesResource2: 2` |
| TURRET | 2.0 | 90 | 5.0 dmg to mobile (`attackDamageWalker`) | 2.5 | `attackDamageTower` is **0** for TURRET, i.e. it cannot hit enemy structures — only mobile units | Upgrade: cost1 -> 4.0 (i.e. **+3.0** more SP), range -> 3.5, dmg -> 15.0 |

All 3 structures: `refundPercentage: 0.75`, `turnsRequiredToRemove: 1`
(`game-configs.json:13-67`).

### 2.2 Mobile units (MP cost = `cost2`)

| Unit | MP cost | Start HP | Speed (tiles/frame) | Dmg vs mobile / vs structure | Range | Self-destruct dmg (mobile/structure) | Breach dmg | Self-destruct trigger |
|---|---|---|---|---|---|---|---|---|
| SCOUT | 1.0 | 15 | 1 | 2.0 / 2.0 | 3.5 | 15.0 / 15.0 | 1.0 | after 5 steps without a target in range |
| DEMOLISHER | 3.0 | 5 | 0.5 | 6.0 / 6.0 | 4.5 | 5.0 / 5.0 | 1.0 | same |
| INTERCEPTOR | 1.0 | 40 | 0.25 | 20.0 / (0, i.e. can't hit structures) | 3.5 | 40.0 / 40.0 | 1.0 | same |

(`game-configs.json:68-129`; `selfDestructStepsRequired: 5`,
`selfDestructRange: 1.5`, `metalForBreach: 1.0` for all three.)

**Gap (Hypothesis, not Verified):** exact self-destruct trigger semantics ("after 5
steps without a target") and SUPPORT's shield mechanism (range, per-unit bonus,
`shieldBonusPerY`) are inferred from field *names* in `gamelib/unit.py`
(`shieldRange`, `shieldPerUnit`, `shieldBonusPerY`, `selfDestructStepsRequired`) and
common Terminal knowledge, but the shipped `game-configs.json` has `shieldRange: 0`
for SUPPORT and no `shieldPerUnit`/`shieldBonusPerY`/`selfDestructStepsRequired` keys
under SUPPORT at all — meaning **we could not fully verify SUPPORT's actual shielding
formula from config alone**; only that it exists as a mechanic in the client code.
Flagged in `COMPLIANCE_REPORT.md` as an open gap.

## 3. Resources — **Verified** (`game-configs.json:158-172`, cross-checked against
`gamelib/game_state.py:253-283` `project_future_MP`)

Two resource pools per player, called **SP** (structure points, internal engine name
`metal`) and **MP** (mobile points, internal engine name `food` — confirmed via
decompiled `com.c1games.terminal.game.PlayerStats` fields `metal`/`food`,
`getMetal()`/`getFood()`).

- `startingHP: 40.0` — starting player health (**not** structure HP; this is the score
  you lose when breached).
- `startingCores (SP): 40.0`, `startingBits (MP): 5.0`.
- `coresPerRound: 5.0` — flat SP income every turn.
- `bitsPerRound: 5.0` plus ramp: `bitGrowthRate: 1.0` extra MP income per round,
  scaled by `turnIntervalForBitSchedule: 10` (i.e. +1.0 additional MP/round baseline
  every 10 turns, per the `project_future_MP` formula: `MP_gained = bitsPerRound +
  bitGrowthRate * floor(turn / turnIntervalForBitSchedule)`).
- `bitDecayPerRound: 0.25` — unspent MP decays 25%/turn (`MP *= (1 - 0.25)` before
  adding new income — confirmed in `project_future_MP` source).
- `maxBits: 150.0` — MP cap.
- `roundStartBitRamp: 10`, `bitRampBitCapGrowthRate: 5.0` — govern the MP cap ramp
  (exact formula not traced in engine bytecode — **Strongly supported**, not fully
  Verified against engine).
- SP does **not** appear to decay (no `spDecayPerRound` key in config).

## 4. Turn Structure, Timing & Win Conditions

### 4.1 Turn cap — **Verified from `engine.jar` bytecode**

Decompiling `com.c1games.terminal.game.GameMain.runLoop` (`javap -v`, bytecode offsets
~627-648) shows, at the top of every loop iteration:

```
if (this.turn == 100 || this.gameover) {
    this.processEndGame(true);   // force end
    return;
}
```

i.e. **the game is hard-capped at turn 100.** If neither player has been reduced to
`health <= 0` (and no crash/timeout has ended it earlier), the game is forced to end
at turn 100 and the winner is decided by the tie-break rules below (§4.3). This is not
present anywhere in `game-configs.json` or the Python `gamelib` — it is a hardcoded
engine constant, only found by reading the compiled bytecode directly. No config file
we found lets you change this.

### 4.2 Per-turn compute time limits — **Verified** (`game-configs.json:145-157`,
names cross-checked against decompiled `com.c1games.terminal.game.PlayerStats` fields
`softTimeLimit`, `timeoutDamageTaken`, `timeoutDeath`)

- `waitTimeBotSoft: 5000` ms / `waitTimeBotMax: 35000` ms — soft/hard per-turn time
  budget when run via the local CLI ("work" mode, what `run_match.py`/our harness use).
- `playWaitTimeBotSoft: 10000` ms / `playWaitTimeBotMax: 40000` ms — separate, more
  generous limits used in "play" mode (used by the website / manual play).
- `waitForever: false` — confirms timeouts are actually enforced, not disabled.
- Exceeding the soft limit repeatedly and/or the hard limit results in
  `timeoutDamageTaken` / eventually `timeoutDeath` per `PlayerStats`
  (`dealTimeDamage`, `getTimeoutDeath`) — **Strongly supported**: field names and
  method names confirm the mechanism exists and is used in the win-condition
  tie-break (§4.3), but we did not trace the exact damage-per-ms formula in bytecode.
- **Compliance implication:** our own algo must reliably finish each turn well under
  5s (soft) and never approach 35s (hard) in local/tournament "work" mode — this is a
  hard constraint on our search/planning time budget per turn.

### 4.3 Win condition & tie-break — **Verified from `engine.jar` bytecode**

Decompiled `com.c1games.terminal.game.GameMain.processEndGame(boolean forceEnd)`:

1. If neither player's `totalHP <= 0` and `forceEnd` is false, the method returns
   immediately (game continues). This is what makes the turn-100 cap force a
   resolution: it calls `processEndGame(true)`, skipping this early-return.
2. **Primary rule: higher remaining `totalHP` (player health) wins.** (Two redundant
   float comparisons in bytecode, `fcmpl`/`fcmpg`, both encode "higher HP wins".)
3. **Tie-break #1 (both HP equal, including the common "both simultaneously reduced to
   ≤0" case): the player with the *lower* `totalTimeSpent` (cumulative computation
   time used across the whole game, in ms) wins.** This is a genuine strategic
   consideration: an otherwise-tied game rewards the faster bot.
4. **Tie-break #2 (HP tied AND cumulative time spent exactly tied): decided by
   `random.nextBoolean()`** — a literal coin flip inside the engine
   (`java.util.Random.nextBoolean()` call, confirmed in bytecode at offset ~145).
5. The engine prints `Winner (p1 perspective, 1 = p1 2 = p2): <1|2>` to stdout and
   records a structured summary (`winner`, `turns`, `frames`, `duration`,
   `crashed`, `timeout_death`, resource-spend stats, etc. per player) — this is our
   harness's authoritative signal (see §7 of `COMPLIANCE_REPORT.md`).

**Practical implication for strategy:** in truly symmetric/mirror matchups (e.g. our
algo vs itself), the game can come down to which process used less cumulative CPU
time — so being fast is not just about avoiding timeouts, it can directly decide close
games.

### 4.4 Crashes — **Verified** (`com.c1games.terminal.game.player.PlayerManager`
`checkCrashed()`/`checkProcessCrashed(int)`, string constant `"AlgoIndex %d crashed
bootup: %s"`)

A crashed algo process is detected and presumably auto-loses / is scored specially
(the `processEndGame` summary map has an explicit `crashed` boolean per player) — we
did not trace the exact win/HP consequence of a crash in bytecode (**Hypothesis**:
almost certainly an immediate loss for the crashed player, standard for this genre of
competition, but not directly confirmed).

## 5. Targeting logic — **Strongly supported** (not independently verified against
engine, since engine.jar has its own separate `TargetAndAttackSystem` implementation
we did not decompile in full; this is the *reference client's own estimate*, used by
`GameState.get_target`/`get_attackers`, documented in its own docstring,
`gamelib/game_state.py:538-615`):

> Targeting priority: **Infantry (mobile) > Nearest unit > Lowest health > Lowest Y
> position (from the attacker's own perspective, inverted for player 1) > Closest to
> the board's horizontal center (x = 13.5)**.

A unit with `attackDamageTower == 0` cannot target structures at all (used by TURRET,
which has `attackDamageTower: 0` in config — TURRET can only ever hit mobile units,
not enemy structures) and a unit with `attackDamageWalker == 0` cannot target mobile
units (INTERCEPTOR has `attackDamageTower: 0` so — by the same logic — INTERCEPTOR
cannot hit structures either, matching its role as an anti-mobile-unit defender).

## 6. Manually verified: an actual match runs end-to-end — **Verified**

```
$ java -jar engine.jar work python-algo/run.sh python-algo/run.sh
...
Winner (p1 perspective, 1 = p1 2 = p2): 1
...
```

Ran multiple times locally; a `.replay` file is produced each time under `replays/`,
loadable at https://terminal.c1games.com/playground. Game length varied
run-to-run (turn ~10-11 in our sample runs) due to the starter algo's own randomized
interceptor placement (`random.seed` printed each run) — i.e. **the starter algo vs.
itself is not fully deterministic**, which is itself a relevant fact for benchmarking
(see `experiments/`).

## 7. What we deliberately did NOT verify (see `COMPLIANCE_REPORT.md` for the full gap list)

- Exact SUPPORT shield formula/range/stacking.
- Exact MP-cap ramp formula (`roundStartBitRamp`/`bitRampBitCapGrowthRate`).
- Exact timeout-damage-per-ms formula and crash-loss mechanics.
- Full `TargetAndAttackSystem`/pathfinding engine bytecode (we relied on the
  reference Python client's own equivalent logic/docstrings instead, which is
  official but not proven byte-identical to the Java engine).
- Any organizer-specific tournament rules not present in this repo (submission
  deadlines, ladder format, disconnection/reconnection handling, anti-cheat, etc.) —
  we have no portal/organizer access.
