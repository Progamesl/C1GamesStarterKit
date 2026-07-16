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

- `defense_v15_dense_opening_algo_folder/` — unpacked, self-contained folder.
- `defense_v15_dense_opening_permfix.zip` — recommended upload archive; preserves
  `run.sh` as executable.

The thin candidate wrapper loads `v6_base/` included inside the package, so it
does not depend on repository paths after upload.

Archive SHA-256:

```text
e39e6df78fc74465507345fb3191be2e6ac92317339d5261d65eef22848f96cb
```

**Verified:** the archive passed `unzip -t`; a clean extraction retained
`run.sh` mode `0755`; without any manual `chmod`, the extracted package
completed and won a real local match against `python-algo`.

## Rollback

The prior accepted package remains untouched at `milestone5-champion` and
`submissions/milestone5_champion/`.
