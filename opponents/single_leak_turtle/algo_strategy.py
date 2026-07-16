import gamelib
import random
from sys import maxsize
import json

"""
ADVERSARIAL COUNTERSEARCH OPPONENT #2 (Milestone 3) -- targets a different,
more specific weakness than `opponents/lategame_defector`: `AlgoStrategy.ever_breached`
in `baselines/defense_v4_tiebreak` (and its `defense_v3_lowcompute` ancestor) is a
PERMANENT, one-way flag -- once set True by a single breach event, it can never go
back to False for the rest of the game, and its only consumer,
`_stalemate_breaker`, unconditionally refuses to fire at all once it's True:

    if self.ever_breached or turn < STALEMATE_CHECK_TURN or turn % STALEMATE_STRIKE_PERIOD != 0:
        return

The (reasonable-sounding, but untested until now) assumption baked into that
one-shot flag is "if the opponent has ever landed a real hit on us, they must be a
genuinely offense-capable opponent, not a passive turtle, so the special
turtle-countermeasure isn't needed." This opponent exists to test whether a single,
CHEAP, otherwise-irrelevant probe attack early in the game -- from an opponent that
is, in every other respect, an exact `opponents/turtle_survivor` clone -- is enough
to permanently disable that one specific countermeasure for the rest of the match,
even though the opponent goes right back to pure zero-offense turtle play
immediately afterward.

Tactic: send exactly ONE cheap SCOUT at turn 1 (before the target's own
`opportunistic_offense` even starts, per its own `turn < 6` gate), then behave
IDENTICALLY to `opponents/turtle_survivor` for the rest of the game (same layout,
zero further offense). Note this does NOT touch the target's new
`all_in_tied_strike` endgame logic at all -- that mode has no `ever_breached` gate --
so this specifically isolates whether the STALEMATE_BREAKER (turns 40-80) mattered
for the final result, separate from the Milestone 3 endgame fix.
"""


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring SINGLE_LEAK_TURTLE opponent...')
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

        # Identical to opponents/turtle_survivor.
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
        gamelib.debug_write('SINGLE_LEAK_TURTLE turn {}'.format(turn))
        game_state.suppress_warnings(True)

        game_state.attempt_spawn(WALL, self.wall_front)
        game_state.attempt_spawn(TURRET, self.turret_line)
        game_state.attempt_spawn(WALL, self.wall_second)
        game_state.attempt_upgrade(self.turret_line)
        game_state.attempt_upgrade(self.wall_front)
        game_state.attempt_upgrade(self.wall_second)

        # The ONE probe: a single cheap scout at turn 1, then never again --
        # everything else about this opponent is a pure zero-offense turtle.
        if turn == 1:
            game_state.attempt_spawn(SCOUT, [13, 0], 1)

        game_state.submit_turn()


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
