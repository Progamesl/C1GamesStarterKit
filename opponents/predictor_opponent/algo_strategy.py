import gamelib
import random
from sys import maxsize
import json
from collections import defaultdict

"""
HELD-OUT OPPONENT ARCHETYPE (Milestone 5 held-out corpus check): "predictor_opponent".

Implements prior-art hypothesis/archetype #3.7 from
docs/STRATEGIC_PRIOR_ART_REPORT.md ("Opponent-move prediction"), which had NOT
been implemented anywhere in `opponents/` before this milestone (checked
against the existing corpus first) -- explicitly the rarest mechanism in that
report's own ranked list (deferred to priority #9), and deliberately picked
here specifically because it is genuinely different from every other
opponent already in this repo: since turns are simultaneous, a predictor
tries to react to what the opponent is ABOUT to do this turn (before their
move is revealed), not to what they already did (that's every reactive
opponent already in the corpus, e.g. `opponents/adaptive_reactive`).

Built "blind" per the held-out-corpus instruction: the predictor's logic
(simple period detection over the last several turns of observed enemy
mobile-unit spawns) is derived purely from the general archetype description
above, not from reading or reverse-engineering any specific current
baseline's actual turn-parity/caching logic.

Mechanism:
  1. Track, via `on_action_frame`'s `spawn` events, every turn's observed
     enemy mobile-unit spawns as (side, unit_type) pairs, keyed by turn
     number, going back PREDICTOR_HISTORY turns.
  2. Before committing this turn's own move, check whether the same
     (side, unit_type) pair recurred at a consistent turn-offset in recent
     history (e.g. every 2 turns, every 3 turns) -- a simple, generic period
     detector, not hardcoded to any specific period.
  3. If a period is detected with enough confidence (>= MIN_OBSERVATIONS
     matching instances), PRE-EMPTIVELY reinforce the predicted side this
     turn, before the enemy's actual move for this turn is known -- the
     genuinely distinguishing feature of this mechanism versus reactive
     defense, which only reinforces *after* seeing where damage landed.
  4. Own baseline offense/defense is otherwise modest and generic, since the
     interesting behavior here is entirely in the predictive reinforcement,
     not in a strong baseline attack.
"""

PREDICTOR_HISTORY = 10
MIN_OBSERVATIONS = 2
CANDIDATE_PERIODS = (2, 3, 4)


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring PREDICTOR_OPPONENT opponent...')
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

        self.type_index_to_shorthand = {
            i: config["unitInformation"][i]["shorthand"] for i in range(6)
        }

        self.default_turrets = [[1, 12], [26, 12], [4, 12], [23, 12], [10, 10], [17, 10]]
        self.default_walls = [[x, 13] for x in [0, 1, 2, 25, 26, 27]]

        # turn_number -> set of (side, unit_type) observed that turn
        self.spawn_history = {}
        self.pending_frame_spawns = []
        self.predictions_made = 0
        self.predictions_confirmed = 0

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        turn = game_state.turn_number
        game_state.suppress_warnings(True)

        self._consume_last_turn_spawns(turn)
        self._score_previous_prediction(turn)

        game_state.attempt_spawn(TURRET, self.default_turrets)
        game_state.attempt_spawn(WALL, self.default_walls)
        game_state.attempt_upgrade(self.default_turrets)

        prediction = self._predict_this_turn(turn)
        if prediction is not None:
            self.predictions_made += 1
            self.last_prediction = (turn, prediction)
            self._preempt(game_state, prediction)
        else:
            self.last_prediction = None

        if turn >= 2 and turn % 4 == 0 and game_state.get_resource(MP) >= 5:
            game_state.attempt_spawn(SCOUT, [13, 0], 3)

        gamelib.debug_write('PREDICTOR_OPPONENT turn {} prediction={} made={} confirmed={}'.format(
            turn, prediction, self.predictions_made, self.predictions_confirmed))

        game_state.submit_turn()

    def _consume_last_turn_spawns(self, current_turn):
        prev_turn = current_turn - 1
        if self.pending_frame_spawns:
            self.spawn_history[prev_turn] = set(self.pending_frame_spawns)
            self.pending_frame_spawns = []
        # Trim old history.
        for t in list(self.spawn_history.keys()):
            if current_turn - t > PREDICTOR_HISTORY:
                del self.spawn_history[t]

    def _score_previous_prediction(self, current_turn):
        if getattr(self, 'last_prediction', None) is None:
            return
        pred_turn, predicted_side = self.last_prediction
        actual = self.spawn_history.get(pred_turn, set())
        if any(side == predicted_side for side, _utype in actual):
            self.predictions_confirmed += 1

    def _predict_this_turn(self, current_turn):
        """Generic period detector: for each candidate period P and each
        (side, unit_type) pair seen recently, check whether it recurred at
        turns current_turn-P, current_turn-2P, ... with enough hits to be
        confident it'll happen again this turn."""
        best_side = None
        best_hits = 0
        for period in CANDIDATE_PERIODS:
            counts = defaultdict(int)
            k = 1
            while True:
                t = current_turn - period * k
                if t not in self.spawn_history or k > 4:
                    break
                for pair in self.spawn_history[t]:
                    counts[pair] += 1
                k += 1
            for (side, _utype), hits in counts.items():
                if hits >= MIN_OBSERVATIONS and hits > best_hits:
                    best_hits = hits
                    best_side = side
        return best_side

    def _preempt(self, game_state, predicted_side):
        """Pre-emptively reinforce the predicted side THIS turn, before the
        enemy's actual move for this turn is known -- the whole point of a
        predictor rather than a reactive defense."""
        reinforce_x = [2, 3, 5, 6] if predicted_side == 'left' else [21, 22, 24, 25]
        game_state.attempt_spawn(TURRET, [[x, 11] for x in reinforce_x])
        friendly_edges = (game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) +
                          game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT))
        candidate_edges = [loc for loc in friendly_edges
                           if (loc[0] < 14) == (predicted_side == 'left')
                           and not game_state.contains_stationary_unit(loc)]
        if candidate_edges and game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP]:
            deploy_location = candidate_edges[random.randint(0, len(candidate_edges) - 1)]
            game_state.attempt_spawn(INTERCEPTOR, deploy_location, 1)

    def on_action_frame(self, turn_string):
        if '"spawn":[]' in turn_string:
            return
        state = json.loads(turn_string)
        spawns = state["events"]["spawn"]
        for sp in spawns:
            location, type_index, _unit_id, player_index = sp[0], sp[1], sp[2], sp[3]
            # Raw action-frame events are 1-indexed with 1=self, 2=opponent
            # (confirmed in python-algo/algo_strategy.py's own on_action_frame
            # handling) -- different from GameUnit.player_index's 0/1
            # convention used elsewhere. We want the opponent's spawns.
            if player_index != 2:
                continue
            unit_type = self.type_index_to_shorthand.get(type_index)
            if unit_type not in (SCOUT, DEMOLISHER, INTERCEPTOR):
                continue
            side = 'left' if location[0] < 14 else 'right'
            self.pending_frame_spawns.append((side, unit_type))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
