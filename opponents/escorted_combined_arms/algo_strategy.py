import gamelib
import random
from sys import maxsize
import json

"""
OPPONENT ARCHETYPE (Milestone 2, for benchmarking, not a submission candidate):
"escorted_combined_arms".

Re-derives prior-art hypothesis #5 (docs/STRATEGIC_PRIOR_ART_REPORT.md 3.3/5.5)
from CURRENT Verified unit stats (docs/GAME_SPEC.md 2.2), not historical ones:
DEMOLISHER (3 MP, 5 HP, 0.5 speed, 6.0 dmg vs both mobile+structure, 4.5 range) is
the only mobile unit that reliably damages structures at range, but it is slow and
fragile. SCOUT (1 MP, 15 HP, speed 1, 2.0/2.0 dmg, 3.5 range) is cheap and fast.

Mechanism (genuinely different attack surface from our other opponents -- see
docs/COUNTEREXAMPLE_SUITE.md for the explicit novelty analysis): send a SCOUT
"screen" down a lane one full turn BEFORE the DEMOLISHER group following the same
lane, so the screen draws/occupies turret attention and clears any INTERCEPTORs
first, then the slower DEMOLISHER arrives one turn later into a lane that's already
partially fought over, rather than sending everything simultaneously (as
opponents/burst_hoarder and opponents/multi_lane_saturation do). Also places a
SUPPORT structure directly behind the launch point -- per prior-art's own
recommendation (section 3.3), we do NOT assume its shield formula is strong (it's
an explicit unverified gap, GAME_SPEC.md 2.1), but including it means this opponent
also incidentally generates real local data on whether a nearby Support measurably
helps a Demolisher's survival, if we look at the replay/logs afterward.
"""

ESCORT_PERIOD = 4


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring ESCORTED_COMBINED_ARMS opponent...')
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

        self.min_defense = [[0, 13], [27, 13], [1, 12], [26, 12]]
        self.pending_lane = None  # set on the "screen" turn, consumed on the "escort" turn

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        turn = game_state.turn_number
        gamelib.debug_write('ESCORTED_COMBINED_ARMS turn {}'.format(turn))
        game_state.suppress_warnings(True)

        game_state.attempt_spawn(TURRET, self.min_defense)

        cycle_pos = turn % ESCORT_PERIOD
        if turn >= 2 and cycle_pos == 0:
            # Screen turn: choose a lane, send scouts, remember the lane for next turn.
            left_defense = self.detect_enemy_unit(game_state, valid_x=list(range(0, 14)))
            right_defense = self.detect_enemy_unit(game_state, valid_x=list(range(14, 28)))
            options = [[6, 7], [21, 7], [13, 0], [14, 0]]
            best = self.least_damage_spawn_location(game_state, options)
            game_state.attempt_spawn(SCOUT, best, 5)
            self.pending_lane = best
        elif self.pending_lane is not None and cycle_pos == 1:
            # Escort turn: the demolisher group follows one turn behind the screen,
            # with a Support placed just behind the launch point.
            support_loc = [self.pending_lane[0], min(self.pending_lane[1] + 2, 6)]
            game_state.attempt_spawn(SUPPORT, support_loc)
            game_state.attempt_spawn(DEMOLISHER, self.pending_lane, 2)
            self.pending_lane = None

        game_state.submit_turn()

    def least_damage_spawn_location(self, game_state, location_options):
        damages = []
        for location in location_options:
            if game_state.contains_stationary_unit(location):
                damages.append(float('inf'))
                continue
            path = game_state.find_path_to_edge(location)
            damage = 0
            if path:
                for path_location in path:
                    damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            else:
                damage = float('inf')
            damages.append(damage)
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x=None, valid_y=None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and \
                       (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
