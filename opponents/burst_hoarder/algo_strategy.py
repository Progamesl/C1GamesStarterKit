import gamelib
import random
from sys import maxsize
import json

"""
OPPONENT ARCHETYPE (for benchmarking, not a submission candidate): "burst_hoarder".

Per prior-art section 3 (docs/STRATEGIC_PRIOR_ART_REPORT.md, "delayed
resource-hoarding into a single burst" -- documented as a mechanism that beat a
strong team, source #6): build modest defense early, then deliberately do NOT spend
any MP for HOARD_TURNS turns (subject to the Verified 25%/turn decay and 150 cap in
docs/GAME_SPEC.md, so hoarding has diminishing returns past the cap -- this opponent
hoards up to roughly the cap, not indefinitely), then unloads one large combined
SCOUT+DEMOLISHER wave. Tests whether our baselines' reactive/opportunistic defenses
can absorb a single large spike rather than a steady trickle.
"""

HOARD_TURNS = 8


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring BURST_HOARDER opponent...')
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

        self.base_turrets = [[1, 12], [26, 12], [13, 11], [14, 11]]
        self.base_walls = [[x, 13] for x in [0, 1, 2, 25, 26, 27]]
        self.has_burst = False

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        turn = game_state.turn_number
        gamelib.debug_write('BURST_HOARDER turn {}'.format(turn))
        game_state.suppress_warnings(True)

        game_state.attempt_spawn(TURRET, self.base_turrets)
        game_state.attempt_spawn(WALL, self.base_walls)
        game_state.attempt_upgrade(self.base_turrets)

        if turn < HOARD_TURNS:
            # Hoard: spend nothing offensive. MP decays 25%/turn unspent and caps
            # at 150 (Verified, docs/GAME_SPEC.md 3) so this is a bounded, not
            # unlimited, stockpile.
            pass
        else:
            self.burst_attack(game_state)

        game_state.submit_turn()

    def burst_attack(self, game_state):
        mp = game_state.get_resource(MP)
        options = [[13, 0], [14, 0]]
        best = self.least_damage_spawn_location(game_state, options)
        demolisher_cost = game_state.type_cost(DEMOLISHER)[MP]
        n_demolishers = int(mp // demolisher_cost // 2)  # spend up to half the bank on demolishers
        if n_demolishers > 0:
            game_state.attempt_spawn(DEMOLISHER, best, n_demolishers)
        game_state.attempt_spawn(SCOUT, best, 1000)

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


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
