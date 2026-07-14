# Strategic Prior-Art Report: Terminal (C1Games / Correlation One)

**Workstream:** Research & strategy (read-only; no code touched by this workstream).
**Companion docs:** `docs/GAME_SPEC.md` and `docs/COMPLIANCE_REPORT.md` (engineering
workstream) were read and used to cross-check every historical numeric claim below.
Those docs reconstruct the *current* ruleset from the actual cloned starter kit
(`game-configs.json`, `python-algo/gamelib/*.py`) plus decompiled `engine.jar`
bytecode — they are the ground truth this report checks history against.

**Process note:** this research was interrupted twice by transient tool/auth errors
mid-session. No data was lost — all web research below was completed and is reported
in full. Flagging per the user's instructions in case any gap in continuity is visible
in tool-call ordering.

## 0. How to read this document

Confidence tags (kept consistent with `GAME_SPEC.md`/`COMPLIANCE_REPORT.md`):

- **Verified** — read directly from a primary source (an actual repo, config file, or
  a named team's own published account), URL cited.
- **Strongly supported** — corroborated by two or more independent sources/teams
  describing the same mechanism.
- **Hypothesis** — my own proposed idea, or a claim resting on a single source; not
  independently confirmed. Falsifiable and testable, not a guarantee.
- **Rejected** — considered and actively recommended against (weak evidence, obsolete,
  or a documented anti-pattern).

**Current-applicability status** for every historical claim is one of:
`current config matches` / `current config contradicts` / `unverified — needs check`.

**Standing caveats (apply to every section below, not repeated each time):**

1. Terminal's balance changes between seasons. Unit costs/stats/mechanics quoted in
   2019-era sources are *not* assumed to hold today unless explicitly cross-checked
   against `game-configs.json` (via `GAME_SPEC.md`) in this repo.
2. Correlation One has explicitly asked competitors **not** to publish complete algo
   source (documented directly in one of the sources below). Nothing here recommends
   copying any published code verbatim. All recommendations are "reimplement the
   underlying mechanism yourselves," which is also the only approach consistent with
   typical originality/anti-plagiarism competition rules.
3. Nothing in this report is "verified to win." Nearly all evidence is self-reported
   postmortems from competitors, not independently reproduced by me. Treat every
   ranked hypothesis as a prioritized experiment to run once local infra exists, not
   as a proven fact.
4. I did not have the ability to log into terminal.c1games.com, view private replays,
   or access any non-public competition data. Everything below came from public web
   pages (Medium, GitHub, Correlation One's own blog, LinkedIn posts, university news
   sites) that I could reach via search/fetch.

---

## 1. Source log

| # | Source | Date / event | Type | Key claim(s) | Confidence | Current-applicability |
|---|---|---|---|---|---|---|
| 1 | Correlation One, ["About Terminal"](https://medium.com/terminal-player-strategies/about-terminal-64ca8eb67f59) (Medium) | Feb 2019 | Official | Season 1 ran Sep–Dec 2018 (~12,000 players), Season 2 Jan–Apr 2019; real-time leaderboard + replay access model | Verified (official source) | Format/history only, not config-dependent |
| 2 | Ryan Draves, ["Ryan D's Terminal Strategy"](https://medium.com/terminal-player-strategies/ryan-ds-terminal-strategy-eaa39f123a7e) | Feb 2019 | Player postmortem | 3rd place global comp / 2nd at UMich live event. Core mechanism: "predictors" that detect opponent patterns + minimax simulation of X defensive/Y offensive placement combos; early-game tolerance discount for scoring-based outcomes | Verified (self-reported placement) | Mechanism (prediction + minimax) is config-independent; specific unit choices not detailed |
| 3 | Griffin Keglevich, ["The Terminus of our Terminal Strategy"](https://medium.com/terminal-player-strategies/the-terminus-of-our-terminal-strategy-19c96da2acf5) (Team 6, UWaterloo) | Feb 2019 | Player postmortem | Abandoned PPO/RL for heuristics (action space too large for 6hr event); built a frame-by-frame attack simulator, value fn `3.5*breaches + core_damage`; reactive defense (build at attacked locations) as decisive fix vs rush; EMP corner-spam identified as a lingering weakness | Verified (self-reported) | Mechanism transfers; value-fn constants are config-specific and must be re-tuned |
| 4 | Josh Durham, ["CMU Team 17 Terminal Strategy"](https://medium.com/terminal-player-strategies/cmu-team-17-terminal-strategy-e0adc7f387f9) | Mar 2019 | Player postmortem | Ranked 12th global. State estimator + dynamic sector-damage-reinforcement defense + attack strategy (EMP-escort vs heavy defense, Ping-swarm vs light defense); explicit "Ping Cannon" (channel-spam) detector + counter; noted "maze algorithms" were prevalent among top-ranked opponents; varied own defense layout slightly each turn to resist being studied | Verified (self-reported) | Mechanism transfers; "Ping"/"EMP" now named Scout/Demolisher, stats differ — see §5/§8 |
| 5 | Kyle Chin, ["CMU Team 13: Our Experience at Terminal Live"](https://medium.com/terminal-player-strategies/cmu-team-13-our-experience-at-terminal-live-33d909647621) | Apr 2019 | Player postmortem | Reached #2 global. C++ minimax "security" (maximin) simulator, 480 sims/sec after optimization; utility `U = score(blue)*health(blue) − score(red)*health(red)`; explicit anti-pattern found: absolute-security metric over-used defensive Scrambler, "played too scared"; biggest single rank jump (19→5) came from fixing simulator *bugs*, not strategy changes | Verified (self-reported) | Mechanism + anti-pattern both transfer; numeric utility weights are config-specific |
| 6 | Prajval Gupta, ["LIVE @Terminal — The Algorithm Battle"](https://medium.com/@prajvalgupta/live-terminal-the-algorithm-battle-7f35ac2bd8ad) (Team Monte Carlo Marauders, UT Austin) | Sep 2019 | Player postmortem | Top 8 of 34, live-streamed quarterfinal loss. 3-stage strategy: destructor-heavy symmetric defense w/ explicit corner priority → early Scrambler harass → V-shaped Encryptor-shielded Ping+EMP combined attack. Lost because their attack was static/repetitive and opponent diverted their path into a second strong defensive line mid-board; explicitly says they should have detected and halted a "getting wasted" attack | Verified (self-reported) | Notes it used **organizer-modified rules** for that specific live event — costs quoted (destructor=2, encryptor=1) are NOT assumed to be standard-season values; current config has Support(EF)=7, contradicts this quote — see §8 |
| 7 | [`luckystarufo/_Terminal_CorrelationOne`](https://github.com/luckystarufo/_Terminal_CorrelationOne) | 2018–2019 | GitHub repo | `versions.md`: v0.1 "inspired by BLACKBEARD" — channel-attack with Pings, Destructors kept off the front line, Filters guide the path (funnel/channel archetype). **Repo explicitly states Correlation One asked the author not to publish complete algo code** | Verified (direct repo text) | Archetype name/shape transfers; repo is also our direct evidence for the originality/no-full-code-sharing norm (see caveat #2) |
| 8 | [`wllmzhu/alpha-terminal`](https://github.com/wllmzhu/alpha-terminal) | Undated (~2019-2020 era styling) | GitHub research repo | Policy-gradient (PPO)/LSTM RL agent, AlphaStar-inspired, "strong amateur" play (reached ~40th percentile per a related account by a different author using a similar ML approach); **README states "Each player begins the game with 30 Health Points"** | Verified (direct repo text) | **Current config contradicts this**: `game-configs.json` `startingHP: 40.0`, Verified in `GAME_SPEC.md` §3. Concrete evidence that a widely-repeated stat has changed (or this repo describes an older/different season) |
| 9 | [Correlation One blog: "Waterloo Students Take Home $25k..."](https://www.correlation-one.com/blog/waterloo-students-take-home-25k-in-cash-prizes-at-terminal-live-ai-coding-competition) | Jan 2019 event | Official recap | First Terminal Live at Waterloo; 500 applicants, top 75 competed, top 8 single-elim bracket, $25k total prizes | Verified (official) | Format/history only |
| 10 | [Imprint: "UW captures Terminal Live's top-prize"](https://archive.uwimprint.ca/article/uw-captures-terminal-lives-top-prize/) | Jan 25 2020 event (Waterloo vs UofT) | Student newspaper | UW beat UofT 7/9 matches; **Team Garpuz** was the event's overall winner (of UW's 3 qualifying teams: Yellow Goose, Traveling Wilburys, Garpuz) | Verified (named winner, no strategy detail published) | No mechanism detail available |
| 11 | Prakhar Singh, LinkedIn profile | "Terminal Live 2019-2020," UT Austin | Self-reported credential | Led a team of 3 to win **$12,000** at Terminal Live, UT Austin, Sep 2019 (also cross-referenced by a contemporaneous Daily Texan article title) | Verified (self-reported placement) | No strategy detail available |
| 12 | [`aubreyyan/terminal_live_2020`](https://github.com/aubreyyan/terminal_live_2020) ("PIP INSTALL UT," UT Austin & Georgia Tech) | Oct 2020 virtual event | GitHub repo (README only, **no source published** "out of respect for competition integrity") | Placed 6th/45, won $1,000. Beat "Super DC Buzz," described as a **Terminal Season 6 finalist** team with "months of experience," in round-robin | Verified (self-reported placement); repo again explicitly withholds source code | Confirms organizer/competitor norm of not publishing full algos (caveat #2); no mechanism detail |
| 13 | [Correlation One blog: "Stanford University Win First Terminal Global Championship"](https://www.correlation-one.com/blog/stanford-university-win-first-terminal-global-championship) | Spring 2021 (announced May 2021) | Official recap | **Team "Smite" (Stanford)** won the first Terminal Global Championship, $30,000, beating Cambridge, ETH Zurich, Princeton, Waterloo in the Final Four; 5,000+ students, 17 universities in the Championship | Verified (official) | No strategy detail published for winner |
| 14 | [Correlation One blog: "Terminal Championship and Winners 2021-2022"](https://www.correlation-one.com/blog/terminal-2021-2022) | Published Sep 2022 | Official recap | 9 regional comps, $150k+ distributed. **Team "QY" (University of Cambridge)** won the 2022 Global Championship ($30,000) over Warsaw, Georgia Tech, Harvey Mudd. Also names Summer '21 and Midwest Spring '22 regional podiums (e.g. Team "Apex," Northwestern, won Midwest Spring 2022) | Verified (official) | No strategy detail published for any named winner |
| 15 | [`langsonzhang/Terminal-C1-Midwest-2022`](https://github.com/langsonzhang/Terminal-C1-Midwest-2022) ("Murphy's Lawyers," UofT) | Spring 2022, C1 Midwest (hosted by Citadel) | GitHub repo | Built the "FUNNEL" algorithm; placed **#5 of 24 teams** against CMU/UMich/UIUC competitors | Verified (self-reported placement); README does not describe the algorithm's internals beyond the name | Archetype name ("funnel") corroborates prevalence claim in source #4, but no technical detail to cross-check against current config |
| 16 | [`yip6ga1lok6/C1-Terminal-Summer-2022`](https://github.com/yip6ga1lok6/C1-Terminal-Summer-2022) | Summer 2022 Invitational | GitHub repo | Ranked **6th of 91 teams** | Verified (self-reported placement) | No strategy detail published |
| 17 | Ahmad Said, LinkedIn post | Citadel Terminal Asia 2025 (~Mar 2025) | Self-reported | Team "Impulse," algo named **"Glass Cannon Namys,"** placed 4th; public replay link referenced (`terminal.c1games.com/competitions/1323`, login-gated, not independently viewed by me) | Verified (self-reported placement + bot name) | Bot name suggests a high-offense/low-defense-investment archetype but no internals published — **Hypothesis only** re: actual mechanism |
| 18 | Elliot Aldridge, LinkedIn post | Citadel Terminal APAC, **April 2026** (most recent data point found) | Self-reported | Team "THE CHUDS" placed 3rd/110+ competitors, 40+ teams, $2,500. **Decisive improvement was switching from a static, hand-placed defense to a reactive defense that rebuilds based on where the opponent attacked in previous rounds** — went 18–0 after the switch. Lost 1st place to team "Bin Birds" (Lucas Liang, Trong Nghia Nguyen) | Verified (self-reported placement, very recent) | **This is the single most recent, most directly relevant data point in this report** — reactive/adaptive defense is described as decisive as of Apr 2026, i.e. essentially concurrent with our own competition prep |
| 19 | `correlation-one/C1GamesStarterKit` — shipped `python-algo/algo_strategy.py` (the file cloned into this workspace) | Current (repo last pushed per search metadata ~Jan 22 2026) | Official starter code | The **default starter bot itself** already encodes reactive defense (rebuild at breach locations), a "demolisher line" attack pattern (cheap stationary units placed as a queue so Demolishers stop at max range instead of walking into the enemy base), and a naive least-damage-path spawn-location heuristic for mobile units | Verified (this is the literal file in our workspace, `python-algo/algo_strategy.py`) | Directly current — this is our own baseline's starting point, not historical |
| 20 | This workspace: `game-configs.json` + `docs/GAME_SPEC.md` + `docs/COMPLIANCE_REPORT.md` (engineering workstream) | Current | Primary config + decompiled-bytecode analysis | Full current unit stat table, board geometry, resource formulas, **100-turn hard cap**, and win tie-break order (HP → less cumulative compute time → coin flip) | Verified (engineering workstream's own bytecode-level analysis) | This *is* "current" — used throughout this report as the cross-check baseline |

---

## 2. Strategy archetype taxonomy (prevalence among documented teams)

| Archetype | Prevalence in sources found | Notable examples |
|---|---|---|
| **Reactive / adaptive defense** (rebuild or reinforce wherever the opponent last attacked/breached, instead of a fixed build order) | **Dominant.** Present in the official starter bot itself, and independently cited as *the* decisive mechanism by teams 3 seasons apart (2019 CMU Team 17/Team 6, and the Apr-2026 APAC 3rd-place team) | #3, #4, #18, #19 |
| **Turn-level simulation / minimax lookahead** before committing a turn's resource spend | **Common among the most competitive documented teams** (top-2-to-12 global finishers in the well-documented 2019 season) | #2, #3, #5 |
| **Escorted combined-arms offense** (cheap shield/screen unit + a dedicated structure-cracking unit, e.g. historical Encryptor-shield + EMP+Ping combo) | **Common**, recurring across eras under different names (Blackbeard-style "channel," V-shaped shield, FUNNEL) | #6, #7, #15 |
| **Funnel / maze / path-control defense** (structure layout engineered to force predictable mobile-unit paths into a kill zone) | **Common at high ranks** — explicitly called out as "prevalent... in the higher ranks" by one 2019 top-12 team, and a named team strategy in 2022 | #4, #15 |
| **Corner-priority defense** (extra weight on corner coverage because corners are a common breach target) | **Common** — independently emphasized by multiple unrelated teams | #3, #6, #19 (starter bot itself warns about this in comments) |
| **Signature detection + counter-strategy switching** (detect a known opponent pattern like a channel/"ping cannon" rush and swap to a purpose-built counter) | **Occasional** — one clearly documented case, described as effective but incomplete (still lost to *dynamic* versions of the same rush) | #4 |
| **Opponent-move prediction ("predictors")** that try to guess the opponent's simultaneous move before committing your own | **Rare** — one team explicitly claims this was their key differentiator and that most competitors did not prioritize it | #2 |
| **Early mobile-unit rush / harass** (send cheap mobile units in the first few turns to probe or chip damage before main strategy kicks in) | **Common as an opponent behavior to defend against**, less commonly documented as the *documenting* team's own primary win condition | #3 ("rush-based defences" as a threat), #6 (their own early Scrambler harass, judged in hindsight as suboptimal) |
| **Delayed resource-hoarding into a single burst** | **Documented mainly as a mechanism that beat a strong team**, not as a self-described winning strategy by its own practitioner | #6 (Monte Carlo Marauders' quarterfinal loss) |
| **Absolute-security / maximin turn evaluation** (always defend against the worst-case simulated opponent response) | **Rare as an intentional design choice, and explicitly documented as a trap** — one top-2 team had to walk it back | #5 |
| **Full reinforcement learning (policy-gradient / PPO / LSTM) as the primary strategy** | **Rare, and not documented as a top-3 finish anywhere I found.** Both documented attempts either pivoted away under time pressure or topped out at "strong amateur" | #3 (abandoned mid-competition), #8 (research project, not a competition placement) |

---

## 3. Top winning mechanisms — detail, evidence, current validity, counter-hypothesis

### 3.1 Reactive / build-where-attacked defense
- **Description:** instead of (or in addition to) a fixed defensive build order, track where the opponent's mobile units breached or dealt damage in the previous turn(s), and prioritize rebuilding/reinforcing exactly there.
- **Evidence tier:** Strongly supported (independently reported by #3, #4, #18; also the literal mechanism already present in our own starter bot, #19).
- **Why it worked:** static defenses are trivially probed and exploited once an opponent finds one gap; reacting to actual damage data concentrates limited resources where they matter most, in real time, without needing to predict the opponent in advance.
- **Current validity:** **Likely still valid, and the most recent evidence we have (Apr 2026) says it's still decisive.** Not itself config-dependent — it's a control-flow idea, not a stat.
- **Counter/improvement hypothesis:** Our reactive defense should be strictly better than "rebuild at the exact breached cell" (the starter bot's own naive version, `python-algo/algo_strategy.py` `build_reactive_defense`): (a) reinforce a small neighborhood around the breach, not just one cell, since opponents can shift aim by ±1 lane between turns; (b) weight reinforcement by *recency and frequency* of hits to that sector, not just latest breach; (c) cap total reactive spend per turn so a repeated-feint opponent can't bait us into overspending SP on a decoy lane. **Testable:** local match win-rate of "single-cell reactive" vs "neighborhood-weighted reactive" vs a fixed baseline, over ≥50 games once infra exists.

### 3.2 Turn-level simulation / minimax lookahead before committing a turn
- **Description:** before submitting a turn, internally simulate several candidate placements/attacks (and, in the more advanced versions, several candidate *opponent* responses too), score each outcome with a value function, and commit the max-scoring option.
- **Evidence tier:** Strongly supported (#2, #3, #5 — three independently-built simulators across three different teams, all in the top ~12 globally in the 2019 season).
- **Why it worked:** removes guesswork from "will this attack actually breach," replacing hand-tuned heuristics with a projected outcome.
- **Current validity:** Mechanism itself is timeless and almost certainly still a strong idea; **but the concrete implementation is now bounded by a Verified engine constraint our own engineering doc found**: local ("work" mode) per-turn budget is **soft 5,000 ms / hard 35,000 ms** (`GAME_SPEC.md` §4.2, Verified from `game-configs.json` + decompiled `PlayerStats` fields), and exceeding it accrues *timeout damage* and can eventually cause a scored loss. One 2019 team reported needing heavy C++ optimization to hit 480 sims/sec; that raw throughput number is not directly comparable today (different hardware, different config), but the *lesson* — a simulator's speed budget is a hard constraint, not a nice-to-have — is Verified as still true via the engine bytecode.
- **Counter/improvement hypothesis:** Build the simulator with an explicit, measured time budget (e.g., target ≤50% of the 5,000 ms soft limit, leaving headroom for GC/JIT variance and other per-turn logic), and benchmark simulations/sec on the actual tournament-like hardware before trusting any depth/breadth of search. **Testable:** instrument wall-clock per turn in local matches; assert p99 turn time stays under budget across a stress test (e.g., a match where both bots max out unit spawns every turn).

### 3.3 Escorted combined-arms offense (shield/screen + structure-cracker)
- **Description:** don't send a single unit type; pair a cheap high-health screen/shield (historically Encryptor-shielded Pings, or Scrambler escort) with a slower, higher-damage anti-structure unit (historically EMP/Demolisher) so the screen absorbs incoming turret fire while the cracker actually damages enemy structures.
- **Evidence tier:** Strongly supported, recurring across at least three independent teams/eras under different names (#6's V-shaped Encryptor shield + Ping+EMP combo; #7's Blackbeard-inspired channel; #15's "FUNNEL" name, though its internals weren't published).
- **Why it worked:** exploits the asymmetry between "cheap unit that mostly needs to survive" and "expensive unit that needs to deal damage" — classic tank/DPS pairing.
- **Current validity:** **Directionally still plausible, but current unit stats change the specific pairing math and one input is unverified.** Cross-check against `GAME_SPEC.md` §2.2 (Verified): **Demolisher (EI)** remains the only mobile unit that reliably damages *structures* at range (4.5 range, 6.0 dmg vs both mobile and structure, but only 5 HP and 0.5 speed — still the "slow glass cannon" role historically described as EMP). **Interceptor (SI)** has 40 HP and 20 dmg **vs mobile units only** (no `attackDamageTower` value in config, meaning it cannot hit structures) — this matches its historical role as an anti-mobile screen/counter-rush unit, not an offensive escort that damages enemy defenses. However, the shield-generating **Support (EF)** unit's actual shield mechanism (range, per-unit bonus, stacking) is an explicit **unverified gap** even in `GAME_SPEC.md` (`shieldRange: 0` in the shipped config, no `shieldPerUnit`/`shieldBonusPerY` keys present) — so the "V-shaped Encryptor shield" idea specifically cannot be validated against current config data alone.
- **Counter/improvement hypothesis:** Build the combined-arms attack around the Verified stats (Demolisher as the structure-cracker, something disposable/cheap as the screen) rather than assuming Support's shield is strong, until the engineering team empirically measures the actual shield bonus in a local match (e.g., spawn a Support near a Scout, diff its effective HP against a no-Support control). **Testable and falsifiable now:** does a Support-shielded Scout survive measurably more turret hits than an unshielded one in a local replay? If the shield bonus turns out to be small/short-range, deprioritize Support-heavy escort strategies in favor of raw numbers (Scout swarm) or Interceptor path-clearing.

### 3.4 Funnel / maze / path-control defense
- **Description:** engineer your own stationary-unit layout so that enemy mobile units are forced along a specific, predictable path (often into a "kill zone" covered by multiple defensive units, or specifically to keep your own Demolishers at maximum range without walking into the enemy base — this is literally what the *current* starter bot's `demolisher_line_strategy` does).
- **Evidence tier:** Strongly supported — independently called "prevalent... in the higher ranks" by one 2019 top-12 team (#4), and used as a named team's core strategy in 2022 (#15, "FUNNEL," #5 of 24).
- **Why it worked:** converts the game's pathing rules (mobile units path along the shortest/least-resistance route through your structures) into a targeting advantage — you choose where the fight happens.
- **Current validity:** **Directionally sound and structurally unchanged** — board geometry (28×28 diamond, pathing along edges) is Verified unchanged in `GAME_SPEC.md` §1, straight from `gamelib/game_map.py`. The exact "keep Demolishers at max range" math depends on current Demolisher `attackRange: 4.5` (Verified) rather than whatever range applied historically, so any maze geometry must be re-derived, not reused from memory of old range values.
- **Counter/improvement hypothesis:** Two-sided use of this mechanism: (a) offensively, build our own cheap-stationary-unit lines to hold Demolishers at their Verified 4.5-tile range from enemy structures (same idea as the shipped starter bot, but tuned/hardened rather than left as-is); (b) defensively, since one 2019 top-12 team explicitly said their algorithm had specific, analyzable weak spots against certain maze *layouts*, build a small library of known maze shapes and test our own defense against each rather than assuming "reactive defense" alone handles maze attackers. **Testable:** run our baseline against several hand-built maze-attacker configurations locally and record breach rate per maze shape.

### 3.5 Signature detection + counter-strategy switching
- **Description:** detect that the opponent is running a specific, recognizable pattern (the clearest documented example: a "ping cannon," i.e., a channel built to funnel many cheap fast mobile units into one corner) and switch to a purpose-built counter-response instead of your generic defense.
- **Evidence tier:** Hypothesis-leaning-Strongly-supported — one clear, detailed account (#4), not independently corroborated by a second team, but internally consistent and plausible.
- **Why it worked (per the source):** a generic reactive defense reinforces the point of damage reactively (after the fact); a signature-based response can pre-empt the *next* wave once the pattern is recognized, and can also proactively attack the weak side of the enemy's own cannon structure (their account: attack the non-output side of the cannon, since it tends to be less defended).
- **Current validity:** Unverified against current config numbers, but the underlying idea (some opponents will have identifiable, repeatable macro patterns; a corridor/channel spam is a geometry pattern, not a stat) is not stat-dependent and plausibly still applicable. The source itself notes this approach still lost to *dynamic* versions of the same rush — i.e., it's a real but incomplete counter.
- **Counter/improvement hypothesis:** Implement a small library of pattern detectors (e.g., "≥N consecutive turns of the same cheap mobile unit spawned from the same edge cell" as a rush signature; "a contiguous same-owner structure corridor pointing at one of our edges" as a channel signature) with logged confidence scores, and a distinct pre-built response per signature — but explicitly test each detector against a *varying* version of its own trigger pattern (randomized spawn offset by 1-2 turns/cells) to avoid the exact failure mode this source reported. **Testable:** construct synthetic opponent scripts that vary a known pattern slightly, and measure detector false-negative rate.

### 3.6 Corner-priority defense
- **Description:** weight defensive investment specifically toward the two board corners, because corners are a disproportionately common target for mobile-unit breach attempts.
- **Evidence tier:** Strongly supported — independently emphasized by the current shipped starter bot's own code comments (#19: "Remember to defend corners") and by an unrelated 2019 team's explicit design rationale (#6: "we...particularly wanted to defend our corners because we have seen that in many algorithms attackers try to sneak in through corners").
- **Why it worked:** corners have fewer adjacent defensible tiles and are a natural target for path-finding mobile units trying to minimize turns exposed to fire.
- **Current validity:** Structural/geometric claim, not stat-dependent — board geometry is Verified unchanged (`GAME_SPEC.md` §1). Very likely still applicable.
- **Counter/improvement hypothesis:** Rather than treating "defend corners" as a static rule, make corner-defense *strength* a tunable, continuously-tested parameter, and specifically stress-test our reactive-defense controller (§3.1) against corner-focused attacks in isolation, since two independent historical sources flagged this as a common attack vector we should assume opponents will try immediately. **Testable:** local matches against a scripted "always aim at whichever corner has fewer turrets" opponent.

### 3.7 Opponent-move prediction ("predictors")
- **Description:** maintain a small ensemble of pattern-recognizers that try to predict what the opponent will do *this* turn (before their move is revealed, since turns are simultaneous), and once a predictor gains confidence, use its prediction to choose your own move as if you already knew theirs.
- **Evidence tier:** Hypothesis-leaning-Strongly-supported — one detailed, credible account (#2, 3rd place globally), no second team independently corroborating the same mechanism (though it's consistent with — and a natural extension of — the minimax-simulation mechanism in §3.2).
- **Why it worked (per the source):** turns are simultaneous, so any accurate prediction of the opponent's move is a direct information advantage; the source explicitly says most competitors were *not* prioritizing this, calling it a real differentiator.
- **Current validity:** Timeless/mechanism-level, not stat-dependent — simultaneous-turn structure is unchanged (confirmed by `GAME_SPEC.md`'s description of the turn loop). The same source also self-reports a real cost: their structure's benefits for prediction reliability came at the price of "a vulnerable early game," i.e., this is not a free lunch.
- **Counter/improvement hypothesis:** Treat this as a *later-stage* enhancement, not a Milestone-1 requirement, given (a) it's the single rarest mechanism in our evidence (only one account), (b) its own author flagged a real trade-off cost, and (c) it likely requires substantial replay/history data to bootstrap reliably. **Testable, deferred:** once we have a working reactive-defense + simulator baseline (§3.1, §3.2) and a corpus of local match replays against varied scripted opponents, measure whether a simple "did the opponent do the same thing on turn N as turn N-2/N-4" predictor improves win rate at all before investing further.

### 3.8 Halting a failing/sunk-cost attack mid-stream
- **Description:** if an ongoing attack strategy is repeatedly failing to convert (units dying without breaching or dealing meaningful damage), detect this and stop reinforcing it rather than continuing to feed resources into a losing pattern.
- **Evidence tier:** Hypothesis — directly named as a specific, identified-but-unsolved failure mode by one team (#6), not corroborated by a second source describing a working solution to it.
- **Why it mattered:** in the one documented case, this exact failure (repeating the same attack pattern turn after turn while the opponent had adapted their board to swallow it) is explicitly blamed for a live-streamed quarterfinal loss by an otherwise Top-8 team.
- **Current validity:** Purely an algorithm-design idea, not stat-dependent. No reason to believe it's obsolete.
- **Counter/improvement hypothesis:** Add an explicit feedback loop: track the realized outcome (units lost vs. damage dealt vs. breach achieved) of the last K turns of a given attack "recipe," and if realized value is trending toward zero/negative for M consecutive turns, suppress that recipe for some cooldown period and re-route resources to defense or to a different recipe. **Testable and clearly falsifiable:** construct a local opponent that specifically reroutes incoming paths into a secondary defensive pocket (mirroring the exact failure from source #6) and confirm our bot detects and stops the failing pattern within a bounded number of turns, instead of continuing indefinitely.

### 3.9 Simulator/evaluation-function correctness as a force multiplier (meta-mechanism)
- **Description:** not a game strategy per se, but a documented empirical finding: for at least one top team, the single largest jump in competitive rank (19th → 5th globally) came from fixing *bugs* in their own simulator (attack-phase and movement edge cases), not from a strategy change.
- **Evidence tier:** Verified as a self-reported claim from a named, highly-placed team (#5, reached #2 globally).
- **Why it mattered:** a strategy is only as good as the internal model it's optimized against; if the simulated damage/movement model diverges from the real engine's behavior, even a theoretically sound strategy will make wrong decisions.
- **Current validity:** Universally applicable, and arguably *more* actionable for us right now than any single game-strategy idea, because our own engineering docs (`GAME_SPEC.md` §7 / `COMPLIANCE_REPORT.md` §3) already flag several **unverified mechanics** (Support's shield formula, the exact MP-cap ramp formula, exact self-destruct trigger semantics) that any internal simulator we build would need to get right.
- **Counter/improvement hypothesis:** Before investing heavily in strategy sophistication, prioritize validating any internal simulator/predictor against the actual `engine.jar` behavior on real local matches (which the engineering workstream already has running) — specifically the mechanics `GAME_SPEC.md` flags as unverified. **Testable:** for each unverified mechanic, design one minimal local match scenario that isolates it (e.g., a single Support near a single Scout, with no other units, to empirically measure the shield bonus) and record the observed effect before trusting any hypothesis in this report that depends on it.

### 3.10 Turn-100 hard cap and compute-time tie-break (current-only, not found in any historical write-up)
- **Description:** the match engine forces the game to end at turn 100 if neither player has reached ≤0 health, and (Verified from decompiled `engine.jar` bytecode, `GameMain.processEndGame`) ties are broken **first by higher remaining player health, then by lower cumulative compute time used across the whole game**, then by a literal coin flip.
- **Evidence tier:** Verified (`GAME_SPEC.md` §4.3, decompiled engine bytecode — the single most rigorously-sourced fact in this entire report, stronger than anything from the historical postmortems).
- **Why this matters:** **none of the 20 historical sources in this report mention a turn cap or a compute-time tie-break at all** — either it didn't exist / wasn't well-known in the 2018-2022 seasons those sources describe, or it simply wasn't strategically relevant enough for any postmortem author to mention. This is a genuinely new-to-us, current-only strategic lever.
- **Current validity:** Verified for *this* codebase/engine build. Not cross-checked against whether the actual tournament runner uses an identical engine build (`COMPLIANCE_REPORT.md` flags this as "Strongly supported, not independently confirmed").
- **Counter/improvement hypothesis (two, both new and untested anywhere in the historical record):**
  1. **Health-banking / damage-race vs. health-preservation trade-off study:** since a durable defense that gets grazed for a small amount of chip damage per turn can still win at turn 100 purely by preserving more HP than a highly aggressive opponent (even one dealing more *total* damage over the game, if it also takes more retaliatory damage), it may be worth explicitly modeling "expected HP differential at turn 100" as a first-class objective alongside "can we force an early kill," rather than only optimizing for fastest possible breach. **Testable:** simulate/replay several archetypes (aggressive glass-cannon vs. turtle) to turn 100 and compare final HP differentials, not just win/loss.
  2. **Compute-time-as-tie-break insurance:** because tie-break #1 after HP is *lower cumulative compute time*, keeping our algo meaningfully faster than the 5,000 ms soft budget (not just "under the limit") is free insurance in any close/mirror-ish matchup, and costs us nothing if we're not otherwise compute-bound. **Testable:** track cumulative compute time per match in local testing and treat "minimize while preserving decision quality" as an explicit optimization target, not just a pass/fail timeout check.

---

## 4. Common mistakes / exploited weaknesses (documented)

- **Static, fixed build-order defenses** were the first thing every team that later improved had to move away from — explicitly identified as a rush-vulnerability by #3 and implicitly by the fact that the *only* adaptive element of the official starter bot itself is its reactive defense (#19).
- **Absolute-security (maximin) turn evaluation** made one top-2-globally team's algorithm "play too scared," over-investing in a defensive-only mobile unit (Scrambler) that performed poorly in practice, until they switched to an "approximate security" metric (#5). This is a genuine, named anti-pattern from a very strong team, not a hypothetical.
- **Repeating a static/failing attack pattern** rather than detecting and halting it was explicitly blamed for a live, streamed quarterfinal loss by an otherwise Top-8 team (#6) — the opponent adapted (diverted the attack path into a secondary defense) and the losing team kept re-running the same recipe.
- **Simulator/engine-model bugs**, not strategic weakness, were blamed for a large chunk of one strong team's underperformance before they were fixed (#5) — a reminder that "the strategy was fine, the model of the world was wrong" is a real, previously-observed failure mode, not just a theoretical risk.
- **Hardcoding counters that assume a static opponent** was an explicit obstacle reported by a top-12 team (#4) — specific counters (e.g., to a "ping cannon") worked against static instances of the pattern but failed against *dynamic* versions of the same opponent archetype.
- **A structurally vulnerable early game**, traded off in exchange for a stronger mid/late-game prediction-driven strategy, was self-identified as a real weakness by a top-3-globally team (#2) — i.e., even a documented winning mechanism (opponent prediction) came with a cost elsewhere in the strategy that the team only later assessed as a net negative.

---

## 5. Ranked hypotheses worth testing first (highest expected value first)

Each is concrete enough to implement and test once local match infra exists (which the
engineering workstream already has running per `GAME_SPEC.md` §6). All are proposals
to independently reimplement a *mechanism*, never to copy any specific team's
published code.

1. **[Strongly supported]** Build a reactive defense controller that reinforces a
   small *neighborhood* around recent breach locations (weighted by recency +
   frequency), not just the exact breached cell — this is the single most
   corroborated mechanism in this report (§3.1), corroborated as recently as Apr 2026,
   and is a strict improvement over what our own starter bot already does.
2. **[Strongly supported, config-bounded]** Build a turn-simulator that scores
   candidate placements/attacks before committing, with an explicit, *measured*
   time budget kept well under the Verified 5,000 ms soft / 35,000 ms hard per-turn
   limits (§3.2). Do this before adding opponent-prediction (#7 below) — simulation
   is the more corroborated, lower-risk mechanism of the two.
3. **[Hypothesis, high-value, cheap to build]** Add a sunk-cost/abort-attack
   detector: track realized value (damage dealt / units lost / breach achieved) of
   an attack "recipe" over its last few uses, and suppress recipes trending toward
   zero value instead of repeating them blindly (§3.8). Directly targets a
   documented Top-8 team's actual tournament loss.
4. **[Hypothesis, new, high-value]** Explicitly test the health-preservation vs.
   damage-race trade-off given the Verified 100-turn hard cap and the
   HP-then-compute-time tie-break (§3.10). No historical source considered this —
   it is a genuinely new lever specific to the current, bytecode-verified ruleset.
5. **[Strongly supported, needs re-derivation]** Build an escorted combined-arms
   attack using the Demolisher as the structure-cracker (Verified as still the only
   mobile unit that reliably damages structures at range) — but do **not** assume
   the historical "Encryptor/Support shield" math; first empirically measure
   Support's actual shield effect locally, since it's an explicit gap even in our
   own engineering doc (§3.3).
6. **[Strongly supported]** Build/maintain a small library of known maze/funnel
   defensive layouts (§3.4) and benchmark our own baseline's breach rate against
   each, since "maze algorithms" were independently reported as common among
   strong opponents historically, and the underlying pathing mechanics are Verified
   unchanged.
7. **[Hypothesis, moderate value, cheap insurance]** Track and actively minimize
   cumulative per-match compute time as a secondary optimization target (not just a
   timeout-avoidance check), given the Verified compute-time tie-break rule (§3.10,
   hypothesis 2). Low cost, plausible small edge in close/mirror matches.
8. **[Hypothesis, moderate value]** Implement 2-3 signature detectors for common
   attack archetypes (persistent same-edge mobile rush; contiguous structure
   corridor "channel"), each paired with a distinct counter-response — but
   explicitly stress-test each detector against *jittered* variants of its own
   trigger pattern, since the one historical account of this mechanism explicitly
   said it failed against dynamic versions of the pattern it was built to catch
   (§3.5).
9. **[Hypothesis, lower priority, defer]** Opponent-move prediction ("predictors")
   — the rarest and most complex mechanism in the record (§3.7), self-reported to
   carry a real early-game cost by its own author. Worth revisiting only after
   #1-#4 are working and we have a replay corpus to bootstrap predictors from.
10. **[Hypothesis, low cost, low urgency]** Add small turn-to-turn variation to our
    own defensive micro-layout so a long ladder-format opponent can't trivially
    memorize our exact structure (§3.4's second half) — cheap to add, but only
    matters if our actual competition format involves enough repeated games against
    the same opponent to make studying us worthwhile (unknown — see Gaps, §7).

---

## 6. Do-not-bother / rejected list

- **Full reinforcement learning (policy-gradient / PPO / LSTM, AlphaStar-style) as
  the primary strategy.** [Rejected for our timeline] Both documented attempts (§3
  intro; Team 6's abandoned PPO effort under competition time pressure, and the
  `alpha-terminal` research project) either pivoted away from RL under real time
  constraints or achieved only "strong amateur" results — not a single top-3 finish
  in anything I found used RL as its core mechanism. The action space and per-turn
  compute budget (Verified 5,000 ms soft limit) make this a poor fit for a
  competition-prep timeline versus heuristic + simulation approaches that
  demonstrably reached #2-3 globally.
- **Absolute-security / pure-maximin turn evaluation as the primary decision
  metric.** [Rejected as primary approach] Explicitly identified by a top-2-globally
  team as making their algorithm "too scared" and wasting resources on an
  ineffective defensive unit; they switched to "approximate security" and improved.
  Fine as one input signal, not as the sole objective function.
- **Copying any specific published algo verbatim** (BLACKBEARD-derived channel code,
  FUNNEL, Glass Cannon Namys, alpha-terminal's RL model, or any other named bot).
  [Rejected on originality/licensing grounds] Correlation One has directly asked at
  least one competitor not to publish complete algo source (§ source #7), and no
  full source for any top-placing team was actually found publicly in this
  research — only names, placements, and prose descriptions. Competition
  originality rules almost certainly prohibit verbatim reuse regardless. Everything
  recommended in §5 is "reimplement the underlying mechanism yourselves."
- **Trusting any specific 2018-2022-era numeric unit stat without re-deriving it from
  `game-configs.json`.** [Rejected/obsolete as stated] Concrete example found in this
  research: one repo's README states the game starts with 30 player health; the
  current, Verified config in this workspace shows `startingHP: 40.0`
  (`GAME_SPEC.md` §3). Another account (under organizer-modified rules for that
  specific live event, by its own admission) quotes Encryptor/Support at ~1 SP;
  current config shows Support at 7 SP — the single most expensive structure per
  unit in the current game, more than 3x a base Turret. Any hypothesis or value
  function that assumes old cost/range numbers must be rebuilt from the current
  config, not memory.
- **Hard-coded static build orders as a terminal (pun intended) strategy** — useful
  only as a cheap bootstrap/opening, universally described as the first thing beaten
  by any adaptive or rush-oriented opponent across every era of sources found.

---

## 7. Gaps — what the engineering team should confirm before trusting any
config-dependent hypothesis in this report

- **Support/Encryptor's actual shield mechanism (range, per-unit bonus, stacking)**
  is an open gap even in `GAME_SPEC.md`/`COMPLIANCE_REPORT.md` (shipped config has
  `shieldRange: 0` and no `shieldPerUnit`/`shieldBonusPerY` keys). This directly
  affects hypothesis #5 (§5) and the current-validity assessment of the historical
  "shielded escort" archetype (§3.3) — needs an empirical local-match measurement,
  not just config reading.
- **Exact MP resource cap ramp-up formula** (`roundStartBitRamp` /
  `bitRampBitCapGrowthRate`) is flagged as "Strongly supported, not fully Verified"
  in `GAME_SPEC.md` §3 — affects how confidently we can model a resource-hoarding /
  delayed-burst hypothesis's actual economics.
- **Exact self-destruct trigger semantics** ("5 steps without a target in range") are
  inferred from field names, not fully traced in engine bytecode
  (`GAME_SPEC.md` §2.1 gap note) — relevant to any path-manipulation or
  sacrificial-unit hypothesis, none of which made it into the ranked list above
  precisely because this mechanic is underverified.
- **Whether the actual tournament runner uses the exact same `engine.jar` /
  `game-configs.json` as this cloned repo.** `COMPLIANCE_REPORT.md` §4 explicitly
  flags this as "Strongly supported... but not independently confirmed against a
  live tournament match." If the organizers are running a newer/different season
  config for our specific event, every current-applicability judgment in this
  report (and in `GAME_SPEC.md`) needs re-validation against that actual config
  before trusting it.
- **No technical (code-level) strategy write-up newer than the 2022 season** was
  found for the *winning* team of any global championship — the 2023-2026 evidence
  in this report (#17, #18) is placement + team name + one paragraph of
  self-reported mechanism, much thinner than the well-documented 2019 season. Our
  confidence that "reactive defense still works" (§3.1) rests heavily on a single
  April-2026 LinkedIn paragraph, not a technical postmortem — strongly supported by
  recency and consistency with older evidence, but not to the same evidentiary
  standard as the 2019 sources.
- **No information at all on our actual opponent pool, matchmaking, or bracket** for
  the competition we're actually entering — every "what beats X" judgment in this
  report is against generic/historical opponent archetypes, not confirmed
  information about who or what we'll actually face.
- **No independent replay analysis was performed by this research workstream** — I
  have no engine access in this read-only role; every mechanism claim above is a
  human competitor's self-reported account of their own algorithm, not something I
  re-derived from raw match data myself. The engineering workstream should validate
  any hypothesis here against actual local match replays before treating it as more
  than a prioritized experiment.
