# Real (non-self-built) opponent results

Tags used throughout, per standing convention: **Verified / Strongly supported
/ Hypothesis / Rejected**.

## 0. What this document is, and its central limitation

Every benchmark in `docs/MILESTONE_1_REPORT.md` through `MILESTONE_5_REPORT.md`
was run against opponents built by this project (either directly, or as
hypothesis-driven "adversarial countersearch" opponents, or as a "held-out
corpus" built blind from prior-art descriptions — see `docs/MILESTONE_5_REPORT.md`
§0 for that distinction). All of those, however methodologically varied, are
still **self-built**: designed, written, and tuned by the same team that built
the champion, which is a real overfitting risk the top-level instructions
explicitly flag.

This document logs the first opponent results that are **not self-built**: the
user manually uploaded our actual current champion package
(`submissions/milestone5_champion/defense_v6_encryptor_fix_algo_folder`,
uploaded as a folder named `python-algo`) to the official competition
platform's browser-based practice sandbox at
`https://terminal.c1games.com/playgroundlive`, and ran it against several of
that sandbox's built-in named practice bots, reporting results back via
screenshots.

**Central limitation, stated plainly up front: none of this is something this
agent can independently run, rerun, or verify.** `terminal.c1games.com` is a
login-gated, JavaScript-rendered web application; this agent's `WebFetch` tool
only returns the static (pre-render) page shell for both
`https://terminal.c1games.com/rules` and `https://terminal.c1games.com/playgroundlive`
(confirmed by direct fetch — see §4), and there is no documented API access
available to this agent for actually playing a match on that platform. Every
result below is **user-reported from manual browser testing**, not something
independently reproduced by this agent the way every other benchmark in this
project's history has been (real local `engine.jar` runs, harness-collected
JSON, replay files this agent can directly inspect). Treat the confidence
level accordingly: this is real evidence, meaningfully different in kind
from a self-built-corpus win, but it is single-sourced and not independently
re-run.

## 1. What these practice bots actually are — Hypothesis, not Verified

The user's own assessment, which this agent has no way to independently
confirm or refute from an authoritative source: these are **platform-provided
practice bots** (a fixed practice-sandbox roster: `R1_Sawtooth`,
`R2_Infiltrator`, `R3_Jukebox`, `R4_Champion`, `Punchbagrob`, `Foreman`,
`Infiltrator`, `Captain`, `Ironclad`, and possibly others), **not** other
competing teams' submitted algorithms and **not** past competition winners.

A genuine, reasonable-effort search for official documentation was made and
is logged in §4 below — **no official Correlation One / C1Games documentation
naming or describing these specific bots was found.** The one piece of
indirect, non-official corroboration found: a third-party student project
repo, [`davidw0311/c1_terminal`](https://github.com/davidw0311/c1_terminal)
(unrelated to this project, unrelated to the user), casually refers to
"the terminalc1 boss algorithm 'IronClad'" as an opponent they tested their
own algo against, and links a demo video of that matchup. This is consistent
with the user's characterization (a fixed, platform-provided "boss" bot named
Ironclad used for practice), but it is **one other player's own anecdotal
description**, not an official source, and does not by itself confirm
anything about the other named bots (`Sawtooth`, `Infiltrator`, `Jukebox`,
`Champion`, `Punchbagrob`, `Foreman`, `Captain`).

**Honest conclusion: it remains unknown, from any source available to this
agent, exactly what these bots are** (hand-written by C1Games staff
specifically as graduated-difficulty practice opponents is the most likely
reading of the R1-R4 naming pattern plus "boss"-style names, but this is
Hypothesis, not Verified) — beyond the reasonable, undisputed baseline fact
that they are **not self-built by this project**, which is the property that
actually matters for the overfitting concern this document exists to address.
If Correlation One documentation describing these bots is ever found or
provided, this section should be updated and the confidence level raised.

## 2. Results log (user-reported, from manual browser testing)

All matches: our current champion (`baselines/defense_v6_encryptor_fix`,
tagged `milestone5-champion`), packaged and uploaded exactly as
`submissions/milestone5_champion/defense_v6_encryptor_fix_algo_folder`,
confirmed by the user to be our actual code (not the vanilla starter bot).

