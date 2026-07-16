import gamelib
import random
from sys import maxsize
import json

"""
ADVERSARIAL PROBE (Milestone 2 hardening, not a submission candidate):
"multi_lane_saturation".

Targets a different specific hypothesis than middle_rush_exploit: that
baselines/defense's reactive-defense per-turn SP spend cap (6 SP, see
`max_reactive_spend_per_turn` in baselines/defense/algo_strategy.py) could be
overwhelmed by breaching at 3+ well-separated points in the SAME turn, forcing it
to only partially repair each one, with damage compounding turn over turn. Sends a
minimal-defense, near-all-MP-every-turn 3-way split (near-left, middle, near-right)
SCOUT swarm from turn 2 onward, escalating count as MP allows, plus periodic
DEMOLISHERs down whichever lane currently looks cheapest.
"""


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring MULTI_LANE_SATURATION opponent...')
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
        self.min_defense = [[0, 13], [27, 13]]
        self.lanes = [[5, 8], [13, 0], [22, 8]]  # near-left, middle, near-right

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        turn = game_state.turn_number
        gamelib.debug_write('MULTI_LANE_SATURATION turn {}'.format(turn))
        game_state.suppress_warnings(True)

        game_state.attempt_spawn(TURRET, self.min_defense)

        if turn >= 2:
            mp = game_state.get_resource(MP)
            scout_cost = game_state.type_cost(SCOUT)[MP]
            demolisher_cost = game_state.type_cost(DEMOLISHER)[MP]
            per_lane_budget = mp / 3.0
            if per_lane_budget >= demolisher_cost and turn % 4 == 0:
                for lane in self.lanes:
                    game_state.attempt_spawn(DEMOLISHER, lane, 1)
            else:
                for lane in self.lanes:
                    n = max(1, int(per_lane_budget // scout_cost))
                    game_state.attempt_spawn(SCOUT, lane, n)

        game_state.submit_turn()


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
