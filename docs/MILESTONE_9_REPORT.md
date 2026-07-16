# Milestone 9 Report — MP-funded defense and uploaded-replay mechanisms

Evidence labels are used literally:

- **Verified** — directly observed in source/config, replay events, or completed
  benchmarks.
- **Strongly supported** — a controlled ablation or multiple independent
  observations support the causal interpretation.
- **Hypothesis** — plausible explanation not isolated by the current evidence.
- **Rejected** — the tested implementation failed its stated gate.

## 1. Scope and bounded decision

This milestone tested exactly the requested three mechanisms, all derived from
the accepted `baselines/defense_v6_encryptor_fix`, not v10-v13:

1. **A — adaptive Interceptor screen:** general action-frame classification of
   repeated Demolishers and large Scout bursts, with three coordinate families
   and three MP-spend profiles.
2. **B — replay-derived dense opening:** 18 base-range Turrets, two upgraded
   endpoint Walls, and delayed stacked Supports.
3. **C — combined:** B plus the best A coordinate family, including an explicit
   bisection of the first combined policy's offense-suppression regression.

The search was stopped after those mechanisms and their bounded corrections.
No opponent name/path is inspected by any candidate.

## 2. Preservation checkpoint

**Verified:** the pre-search state was preserved and pushed before mechanism
work:

| Commit | Preserved evidence |
|---|---|
| `7a916e3` | `experiments/analyze_replay.py` |
| `58b8ada` | rejected v13 signature-response attempt and debug JSONL |
| `d36b2f0` | `replay_shield_stack`, regression registration, supported and no-support baseline evidence |

The raw uploaded replay was not copied into Git. `.replay` files are already
ignored as external/raw artifacts, and the source/licensing status is unknown.
The stable derived metrics and provenance are preserved in this report.

## 3. Uploaded replay analysis

Input:
`/home/ubuntu/.cursor/projects/workspace/uploads/6-4-2026-15-15-3_b9bf.replay`

- **Verified:** 562,489 bytes, 212 non-empty replay records.
- **Verified:** SHA-256
  `5be9117249587489316c46d752fa58f400d3c0952dabe63d0af83ac50dad6382`.
- **Verified:** analyzer completed with no schema warnings.
- **Verified:** P1 won on turn 20, final health **20-0**. Neither player
  crashed or timed out.

### 3.1 Opening geometry

**Verified:** P1 spent the 40 starting SP on 18 unupgraded Destructors/Turrets
(`DF`) plus two upgraded endpoint Filters/Walls (`FF`):

```text
Walls:   [0,13], [27,13] (both upgraded)

Turrets: [1,13], [1,12], [26,13], [26,12]
         [2,13], [2,12], [25,13], [25,12]
         [3,13], [3,12], [24,13], [24,12]
         [11,12], [16,12], [12,11], [15,11]
         [14,13], [12,13]
```

The Turrets remained at base range. Under this config, that preserves range
4.5 instead of accepting the upgraded Turret's range reduction to 3.5.

**Verified:** P1 then built delayed Support/Encryptor groups:

- T2: `[15,1]`.
- T15: `[20,12]`, `[19,11]`, `[17,11]`, `[18,10]`; three upgraded that turn.
- T20: `[7,12]`, `[8,11]`, `[10,11]`, `[9,10]`; all four upgraded.
- Aggregate: 9 Supports built, 7 upgraded.

P2 built 18 Supports but upgraded none. P1 therefore had fewer shield events
(228 vs 338) but much more total shield granted (1500.9 vs 676).

### 3.2 Mobile attacks and breaches

**Verified correction:** both players used Scouts (`PI`) only in this replay;
the analyzer recorded no Demolisher or Interceptor spawns.

| Turn | Player | Spawn | Origin | Breaches |
|---:|---|---:|---|---|
| 2 | P1 | 11 Scouts | `[14,0]` | 6 at `[1,15]` |
| 5 | P2 | 16 Scouts | `[13,27]` | 1 at `[24,10]` |
| 11 | P2 | 18 Scouts | `[13,27]` | 5 at `[24,10]` |
| 15 | P1 | 22 Scouts | `[16,2]` | 12 at `[6,20]` |
| 16 | P2 | 18 Scouts | `[14,27]` | 4 at `[5,8]` |
| 20 | P1 | 19 Scouts | `[7,6]` | 12 at `[20,21]` |

Totals: P1 spawned 52 Scouts and dealt 30 breach damage; P2 spawned 52 Scouts
and dealt 10. P1's sparse 22- and 19-Scout shielded attacks supplied 24 of its
30 breaches and the turn-20 kill.

## 4. Replay-derived stress fixture and ablation

`opponents/replay_shield_stack` reproduces observable mechanisms, not
unavailable participant source:

- approximately 18 base-range Turrets and upgraded endpoint Walls;
- permanent upgraded Support corridors;
- MP hoarding and sparse all-in Scout bursts;
- lane choice from path risk and available shield, not an opponent ID.

The ablation `REPLAY_STACK_DISABLE_SUPPORTS=1` changes only the fixture's desired
Support count to zero.

| v6 matchup | Result | Mean turn |
|---|---:|---:|
| Shielded fixture | 0/20 | 15.0 |
| No-support fixture | 0/20 | 46.0 |

**Verified:** the milestone5 champion loses both variants in both seats.

**Strongly supported:** shielding is the cause of the much faster turn-15
failure, but is not the only winning mechanism: removing it delays the fixture
by 31 turns and still leaves v6 at 0/20.

## 5. Mechanism A — adaptive MP-funded Interceptors

Implementation: `baselines/defense_v14_adaptive_interceptors`.

**Verified config premise:** Interceptors cost 1 MP, have 40 base HP, range 4.5,
and deal 15 damage to mobile units. Demolishers cost 2 MP and have 5 HP; Scouts
cost 1 MP and have 15 HP before shields.

The detector retains per-turn type, count, origin/flank, consecutive
Demolisher cadence, Scout-burst cadence, and recent history. It requires two
qualifying Demolisher turns for confirmation. Large Scout timing is estimated
from public MP income/decay after the first sample, then replaced by observed
cadence after the second.

### 5.1 Controlled 3x3 sweep

Coordinate families per flank:

- `mirror`: rotate the observed enemy origin into the reciprocal friendly edge
  lane (defaults `[4,9]` / `[23,9]`);
- `corner`: `[3,10]` / `[24,10]`;
- `deep`: `[7,6]` / `[20,6]`.

Spend profiles:

| Profile | Sustained | Emergency | Demo threshold | Scout threshold |
|---|---:|---:|---:|---:|
| low | 35% | 60% | 2 | 12 |
| medium | 60% | 85% | 2 | 8 |
| high | 85% | 100% | 1 | 6 |

All 27 coordinate/spend/target cells were run in both seats (n=2 per cell).

- `mirror`: 0/6 v33 games across profiles; 0/6 shielded; 0/6 no-support.
- `corner`: 0/6 v33; 0/6 shielded; 0/6 no-support.
- `deep`: 0/6 v33; 0/6 shielded; **6/6 no-support**.
- v33 mean survival improved monotonically for deep placement:
  61.0 (low), 65.0 (medium), 69.0 (high), but remained 0 wins.

**Strongly supported:** deep placement works better because its path remains in
the mobile combat area longer. Mirror/corner screens often ended after only a
few cells or chased the previous burst lane.

### 5.2 Trajectory-grounded corrections

The first Scout response followed the previous burst's flank. Replay events
showed the next wave on the opposite flank and **zero Interceptor attacks**.
Two-flank emergency coverage fixed engagement: subsequent probes recorded 15
and 13 Interceptor attacks on turns 10 and 15.

The first implementation also spent heavily on every turn after a burst.
Because mobile units do not persist between turns, those post-hoc screens could
not hit the completed wave and left little MP on the actual repeat turn.
Cadence-timed deployment raised observed Interceptor attacks to 19 on T15 and
44 on T20 and delayed the shielded loss from T15 to T20, but did not reverse it.

Selected deep/high n=10:

| Target | Result | Mean turn | Decision |
|---|---:|---:|---|
| v33 | 0/10 | 69.0 | Delay only |
| shielded replay fixture | 0/10 | 15.0 | No improvement in A alone |
| no-support fixture | 10/10 | 58.0 | Reversed |

**Rejected as a promotion candidate:** A does reverse the no-support 0/20, but
it remains 0/10 against both supported real-threat models and is strictly
dominated by B below.

## 6. Mechanism B — replay-derived dense opening

Implementation: `baselines/defense_v15_dense_opening`.

B changes v6's SP policy only: it builds the observed 18-Turret opening, keeps
the Turrets unupgraded for range, upgrades endpoint Walls, then adds one fully
upgraded corridor Support at a time after the opening is intact. v6's MP
offense, breach tracking, reactive defense, and endgame policy remain
unchanged.

| Target | Result | Mean turn |
|---|---:|---:|
| v33 | **10/10** | 26.2 |
| shielded replay fixture | 0/10 | 15.0 |
| no-support fixture | **10/10** | 24.0 |

**Verified:** B reverses two independent 0/20 losses in both seats, including
the real public v33 opponent. It does not solve the fully shielded fixture.

**Strongly supported:** opening density/base range, not Interceptor spending,
is the decisive v33 mechanism: B wins 10/10 while A wins 0/10 and the combined
candidate below is worse than B.

## 7. Mechanism C — combined

