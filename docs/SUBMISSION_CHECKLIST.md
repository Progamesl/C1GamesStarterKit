# Submission Checklist

A concrete, step-by-step checklist for actually submitting to the
competition. Read `docs/TOURNAMENT_STRATEGY_BRIEF.md` §9 first if you're
here because something went wrong and you need a rollback — this document
assumes you already know *which* algo you're submitting and just need to
get it uploaded correctly.

**Full detail behind every claim here**: `docs/COMPLIANCE_REPORT.md`
(packaging/legal), `docs/REAL_OPPONENT_RESULTS.md` (manual portal testing
notes), `docs/GAME_SPEC.md` (rules).

---

## 0. What to upload, right now, in one line

**Upload `submissions/milestone5_champion/defense_v6_encryptor_fix_algo_folder/`
as a raw folder if the portal accepts folders. Otherwise upload
`submissions/milestone5_champion/defense_v6_encryptor_fix_permfix.zip`. Do
NOT upload `defense_v6_encryptor_fix.zip` (the plain one) — it has a known
packaging bug, §3.**

---

## 1. Pre-submission sanity checks (run these before you upload anything)

Run every one of these locally first. All of them should already pass as
of the last commit to this repo, but re-verify — don't trust a stale
memory of "we checked this already" right before a real submission.

```bash
cd /workspace

# 1a. Confirm algo_strategy.py is present and is the entry point (Verified
#     requirement -- README.md + python-algo/README.md both state uploads
#     missing this file fail compilation).
test -f submissions/milestone5_champion/defense_v6_encryptor_fix_algo_folder/algo_strategy.py \
  && echo "OK: algo_strategy.py present" || echo "FAIL: missing entry point"

# 1b. Confirm it's valid Python (a syntax error here == a guaranteed compile
#     failure on the portal).
python3 -c "import ast; ast.parse(open('submissions/milestone5_champion/defense_v6_encryptor_fix_algo_folder/algo_strategy.py').read())" \
  && echo "OK: syntax valid"

# 1c. Confirm run.sh is executable IN THE ACTUAL ARTIFACT you're about to
#     upload (the exact bug in section 3 below -- check the real file, not
#     just the source directory).
ls -la submissions/milestone5_champion/defense_v6_encryptor_fix_algo_folder/run.sh
# Expect: -rwxr-xr-x (mode 755). If it shows -rw-r--r-- (644), STOP -- see
# section 3, do not upload as-is.

# 1d. Confirm the zip (if you're using the zip instead of the folder) also
#     has run.sh executable, by inspecting the zip's own permission
#     metadata without extracting:
python3 -c "
import zipfile
zf = zipfile.ZipFile('submissions/milestone5_champion/defense_v6_encryptor_fix_permfix.zip')
for info in zf.infolist():
    if info.filename.endswith('run.sh'):
        mode = (info.external_attr >> 16) & 0o777
        print(f'{info.filename}: mode={oct(mode)}')
"
# Expect: mode=0o755. If you instead check defense_v6_encryptor_fix.zip
# (the PLAIN one, not _permfix), expect to see 0o644 -- that's the known
# bug, and exactly why you should not upload that file.

# 1e. Full fresh-extraction end-to-end test: unzip into a clean temp dir
#     (no manual chmod!) and run a real local match to confirm it actually
#     boots and plays.
rm -rf /tmp/submission_verify && mkdir -p /tmp/submission_verify
unzip -q submissions/milestone5_champion/defense_v6_encryptor_fix_permfix.zip -d /tmp/submission_verify
ls -la /tmp/submission_verify/defense_v6_encryptor_fix/run.sh   # confirm still 755 after extraction
python3 experiments/harness.py --algo1 /tmp/submission_verify/defense_v6_encryptor_fix --algo2 python-algo -n 1 --tag submission_final_check

# 1f. Confirm you're uploading the right thing: diff the exact file you're
#     about to upload against the tagged commit's version, expect NO diff.
diff <(git show milestone5-champion:baselines/defense_v6_encryptor_fix/algo_strategy.py) \
     submissions/milestone5_champion/defense_v6_encryptor_fix_algo_folder/algo_strategy.py \
  && echo "OK: matches the tagged commit exactly"
# For a full-directory check (not just algo_strategy.py), extract the whole
# tagged tree into a scratch dir and diff that instead:
rm -rf /tmp/tag_check && mkdir -p /tmp/tag_check
git archive milestone5-champion -- baselines/defense_v6_encryptor_fix | tar -x -C /tmp/tag_check
diff -rq /tmp/tag_check/baselines/defense_v6_encryptor_fix \
         submissions/milestone5_champion/defense_v6_encryptor_fix_algo_folder \
  | grep -v "run.ps1\|README.md\|\.zipignore"   # these are expected to differ/be absent, not code
```

