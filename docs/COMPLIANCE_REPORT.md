# Compliance Report

Status as of Milestone 1 (initial pass). Tags: **Verified / Strongly supported /
Hypothesis / Rejected**, per the top-level instructions — nothing here should be read
as certain unless tagged Verified with a citation.

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
