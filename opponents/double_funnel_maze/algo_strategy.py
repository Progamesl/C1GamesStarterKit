import gamelib
import random
from sys import maxsize
import json

"""
OPPONENT ARCHETYPE (Milestone 2, for benchmarking, not a submission candidate):
"double_funnel_maze".

A distinct maze/path-control shape from opponents/funnel_maze (prior-art hypothesis
#6, docs/STRATEGIC_PRIOR_ART_REPORT.md 3.4): instead of a single corridor on one
side, this builds TWO symmetric wall corridors (one near each flank) that both
redirect inward toward a shared central kill zone, and alternates DEMOLISHER pushes
down whichever corridor currently looks cheaper. Novelty vs. funnel_maze: this
tests whether our baselines' defenses have a blind spot specifically at the
board's center (where both corridors converge) rather than off to one side, and
whether alternating attack sides defeats a defense tuned to expect one lane.
"""


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring DOUBLE_FUNNEL_MAZE opponent...')
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

        # Two corridors, one from each flank, both directing traffic to a shared
        # central kill zone around x=12-15, y=8-9.
        self.maze_walls = (
            [[x, 13] for x in [0, 1, 2, 3, 24, 25, 26, 27]] +
            # left corridor walls
            [[4, y] for y in range(9, 14)] + [[9, y] for y in range(9, 13)] +
            # right corridor walls
            [[23, y] for y in range(9, 14)] + [[18, y] for y in range(9, 13)]
        )
        self.kill_zone_turrets = [[12, 8], [13, 8], [14, 8], [15, 8], [13, 7], [14, 7]]
        self.left_launch = [5, 8]
        self.right_launch = [22, 8]

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        turn = game_state.turn_number
        gamelib.debug_write('DOUBLE_FUNNEL_MAZE turn {}'.format(turn))
        game_state.suppress_warnings(True)

        game_state.attempt_spawn(WALL, self.maze_walls)
        game_state.attempt_spawn(TURRET, self.kill_zone_turrets)
        game_state.attempt_upgrade(self.kill_zone_turrets)

        if turn >= 3 and game_state.get_resource(MP) >= 6:
            lane = self.left_launch if turn % 2 == 0 else self.right_launch
            game_state.attempt_spawn(DEMOLISHER, lane, 2)

        game_state.submit_turn()


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
