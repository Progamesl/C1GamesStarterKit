"""Milestone 9 mechanism C: dense opening plus adaptive Interceptor screen.

This is the bounded combination of mechanisms A and B.  The behavioral
classifier/screen is inherited from ``defense_v14_adaptive_interceptors``;
only v6's SP build and upgrade hooks are replaced with the independently
replay-derived dense opening from ``defense_v15_dense_opening``.
"""

from __future__ import annotations

import importlib.util
import os
import sys


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ADAPTIVE_DIR = os.path.join(
    REPO_ROOT, "baselines", "defense_v14_adaptive_interceptors"
)
sys.path.insert(0, ADAPTIVE_DIR)
_SPEC = importlib.util.spec_from_file_location(
    "milestone9_adaptive_base", os.path.join(ADAPTIVE_DIR, "algo_strategy.py")
)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("could not load defense_v14_adaptive_interceptors")
adaptive = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(adaptive)
gamelib = adaptive.gamelib
v6 = adaptive.v6


class AlgoStrategy(adaptive.AlgoStrategy):
    def on_game_start(self, config):
        # Deep coordinates were the only coordinate family to turn any sweep
        # matchup into wins. High is only a default; the controlled combined
        # sweep can still override either value through the inherited env knobs.
        os.environ.setdefault("M9_SCREEN_COORD_PROFILE", "deep")
        os.environ.setdefault("M9_SCREEN_SPEND_PROFILE", "high")
        super().on_game_start(config)

        self.dense_opening_turrets = [
            [1, 13], [1, 12], [26, 13], [26, 12],
            [2, 13], [2, 12], [25, 13], [25, 12],
            [3, 13], [3, 12], [24, 13], [24, 12],
            [11, 12], [16, 12], [12, 11], [15, 11],
            [14, 13], [12, 13],
        ]
        self.endpoint_walls = [[0, 13], [27, 13]]
        self.corridor_supports = [
            [20, 12], [19, 11], [17, 11], [18, 10],
            [7, 12], [8, 11], [10, 11], [9, 10],
        ]

    def _screen_plan(self, game_state):
        plan = super()._screen_plan(game_state)
        if plan is None:
            return None
        mode, flanks, budget = plan

        # Bisection of combined-v1's v33 regression: dense-only won quickly,
        # while dense+screen survived much longer but never attacked because
        # mechanism A intentionally banked every leftover MP. During sustained
        # Demolisher pressure (not a Scout emergency), reserve v6's normal
        # 9-MP offense threshold on even turns. Odd turns still devote the
        # selected full fraction to the screen.
        if (
            "sustained-demo" in mode
            and "scout" not in mode
            and game_state.turn_number >= 6
            and game_state.turn_number % 2 == 0
        ):
            mp = int(game_state.get_resource(v6.MP))
            budget = min(budget, max(1, mp - 9))
        return mode, flanks, budget

    def opportunistic_offense(self, game_state):
        plan = self._screen_plan(game_state)
        if plan is None:
            return v6.AlgoStrategy.opportunistic_offense(self, game_state)

        mode, flanks, budget = plan
        self._deploy_screen(game_state, mode, flanks, budget)
        if (
            "sustained-demo" in mode
            and "scout" not in mode
            and game_state.turn_number >= 6
        ):
            # The reserve above makes this a real v6 attack on even turns;
            # v6 naturally does nothing offensive on odd turns.
            return v6.AlgoStrategy.opportunistic_offense(self, game_state)

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
        game_state.attempt_upgrade(self.endpoint_walls)
        game_state.attempt_upgrade(self.corridor_supports)


if __name__ == "__main__":
    AlgoStrategy().start()
