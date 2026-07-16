import gamelib
import random
from sys import maxsize
import json

"""
OPPONENT ARCHETYPE (Milestone 2 endgame-policy investigation tool, NOT a submission
candidate, not even meant to be "good" offensively): "turtle_survivor".

Purely a test fixture: maximal static defense (double-layered walls across the
entire front, a dense turret line, upgrades everything it can afford every turn),
and ZERO offense, ever. Exists only to try to survive as long as possible /
force matches to run long (toward the Verified 100-turn hard cap, GAME_SPEC.md
4.1) so we can observe how our champion behaves in the late game -- this is our
best available substitute for "constructing the relevant board states directly"
per the Milestone 2 brief, since the engine doesn't expose a way to set arbitrary
health/turn state directly; forcing a long, low-tempo game via a very hard-to-crack
opponent is the closest local approximation.
"""


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring TURTLE_SURVIVOR opponent...')
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

        self.wall_front = [[x, 13] for x in range(0, 28) if self._in_bounds(x, 13)]
        self.wall_second = [[x, 12] for x in range(1, 27) if self._in_bounds(x, 12)]
        self.turret_line = [[x, 11] for x in range(2, 26, 2) if self._in_bounds(x, 11)]

    def _in_bounds(self, x, y):
        # Diamond board: rough bound check mirroring GameMap.in_arena_bounds
        # (docs/GAME_SPEC.md section 1); attempt_spawn silently no-ops on invalid
        # cells anyway, this is just to avoid wasting calls.
        half = 14
        if y >= half:
            return False
        return (half - 1 - y) <= x <= (half + y)

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('TURTLE_SURVIVOR turn {}'.format(game_state.turn_number))
        game_state.suppress_warnings(True)

        game_state.attempt_spawn(WALL, self.wall_front)
        game_state.attempt_spawn(TURRET, self.turret_line)
        game_state.attempt_spawn(WALL, self.wall_second)
        game_state.attempt_upgrade(self.turret_line)
        game_state.attempt_upgrade(self.wall_front)
        game_state.attempt_upgrade(self.wall_second)

        # No offense, ever -- MP is simply left to decay (Verified 25%/turn,
        # GAME_SPEC.md 3). This opponent's only goal is surviving, not winning.

        game_state.submit_turn()


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
