import gamelib
import random
import math
import warnings
from sys import maxsize
import json
from collections import defaultdict

"""
BASELINE: "defense" -- conservative, balanced defense.

Design intent (see docs/GAME_SPEC.md for cited stats, docs/STRATEGIC_PRIOR_ART_REPORT.md
section 5 for the prior-art hypotheses this draws on):

  - Full-width TURRET/WALL core (not just corners), with extra corner weight, since
    corners are a documented common attack vector (prior-art #6/#19).
  - Reactive defense reinforces a small NEIGHBORHOOD around recent breaches, weighted
    by recency+frequency, with a per-turn SP spend cap -- a strict improvement over the
    starter bot's single-cell reactive defense (prior-art hypothesis #1), and resistant
    to being baited into overspending on a decoy lane.
  - Upgrades existing TURRETs (big jump: 90->still 90 HP but dmg 5->15, range 2.5->3.5,
    for +3.0 SP) before spending on new width, once the core line exists.
  - Offense is opportunistic only: spend genuinely spare MP on SCOUT probes, never at
    the expense of defense. This archetype is deliberately not trying to race the
    turn-100 clock; it is trying to have the best health differential at turn 100 if
    the game goes long (prior-art hypothesis #4), and to simply not lose to a rush.
  - Kept computationally cheap (no deep simulation) to stay well under the Verified
    5000ms soft / 35000ms hard per-turn time budget (docs/GAME_SPEC.md 4.2), which is
    also free insurance for the HP-tied, lower-compute-time tie-break (4.3).
"""


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring DEFENSE baseline...')
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

        # breach_history[(x,y)] = number of times we've been hit here, decayed each turn
        self.breach_history = defaultdict(float)
        self.max_reactive_spend_per_turn = 6  # SP cap on reactive rebuilding per turn

        # Full-width core defense line locations (front row) and the corner-weighted
        # turret anchors placed one row back, out of enemy demolisher's direct line.
        self.core_turret_anchors = [
            [1, 12], [26, 12],      # corners: highest priority
            [4, 12], [23, 12],
            [7, 11], [20, 11],
            [10, 10], [17, 10],
            [13, 10], [14, 10],
        ]
        self.core_wall_front = [[x, 13] for x in [0, 1, 2, 3, 4, 5, 22, 23, 24, 25, 26, 27]]

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('DEFENSE turn {}'.format(game_state.turn_number))
        game_state.suppress_warnings(True)

        self._decay_breach_history()
        self.build_core_defense(game_state)
        self.reactive_defense(game_state)
        self.upgrade_core(game_state)
        self.opportunistic_offense(game_state)

        game_state.submit_turn()

    def _decay_breach_history(self):
        for loc in list(self.breach_history.keys()):
            self.breach_history[loc] *= 0.6
            if self.breach_history[loc] < 0.05:
                del self.breach_history[loc]

    def build_core_defense(self, game_state):
        game_state.attempt_spawn(TURRET, self.core_turret_anchors)
        game_state.attempt_spawn(WALL, self.core_wall_front)
        # Cheap SUPPORT behind the middle to hedge our bets on the (partially
        # unverified, see GAME_SPEC.md 2.1 gap note) shield mechanic, but only once
        # the SP core exists -- never before turret/wall coverage.
        if game_state.get_resource(SP) > 10:
            game_state.attempt_spawn(SUPPORT, [[13, 3], [14, 3]])

    def upgrade_core(self, game_state):
        # Upgrading a TURRET is a big power jump (dmg 5->15, range 2.5->3.5) for a
        # marginal +3.0 SP over its base cost -- prioritize this over raw width once
        # the core anchors are down.
        game_state.attempt_upgrade(self.core_turret_anchors)
        game_state.attempt_upgrade(self.core_wall_front)

    def reactive_defense(self, game_state):
        """Reinforce a neighborhood around recently-breached cells, weighted by
        recency+frequency, capped in total SP spend so a repeated-feint opponent
        can't bait us into overspending on a decoy lane (prior-art hypothesis #1)."""
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

    def opportunistic_offense(self, game_state):
        """Only spend MP we can genuinely spare; never touch SP set aside for
        defense. Simple least-damage scout probe, reusing the same path-risk
        heuristic idea as the starter bot but gated on turn parity + a higher MP
        floor so this archetype doesn't behave like a rush."""
        if game_state.turn_number < 6:
            self.stall_with_interceptors(game_state)
            return

        mp = game_state.get_resource(MP)
        if mp >= 9 and game_state.turn_number % 2 == 0:
            options = [[13, 0], [14, 0], [3, 10], [24, 10]]
            best = self.least_damage_spawn_location(game_state, options)
            game_state.attempt_spawn(SCOUT, best, 1000)

    def stall_with_interceptors(self, game_state):
        friendly_edges = (game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) +
                          game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT))
        deploy_locations = [loc for loc in friendly_edges if not game_state.contains_stationary_unit(loc)]
        spent = 0
        while (game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP]
               and len(deploy_locations) > 0 and spent < 2):
            deploy_location = deploy_locations[random.randint(0, len(deploy_locations) - 1)]
            if game_state.attempt_spawn(INTERCEPTOR, deploy_location):
                spent += 1

    def least_damage_spawn_location(self, game_state, location_options):
        damages = []
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            if path:
                for path_location in path:
                    damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            else:
                damage = float('inf')
            damages.append(damage)
        return location_options[damages.index(min(damages))]

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
