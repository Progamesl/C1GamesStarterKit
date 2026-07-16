import gamelib
import random
from sys import maxsize
import json
from collections import defaultdict

"""
HELD-OUT OPPONENT ARCHETYPE (Milestone 5 held-out corpus check): "signature_detector".

Implements prior-art hypothesis/archetype #3.5 from
docs/STRATEGIC_PRIOR_ART_REPORT.md ("Signature detection + counter-strategy
switching"), which had NOT been implemented anywhere in `opponents/` before
this milestone (checked against the existing corpus first). Per the report:
one 2019 top-12 team's account describes detecting a recognizable, repeated
opponent pattern (a "ping cannon" -- many cheap mobile units funneled from the
same spot, turn after turn) and switching from a generic defense into a
purpose-built counter-response once the pattern is confident, rather than
reacting only to the damage the pattern already dealt (that's
`opponents/adaptive_reactive`'s mechanism instead -- this is a genuinely
different, earlier-triggering signal: side/type *repetition*, not damage
*location*).

Built "blind" per the held-out-corpus instruction: this opponent's detector
and counter-response are derived purely from the general archetype
description above, not from reading or reverse-engineering any specific
current baseline's code.

Mechanism:
  1. Track, via `on_action_frame`'s `spawn` events, which side (left half
     x<14 / right half x>=14) and which mobile unit type the enemy spawned
     each turn.
  2. If the SAME (side, type) pair repeats for >= SIGNATURE_THRESHOLD
     consecutive turns, declare a detected "signature" and enter counter
     mode.
  3. Counter mode (per the source's own account of what worked): mass-
     reinforce turrets specifically on the detected side (rather than the
     uniform light defense used before detection), AND launch our own
     counter-offense at the OPPOSITE side (the source's stated rationale:
     a channel/cannon's "non-output side" tends to be less defended).
  4. If the signature stops repeating for a few turns, decay back to the
     default light/uniform defense rather than staying locked into the
     counter-response forever (avoids permanently overcommitting to a
     one-time pattern).
"""

SIGNATURE_THRESHOLD = 3
DECAY_TURNS = 4


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring SIGNATURE_DETECTOR opponent...')
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

        # Type index -> shorthand, for decoding on_action_frame "spawn" events
        # ([location, type_index, unit_id, player_index]).
        self.type_index_to_shorthand = {
            i: config["unitInformation"][i]["shorthand"] for i in range(6)
        }

        self.default_turrets = [[1, 12], [26, 12], [4, 12], [23, 12]]
        self.default_walls = [[x, 13] for x in [0, 1, 2, 3, 24, 25, 26, 27]]

        # (side, unit_type) -> consecutive-turn streak count
        self.streaks = defaultdict(int)
        self.last_turn_signature = None  # (side, unit_type) seen last turn, or None
        self.detected_signature = None   # (side, unit_type) currently locked onto
        self.turns_since_signature_seen = 0
        self.this_turn_enemy_spawns = []  # [(side, unit_type), ...] filled by on_action_frame

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        turn = game_state.turn_number
        gamelib.debug_write('SIGNATURE_DETECTOR turn {} detected={}'.format(
            turn, self.detected_signature))
        game_state.suppress_warnings(True)

        self._update_streaks_from_last_turn()

        game_state.attempt_spawn(TURRET, self.default_turrets)
        game_state.attempt_spawn(WALL, self.default_walls)
        game_state.attempt_upgrade(self.default_turrets)

        if self.detected_signature is not None:
            self._counter_response(game_state)
        else:
            # Generic light offense while no signature is locked on: an
            # occasional cheap probe, nothing committed.
            if turn >= 2 and turn % 5 == 0 and game_state.get_resource(MP) >= 5:
                game_state.attempt_spawn(SCOUT, [13, 0], 3)

        game_state.submit_turn()

    def _update_streaks_from_last_turn(self):
        """Consume the (side, unit_type) pairs observed via on_action_frame
        during the turn that just completed, update consecutive-streak
        counters, and lock onto (or decay away from) a detected signature."""
        observed = set(self.this_turn_enemy_spawns)
        self.this_turn_enemy_spawns = []

        if observed:
            for key in observed:
                self.streaks[key] += 1
            for key in list(self.streaks.keys()):
                if key not in observed:
                    self.streaks[key] = 0
            best_key, best_streak = max(self.streaks.items(), key=lambda kv: kv[1], default=(None, 0))
            if best_streak >= SIGNATURE_THRESHOLD:
                if self.detected_signature != best_key:
                    gamelib.debug_write('SIGNATURE_DETECTOR: locking onto signature {}'.format(best_key))
                self.detected_signature = best_key
                self.turns_since_signature_seen = 0
            elif self.detected_signature is not None and self.detected_signature in observed:
                self.turns_since_signature_seen = 0
        if self.detected_signature is not None:
            self.turns_since_signature_seen += 1
            if self.turns_since_signature_seen > DECAY_TURNS:
                gamelib.debug_write('SIGNATURE_DETECTOR: signature {} went quiet, decaying back to default'.format(
                    self.detected_signature))
                self.detected_signature = None
                self.streaks = defaultdict(int)

    def _counter_response(self, game_state):
        side, unit_type = self.detected_signature
        # Mass-reinforce the side the signature is coming FROM.
        reinforce_x = [2, 3, 5, 6] if side == 'left' else [21, 22, 24, 25]
        game_state.attempt_spawn(TURRET, [[x, 11] for x in reinforce_x])
        game_state.attempt_upgrade([[x, 11] for x in reinforce_x])

        # Counter-attack the OPPOSITE side (the signature's "non-output
        # side"), per the archetype's own stated rationale.
        attack_lane = [21, 7] if side == 'left' else [6, 7]
        if game_state.get_resource(MP) >= 5:
            game_state.attempt_spawn(SCOUT, attack_lane, 1000)

    def on_action_frame(self, turn_string):
        if '"spawn":[]' in turn_string:
            return
        state = json.loads(turn_string)
        spawns = state["events"]["spawn"]
        for sp in spawns:
            location, type_index, _unit_id, player_index = sp[0], sp[1], sp[2], sp[3]
            # Raw action-frame events use 1-indexed player numbering where 1
            # is always yourself and 2 is always the opponent (confirmed in
            # python-algo/algo_strategy.py's own on_action_frame handling) --
            # DIFFERENT from GameUnit.player_index's 0=self/1=enemy
            # convention used elsewhere (e.g. game_state.game_map). We want
            # the OPPONENT's spawns here.
            if player_index != 2:
                continue
            unit_type = self.type_index_to_shorthand.get(type_index)
            if unit_type not in (SCOUT, DEMOLISHER, INTERCEPTOR):
                continue
            side = 'left' if location[0] < 14 else 'right'
            self.this_turn_enemy_spawns.append((side, unit_type))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
