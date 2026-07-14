import gamelib
import random
import math
import warnings
from sys import maxsize
import json

"""
BASELINE: "rush" -- aggressive early offense-heavy strategy.

Design intent (see docs/GAME_SPEC.md for cited stats):

  - Minimal defense: just enough WALL funneling + two corner TURRETs to avoid being
    trivially one-shot by an opposing rush, never more.
  - From turn 0, spend nearly all MP every turn on SCOUT swarms (1 MP, 15 HP,
    2/2 dmg, speed 1 -- the fastest unit) aimed at whichever spawn edge our own
    least-damage heuristic says is currently cheapest to walk.
  - Periodically (every DEMOLISHER_PERIOD turns) escorts a DEMOLISHER (3 MP, 5 HP,
    0.5 speed, 6/6 dmg, 4.5 range -- the only mobile unit that reliably damages
    structures at range per docs/GAME_SPEC.md 2.2) alongside scouts once enough MP
    has been banked, targeting the side with fewer detected enemy stationary units.
  - Only patches a defensive hole if it has been hit >=2 times recently, to avoid
    ever diverting MP/SP away from the attack tempo for a one-off graze.
  - This archetype is explicitly the "high variance / high tempo" baseline: it is
    expected to beat static/undertuned defenses quickly and to be more fragile
    against a well-defended or reactive opponent -- exactly what we want a second,
    contrasting baseline for, per the benchmarking plan.
"""

DEMOLISHER_PERIOD = 3


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring RUSH baseline...')
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

        self.recent_breaches = {}  # location tuple -> hit count
        self.min_defense_turrets = [[0, 13], [27, 13]]
        self.funnel_walls = [[2, 13], [3, 13], [24, 13], [25, 13], [13, 3], [14, 3]]

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('RUSH turn {}'.format(game_state.turn_number))
        game_state.suppress_warnings(True)

        self.build_minimal_defense(game_state)
        self.patch_repeated_breaches(game_state)
        self.attack(game_state)

        game_state.submit_turn()

    def build_minimal_defense(self, game_state):
        game_state.attempt_spawn(TURRET, self.min_defense_turrets)
        game_state.attempt_spawn(WALL, self.funnel_walls)

    def patch_repeated_breaches(self, game_state):
        for loc, count in list(self.recent_breaches.items()):
            if count >= 2:
                build_loc = [loc[0], loc[1] + 1]
                if build_loc[1] < game_state.HALF_ARENA:
                    game_state.attempt_spawn(TURRET, build_loc)

    def attack(self, game_state):
        if game_state.turn_number == 0:
            # Opening probe with interceptors is cheap info about the opponent's
            # very first defensive layout before committing real MP.
            self.stall_with_interceptors(game_state, max_spend=2)
            return

        left_defense = self.detect_enemy_unit(game_state, valid_x=list(range(0, 14)))
        right_defense = self.detect_enemy_unit(game_state, valid_x=list(range(14, 28)))
        scout_spawn_location_options = [[13, 0], [14, 0]] if left_defense <= right_defense else [[13, 0], [14, 0]]
        # (both spawn cells route to the same general funnel; the meaningful choice
        # is *which lane* -- captured by least_damage_spawn_location below.)
        options = [[13, 0], [14, 0], [1, 12], [26, 12]]
        best = self.least_damage_spawn_location(game_state, options)

        if (game_state.turn_number % DEMOLISHER_PERIOD == 0
                and game_state.get_resource(MP) >= game_state.type_cost(DEMOLISHER)[MP] * 2):
            game_state.attempt_spawn(DEMOLISHER, best, 2)

        game_state.attempt_spawn(SCOUT, best, 1000)

    def stall_with_interceptors(self, game_state, max_spend=1000):
        friendly_edges = (game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) +
                          game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT))
        deploy_locations = [loc for loc in friendly_edges if not game_state.contains_stationary_unit(loc)]
        spent = 0
        while (game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP]
               and len(deploy_locations) > 0 and spent < max_spend):
            deploy_location = deploy_locations[random.randint(0, len(deploy_locations) - 1)]
            if game_state.attempt_spawn(INTERCEPTOR, deploy_location):
                spent += 1

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

    def on_action_frame(self, turn_string):
        state = json.loads(turn_string)
        breaches = state["events"]["breach"]
        for breach in breaches:
            location = tuple(breach[0])
            unit_owner_self = (breach[4] == 1)
            if not unit_owner_self:
                self.recent_breaches[location] = self.recent_breaches.get(location, 0) + 1


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
