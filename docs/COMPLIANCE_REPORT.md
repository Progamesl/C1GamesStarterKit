# Compliance Report

Status as of Milestone 1 (initial pass), updated through Milestone 4. Tags:
**Verified / Strongly supported / Hypothesis / Rejected**, per the top-level
instructions — nothing here should be read as certain unless tagged Verified with a
citation.

## 0. CRITICAL Milestone 4 correction: wrong game config used through Milestone 3 — now fixed

**Every benchmark result, win-rate number, and balance-sensitive design decision from
Milestones 1 through 3 (including the `milestone1-fallback`, `milestone2-champion`,
and `milestone3-champion` tags) was produced using `game-configs.json` as shipped by
the generic public `correlone-one/C1GamesStarterKit` clone — the "Terminal Online
Season 8" / sandbox-default config.** The user subsequently located the actual
competition's own in-portal config picker and found it defaults to **"High School
Terminal 2026"**, a materially different ruleset (see `docs/GAME_SPEC.md` §2.5 for
the full field-by-field diff, decompiled-bytecode verification of exactly which
config file the engine reads, and per-field strategic-relevance notes). Headline
differences: player `startingHP` 40→30, WALL `startHealth` 75→40 (a ~47% cut),
TURRET `attackRange` 2.5→4.5 (an 80% *increase*), DEMOLISHER MP cost 3→2, INTERCEPTOR
`attackDamageWalker` 20→15 (a stat the user's own report did not flag, found only by
our own exhaustive structural diff of both JSON files), and — most structurally
significant — SUPPORT ("Encryptor") flipping from a **resource-generating economy
unit with an inert (`shieldRange:0`) shield field** to a **real shield/support unit
with zero economy function** (`generatesResource1`/`generatesResource2` keys are
fully absent under the correct config, not just zeroed).