**If any of 1a-1e fails, stop and fix it before uploading — do not upload
"and see what happens."**

## 2. The actual upload steps

1. Go to `https://terminal.c1games.com` and log in.
2. Navigate to the algo upload/management page (per `README.md`'s
   "Uploading Algos" section: *"Simply select the folder of your algo when
   prompted... Make sure to select the specific language folder... do not
   select the entire starterkit itself."*).
3. **Select `defense_v6_encryptor_fix_algo_folder/` if the portal's file
   picker supports selecting a folder directly** (safest — this sidesteps
   the zip/permission question in section 3 entirely, since a folder
   upload never goes through zip compression/extraction).
4. **If the portal only accepts a zip file**, upload
   `defense_v6_encryptor_fix_permfix.zip` — **not**
   `defense_v6_encryptor_fix.zip` (see section 3 for why).
5. Wait for the platform's own compile/validation step to finish. This is
   the point where a missing `algo_strategy.py` or a syntax error would be
   caught server-side (per `README.md` — we have not personally observed
   this step, since we have no portal access; treat point 6 below as the
   actual confirmation of success).
6. **Confirm success the only way we can currently recommend**: run (or
   have someone run) at least one match against a practice-sandbox
   opponent afterward and check that our algo actually plays coherent moves
   (see section 5 for what "coherent" looks like) rather than instantly
   forfeiting/crashing turn 1.

## 3. The one packaging gotcha you must know about (`run.sh` executable bit)

**Root cause (Verified by decompiling `engine.jar`,
`docs/COMPLIANCE_REPORT.md` §1.1):** the official `scripts/zipalgo_mac` /
`scripts/zipalgo_linux` tools produce a zip where `run.sh` loses its
executable permission bit (`0o100644` instead of `0o100755`). The engine
has a self-healing attempt (`chmod u+x` before launching `run.sh`) but never
waits for that `chmod` to finish before trying to execute the file —a real
race condition. We measured roughly a 6% local crash rate
(`java.io.IOException: error=13, Permission denied` /
`AlgoIndex 0 crashed bootup`) across repeated boot attempts of an
intentionally non-executable zip. The tournament runner may be slower or
containerized, which would plausibly make this race *worse*, not better —
unverified, but a real risk we can't rule out.

**The fix, already applied to every submission package in this repo**: zip
with the plain system `zip` tool instead (preserves permission bits by
default), or upload the unzipped folder directly. Every `*_permfix.zip` and
`*_algo_folder/` in every `submissions/*/` directory has already been fixed
and independently re-verified (fresh `unzip`, no manual `chmod`, real local
match run to completion). **This is why step 4 above says "not the plain
zip" — that plain zip still has the bug, kept only for transparency with
what the official tool actually produces.**

**If you ever need to build a NEW package from scratch** (e.g. after a
future champion change), do this, not the official tool alone:

```bash
cd /workspace
find baselines/<your_algo_dir> -name "__pycache__" -exec rm -rf {} +

# Optional: also produce the plain official-tool zip for transparency/parity
./scripts/zipalgo_linux baselines/<your_algo_dir> submissions/<dest>/<name>.zip

# The one that actually matters -- preserves the executable bit:
cd baselines
zip -r ../submissions/<dest>/<name>_permfix.zip <your_algo_dir> \
  -x '*.git*' '<your_algo_dir>/README.md' '<your_algo_dir>/*.ps1' '*__pycache__*'
cd ..

# And/or just copy the folder directly with the bit already set, as a
# third, zip-free option:
cp -r baselines/<your_algo_dir> submissions/<dest>/<name>_algo_folder
chmod +x submissions/<dest>/<name>_algo_folder/run.sh
```

Then re-run section 1's checks against the new artifact before uploading.

## 4. Known gaps in this checklist (things we could not verify ourselves)

Stated honestly rather than glossed over — we have **no portal login
access**, so several things below are inference from the starter kit's own
docs/code, not confirmed against the real submission flow:

- **Upload size limits**: unknown.
- **Allowed third-party pip packages**: unknown, and `run.sh` invokes plain
  `python3` with no `pip install` step anywhere in the starter kit —
  treat "standard library only" as the safe assumption unless you have
  reason to believe otherwise. Our current champion has zero third-party
  imports (check with `grep -n "^import\|^from" algo_strategy.py` if you
  add anything — it should only ever show `gamelib`, `random`, `math`,
  `warnings`, `sys`, `json`, `collections`).
- **Whether the portal's own upload flow independently fixes the `run.sh`
  permission bit server-side** (which would make section 3 moot for real
  submissions specifically, though the local risk would remain real
  either way): unknown. Given the fix has zero downside, upload the fixed
  artifact regardless of whether this turns out to matter.
- **Memory limits, wall-clock quota for a full match, and any
  compile-time check beyond "does `algo_strategy.py` exist and parse"**:
  unknown.
- **Whether the actual tournament config matches this repo's
  `game-configs.json`** ("High School Terminal 2026") exactly: **strongly
  supported** (it's the official kit's own config file, used by the same
  `engine.jar` shipped in this same repo) but not independently confirmed
  against a live tournament match.

If you have portal access and can check any of these directly before the
event, please do — update this section with what you find.

## 5. What success vs. failure actually looks like

**A successful submission**, based on what we can infer/have observed:

- The portal accepts the upload without an immediate error (per point 5 in
  section 2 — we have not personally observed this step, but a missing
  entry point or syntax error is documented to fail compilation).
- A subsequent match (practice sandbox or real) shows OUR algo placing
  real structures and mobile units turn-by-turn (TURRETs/WALLs appearing in
  the corner staircase pattern described in `docs/TOURNAMENT_STRATEGY_BRIEF.md`
  §2, SCOUTs/DEMOLISHERs launching from turn ~6 onward) — not an instant
  forfeit, not a blank board.
- Reported per-turn compute time is small (double-digit-to-low-hundreds
  milliseconds range, based on our own local measurements and one
  real-platform data point: ~343ms cumulative over 26 rounds via the user's
  manual practice-sandbox test, `docs/REAL_OPPONENT_RESULTS.md` §3.2) — a
  match where our algo is reported taking multiple seconds per turn would
  be a red flag worth investigating (possible sign the wrong/broken package
  was uploaded, or an unexpected environment difference).

**A failed submission looks like one of:**

- **Immediate compile/validation rejection** — almost certainly a missing
  `algo_strategy.py`, a syntax error, or (per the README) selecting the
  wrong folder (the whole starter kit instead of just the algo directory).
  Re-run section 1's checks; they would have caught this.
- **`AlgoIndex 0 crashed bootup`** / a `Permission denied` error at match
  start — the exact symptom of the `run.sh` executable-bit race in section
  3. If you see this and you uploaded the plain (non-permfix) zip, that's
  almost certainly why — re-upload the `_permfix.zip` or the raw
  `_algo_folder/`.
- **Our algo does nothing / plays only the default starter-kit behavior** —
  a sign the wrong folder or an unmodified `python-algo/` was uploaded by
  mistake instead of our actual champion. Re-check step 3 in section 2.
- **A game that reaches turn 100 with us clearly ahead but somehow still
  losing** — check `docs/TOURNAMENT_STRATEGY_BRIEF.md` §5 for the
  compute-time tie-break rule; this would be worth investigating rather
  than assumed to be an engine bug, since it's a real, documented rule, not
  a hypothetical.

## 6. Timing recommendation

Do section 1's checks and the actual upload (section 2) **well before** any
hard deadline — not because we know anything specific about how long the
portal takes to process an upload (unverified, section 4), but because
section 1's checks are cheap (minutes) and finding a problem with enough
time left to fall back to a previous known-good tag
(`docs/TOURNAMENT_STRATEGY_BRIEF.md` §9) is the entire point of doing them
at all.
