import gamelib
import random
from sys import maxsize
import json

"""
MILESTONE 7 STRESS-TEST OPPONENT: "scout_demolisher_corner_mix".

A third lane-variation/composition stress test: same continuous, un-paused,
100%-MP, single-fixed-corner-lane posture as `travelling_salesmen_v33`
(docs/MILESTONE_6_REPORT.md), but mixes SCOUTs in with the DEMOLISHERs every
wave instead of sending pure Demolishers. Scouts are cheaper (1 MP vs 2) and
weaker per-unit, but a mixed wave changes the arithmetic of how many bodies
converge on our corner cluster per turn and in what HP distribution -- this
specifically checks whether a Milestone 7 fix tuned against v33's own exact
composition (confirmed via reading v33's own `algo_strategy.py`: pure EMP/
Demolisher, no Scouts at all, ever) generalizes to a merely-similar-looking
but compositionally different rush, rather than being an accidental
overfit to "exactly Demolishers, exactly this HP/damage profile."
"""

MIX_DEMOLISHER_MP_FRACTION = 0.5  # rest goes to scouts


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring SCOUT_DEMOLISHER_CORNER_MIX opponent...')
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
        # Fixed single lane, same as v33's own commitment pattern -- the
        # variable under test here is COMPOSITION, not lane variety (that's
        # covered by the other two stress opponents).
        self.lane = [23, 9]

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        turn = game_state.turn_number
        gamelib.debug_write('SCOUT_DEMOLISHER_CORNER_MIX turn {}'.format(turn))
        game_state.suppress_warnings(True)

        game_state.attempt_spawn(TURRET, self.corner_turrets)
        game_state.attempt_spawn(WALL, self.wall_front)

        if turn >= 4:
            mp = game_state.get_resource(MP)
            demolisher_cost = game_state.type_cost(DEMOLISHER)[MP]
            demolisher_budget = mp * MIX_DEMOLISHER_MP_FRACTION
            num_demolishers = int(demolisher_budget // demolisher_cost)
            if num_demolishers > 0:
                game_state.attempt_spawn(DEMOLISHER, self.lane, num_demolishers)
            game_state.attempt_spawn(SCOUT, self.lane, 1000)

        game_state.submit_turn()


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