**Verified fix, as of this milestone:** the repo-root `game-configs.json` (the exact
file `engine.jar` reads for every local match — confirmed both by decompiling
`Config.useConfigFile()`'s bytecode and by an actual local match run whose "Looking
for Config file at:" debug line printed the repo-root path) has been replaced with
the corrected "High School Terminal 2026" config. The old config is preserved,
unmodified, at `game-configs.season8-generic.json.bak` for audit trail — it is no
longer used for anything going forward except historical reference.

**What this means for everything before this point:** all Milestone 1-3 win-rate
numbers, the `defense_v3_lowcompute` compute-time tie-break fix, the
`defense_v4_tiebreak` mode-transition fix, and the entire `turtle_survivor`
corner-weak-point geometric analysis from the (in-progress, now superseded)
Milestone 4 offensive-tactics work are all **balance-invalid** — they measure real
things (crashes, compute time, control-flow bugs) under a ruleset we are not actually
competing under. **Architecture and infrastructure lessons (git/tagging discipline,
harness design, the `run.sh` permission-race finding in §1.1 below, the turn-100
cap/tie-break rule itself, which lives in engine bytecode and is unaffected by this
config) still apply and are not invalidated.** See `docs/MILESTONE_4_REPORT.md` for
the full corrected-config re-benchmark and the resulting champion decision.

## 1. Language & submission format

- **Verified**: Python is a fully supported, first-class language. The starter kit's
  own `python-algo/` is the only per-language starter algo directory left in the repo
  root (upstream commit history literally includes a commit titled *"feat/remove rust
  and java support (#147)"*, meaning as of this snapshot the officially supported
  *starter* languages have been trimmed — only `python-algo` remains at the top
  level; `community/` exists for community-contributed languages but is otherwise
  empty in this checkout).
- **Verified**: `algo_strategy.py` must remain present and be the entry point — both
  `README.md` ("Note that `algo_strategy.py` must remain the entry point for Python
  algos — the platform requires this filename and will reject uploads where it is
  absent.") and `python-algo/README.md` ("Uploads missing `algo_strategy.py` will fail
  compilation.") state this.
- **Verified**: submission is a zip of the entire algo folder (e.g. `python-algo/`),
  produced by the provided `scripts/zipalgo_<platform>` binary, which respects a
  `.zipignore` file (git-ignore-style excludes) in the algo directory
  (`scripts/README.md` "Uploading your algo" section). Do **not** zip/select the
  whole starter-kit repo — select only the language folder (`README.md` "Uploading
  Algos").
- **Verified**: `python-algo/algo.json` just declares `{"language": "python"}` — this
  is presumably how the platform identifies the runtime; we have not seen server-side
  confirmation since we have no portal access (see gaps below).
- **Gap (cannot verify)**: exact upload size limits, allowed third-party pip
  dependencies (if any — the starter kit's `run.sh` invokes plain `python3` with no
  requirements.txt/pip install step, so **Hypothesis**: only the Python 3 standard
  library is safely usable, since there is no evidence the platform runs `pip
  install` before executing an uploaded algo). We did not find a
  `requirements.txt` anywhere in the repo.

### 1.1 `run.sh` executable-bit race condition in the official `scripts/zipalgo_mac` tool + `engine.jar` — audited across all 3 packages, all now fixed

**Original Milestone 3 finding:** zipping an algo with the starter kit's own
official `scripts/zipalgo_mac` tool, exactly as documented, produces a zip in
which `run.sh` **loses its executable permission bit** (mode `0o100644`, i.e.
`rw-r--r--`, instead of `0o100755`). Re-extracting that zip into a clean
directory with a plain `unzip` and running a real local match reproduced a
genuine engine-level crash:

```
Algo Crashed. Crash: true !processIsAlive: null
java.io.IOException: error=13, Permission denied
AlgoIndex 0 crashed bootup: .../run.sh
```

**Milestone 4 root-cause refinement (Verified via decompiling `engine.jar`):**
this is not a deterministic failure — it's a genuine **race condition inside the
engine itself**. Decompiling `com/c1games/terminal/game/player/SimpleAlgoPlayer.class`
(`javap -c -p`, extracted from `engine.jar`) shows the engine already has a
self-healing attempt for exactly this on non-Windows: it calls
`Runtime.getRuntime().exec("chmod u+x " + runPath)` (literal string constant
found in the class's constant pool: `"chmod u+x \u0001"`) immediately before
constructing the `ProcessBuilder` that directly executes `run.sh`. **Critically,
the bytecode never calls `.waitFor()` (or any other synchronization) on that
`chmod` process before proceeding** — it's fired off asynchronously and the code
immediately moves on to spawn `run.sh` regardless of whether the `chmod` has
actually completed yet.

**Empirical characterization (Verified, small local sample):** across this
investigation's repeated boot attempts of intentionally non-executable
(`0o100644`) `run.sh` zips, we observed **1 crash out of ~16 total local boot
attempts (~6%)** — i.e. the async `chmod` usually wins the race on a fast local
disk with no contention, but it is not guaranteed to, and we have a direct,
reproducible crash log proving it can lose. **We could not test under anything
resembling real tournament server conditions** (the class `com/c1games/terminal/util/DockerAlgo`
also present in `engine.jar` suggests the production environment may run algos
inside Docker containers, which would add meaningfully more filesystem/process
overhead per boot than our bare-metal local `engine.jar` runs — plausibly making
this race more likely to be lost, not less, though this is **Hypothesis**, not
verified, since we have no access to that environment).

**Audit result: all 3 existing submission packages had this exact same latent
bug**, since all 3 were built with the same official `zipalgo_mac` tool:

| Package | Original zip `run.sh` mode | Bug present? | Fixed? |
|---|---|---|---|
| `submissions/emergency_fallback/defense_baseline.zip` (Milestone 1) | `0o100644` | Yes | **Yes — `defense_baseline_permfix.zip` added, Verified via fresh extraction** |
| `submissions/milestone2_champion/defense_v3_lowcompute.zip` (Milestone 2) | `0o100644` | Yes | **Yes — `defense_v3_lowcompute_permfix.zip` added, Verified via fresh extraction** |
| `submissions/milestone3_champion/defense_v4_tiebreak.zip` (Milestone 3) | `0o100644` | Yes | **Yes — `defense_v4_tiebreak_permfix.zip` added, Verified via fresh extraction** |

Each `*_permfix.zip` was built with the system `zip` tool instead (which
preserves unix permission bits by default — confirmed `0o100755` on `run.sh` in
every case), and each was independently re-verified with the same
fresh-extraction protocol: `unzip` into a brand-new temp directory with **no
manual `chmod`**, then a real local match against `python-algo` via `engine.jar`
— all 3 booted and completed with 0 crashes. Every `*_algo_folder/` unzipped
folder in all 3 submission directories also now has `run.sh`'s executable bit set
directly (sidesteps the question entirely, since a folder upload never goes
through zip compression/extraction at all).

**What we could NOT verify (no portal access, per section 4 below):** whether the
actual tournament submission portal's upload/extraction flow restores this
permission bit server-side via its own logic independent of the race described
above (plausible, in which case the underlying risk may be moot for real
submissions), or preserves whatever a `zip`/`unzip` round-trip produces. **Given
we can reproduce a real crash locally either way (from the race, independent of
the portal), and the fix has zero downside, we are treating the `*_permfix.zip` /
`*_algo_folder/` artifacts as the recommended upload artifacts for all 3
milestones' packages going forward, superseding the plain `zipalgo_mac` output.**

**Net assessment: this was a real, previously-undiscovered risk that could have
caused a match forfeit on submission regardless of which milestone's champion
was ultimately submitted, since it affected the packaging tool itself, not any
one algo's code. All 3 known packages are now confirmed fixed and independently
re-verified.**

## 2. Runtime / resource limits

- **Verified** (`game-configs.json` `timingAndReplay`, cross-checked against
  decompiled `PlayerStats` timeout fields — see `GAME_SPEC.md` §4.2): per-turn budget
  in local/"work" mode is **soft 5000ms / hard 35000ms**; website "play" mode is
  **soft 10000ms / hard 40000ms**. Exceeding these accrues timeout damage and can lead
  to `timeoutDeath`.
- **Verified** (`engine.jar` bytecode, `GameMain.runLoop`): hard **100-turn cap**; if
  reached, winner is decided by remaining health, then by cumulative compute time used
  (less is better), then by a random coin flip. See `GAME_SPEC.md` §4.3 for the full
  derivation.
- **Gap (cannot verify)**: memory limits for an uploaded algo process. Nothing in the
  config files or the parts of `engine.jar` we decompiled mentions a memory ceiling.
  This is very plausibly enforced server-side (e.g. container limits) rather than in
  the engine itself, so its absence from the engine bytecode doesn't mean it doesn't
  exist — **we need the user/organizer to confirm actual memory limits on the
  tournament runners.**
- **Gap (cannot verify)**: wall-clock/CPU quota for total match duration, or an
  overall "algo must respond within N seconds of upload" compile-time check.

## 3. Rules we could not fully verify (see `GAME_SPEC.md` §7 for the complete list)

Summarized:
1. SUPPORT unit's exact shield mechanism/formula.
2. MP resource cap ramp-up formula details.
3. Exact crash-handling consequence (assumed loss, not confirmed in bytecode).
4. Full Java engine `TargetAndAttackSystem` — we relied on the official Python
   client's equivalent (documented, but a separate implementation from the Java
   engine's internal one).
5. Any config/rule differences between local "work" mode (what we benchmark with)
   and the actual tournament runner environment (network conditions, exact JVM
   version/flags used server-side, whether replay/logging settings differ).

## 4. Things we explicitly do NOT have access to (hard gaps, need user/organizer)

- Tournament login credentials, submission portal behavior, upload validation
  specifics beyond what's in this repo's docs/scripts.
- Ladder match history / opponent pool composition / matchmaking logic.
- Any organizer announcements about season/rule changes not reflected in this
  checkout of the starter kit (we cloned fresh — commit `72b7589`, last pushed to
  upstream per `git log` — so this should be reasonably current, but we have no way
  to confirm there isn't a newer, unpublished ruleset the organizers are using for
  this specific event).
- Confirmation that `game-configs.json` in this repo is *exactly* the config used on
  the tournament servers (it's the config used by our locally-run `engine.jar`, which
  is the same jar shipped in the same repo — **Strongly supported** that it matches
  tournament settings, since it's the official kit, but not independently confirmed
  against a live tournament match).
- **Direct API/programmatic access to `terminal.c1games.com` (including its
  `/playgroundlive` practice sandbox) — this agent has no way to log in, upload an
  algo, run a match, or fetch a replay from that platform itself.** Every benchmark
  in Milestones 1-5 was run against a *self-built* opponent corpus (direct builds,
  hypothesis-driven adversarial opponents, and a "held-out" corpus built blind from
  prior-art descriptions — see `docs/MILESTONE_5_REPORT.md` §0), which is a real
  overfitting risk. As of this entry, the user has manually run our packaged
  champion against several of that platform's named practice bots and reported
  results back — see `docs/REAL_OPPONENT_RESULTS.md` §§1-5 for the full log. This
  is genuinely non-self-built evidence, but it is single-sourced, user-reported, not
  independently reproducible by this agent, and very thin (3 opponents, 4 games) —
  it narrows this gap, it does not close it. The practice sandbox's actual bot
  roster and what those bots represent (platform practice bots vs. anything
  resembling past competitors) also remains under-documented from any official
  source found so far — see `docs/REAL_OPPONENT_RESULTS.md` §1 and §4 for the
  specific search performed and what was and wasn't found.
  **Milestone 6 update — this gap is now substantially narrower, though not fully
  closed:** this agent found, vetted, and locally ran (via the same local
  `engine.jar` used for every other benchmark in this project — fully
  reproducible, unlike the practice-sandbox results above) 5 real, substantial,
  publicly-sourced Terminal python-algo bots from other teams' GitHub repos, used
  strictly as unmodified black-box opponents. One of them
  (`travelling_salesmen_v33`, from a repo claiming a real competition win) beats
  our champion decisively (0/20, both seats) — the first genuinely independent
  opponent to do so in this project's history. See §7 below and
  `docs/MILESTONE_6_REPORT.md` for the full record. Actual live-ladder/tournament
  matches against other real teams' algos, and any former Global Championship
  winner's actual source code, remain completely inaccessible to this agent — a
  targeted check for the 4 most relevant named winners (Smite, QY, Garpuz, Bin
  Birds) confirmed none have published their code (`docs/MILESTONE_6_REPORT.md`
  §1.1), consistent with the organizer norm already documented in
  `docs/STRATEGIC_PRIOR_ART_REPORT.md` source #7.
  **Round 2 follow-up (same milestone, per an explicit "find the strongest
  possible opponent" upgrade to this task):** a 5th named champion (Lee Isaac,
  2022 Citadel Terminal Summer Invitational, Rank 1/42) was found and checked
  directly — same result, no published code, confirming this is now a firmly
  established pattern rather than a small sample. Two more real,
  human-competition-placed bots that had been *found* in an earlier pass but
  not yet benchmarked were actually run this round (`public_opponents/funnel_uoft`,
  #5/24 teams; `public_opponents/summer2022_6th`, 6th/91 teams) — both lost
  decisively (10/0 each, both seats), consistent with every other independent
  opponent except the one still-open `travelling_salesmen_v33` loss. One more
  candidate (`wllmzhu/alpha-terminal`, an RL agent) was found to be
  unbenchmarkable for a legitimate reason (no trained checkpoint file
  published, only the untrained architecture) rather than excluded as a dud.
  See `docs/REAL_OPPONENT_RESULTS.md` §7 for the full round-2 record.

## 7. Milestone 6: sourcing and license notes for black-box public-opponent testing

Per the user's explicit instruction, every repo below is used **strictly as an
unmodified local black-box test opponent** — dropped into
`public_opponents/<name>/` exactly as cloned (only file-permission fixes, no
logic changes), run through this project's own harness/`engine.jar`, never
read for the purpose of copying or adapting any of its logic into
`baselines/`. Full benchmark results are in `docs/MILESTONE_6_REPORT.md`.

| Repo | Author(s) | License found | Our usage |
|---|---|---|---|
| [`satvikmittal638/Terminal-2026-Skill-Issue`](https://github.com/satvikmittal638/Terminal-2026-Skill-Issue) | Satvik Mittal, Om Gore, Chatanya Maheshwari | Standard Correlation One starter-kit `License.md` (covers starter-kit-derived files; no separate license for the team's own strategy code) | Black-box test opponent only (`public_opponents/skill_issue_final3gem/`) |
| [`The-Travelling-Salesmen/terminal-c1`](https://github.com/The-Travelling-Salesmen/terminal-c1) | Team "Travelling Salesmen" (contributors per GitHub: FH, r-k-jonynas) | Same starter-kit `License.md` situation as above | Black-box test opponent only, 5 iterations tested (`public_opponents/travelling_salesmen_*`) |
| [`davidw0311/c1_terminal`](https://github.com/davidw0311/c1_terminal) | davidw0311 | No LICENSE file (defaults to all-rights-reserved) | Black-box test opponent only (`public_opponents/davidw0311_mcts/`) |
| [`vinharish77/TerminalCompetition`](https://github.com/vinharish77/TerminalCompetition) | vinharish77 | Not checked — repo confirmed to be an untouched starter-kit fork, **not used** (correctly excluded as a dud) |  |
| [`langsonzhang/Terminal-C1-Midwest-2022`](https://github.com/langsonzhang/Terminal-C1-Midwest-2022) | "Murphy's Lawyers" (Langson Zhang, Stan Hua, George/`CardboardTank`), UofT | Same starter-kit `License.md` situation as above | Black-box test opponent only (`public_opponents/funnel_uoft/`) — real placement claim (#5/24 teams) |
| [`yip6ga1lok6/C1-Terminal-Summer-2022`](https://github.com/yip6ga1lok6/C1-Terminal-Summer-2022) | yip6ga1lok6 (team not further identified in-repo) | Same starter-kit `License.md` situation as above | Black-box test opponent only (`public_opponents/summer2022_6th/`) — real placement claim (6th/91 teams); repo's `python-algo` variant specifically is the one run (repo also ships `rust-algo`/`java-algo` of unclear relative finality) |

**Conservative reading applied throughout, stated explicitly**: even though
the starter-kit `License.md` found in every repo above is fairly permissive
for the starter-kit-derived files it actually covers, none of these teams
published a separate license for their *own* strategic code additions
(`algo_strategy.py`'s custom logic, `defence.py`, `adaptive_opening.py`,
etc.). Absent an explicit grant, that layer defaults to standard copyright —
which is exactly why every use of this code in this project has been limited
to running it unmodified as a local test opponent, never reading it for
inspiration to copy or adapt into our own submission.

## 5. Known repo quirks fixed locally (do not affect legality, just hygiene)

- `scripts/test_algo_mac` and `scripts/test_algo_linux` are compiled binaries that
  were **not** marked `binary` in the upstream `.gitattributes` (only
  `zipalgo_mac`/`zipalgo_linux` and `*.jar`/`*.exe` were). This risked CRLF-corruption
  of those binaries on some checkouts/commits. We added them to `.gitattributes` as
  `binary` in our first commit. This is a defensive fix for our own working copy; it
  does not change game rules or submission format.
- This machine's `/usr/bin/java` is a macOS stub with no real JRE. We downloaded a
  local (non-system, no-sudo) Eclipse Temurin JDK 17 into `tools/` (gitignored,
  redownloadable via `tools/setup_java.sh`) purely so we could run `engine.jar`
  locally. This has no bearing on the actual tournament runner, which presumably has
  its own correctly configured JVM.

## 6. Net assessment

We have enough Verified information (board geometry, full unit stat table, resource
formulas, the two most important win-condition rules — turn cap and tie-break — and a
confirmed-working local match pipeline) to build and legally benchmark real baselines
per Milestone 1. The remaining gaps (SUPPORT shield formula, memory limits, exact
crash consequence) are real but do not block building a legal, working, reasonably
well-defended baseline; they matter more for late-stage optimization (Milestone 2)
and are flagged there.
