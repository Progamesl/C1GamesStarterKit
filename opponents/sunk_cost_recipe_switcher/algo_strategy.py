import gamelib
import random
from sys import maxsize
import json
from collections import defaultdict

"""
OPPONENT ARCHETYPE (Milestone 2, for benchmarking, not a submission candidate):
"sunk_cost_recipe_switcher".

Implements prior-art hypothesis #3 (docs/STRATEGIC_PRIOR_ART_REPORT.md 3.8/5.3):
track the REALIZED value (did our unit(s) actually breach the enemy's back edge,
i.e. deal player-health damage) of the last few uses of each of 3 fixed attack
"recipes" (LEFT scout swarm, RIGHT scout swarm, MIDDLE demolisher push), and if the
currently-active recipe's rolling score goes non-positive for 2 consecutive uses,
switch to the next recipe in rotation instead of repeating a failing pattern
indefinitely. This is a genuinely different attack surface than our other
opponents: it is not about *where* to strike this turn (that's the existing
least-damage-path heuristic used everywhere else) but about *whether to keep using
an entire attack pattern* based on multi-turn realized outcomes -- directly models
the specific documented failure mode from prior-art source #6 (a Top-8 team lost a
live quarterfinal by repeating a static attack recipe against an opponent that had
adapted), but from the attacking side, trying to avoid making that same mistake.
"""

RECIPE_PERIOD = 3  # try a recipe once every this-many turns
EVAL_WINDOW = 2    # turns after firing a recipe during which we watch for a breach


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring SUNK_COST_RECIPE_SWITCHER opponent...')
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
        self.recipes = ["LEFT", "RIGHT", "MIDDLE_DEMO"]
        self.active_idx = 0
        self.recipe_score = defaultdict(float)
        self.consecutive_failures = defaultdict(int)
        # pending evaluations: list of (turn_fired, recipe_name)
        self.pending_eval = []
        self.breached_this_turn = False

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        turn = game_state.turn_number
        gamelib.debug_write('SUNK_COST_RECIPE_SWITCHER turn {} active_recipe={} scores={}'.format(
            turn, self.recipes[self.active_idx], dict(self.recipe_score)))
        game_state.suppress_warnings(True)

        game_state.attempt_spawn(TURRET, self.min_defense)

        self._evaluate_pending(turn)

        if turn >= 2 and turn % RECIPE_PERIOD == 0:
            self._fire_recipe(game_state, turn)

        game_state.submit_turn()

    def _evaluate_pending(self, turn):
        still_pending = []
        for fired_turn, recipe in self.pending_eval:
            if turn - fired_turn > EVAL_WINDOW:
                # Window closed with no observed breach credit -> treat as a failed use.
                self.recipe_score[recipe] -= 1.0
                self.consecutive_failures[recipe] += 1
                self._maybe_switch(recipe)
            else:
                still_pending.append((fired_turn, recipe))
        self.pending_eval = still_pending

    def _maybe_switch(self, recipe):
        if self.recipes[self.active_idx] == recipe and self.consecutive_failures[recipe] >= 2:
            self.active_idx = (self.active_idx + 1) % len(self.recipes)
            self.consecutive_failures[recipe] = 0
            gamelib.debug_write('SUNK_COST_RECIPE_SWITCHER: switching away from {} -> {}'.format(
                recipe, self.recipes[self.active_idx]))

    def _fire_recipe(self, game_state, turn):
        recipe = self.recipes[self.active_idx]
        if recipe == "LEFT":
            game_state.attempt_spawn(SCOUT, [6, 7], 1000)
        elif recipe == "RIGHT":
            game_state.attempt_spawn(SCOUT, [21, 7], 1000)
        elif recipe == "MIDDLE_DEMO":
            if game_state.get_resource(MP) >= game_state.type_cost(DEMOLISHER)[MP] * 2:
                game_state.attempt_spawn(DEMOLISHER, [13, 0], 2)
        self.pending_eval.append((turn, recipe))

    def on_action_frame(self, turn_string):
        state = json.loads(turn_string)
        breaches = state["events"]["breach"]
        for breach in breaches:
            unit_owner_self = (breach[4] == 1)
            if unit_owner_self and self.pending_eval:
                # Credit the currently-oldest pending recipe with a successful breach.
                fired_turn, recipe = self.pending_eval[0]
                self.recipe_score[recipe] += 2.0
                self.consecutive_failures[recipe] = 0


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
