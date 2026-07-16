"""Milestone 9 mechanism B: replay-derived dense opening on accepted v6.

The uploaded replay exposes actions, not participant source.  This candidate
therefore implements only independently observable mechanisms:

* spend the opening 40 SP on 18 base (long-range) Turrets and two upgraded
  endpoint Walls;
* never convert those Turrets to the shorter-range upgraded form;
* after the opening is intact, accumulate SP and add upgraded Support groups
  along the two observed mobile corridors.

All MP policy, breach tracking, reactive defense, and endgame behavior come
unchanged from ``defense_v6_encryptor_fix``.
"""

from __future__ import annotations

import importlib.util
import os
import sys


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CANDIDATE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_V6_DIR = os.path.join(CANDIDATE_DIR, "v6_base")
REPO_V6_DIR = os.path.join(REPO_ROOT, "baselines", "defense_v6_encryptor_fix")
# Submission packages include a local v6_base copy so this thin, auditable
# mechanism diff is self-contained. Repository experiments continue to use the
# canonical accepted baseline directly.
V6_DIR = (
    LOCAL_V6_DIR
    if os.path.isfile(os.path.join(LOCAL_V6_DIR, "algo_strategy.py"))
    else REPO_V6_DIR
)
sys.path.insert(0, V6_DIR)
_SPEC = importlib.util.spec_from_file_location(
    "milestone9_dense_v6_base", os.path.join(V6_DIR, "algo_strategy.py")
)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("could not load defense_v6_encryptor_fix")
v6 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(v6)
gamelib = v6.gamelib


class AlgoStrategy(v6.AlgoStrategy):
    def on_game_start(self, config):
        super().on_game_start(config)

        # P1 opening coordinates observed directly in the uploaded replay.
        # They are actions visible to either player; no participant code is
        # available or used.
        self.dense_opening_turrets = [
            [1, 13], [1, 12], [26, 13], [26, 12],
            [2, 13], [2, 12], [25, 13], [25, 12],
            [3, 13], [3, 12], [24, 13], [24, 12],
            [11, 12], [16, 12], [12, 11], [15, 11],
            [14, 13], [12, 13],
        ]
        self.endpoint_walls = [[0, 13], [27, 13]]

        # The replay added these as two delayed groups.  Add one fully-upgraded
        # anchor at a time only after turn 4; this preserves the mechanism while
        # avoiding an exact hardcoded replay turn schedule.
        self.corridor_supports = [
            [20, 12], [19, 11], [17, 11], [18, 10],
            [7, 12], [8, 11], [10, 11], [9, 10],
        ]

    def _dense_opening_intact(self, game_state):
        return all(
            game_state.contains_stationary_unit(location)
            for location in self.dense_opening_turrets + self.endpoint_walls
        )

    def build_core_defense(self, game_state):
        game_state.attempt_spawn(v6.TURRET, self.dense_opening_turrets)
        game_state.attempt_spawn(v6.WALL, self.endpoint_walls)
        game_state.attempt_upgrade(self.endpoint_walls)

        if game_state.turn_number < 4 or not self._dense_opening_intact(game_state):
            return

        desired = min(
            len(self.corridor_supports),
            1 + (game_state.turn_number - 4) // 2,
        )
        for location in self.corridor_supports[:desired]:
            game_state.attempt_spawn(v6.SUPPORT, location)
            game_state.attempt_upgrade(location)

    def upgrade_core(self, game_state):
        # Intentionally do not upgrade Turrets: in this config the base unit's
        # 4.5 range drops to 3.5 on upgrade. Endpoint Walls and corridor
        # Supports retain their useful upgrades.
        game_state.attempt_upgrade(self.endpoint_walls)
        game_state.attempt_upgrade(self.corridor_supports)


if __name__ == "__main__":
    AlgoStrategy().start()
