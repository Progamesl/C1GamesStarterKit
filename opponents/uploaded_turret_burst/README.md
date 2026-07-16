# Uploaded turret-burst opponent fixture

`algo_strategy.py` is a byte-for-byte copy of the independently supplied file:

```text
/home/ubuntu/.cursor/projects/workspace/uploads/algo_strategy__1__4336.py
SHA-256: a5f61c5a5c6256f580131edaf7d1aae97facd25c24a0a147fbc485b5c6d703f1
```

No strategy logic was changed. The only compatibility adaptation is in
`run.sh`: it adds this repository's stock `python-algo/` directory to
`PYTHONPATH`, allowing the unchanged `import gamelib` statement to run under
the local engine and correct High School Terminal 2026 configuration.

The stale `wall.health == 60` condition remains unchanged as part of the
black-box opponent. It does not prevent the fixture from running.
