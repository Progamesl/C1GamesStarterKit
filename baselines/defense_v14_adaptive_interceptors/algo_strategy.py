"""Milestone 9 mechanism A: adaptive, MP-funded mobile defense.

This candidate deliberately subclasses the accepted
``defense_v6_encryptor_fix`` implementation.  Its SP build order, reactive
defense, upgrades, and non-threat offense are inherited unchanged.  The only
new behavior is a general action-frame classifier for enemy mobile pressure:

* repeated Demolisher spawns activate a sustained Interceptor screen;
* a large Scout burst activates a bounded watch, then cadence prediction;
* turns 0-4 use the same two-MP startup allowance as v6, but at controlled
  coordinates instead of random edge cells.

No opponent name, directory, or exact v33 turn number is inspected.

The coordinate and spend profiles are environment-selectable only so the
bounded experiment can compare mechanisms without generating nine near-copy
directories:

``M9_SCREEN_COORD_PROFILE`` = mirror | corner | deep
``M9_SCREEN_SPEND_PROFILE`` = low | medium | high
"""

from __future__ import annotations

import importlib.util
import json
import math
import os
import sys
from collections import defaultdict


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V6_DIR = os.path.join(REPO_ROOT, "baselines", "defense_v6_encryptor_fix")
sys.path.insert(0, V6_DIR)
_SPEC = importlib.util.spec_from_file_location(
    "milestone9_v6_base", os.path.join(V6_DIR, "algo_strategy.py")
)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("could not load defense_v6_encryptor_fix")
v6 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(v6)
gamelib = v6.gamelib


COORD_PROFILES = {
    # Mirror the observed enemy edge origin through the center of the board.
    # This sends the screen up the reciprocal lane.
    "mirror": {
        "left": [4, 9],
        "right": [23, 9],
    },
    # Closest legal friendly-edge cells to the recurring corner breach zones.
    "corner": {
        "left": [3, 10],
        "right": [24, 10],
    },
    # Deeper edge cells used by independent public bots for broad coverage.
    "deep": {
        "left": [7, 6],
        "right": [20, 6],
    },
}

SPEND_PROFILES = {
    "low": {
        "sustained_fraction": 0.35,
        "emergency_fraction": 0.60,
        "demo_min_count": 2,
        "scout_burst_min": 12,
    },
    "medium": {
        "sustained_fraction": 0.60,
        "emergency_fraction": 0.85,
        "demo_min_count": 2,
        "scout_burst_min": 8,
    },
    "high": {
        "sustained_fraction": 0.85,
        "emergency_fraction": 1.00,
        "demo_min_count": 1,
        "scout_burst_min": 6,
    },
}

STARTUP_SCREEN_LAST_TURN = 4
DEMO_CONFIRM_TURNS = 2
DEMO_DECAY_TURNS = 2
SCOUT_CADENCE_TOLERANCE = 0


