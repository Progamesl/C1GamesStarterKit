import gamelib
import json

"""
Fully passive probe partner for the SUPPORT/shield-mechanism experiment
(docs/MILESTONE_4_REPORT.md). Never spawns anything, never attacks -- exists
purely so the other side (experiments/shield_probe) can be observed in a
replay uncontaminated by combat damage.
"""


class AlgoStrategy(gamelib.AlgoCore):
    def on_game_start(self, config):
        self.config = config

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        game_state.suppress_warnings(True)
        game_state.submit_turn()


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