| Opponent | Result | Rounds | Notes |
|---|---|---|---|
| `R4_Champion` | **WON 16-0** | 26 | `R4_Champion`'s reported cumulative compute time across the match was ~23.7s vs. our ~343ms — see §3 for why this is logged as a compliance/robustness data point, not just a fun fact. |
| `Captain` | **WON 30 to -6** | 10 | Decisive blowout. `Captain` reportedly spent 0 mobile-unit (MP) points the entire match — a pure-turtle opponent that never mounted any offense and got breached, structurally similar to this project's own `opponents/turtle_survivor`/`single_leak_turtle` self-built archetypes, except this one is not self-built. |
| `Ironclad` (run 1) | **TIE 14-14** | 100 | Reported stat panels for both players were suspiciously *identical* — 86 vs 86 structure points, 260/852 vs 260/852 resources, matching damage-taken percentages to the decimal on both sides. This does not look like two genuinely distinct strategies converging on the same numbers by chance; it looks more like either a mirror-match (our own algo somehow facing itself) or a display/UI artifact in the practice sandbox. **Not resolved — see §3.1.** |
| `Ironclad` (run 2, same matchup immediately after) | **WON 28 to -1** | 54 | Decisive, and — critically — with **clearly asymmetric, internally coherent stats**: `Ironclad` ran a real, distinct strategy (heavy DEMOLISHER + INTERCEPTOR spam, zero SCOUTs, ~400 MP spent total), unlike anything in run 1's suspiciously-mirrored panel. |

**Aggregate, stated honestly given the sample size:** 3 distinct named
opponents, 4 total data points (2 of them the same matchup back-to-back), our
champion's real record is 3 wins, 0 clean losses, 1 unresolved tie with
strong reason to suspect it wasn't a genuine head-to-head result at all (§3.1).
This is a **meaningfully positive but very thin** evidence base — nowhere
near enough games, opponents, or independent verification to draw a strong
conclusion, but directionally consistent with (not contradicting) the
self-built-corpus results from Milestones 1-5.

## 3. Open questions, flagged honestly rather than guessed at

### 3.1 The Ironclad run-to-run variance (14-14 tie, then 28 to -1 win, same matchup)

This is the important open question the user asked to be flagged clearly,
and it is **not resolved** by anything available to this agent. Laying out
what is and isn't known, without false confidence in either direction:

**What is Verified from this project's own documentation
(`docs/GAME_SPEC.md` §4.3, decompiled directly from `engine.jar` bytecode):**
the engine has (at least) two genuinely non-deterministic mechanisms built
into match resolution:
1. **Tie-break #2** (only reached if HP is tied *and* cumulative compute time
   is *also* exactly tied): decided by a literal `java.util.Random.nextBoolean()`
   coin flip inside the engine itself. This is a real, confirmed source of
   engine-level non-determinism, but it only explains *who wins* a tied game,
   not why the reported *stats* (structure points, resources, damage
   percentages) would come out identical between two players running
   different code.
2. The starter algo itself (and, by inspection, potentially other bots built
   on the same starter-kit pattern) seeds `random.seed(seed)` in `__init__`
   and — in the *starter* algo's own case, confirmed in this project's
   earlier probes (`docs/GAME_SPEC.md` §6) — uses that randomness for
   interceptor placement, making starter-kit-derived bots non-deterministic
   run-to-run even against a fixed opponent.
3. **Correction made while writing this document, worth stating plainly
   rather than quietly fixing: our own champion is not fully deterministic
   either.** A first draft of this section claimed it was; re-checking with
   `grep -n "random\." baselines/defense_v6_encryptor_fix/algo_strategy.py`
   turned up a real decision-time usage beyond the inert boilerplate
   `random.seed()` call in `__init__`:

   ```349:349:baselines/defense_v6_encryptor_fix/algo_strategy.py
               deploy_location = deploy_locations[random.randint(0, len(deploy_locations) - 1)]
   ```

   — `stall_with_interceptors` (called from `PRESERVE` and `ALL_IN_TIED` mode,
   `docs/MILESTONE_5_REPORT.md` §8) picks a **random** edge location for each
   interceptor it spawns, every time it's called. This means any of this
   project's own past benchmark games that reached turn 81+ in `PRESERVE` or
   `ALL_IN_TIED` mode (confirmed in Milestone 5 to happen regularly against
   long-game opponents — see `docs/MILESTONE_5_REPORT.md` §8.1) had a
   genuinely randomized element in our own play, not just potential
   opponent-side randomness. This doesn't change *which* mode is entered or
   the overall strategy, and interceptors are a purely defensive, low-stakes
   unit choice here (their placement rotates among safe friendly edge tiles),
   so this is very unlikely to be strategically significant — but it is a
   real source of run-to-run variance in our own historical benchmark data
   that this project had not previously called out explicitly, and it
   directly reinforces the caution urged below about single-game evidence.

   Whether `Ironclad` (not our code, no source visibility) has an analogous
   randomized-decision pattern is separately unknown either way.