class AlgoStrategy(v6.AlgoStrategy):
    def on_game_start(self, config):
        super().on_game_start(config)

        coord_name = os.environ.get("M9_SCREEN_COORD_PROFILE", "mirror").lower()
        spend_name = os.environ.get("M9_SCREEN_SPEND_PROFILE", "medium").lower()
        if coord_name not in COORD_PROFILES:
            raise ValueError("unknown M9_SCREEN_COORD_PROFILE: {}".format(coord_name))
        if spend_name not in SPEND_PROFILES:
            raise ValueError("unknown M9_SCREEN_SPEND_PROFILE: {}".format(spend_name))

        self.coord_profile_name = coord_name
        self.coord_profile = COORD_PROFILES[coord_name]
        self.spend_profile_name = spend_name
        self.spend_profile = SPEND_PROFILES[spend_name]

        self.enemy_scout = config["unitInformation"][3]["shorthand"]
        self.enemy_demolisher = config["unitInformation"][4]["shorthand"]
        self.type_index_to_shorthand = {
            index: unit["shorthand"]
            for index, unit in enumerate(config["unitInformation"])
        }

        # Raw action-frame observations, keyed by the combat turn in which the
        # enemy units spawned.  on_turn N consumes all observations through N-1.
        self.mobile_spawns_by_turn = defaultdict(list)
        self.last_history_turn = -1
        self.recent_attack_history = []

        self.demo_streak = {"left": 0, "right": 0}
        self.demo_quiet = {"left": 0, "right": 0}
        self.demo_active = {"left": False, "right": False}
        self.last_enemy_origin = {"left": None, "right": None}

        self.last_scout_burst_turn = None
        self.scout_burst_interval = None
        self.scout_estimated_interval = None
        self.scout_burst_flanks = []
        self.current_turn = 0

        gamelib.debug_write(
            "M9_SCREEN_CONFIG coordinates={} spend={} values={}".format(
                self.coord_profile_name,
                self.spend_profile_name,
                self.spend_profile,
            )
        )

    def on_turn(self, turn_state):
        # Consume observations before v6 reaches opportunistic_offense, where
        # the response is selected. Parsing once per turn is negligible next to
        # pathfinding and avoids changing the accepted v6 GameState internals.
        raw_state = json.loads(turn_state)
        self.current_turn = int(raw_state.get("turnInfo", [0, 0])[1])
        self._consume_attack_history(self.current_turn)
        super().on_turn(turn_state)

    @staticmethod
    def _own_flank_for_enemy_origin(origin):
        # Action-frame enemy coordinates are absolute/top-side coordinates.
        # Rotate 180 degrees to express the reciprocal friendly edge cell.
        mirrored_x = 27 - int(origin[0])
        return "left" if mirrored_x < 14 else "right"

    def _estimate_scout_refill_turns(self, burst_count):
        """Estimate the earliest repeat of an all-in Scout burst.

        Mobile units do not persist into the next turn, so a large screen one
        turn *after* a completed burst cannot hit that burst. The first sweep
        verified that such post-hoc screens attacked nothing and drained the MP
        needed when the next wave actually arrived. Before a second sample gives
        us observed cadence, use only public resource rules and wave size to
        estimate the earliest plausible refill turn.
        """
        resources = self.config.get("resources", {})
        income = float(resources.get("bitsPerRound", 5.0))
        decay = float(resources.get("bitDecayPerRound", 0.25))

        # Conservatively allow one normal turn of MP to remain after the burst.
        # This predicts the earliest repeat rather than assuming the enemy spent
        # literally its final point.
        bank = income
        for gap in range(1, 13):
            bank = bank * (1.0 - decay) + income
            if bank >= burst_count:
                return gap
        return 12

    def _consume_attack_history(self, current_turn):
        for turn in range(self.last_history_turn + 1, current_turn):
            observations = self.mobile_spawns_by_turn.pop(turn, [])
            per_flank = {
                "left": {self.enemy_scout: 0, self.enemy_demolisher: 0},
                "right": {self.enemy_scout: 0, self.enemy_demolisher: 0},
            }
            origins = {"left": [], "right": []}
            for unit_type, origin in observations:
                flank = self._own_flank_for_enemy_origin(origin)
                per_flank[flank][unit_type] += 1
                origins[flank].append(origin)
                self.last_enemy_origin[flank] = origin

            history_entry = {
                "turn": turn,
                "left_scouts": per_flank["left"][self.enemy_scout],
                "right_scouts": per_flank["right"][self.enemy_scout],
                "left_demolishers": per_flank["left"][self.enemy_demolisher],
                "right_demolishers": per_flank["right"][self.enemy_demolisher],
            }
            self.recent_attack_history.append(history_entry)
            self.recent_attack_history = self.recent_attack_history[-12:]

            for flank in ("left", "right"):
                demo_count = per_flank[flank][self.enemy_demolisher]
                if demo_count >= self.spend_profile["demo_min_count"]:
                    self.demo_streak[flank] += 1
                    self.demo_quiet[flank] = 0
                else:
                    self.demo_streak[flank] = 0
                    self.demo_quiet[flank] += 1

                if self.demo_streak[flank] >= DEMO_CONFIRM_TURNS:
                    self.demo_active[flank] = True
                elif self.demo_quiet[flank] >= DEMO_DECAY_TURNS:
                    self.demo_active[flank] = False

            scout_counts = {
                flank: per_flank[flank][self.enemy_scout]
                for flank in ("left", "right")
            }
            burst_flanks = [
                flank
                for flank, count in scout_counts.items()
                if count >= self.spend_profile["scout_burst_min"]
            ]
            if burst_flanks:
                if self.last_scout_burst_turn is not None:
                    interval = turn - self.last_scout_burst_turn
                    # Ignore impossible/noisy gaps, but otherwise retain the
                    # observed cadence rather than assuming replay_stack's five.
                    if 2 <= interval <= 12:
                        self.scout_burst_interval = interval
                else:
                    burst_count = sum(scout_counts.values())
                    self.scout_estimated_interval = self._estimate_scout_refill_turns(
                        burst_count
                    )
                self.last_scout_burst_turn = turn
                self.scout_burst_flanks = burst_flanks

        self.last_history_turn = max(self.last_history_turn, current_turn - 1)

    def _screen_location(self, flank):
        if self.coord_profile_name == "mirror":
            origin = self.last_enemy_origin.get(flank)
            if origin is not None:
                mirrored = [27 - int(origin[0]), 27 - int(origin[1])]
                # Enemy mobile units can only originate on their legal edge, so
                # the rotation should be a friendly edge. Keep a bounded fallback
                # for malformed or synthetic action-frame input.
                if 0 <= mirrored[0] <= 27 and 0 <= mirrored[1] <= 13:
                    return mirrored
        return list(self.coord_profile[flank])

    def _screen_plan(self, game_state):
        turn = game_state.turn_number
        if turn <= STARTUP_SCREEN_LAST_TURN:
            return "startup", ["left", "right"], 2

        modes = []
        flanks = set()
        emergency = False

        for flank in ("left", "right"):
            if self.demo_active[flank]:
                modes.append("sustained-demo")
                flanks.add(flank)
            elif self.demo_streak[flank] == 1:
                # One qualifying turn is evidence, not confirmation. Spend at
                # most the old v6 startup allowance while classifying.
                modes.append("demo-probe")
                flanks.add(flank)

        if self.last_scout_burst_turn is not None:
            interval = (
                self.scout_burst_interval
                if self.scout_burst_interval is not None
                else self.scout_estimated_interval
            )
            expected = self.last_scout_burst_turn + interval
            if abs(turn - expected) <= SCOUT_CADENCE_TOLERANCE:
                modes.append(
                    "scout-cadence"
                    if self.scout_burst_interval is not None
                    else "scout-estimated"
                )
                # The trajectory sweep showed that using only the previous
                # flank chased replay_stack one burst behind: the next large
                # wave arrived opposite and the Interceptors attacked nothing.
                # Cadence predicts WHEN, not safely WHERE, so split the same
                # bounded budget across both legal flanks.
                flanks.update(("left", "right"))
                emergency = True

        if not flanks:
            return None

        mp = int(math.floor(game_state.get_resource(v6.MP)))
        if "demo-probe" in modes and not self.demo_active["left"] and not self.demo_active["right"]:
            budget = min(2, mp)
        else:
            fraction_key = "emergency_fraction" if emergency else "sustained_fraction"
            budget = int(math.floor(mp * self.spend_profile[fraction_key]))
            budget = max(min(len(flanks), mp), budget)
            budget = min(mp, budget)
        return "+".join(sorted(set(modes))), sorted(flanks), budget

    def _deploy_screen(self, game_state, mode, flanks, budget):
        if budget <= 0 or not flanks:
            return 0
        locations = [self._screen_location(flank) for flank in flanks]
        spawned = 0
        for index in range(budget):
            location = locations[index % len(locations)]
            if game_state.contains_stationary_unit(location):
                flank = flanks[index % len(flanks)]
                location = list(self.coord_profile[flank])
            spawned += game_state.attempt_spawn(v6.INTERCEPTOR, location, 1)
        gamelib.debug_write(
            "M9_SCREEN turn={} mode={} flanks={} budget={} spawned={} "
            "locations={} demo_streak={} scout_last={} scout_interval={} "
            "scout_estimate={}".format(
                game_state.turn_number,
                mode,
                flanks,
                budget,
                spawned,
                locations,
                self.demo_streak,
                self.last_scout_burst_turn,
                self.scout_burst_interval,
                self.scout_estimated_interval,
            )
        )
        return spawned

    def opportunistic_offense(self, game_state):
        plan = self._screen_plan(game_state)
        if plan is None:
            # Exact accepted-v6 behavior when no general mobile threat is active.
            return super().opportunistic_offense(game_state)
        mode, flanks, budget = plan
        self._deploy_screen(game_state, mode, flanks, budget)
        # Keep uncommitted MP banked for the next defensive screen. Calling v6's
        # offense here would dump all remainder into Scouts and defeat the
        # controlled-fraction policy.

    def on_action_frame(self, turn_string):
        if '"breach":[]' in turn_string and '"spawn":[]' in turn_string:
            return
        state = json.loads(turn_string)
        events = state.get("events", {})

        # Preserve accepted-v6 breach tracking exactly.
        for breach in events.get("breach", []):
            location = tuple(breach[0])
            unit_owner_self = breach[4] == 1
            if not unit_owner_self:
                self.breach_history[location] += 1.0
                self.ever_breached = True

        turn = int(state.get("turnInfo", [1, self.current_turn])[1])
        for spawn in events.get("spawn", []):
            if len(spawn) < 4 or int(spawn[3]) != 2:
                continue
            unit_type = self.type_index_to_shorthand.get(int(spawn[1]))
            if unit_type not in (self.enemy_scout, self.enemy_demolisher):
                continue
            self.mobile_spawns_by_turn[turn].append(
                (unit_type, [int(spawn[0][0]), int(spawn[0][1])])
            )


if __name__ == "__main__":
    AlgoStrategy().start()
