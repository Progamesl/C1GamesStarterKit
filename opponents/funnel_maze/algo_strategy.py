import gamelib
import random
from sys import maxsize
import json

"""
OPPONENT ARCHETYPE (for benchmarking, not a submission candidate): "funnel_maze".

Deliberately static maze/path-control defense, per prior-art hypothesis #6
(docs/STRATEGIC_PRIOR_ART_REPORT.md 3.4): a wall layout engineered to force enemy
mobile units along one predictable corridor into a turret kill zone, rather than a
reactive defense. Attacks with an occasional DEMOLISHER line down its own corridor.
This exists purely to test whether our "defense" baseline's reactive style has a
blind spot against a maze it hasn't seen before -- it is intentionally a different
archetype from anything in baselines/.
"""


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring FUNNEL_MAZE opponent...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0

        # A single funnel corridor on the right side: a wall channel that forces
        # any mobile unit path down column x=24-26 into a 3-turret kill zone.
        self.maze_walls = (
            [[x, 13] for x in range(0, 22)] +
            [[22, 13], [22, 12], [22, 11], [22, 10], [22, 9]] +
            [[26, 9], [26, 10], [26, 11], [26, 12], [26, 13]] +
            [[x, 9] for x in range(22, 27)]
        )
        self.kill_zone_turrets = [[23, 9], [24, 9], [25, 9], [24, 8]]
        self.corridor_exit = [24, 9]

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('FUNNEL_MAZE turn {}'.format(game_state.turn_number))
        game_state.suppress_warnings(True)

        game_state.attempt_spawn(WALL, self.maze_walls)
        game_state.attempt_spawn(TURRET, self.kill_zone_turrets)
        game_state.attempt_upgrade(self.kill_zone_turrets)

        if game_state.turn_number >= 3 and game_state.get_resource(MP) >= 6:
            game_state.attempt_spawn(DEMOLISHER, [24, 13], 2)

        game_state.submit_turn()


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
