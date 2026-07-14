import gamelib
import random
from sys import maxsize
import json

"""
ADVERSARIAL COUNTERSEARCH OPPONENT (Milestone 3, deliberately built to exploit a
specific, newly-identified weakness in `baselines/defense_v4_tiebreak` -- NOT a
"realistic" strategic archetype, same spirit as `opponents/turtle_survivor`).

Motivating weakness, found by re-reading defense_v4_tiebreak's own `on_turn` mode
dispatch after the Milestone 3 tie-break fix was written: the OLD endgame-preserve
mode (triggered whenever `my_health >= enemy_health` near the turn cap, in
defense_v3_lowcompute) always called `stall_with_interceptors` -- cheap, but still
SOME defensive screening against a late incoming attack. The NEW `all_in_tied_strike`
mode (triggered only on an EXACT tie near the cap, in defense_v4_tiebreak) spends
100% of available MP on offense and deploys ZERO interceptors -- it assumes, because
every opponent we've tested so far that reaches an exact 40-40 tie is a pure-turtle
opponent that will never attack, that there is no incoming threat to screen against.
That assumption is exactly what this opponent is built to violate.

Tactic: play an IDENTICAL maximal turtle defense to `opponents/turtle_survivor` for
the entire early/mid game (same wall/turret layout, same zero offense) -- specifically
to bait a tied-health, near-cap board state and put the target into
`all_in_tied_strike` mode, exactly like turtle_survivor does. Then, starting at
LATE_SURGE_TURN, defect: stop banking MP passively and instead dump the entire banked
stockpile into a single maximal, concentrated scout+demolisher wave aimed at the
target's cheapest lane, for the remaining turns -- while the target (per the theory
above) is spending its own turns purely on offense against us with no defensive
interceptors up, and is also busy taking damage from *and* trying to overcome our own
still-fully-upgraded static defense.

This is a legal, single-file `algo_strategy.py` opponent (same interface every other
entry in `opponents/` uses); it does not modify or inspect the target's code.
"""

LATE_SURGE_TURN = 90


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring LATEGAME_DEFECTOR opponent...')
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

        # Identical to opponents/turtle_survivor's defensive layout -- the whole
        # point is to look exactly like a pure turtle until the defection turn.
        self.wall_front = [[x, 13] for x in range(0, 28) if self._in_bounds(x, 13)]
        self.wall_second = [[x, 12] for x in range(1, 27) if self._in_bounds(x, 12)]
        self.turret_line = [[x, 11] for x in range(2, 26, 2) if self._in_bounds(x, 11)]

    def _in_bounds(self, x, y):
        half = 14
        if y >= half:
            return False
        return (half - 1 - y) <= x <= (half + y)

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        turn = game_state.turn_number
        gamelib.debug_write('LATEGAME_DEFECTOR turn {} defecting={}'.format(
            turn, turn >= LATE_SURGE_TURN))
        game_state.suppress_warnings(True)

        # Keep our own defense fully maintained regardless of mode -- defecting
        # to offense doesn't mean giving up our own board.
        game_state.attempt_spawn(WALL, self.wall_front)
        game_state.attempt_spawn(TURRET, self.turret_line)
        game_state.attempt_spawn(WALL, self.wall_second)
        game_state.attempt_upgrade(self.turret_line)
        game_state.attempt_upgrade(self.wall_front)
        game_state.attempt_upgrade(self.wall_second)

        if turn >= LATE_SURGE_TURN:
            self._all_in_strike(game_state)

        game_state.submit_turn()

    def _all_in_strike(self, game_state):
        best = self._least_damage_spawn_location(game_state, [[13, 0], [3, 10], [24, 10]])
        mp = game_state.get_resource(MP)
        demolisher_cost = game_state.type_cost(DEMOLISHER)[MP]
        num_demolishers = int((mp * 0.4) // demolisher_cost)
        if num_demolishers > 0:
            game_state.attempt_spawn(DEMOLISHER, best, num_demolishers)
        game_state.attempt_spawn(SCOUT, best, 1000)

    def _least_damage_spawn_location(self, game_state, location_options):
        turret_damage = gamelib.GameUnit(TURRET, game_state.config).damage_i
        damages = []
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            if path:
                for path_location in path:
                    damage += len(game_state.get_attackers(path_location, 0)) * turret_damage
            else:
                damage = float('inf')
            damages.append(damage)
        return location_options[damages.index(min(damages))]


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
