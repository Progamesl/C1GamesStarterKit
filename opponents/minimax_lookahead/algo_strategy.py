import gamelib
import random
import time
from sys import maxsize
import json

"""
HELD-OUT OPPONENT ARCHETYPE (Milestone 5 held-out corpus check): "minimax_lookahead".

Implements prior-art hypothesis/archetype #3.2 from
docs/STRATEGIC_PRIOR_ART_REPORT.md ("Turn-level simulation / minimax lookahead
before committing a turn"), which had NOT been implemented anywhere in
`opponents/` before this milestone (every existing opponent/baseline in this
repo picks a single fixed recipe, or at most the cheapest LANE for one
already-decided unit type -- none of them score several qualitatively
different whole-turn RECIPES against each other before choosing). Per the
report: three independently-built 2019 simulators (all top-12-globally
finishers) scored candidate placements/attacks with a value function and
committed the max-scoring option, bounded by the engine's real per-turn
compute budget.

Built "blind" per the held-out-corpus instruction: this opponent's recipe
set, scoring function, and time-budget discipline are derived purely from
the general archetype description above (and the Verified per-turn compute
budget in docs/GAME_SPEC.md), not from reading or reverse-engineering any
specific current baseline's code.

Mechanism, every turn:
  1. Build a small set of candidate whole-turn RECIPES (not just lane
     choices): "defend only", "scout rush left", "scout rush right",
     "scout rush center", "demolisher push center".
  2. Score each with a simple utility combining (a) projected MP-efficiency
     of the attack (crude: MP spent, discounted by projected in-flight
     turret damage along the path, per-unit) against (b) a defense-value
     term (structural SP left unspent is worth something too, to avoid
     always attacking even when defense is thin) -- a genuine, if simple,
     multi-candidate evaluation, not a single fixed heuristic.
  3. Commit only the single highest-scoring recipe for the turn.
  4. Explicitly measure and log actual wall-clock decision time every turn
     (per the report's own "measure it, don't just trust it" lesson,
     §3.2/3.9) against a self-imposed target well under the Verified 5000ms
     soft per-turn budget (docs/GAME_SPEC.md 4.2) -- this doubles as an
     incidental robustness check on whether a genuinely more compute-heavy
     opponent (multiple path evaluations per turn, not just one) stays
     comfortably inside the compute-time tie-break's own stated "keep this
     fast" lesson (§3.10 hypothesis 2).
"""

TIME_BUDGET_TARGET_MS = 400  # self-imposed target, well under the Verified 5000ms soft limit


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring MINIMAX_LOOKAHEAD opponent...')
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

        self.core_turrets = [[1, 12], [26, 12], [4, 12], [23, 12], [10, 10], [17, 10]]
        self.core_walls = [[x, 13] for x in [0, 1, 2, 25, 26, 27]]
        self.turns_over_budget = 0

    def on_turn(self, turn_state):
        turn_start = time.time()
        game_state = gamelib.GameState(self.config, turn_state)
        turn = game_state.turn_number
        game_state.suppress_warnings(True)

        game_state.attempt_spawn(TURRET, self.core_turrets)
        game_state.attempt_spawn(WALL, self.core_walls)
        game_state.attempt_upgrade(self.core_turrets)

        if turn >= 2:
            self._choose_and_execute_best_recipe(game_state)

        game_state.submit_turn()

        decision_ms = (time.time() - turn_start) * 1000.0
        if decision_ms > TIME_BUDGET_TARGET_MS:
            self.turns_over_budget += 1
        gamelib.debug_write('MINIMAX_LOOKAHEAD turn {} decision_time_ms={:.1f} over_budget_count={}'.format(
            turn, decision_ms, self.turns_over_budget))

    def _choose_and_execute_best_recipe(self, game_state):
        mp = game_state.get_resource(MP)
        sp_unspent_value = game_state.get_resource(SP)  # crude proxy: unspent SP is "banked" defensive value

        candidates = self._build_candidates(game_state, mp)
        scored = [(self._score_recipe(game_state, c, sp_unspent_value), c) for c in candidates]
        scored.sort(key=lambda sc: sc[0], reverse=True)
        best_score, best_recipe = scored[0]
        gamelib.debug_write('MINIMAX_LOOKAHEAD candidates={} -> chose {} (score={:.2f})'.format(
            [(c['name'], round(s, 2)) for s, c in scored], best_recipe['name'], best_score))
        self._execute_recipe(game_state, best_recipe)

    def _build_candidates(self, game_state, mp):
        candidates = [{'name': 'defend_only', 'unit': None, 'location': None, 'count': 0}]
        if mp >= 3:
            for name, loc in (('scout_left', [7, 6]), ('scout_right', [20, 6]), ('scout_center', [13, 0])):
                candidates.append({'name': name, 'unit': SCOUT, 'location': loc, 'count': 1000})
        demolisher_cost = game_state.type_cost(DEMOLISHER)[MP]
        if mp >= demolisher_cost * 2:
            candidates.append({'name': 'demolisher_center', 'unit': DEMOLISHER, 'location': [13, 0], 'count': 2})
        return candidates

    def _score_recipe(self, game_state, recipe, sp_unspent_value):
        if recipe['unit'] is None:
            # Defense-only: value scales with how much SP we still have
            # banked (a proxy for "our structure is in good shape"), capped
            # so a large banked reserve doesn't make this dominate forever
            # regardless of how favorable an attack option looks.
            return 1.0 + 0.1 * min(sp_unspent_value, 20.0)

        location = recipe['location']
        if game_state.contains_stationary_unit(location):
            return -float('inf')
        path = game_state.find_path_to_edge(location)
        if not path:
            return -float('inf')

        turret_damage = gamelib.GameUnit(TURRET, game_state.config).damage_i
        projected_incoming_damage = sum(
            len(game_state.get_attackers(loc, 0)) * turret_damage for loc in path
        )
        unit_health = gamelib.GameUnit(recipe['unit'], game_state.config).max_health
        # Crude survivability-weighted value: MP spent is only "worth it" if
        # the unit is not projected to die several times over before
        # reaching the end of its path. Asymptotic (never hits exactly 0)
        # so relative ordering between heavily-defended lanes still matters,
        # instead of every well-defended option degenerating to an
        # indistinguishable floor.
        survivability = unit_health / (unit_health + projected_incoming_damage)
        if recipe['unit'] == DEMOLISHER:
            mp_committed = min(recipe['count'], 20) * game_state.type_cost(recipe['unit'])[MP]
        else:
            # "count": 1000 means "spend everything available" -- value the
            # recipe by how much MP it would actually commit, not a flat
            # constant, so a bigger available war-chest makes attacking
            # more attractive relative to the capped defend-only score.
            mp_committed = min(game_state.get_resource(MP), 30.0)
        return survivability * mp_committed

    def _execute_recipe(self, game_state, recipe):
        if recipe['unit'] is None:
            return
        game_state.attempt_spawn(recipe['unit'], recipe['location'], recipe['count'])


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
