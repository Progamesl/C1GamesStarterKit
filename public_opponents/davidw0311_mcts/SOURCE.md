# Source

- Repo: https://github.com/davidw0311/c1_terminal
- Folder: `AI_alg_v1-4-add-substrat/`
- Author: davidw0311 (personal/student project, no placement claim)
- License: none found (no LICENSE file; defaults to all-rights-reserved)
- 971-line MCTS-based algo (numpy/scipy), tracks enemy spawns via
  on_action_frame. Notably slow: ~131-160s total compute per game (vs our
  ~200ms), the slowest opponent benchmarked in this project, but still well
  under the 5000ms soft / 35000ms hard per-turn caps.
- Usage: unmodified local black-box test opponent only.