Implementation: `baselines/defense_v16_dense_interceptors`.

The first combination inherited A's “bank all remainder” behavior. That removed
B/v6's winning offense: all three spend profiles went 0/2 against v33 while
surviving roughly 86-88 turns. This was a real mode-switch regression.

The isolated correction reserves v6's normal 9-MP offense threshold on even
turns during sustained-Demolisher mode; odd turns retain the selected full
screen fraction. Scout emergencies still prioritize defense. This restored
some wins without an opponent-specific check.

Corrected deep/high n=10:

| Target | Result | Mean turn |
|---|---:|---:|
| v33 | 6/10 | 88.6 |
| shielded replay fixture | 0/10 | 20.0 |
| no-support fixture | 10/10 | 24.0 |

**Rejected:** C adds no target win that B lacks, falls from B's 10/10 to 6/10
against v33, and only delays the still-0/10 shielded matchup. This is exactly
the kind of mode-switch regression the acceptance gate disallows.

## 8. Direct targeted comparison with `milestone5-champion`

| Candidate | v33 | Shielded replay | No-support replay |
|---|---:|---:|---:|
| v6 / `milestone5-champion` | 0/20 | 0/20 | 0/20 |
| A adaptive screen | 0/10 | 0/10 | 10/10 |
| B dense opening | **10/10** | 0/10 | **10/10** |
| C combined | 6/10 | 0/10 | 10/10 |

There were zero candidate crashes and zero harness errors in these 90 n=10
targeted games.

## 9. Full regression and promotion decision

Full B regression completed across the current 31-opponent self-built and
public corpus at n=10 per matchup:

| Scope | Result |
|---|---:|
| All 31 opponents | **300/310** |
| 29 opponents previously beaten by `milestone5-champion` | **290/290** |
| `travelling_salesmen_v33` | **10/10** |
| Fully shielded `replay_shield_stack` | 0/10 |
| Candidate crashes / harness errors | **0 / 0** |

Every matchup except the fully shielded replay fixture was 10/10. In
particular, the explicit public checks against
`travelling_salesmen_adapdef`, `travelling_salesmen_frumblesnatch`,
`davidw0311_mcts`, and `summer2022_6th` were all 10/10 in both seats.

**Verified: zero regressions.** B retained all 290/290 games against opponents
the milestone5 champion already beat. The shielded fixture is an unresolved
loss, not a new regression: milestone5 was already 0/20 against it. B adds two
independent gains over milestone5: v33 improves from 0/20 to 10/10, and the
no-support replay ablation improves from 0/20 to 10/10.

**Promotion decision:** `baselines/defense_v15_dense_opening` is the new
champion. A and C remain rejected. The final commit is tagged
`milestone9-champion`; `milestone5-champion` remains the rollback point.

## 10. Submission package validation

`submissions/milestone9_champion/` contains the unpacked self-contained algo
folder and the recommended permission-preserving archive
`defense_v15_dense_opening_permfix.zip`.

- Archive SHA-256:
  `e39e6df78fc74465507345fb3191be2e6ac92317339d5261d65eef22848f96cb`.
- `unzip -t` passed with no errors.
- A clean extraction retained `run.sh` mode `0755`.
- The clean extracted archive ran directly and beat
  `travelling_salesmen_v33` in a real local engine match.
- The post-package repository fallback smoke also won 2/2 against v33, one
  game in each seat, with zero crashes or harness errors.

## 11. Evidence conclusions

- **Verified:** the uploaded replay is a P1 20-0 turn-20 win driven by an
  18-Turret base-range opening, delayed stacked shielding, and sparse all-in
  Scout waves.
- **Verified:** adaptive Interceptors are functional and can reverse the
  no-support fixture, but cannot overcome the fully shielded fixture as tested.
- **Strongly supported:** the original “MP attack vs SP rebuild” hypothesis
  identifies a real pressure mismatch, but is incomplete. MP-funded defense
  alone is not the best v33 answer; dense base-range static coverage is.
- **Strongly supported:** Support shielding is the remaining replay-fixture
  mechanism. Every candidate is 0/10 with it; A/B/C are 10/10 without it.
- **Verified:** B is promoted as `milestone9-champion`: 300/310 on the current
  corpus, including 10/10 against v33 and 290/290 retained prior wins, with no
  candidate crashes, harness errors, or previously won matchup regressions.
- **Rejected:** opponent-ID hardcoding, next-turn post-hoc Scout screens,
  mirror/corner Interceptor placement, A as champion, and C as champion.
- **Hypothesis:** stacked shields raise each Scout's effective health enough
  that 15-damage Interceptor volleys cannot reduce a burst before the surviving
  Scouts breach. The replay evidence is consistent with this, but this bounded
  milestone did not add a fourth mechanism to isolate it further.
