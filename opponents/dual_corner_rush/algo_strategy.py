import gamelib
import random
from sys import maxsize
import json

"""
MILESTONE 7 STRESS-TEST OPPONENT: "dual_corner_rush".

A second lane-variation stress test alongside
`opponents/alternating_corner_rush`: instead of switching flanks over time,
this splits its MP roughly evenly and rushes BOTH corners simultaneously,
every turn, continuously and un-paused (same "never gated" posture as
`travelling_salesmen_v33`, but attacking both of our flanks at once instead
of committing everything to one). This specifically stress-tests whether a
Milestone 7 fix that reallocates SP toward whichever ONE side is under
`lockdown` (docs/MILESTONE_7_REPORT.md) still holds up when BOTH sides are
under real, simultaneous pressure at once -- a genuinely different, harder
threat shape than v33's single-lane commitment, not just a copy of it.
"""


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring DUAL_CORNER_RUSH opponent...')
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

        self.wall_front = [[x, 13] for x in [0, 1, 2, 3, 4, 5, 22, 23, 24, 25, 26, 27]]
        self.corner_turrets = [[1, 12], [26, 12], [3, 11], [24, 11]]
        self.left_lane = [4, 9]
        self.right_lane = [23, 9]

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        turn = game_state.turn_number
        gamelib.debug_write('DUAL_CORNER_RUSH turn {}'.format(turn))
        game_state.suppress_warnings(True)

        game_state.attempt_spawn(TURRET, self.corner_turrets)
        game_state.attempt_spawn(WALL, self.wall_front)

        if turn >= 4:
            demolisher_cost = game_state.type_cost(DEMOLISHER)[MP]
            mp = game_state.get_resource(MP)
            half_budget = mp / 2.0
            num_each = int(half_budget // demolisher_cost)
            if num_each > 0:
                game_state.attempt_spawn(DEMOLISHER, self.left_lane, num_each)
                game_state.attempt_spawn(DEMOLISHER, self.right_lane, num_each)
            # Any odd leftover MP: send it wherever's cheapest this turn.
            game_state.attempt_spawn(DEMOLISHER, self.left_lane, 1000)

        game_state.submit_turn()


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
