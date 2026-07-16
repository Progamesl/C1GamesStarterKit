import gamelib
import random
from sys import maxsize
import json

"""
MILESTONE 7 STRESS-TEST OPPONENT: "alternating_corner_rush".

`public_opponents/travelling_salesmen_v33` beats every prior champion via a
continuous, un-paused, 100%-MP Demolisher rush at a SINGLE fixed corner lane
(confirmed empirically, docs/MILESTONE_6_REPORT.md sec 3: it always ends up
attacking the same relative flank against our mirror-symmetric defense,
because `should_right_be_open`'s tie only ever breaks one way against a
perfectly symmetric target). This exists to check whether a Milestone 7
defense fix that handles v33's one-sided pattern also holds up against a
rush that deliberately ALTERNATES flanks -- i.e. whether the fix is a
genuine full-width improvement or an accidental one-sided overfit to v33's
own specific (and, it turns out, not even fully committed) targeting.

Same continuous, un-paused, 100%-MP posture as v33 (never gated, never
pauses), but explicitly switches which corner it commits to every
ALTERNATE_PERIOD turns regardless of any read of the opponent's own defense
-- a strictly harder, less exploitable version of "pick a side" than v33's
own weight-based heuristic, specifically to stress-test generalization
rather than to mimic v33 exactly (mimicking it exactly would risk the
overfitting failure mode the user explicitly warned about).
"""

ALTERNATE_PERIOD = 6


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring ALTERNATING_CORNER_RUSH opponent...')
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

        # A modest, symmetric static defense (NOT the point of this
        # opponent -- the point is the alternating rush) so it isn't a
        # complete pushover to unrelated offense either.
        self.wall_front = [[x, 13] for x in [0, 1, 2, 3, 4, 5, 22, 23, 24, 25, 26, 27]]
        self.corner_turrets = [[1, 12], [26, 12], [3, 11], [24, 11]]
        self.left_lane = [4, 9]
        self.right_lane = [23, 9]

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        turn = game_state.turn_number
        gamelib.debug_write('ALTERNATING_CORNER_RUSH turn {}'.format(turn))
        game_state.suppress_warnings(True)

        game_state.attempt_spawn(TURRET, self.corner_turrets)
        game_state.attempt_spawn(WALL, self.wall_front)

        if turn >= 4:
            # Flip flank every ALTERNATE_PERIOD turns, unconditionally --
            # deliberately not reading our own defense's state at all, so
            # this can't be baited/faked out the way a weight-based
            # heuristic could.
            lane = self.left_lane if (turn // ALTERNATE_PERIOD) % 2 == 0 else self.right_lane
            game_state.attempt_spawn(DEMOLISHER, lane, 1000)

        game_state.submit_turn()


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
