import gamelib
import random
from sys import maxsize
import json

"""
OPPONENT ARCHETYPE (for benchmarking, not a submission candidate): "adaptive_reactive".

Per prior-art hypothesis #1/#18 (docs/STRATEGIC_PRIOR_ART_REPORT.md 3.1), the most
corroborated mechanism across all documented sources: track which side (left/right
half of the board) the opponent's attacks have come from over the last few turns,
and pre-emptively reinforce whichever side has been attacked more, rather than a
static layout. Attacks toward whichever side WE detect has fewer of the opponent's
stationary units. This is meant to stress-test our baselines against something that
actively responds to *our* behavior, not just a fixed script.
"""


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring ADAPTIVE_REACTIVE opponent...')
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

        self.left_hits = 0
        self.right_hits = 0
        self.base_turrets = [[3, 12], [24, 12], [13, 11], [14, 11]]
        self.base_walls = [[x, 13] for x in [2, 3, 4, 23, 24, 25]]

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('ADAPTIVE_REACTIVE turn {}'.format(game_state.turn_number))
        game_state.suppress_warnings(True)

        game_state.attempt_spawn(TURRET, self.base_turrets)
        game_state.attempt_spawn(WALL, self.base_walls)
        game_state.attempt_upgrade(self.base_turrets)

        # Reinforce whichever side has taken more damage recently (decay so old
        # information doesn't dominate forever).
        self.left_hits *= 0.7
        self.right_hits *= 0.7
        if self.left_hits > self.right_hits:
            game_state.attempt_spawn(TURRET, [[6, 10], [7, 10]])
        elif self.right_hits > self.left_hits:
            game_state.attempt_spawn(TURRET, [[20, 10], [21, 10]])

        self.attack(game_state)

        game_state.submit_turn()

    def attack(self, game_state):
        if game_state.get_resource(MP) < 5:
            return
        left_defense = self.detect_enemy_unit(game_state, valid_x=list(range(0, 14)))
        right_defense = self.detect_enemy_unit(game_state, valid_x=list(range(14, 28)))
        target = [3, 10] if left_defense <= right_defense else [24, 10]
        game_state.attempt_spawn(SCOUT, target, 1000)

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x=None, valid_y=None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and \
                       (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units

    def on_action_frame(self, turn_string):
        state = json.loads(turn_string)
        breaches = state["events"]["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = (breach[4] == 1)
            if not unit_owner_self:
                if location[0] < 14:
                    self.left_hits += 1
                else:
                    self.right_hits += 1


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