**What is not known:**
- Whether `Ironclad` itself has some adaptive or randomized behavior that
  could produce two different lines of play against the identical opponent
  in back-to-back matches. Plausible given the starter-kit's own precedent
  above, but **Hypothesis**, not confirmed — we have no access to `Ironclad`'s
  source.
- Whether the suspiciously-identical stat panel in run 1 reflects a genuine
  (if implausible-looking) coincidence, a practice-sandbox-specific display
  bug (e.g. showing the same player's panel twice, or a caching/refresh
  artifact in the UI), or something else entirely (e.g. the sandbox
  accidentally matching our algo against itself instead of against
  `Ironclad` for that one run). **No way to distinguish between these
  from a screenshot after the fact** — this would need either the actual
  `.replay` file (not available to this agent; the practice sandbox is a
  separate system from the local `engine.jar` this project's harness uses,
  and there is no indication the two produce interchangeable replay files)
  or a repeat of the same test with more careful logging.
- Whether the local `engine.jar` this project's entire benchmark corpus has
  been run on is fully deterministic for a fixed pair of *deterministic*
  algos, aside from the two known randomness sources above. This project's
  own harness has never specifically tested for this (every self-built
  opponent benchmark implicitly assumed determinism-modulo-the-known-sources,
  but never froze all inputs including any engine-internal randomness and
  diffed repeated runs byte-for-byte).

