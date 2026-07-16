# Milestone 9 champion submission

**Algo:** `baselines/defense_v15_dense_opening`

**Tag:** `milestone9-champion`

The candidate keeps accepted v6's MP offense, breach tracking, reactive
defense, and endgame policy. Its SP policy uses the uploaded replay's observable
mechanism: an 18-Turret base-range opening, upgraded endpoint Walls, then
delayed upgraded Support corridors.

## Evidence

- v33: 10/10 wins (milestone5 champion: 0/20).
- replay-stack without Supports: 10/10 wins (milestone5 champion: 0/20).
- fully shielded replay-stack: 0/10; this remains unresolved.
- current 31-opponent regression: 300/310 overall, with 10/10 against every
  opponent except the fully shielded replay fixture.
- all 290/290 games against opponents previously beaten by the milestone5
  champion were retained; zero candidate crashes and zero harness errors.

See `docs/MILESTONE_9_REPORT.md` for the full bounded search and replay-derived
evidence.

## Package

- `defense_v15_dense_opening_flat_algo_folder/` — **recommended** unpacked
  package. It has the full strategy in one top-level `algo_strategy.py` and a
  top-level `gamelib/`; it has no dynamic import or nested strategy dependency.
- `defense_v15_dense_opening_flat_permfix.zip` — **recommended upload
  archive**; deterministic and preserves `run.sh` as executable.
- `defense_v15_dense_opening_algo_folder/` and
  `defense_v15_dense_opening_permfix.zip` — original nested package, retained
  for provenance only.

The original package's thin wrapper imports its bundled `v6_base/`. It works
when the directory tree is preserved, but a simulation that removed
`v6_base/` (matching a portal that flattens or ignores nested files) failed
before game start with `FileNotFoundError`. The portal's actual handling is
not locally observable, so the flattened package removes that avoidable risk
before another website test.

Flattened archive SHA-256:

```text
0d262970cb5c27168884d2cbff4a560f8f5b600dcb20350b22be756b245acc7d
```

**Verified:** the flattened archive passed `unzip -t`; a fresh extraction
retained `run.sh` mode `0755` and contained no `v6_base/`. Without manual
changes, that extraction completed four real local games: 2/2 wins against
`travelling_salesmen_v33` and the same expected 0/2 result against the newly
uploaded stress opponent, with zero crashes. This matching strategy behavior
shows that the uploaded-opponent loss is reproducible with the flattened
package and is not explained solely by the old nested import.

## Rollback

The prior accepted package remains untouched at `milestone5-champion` and
`submissions/milestone5_champion/`.
