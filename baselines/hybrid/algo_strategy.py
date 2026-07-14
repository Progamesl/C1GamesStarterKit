import gamelib
import random
import math
import warnings
from sys import maxsize
import json
from collections import defaultdict

"""
BASELINE: "hybrid" -- solid core defense + periodic banked-MP bursts.

Design intent (see docs/GAME_SPEC.md for cited stats, docs/STRATEGIC_PRIOR_ART_REPORT.md
for the prior-art hypotheses this draws on):

  - Establishes a moderate (cheaper/faster than the "defense" baseline's full-width
    line) corner-priority core, then switches into a bank-and-burst attack pattern
    once that core is judged "good enough."
  - Reactive defense uses the same neighborhood+decay approach as the "defense"
    baseline (prior-art hypothesis #1), capped in per-turn SP spend.
  - Offense: rather than spending MP every turn (rush archetype) or only
    opportunistically (defense archetype), *banks* MP for BURST_PERIOD turns and then
    commits a combined-arms strike (DEMOLISHER, the only mobile unit that reliably
    damages structures at range, escorted by SCOUTs) at whichever side currently has
    fewer detected enemy stationary units -- a simplified version of the "escorted
    combined-arms offense" archetype (prior-art hypothesis #5), deliberately not
    relying on the SUPPORT shield mechanic since its actual formula is an open gap.
  - Simple endgame awareness: once turn_number > 80 (approaching the Verified
    100-turn cap, docs/GAME_SPEC.md 4.3) AND we are currently ahead on health,
    switches to a pure health-preservation mode (no more offense, max defense) since
    the tie-break at turn 100 rewards higher remaining health first -- a simplified,
    directly-testable version of prior-art hypothesis #4. This is intentionally a
    crude threshold-based policy for Milestone 1; Milestone 2 plans a more rigorous
    version (docs/GAME_SPEC.md's win-condition section + a dedicated endgame policy).
"""

BURST_PERIOD = 4
DEFENSE_READY_TURN = 6
ENDGAME_TURN_THRESHOLD = 80


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring HYBRID baseline...')
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

        self.breach_history = defaultdict(float)
        self.max_reactive_spend_per_turn = 6
        self.core_turret_anchors = [[0, 13], [27, 13], [6, 11], [21, 11], [13, 10], [14, 10]]
        self.core_wall_front = [[1, 12], [2, 12], [25, 12], [26, 12]]

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        turn = game_state.turn_number
        gamelib.debug_write('HYBRID turn {}'.format(turn))
        game_state.suppress_warnings(True)

        self._decay_breach_history()
        self.build_core_defense(game_state)
        self.reactive_defense(game_state)

        ahead_on_health = game_state.my_health >= game_state.enemy_health
        endgame_preserve = (turn > ENDGAME_TURN_THRESHOLD) and ahead_on_health

        if endgame_preserve:
            gamelib.debug_write('HYBRID: endgame health-preservation mode (turn {}, my_hp={}, enemy_hp={})'.format(
                turn, game_state.my_health, game_state.enemy_health))
            self.upgrade_core(game_state)
            self.stall_with_interceptors(game_state, max_spend=3)
        elif turn < DEFENSE_READY_TURN:
            self.stall_with_interceptors(game_state, max_spend=2)
        else:
            self.upgrade_core(game_state)
            self.banked_burst_attack(game_state)

        game_state.submit_turn()

    def _decay_breach_history(self):
        for loc in list(self.breach_history.keys()):
            self.breach_history[loc] *= 0.6
            if self.breach_history[loc] < 0.05:
                del self.breach_history[loc]

    def build_core_defense(self, game_state):
        game_state.attempt_spawn(TURRET, self.core_turret_anchors)
        game_state.attempt_spawn(WALL, self.core_wall_front)

    def upgrade_core(self, game_state):
        game_state.attempt_upgrade(self.core_turret_anchors)

    def reactive_defense(self, game_state):
        if not self.breach_history:
            return
        ranked = sorted(self.breach_history.items(), key=lambda kv: -kv[1])
        spent = 0
        for (bx, by), weight in ranked:
            if spent >= self.max_reactive_spend_per_turn:
                break
            neighborhood = [[bx, by + 1], [bx - 1, by + 1], [bx + 1, by + 1]]
            for loc in neighborhood:
                if spent >= self.max_reactive_spend_per_turn:
                    break
                if loc[1] >= game_state.HALF_ARENA:
                    continue
                cost = game_state.type_cost(TURRET)[SP]
                if game_state.attempt_spawn(TURRET, loc):
                    spent += cost

    def banked_burst_attack(self, game_state):
        """Bank MP for BURST_PERIOD turns, then commit a demolisher+scout strike."""
        turn = game_state.turn_number
        is_burst_turn = (turn % BURST_PERIOD == 0)
        mp = game_state.get_resource(MP)

        if not is_burst_turn:
            # Banking turn: spend nothing offensive, just let MP accumulate
            # (subject to maxBits cap per docs/GAME_SPEC.md 3).
            return

        left_defense = self.detect_enemy_unit(game_state, valid_x=list(range(0, 14)))
        right_defense = self.detect_enemy_unit(game_state, valid_x=list(range(14, 28)))
        options = [[3, 10], [24, 10], [13, 0], [14, 0]]
        best = self.least_damage_spawn_location(game_state, options)

        demolisher_cost = game_state.type_cost(DEMOLISHER)[MP]
        if mp >= demolisher_cost * 2:
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
                self.breach_history[location] += 1.0


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