**Practical consequence, stated as the user requested: this is a real reason
to treat single-game evidence — including this project's own past win-rate
claims from earlier milestones — with somewhat more caution than before,
specifically regarding any claim that rests on a *single* game rather than a
real sample size.** This project's standing acceptance discipline (never
accept/reject based on small-sample noise, always use n=8-20 per matchup) was
already designed for a version of this concern (opponent-side variance in
non-adaptive-but-randomized play, e.g. the starter algo's own randomized
interceptor placement), and continues to be the right mitigation — but this
finding is a concrete, real-world instance of exactly that variance showing
up in a single side-by-side pair of games, which is a good reason not to
loosen that discipline, and a reason to be skeptical of any *n=1* result
(ours or anyone else's) going forward, including isolated screenshots like
these ones.

### 3.2 `R4_Champion`'s compute time (~23.7s vs. our ~343ms)

Logged as a compliance/robustness data point per the user's request, not
just a curiosity: this project's own `docs/GAME_SPEC.md` §4.2 documents a
5000ms **soft** per-turn limit and a 35000ms **hard** per-turn limit
(`waitTimeBotSoft`/`waitTimeBotMax`, Verified from `game-configs.json` and
cross-checked against decompiled `PlayerStats` timeout fields). `R4_Champion`'s
~23.7s **cumulative** time over 26 rounds averages to roughly 911ms/turn —
comfortably under the 5s soft limit, so this is not evidence of `R4_Champion`
approaching a timeout. What it *is* evidence of: our own champion is
dramatically faster (343ms cumulative over 26 rounds ≈ 13ms/turn on average),
which matters directly for the compute-time tie-break (`docs/GAME_SPEC.md`
§4.3, tie-break #1: on an exact HP tie, lower cumulative time wins) —
consistent with, and now with one more real data point supporting, this
project's standing design principle (carried since Milestone 2/3) of keeping
per-turn computation minimal specifically to win that tie-break margin.

## 4. Search for official documentation of the practice bot roster

Per the user's request, a genuine (not perfunctory) search was made for
official Correlation One / C1Games documentation of what these named practice
bots are, before concluding this remains unknown:

- Direct `WebFetch` of `https://terminal.c1games.com/rules` and
  `https://terminal.c1games.com/playgroundlive`: both return only the static
  landing-page shell (site stats: player/match/algo counters), not the actual
  rules/practice content — confirming (Verified, by direct observation) that
  this is a JavaScript-rendered single-page application this agent's fetch
  tooling cannot render past the login-gated shell. The "Learn" nav link the
  user's screenshot shows was not independently reachable.
- Direct `WebFetch` of `https://correlation-one.github.io/C1GamesStarterKit/`
  (the starter kit's own doc server, linked from the official GitHub repo):
  no mention of `Ironclad`, `Sawtooth`, `Infiltrator`, `Jukebox`, `Champion`,
  `Punchbagrob`, `Foreman`, or `Captain` anywhere in the fetched page.
- Multiple web searches for combinations of the specific bot names alongside
  "terminal c1games" / "practice" / "boss" turned up **no official source**.
  One search's own AI-generated synthesis incorrectly claimed these terms
  "do not exist" in the context of the Terminal game and speculatively
  associated "R1-R4" with an unrelated mobile game — flagged here explicitly
  as a demonstration that **web-search AI summaries in this specific case
  were actively wrong/unreliable**, not as a real finding; this document only
  relies on directly-quoted primary source content, never a search engine's
  own synthesized summary.
- The one relevant (non-official) hit, already covered in §1:
  `davidw0311/c1_terminal`'s casual reference to "the terminalc1 boss
  algorithm 'IronClad'."

**Conclusion: no official documentation of this practice bot roster was
found.** This is stated plainly rather than papered over — if the user or a
future session finds the actual "Learn" page content (e.g. by being logged
in, which this agent cannot do), it should be added here.

## 5. What this document does not do (as of when §§1-4 were written)

This was, at the time, a documentation/evidence-logging task, not a new
benchmark-and-decide cycle. Per the user's explicit instruction at that point:
- **No champion change.** `baselines/defense_v6_encryptor_fix`
  (`milestone5-champion`) remains the current champion.
- **No new tag.** These results, while directionally positive, are far too
  thin (3 opponents, 4 games, entirely user-reported and unreproducible by
  this agent) to be treated as a real acceptance/rejection signal the way
  Milestones 1-5's real local benchmarks were.
- **This does not close the "overfitting to our own corpus" gap** raised at
  the top of this document — it's a first, genuinely-independent (if
  extremely thin) data point in that direction, not a resolution of it. See
  `docs/COMPLIANCE_REPORT.md`'s open-gaps section for how this is now
  reflected there, and the black-box-GitHub-opponent research (paused, not
  abandoned, per the user's instruction) as the other in-progress avenue
  toward closing it further.

**This is superseded by §6 below**, which resumed and completed exactly that
paused black-box-GitHub-opponent research in Milestone 6.

## 6. Black-box, publicly-sourced GitHub opponents (Milestone 6 — this IS a real, reproducible benchmark)

Unlike §§1-4 above, everything in this section **is** independently
reproducible by this agent: real code, cloned from public GitHub repos, run
unmodified as black-box opponents through this project's own local
`engine.jar`/harness, with real replay files this agent inspected directly.
This is qualitatively stronger evidence than §§1-4, closing (not just adding
one more thin data point to) a meaningful chunk of the "self-built opponent
corpus" overfitting concern raised at the top of this document. Full sourcing,
vetting, and root-cause detail is in `docs/STRATEGIC_PRIOR_ART_REPORT.md`
source-log entries #21-24 and `docs/MILESTONE_6_REPORT.md`; this section is
the results summary.

| Opponent | Source | Real placement claim | Result vs. `milestone5-champion` (n, both seats) |
|---|---|---|---|
| `skill_issue_final3gem` | [`satvikmittal638/Terminal-2026-Skill-Issue`](https://github.com/satvikmittal638/Terminal-2026-Skill-Issue) | 3rd/4 shown, "Citadel Terminal Competition," Mar 2026 | **WON 20/0** |
| `travelling_salesmen_adapdef` | [`The-Travelling-Salesmen/terminal-c1`](https://github.com/The-Travelling-Salesmen/terminal-c1) | Claimed "#1 spot at Harvard" (repo description) — but see correction below, this specific folder is mostly unmodified starter-kit boilerplate | **WON 20/0** |
| `travelling_salesmen_frumblesnatch` | same repo, `frumblesnatch-v1` folder | Same repo/claim, different iteration | **WON 19/20** (1 loss at n=20 — see note below) |
| `travelling_salesmen_v33` (self-declared **"Snorkeldink-V69"** internally, `snorkeldink-v3-3` folder) | same repo — this is the actual most-evolved, most-dangerous iteration, corrected from an earlier (wrong) assumption that `AdapDef` was their strongest — see below | Same repo/claim; this is the version whose mechanism (see below) plausibly *is* what "helped clinch #1 at Harvard" | **LOST 0/20, both seats** — see `docs/MILESTONE_6_REPORT.md` for full root-cause + patch-attempt writeup |
| `travelling_salesmen_v32`/`v31` (`snorkeldink-v3-2`/`v3-1` folders, smoke-tested only) | same repo | Same repo/claim, intermediate iterations | `v3-2`: **LOST 0/6** (same mechanism as v3-3); `v3-1`: **WON 6/0** (mechanism not yet present in this iteration) |
| `davidw0311_mcts` | [`davidw0311/c1_terminal`](https://github.com/davidw0311/c1_terminal) | No placement claim (personal/student project) | **WON 20/0** |

**A real, reproducible, decisive loss was found** against
`travelling_salesmen_v33`: our champion loses every single game, both seats,
to a real, publicly-sourced, plausibly-competition-relevant opponent. This is
exactly the kind of finding the overfitting concern was worried we'd never
surface by only testing against self-built opponents — see
`docs/MILESTONE_6_REPORT.md` §3-5 for the full root-cause analysis (a
continuous, un-paused, 100%-MP Demolisher rush at a single lane grinds down
our single-layer corner defense faster than it can be rebuilt) and honest
report of five separate patch attempts, none of which fully closed the gap.
**`milestone5-champion` remains the recommended champion** — not because this
loss doesn't matter, but because every attempted patch either failed to fix
it or wasn't proven not to introduce other regressions strongly enough to
justify replacing a champion that is otherwise undefeated across 24 other
opponents (20 self-built + 4 other independent ones) with an unproven
alternative. See the milestone report for the full reasoning.

**Correction made during this work, logged transparently**: an earlier pass
(before this section was written) had assumed `travelling_salesmen_adapdef`
was this repo's strongest/final iteration (based on its more
"official-sounding" folder name) and benchmarked only that one, recording a
clean win. Deeper inspection (comparing `AdapDef`'s file contents line-by-line
against the other iterations) found `AdapDef` actually retains large amounts
of unmodified starter-kit boilerplate (default debug strings, unused starter
helper methods) and never resolved a resource-discipline bug present in
earlier versions (unconditionally spending on defense every turn regardless
of whether its own initial build is complete) that `v3-3`/`v3-2` explicitly
fixed (a `save_cores` gate). This is presented as a correction, not buried —
the initial "we found the strongest one and won" conclusion was wrong, and
finding that out required actually reading and running more than one file per
repo rather than trusting a folder name.

## 7. Second search round: hunting specifically for the STRONGEST/former-champion code (Milestone 6, round 2)

Per the user's explicit upgraded goal — find and test against the strongest
publicly available bot, ideally an actual former tournament winner/world
champion — this round re-checked the named champions already identified in
`docs/STRATEGIC_PRIOR_ART_REPORT.md` (Smite/Stanford, QY/Cambridge, Garpuz/UW)
plus one newly-found named champion, and separately followed up on two
real-placement repos that had been *found* in an earlier pass but not yet
actually benchmarked. Full sourcing/vetting/config-diff detail is in
`docs/STRATEGIC_PRIOR_ART_REPORT.md` source-log entries #15, #16, #25, #26 —
this section is the results summary.

### 7.1 Former champions: still no public code found (now 5 named individuals/teams checked, zero hits)

**Smite (Stanford, 2021 Global Champions), QY (Cambridge, 2022 Global
Champions), and Garpuz (UW, 2020 regional winner) were re-checked directly
this round and confirmed to still have no public repo** — consistent with
the Milestone 6 round-1 finding for these same three (plus Bin Birds). One
**new** named champion was found and checked: **"Lee Isaac," 2022 Citadel
Terminal Summer Invitational Champion (Rank 1 of 42, $6,500 prize)**, per
their own LinkedIn credential list (which separately claims a peak Season 8
rank of 1st out of 800+ players — the single highest-profile individual credential
found in this entire search, across both rounds). Their LinkedIn links a
GitHub account (`Lee-Isaac`) — but that accounts belongs to a **different,
unrelated person** with the same name (a DevOps engineer in Seoul, 60
unrelated repos, zero Terminal/C1Games code). No other GitHub account could
be tied to this specific champion. **This is now the fifth separately-checked
named champion/high-placer with zero published code** (Smite, QY, Garpuz, Bin
Birds, Lee Isaac) — the "organizer asked us not to publish complete algos"
norm documented directly in `luckystarufo`'s repo (source #7) is very firmly
established at this point, not a one-off. **Conclusion: the ceiling on
finding an actual former-champion's code via public search has been reached.**

### 7.2 Two more real-placement repos, found earlier, actually benchmarked this round

| Opponent | Source | Real placement claim | Result vs. `milestone5-champion` (n=10, both seats) |
|---|---|---|---|
| `funnel_uoft` | [`langsonzhang/Terminal-C1-Midwest-2022`](https://github.com/langsonzhang/Terminal-C1-Midwest-2022) ("Murphy's Lawyers," UofT) | **#5 of 24 teams**, C1 Midwest Spring 2022, against CMU/UMich/UIUC competitors | **WON 10/10**, both seats, no crashes — the fastest, most lopsided sweep of any independent opponent tested (mean 10 turns, 31-0 points_scored) |
| `summer2022_6th` | [`yip6ga1lok6/C1-Terminal-Summer-2022`](https://github.com/yip6ga1lok6/C1-Terminal-Summer-2022) | **6th of 91 teams**, Summer Invitational 2022 | **WON 10/10**, both seats, no crashes (mean 56 turns — a real, drawn-out engagement, unlike `funnel_uoft`, but still a clean sweep) |

Both are real, substantial (723/752-line), non-stub `algo_strategy.py` files
with real supporting logic, run strictly as unmodified black-box opponents
(dropped into `public_opponents/funnel_uoft/` and
`public_opponents/summer2022_6th/` exactly as cloned, only `run.sh`
permission fixes). **Config-mismatch caveat, stated honestly and cutting both
ways per the user's instruction**: both ship an old
`seasonCompatibilityMode: 5`-era config quite different from ours (see
`docs/STRATEGIC_PRIOR_ART_REPORT.md` #15/#16 for the exact stat diffs — e.g.
`funnel_uoft`'s Support started completely unshielded at 1 HP, `summer2022_6th`'s
base Turret hit for over 3x our current base damage but cost 3x more) — their
real historical placement could plausibly translate into either a stronger or
weaker showing under our corrected config than what actually happened here.
Both wins are still genuine, decisive, and reproducible under the config we
are actually being scored on, exactly as recorded above — this caveat affects
how much the result should update our confidence about the *broader* pattern
of "will decent human-designed bots beat us," not whether these two specific
recorded wins are real.

### 7.3 One repo found, deliberately not benchmarked, with an honest reason

`wllmzhu/alpha-terminal` (an RL/policy-gradient agent, previously flagged in
`docs/STRATEGIC_PRIOR_ART_REPORT.md` #8 for a stat mismatch) was re-examined
this round specifically for runnability. Its own code is real and substantial
(283-line `algo_strategy.py` + a small `torch`-based `arch/` package for the
policy network) — but **the repo ships no trained checkpoint file at all**,
only the untrained architecture and a training loop. Directly inspecting its
own `CheckpointManager` confirms it falls back to a **freshly, randomly
initialized policy network** whenever no checkpoint is found on disk (which
is always true for a fresh clone). Benchmarking this would only test a random
policy, not the actual "strong amateur" agent the repo's own linked report
describes — reported here as a **deliberate, reasoned exclusion**, not a dud
(unlike `vinharish77/TerminalCompetition`, re-confirmed again this round as
an untouched starter-kit fork with no custom logic at all).

### 7.4 Headline conclusion for this round

**No former world/global champion's actual code was found or run — this
remains a hard ceiling, now confirmed across 5 independently-checked named
individuals/teams.** Two more real, human-competition-placed bots *were*
found and benchmarked, and **both lost decisively (10/0 each, both seats)** —
consistent with every other genuinely independent opponent found in this
project except the one real, still-unpatched exception
(`travelling_salesmen_v33`, §6 above). This strengthens rather than weakens
the case that `travelling_salesmen_v33` is a specific, real, structural
weakness worth treating as the top flagged risk (not that our champion is
simply "weak against real opponents in general" — the evidence base now
spans 7 genuinely independent opponents, 6 clean wins and 1 clean, well
-understood, honestly-still-open loss).
