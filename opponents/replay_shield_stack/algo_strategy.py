"""Replay-derived stress opponent: dense turrets + shield-stacked Scout bursts.

This is an independent implementation of mechanisms observable in a user-supplied
High School Terminal 2026 replay; it is not copied from either replay participant.

Mechanisms under test:
  * spend the opening 40 SP on an unusually dense, 18-turret defense;
  * preserve the base turret's longer 4.5 range (do not blindly upgrade it);
  * grow two permanent, upgraded Encryptor corridors near the central gates;
  * deliberately hoard MP, then spend the entire bank on sparse Scout waves;
  * recompute the wave lane from current paths, enemy turret exposure, and the
    shield actually available on each path, rather than using one fixed spawn.

The opponent is a local stress fixture, not a submission candidate.
"""

import math
import os
import sys


# Keep local opponents lightweight by using the repository's canonical starter
# gamelib.  The engine starts this file through run.sh from any working directory.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "python-algo"))

import gamelib  # noqa: E402


MIN_BURST_MP = 16
MIN_BURST_GAP = 5
FIRST_BURST_TURN = 5
LANE_TIE_EPSILON = 0.04
DISABLE_SUPPORTS = os.environ.get("REPLAY_STACK_DISABLE_SUPPORTS") == "1"


class AlgoStrategy(gamelib.AlgoCore):
    def on_game_start(self, config):
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        MP, SP = 1, 0

        # 18 * 2 SP turrets + 2 * (1 build + 1 upgrade) endpoint walls = 40 SP.
        # The two central front cells stay open as permanent mobile gates.
        self.endpoint_walls = [[0, 13], [27, 13]]
        self.opening_turrets = [
            [1, 13], [1, 12], [26, 13], [26, 12],
            [2, 13], [2, 12], [25, 13], [25, 12],
            [3, 13], [3, 12], [24, 13], [24, 12],
            [11, 12], [16, 12], [12, 11], [15, 11],
            [12, 13], [15, 13],
        ]

        # Two forward corridors.  A late central path can pass through the
        # radii of both groups, making shield strength compound over time.
        self.support_anchors = [
            [17, 11], [19, 11], [20, 12], [18, 10],
            [10, 11], [8, 11], [7, 12], [9, 10],
        ]

        # Add width/depth only after the opening core and currently scheduled
        # support work.  No anchor blocks the permanent [13,13]/[14,13] gates.
        self.expansion_turrets = [
            [4, 13], [23, 13], [5, 13], [22, 13],
            [6, 13], [21, 13], [7, 13], [20, 13],
            [8, 13], [19, 13], [9, 13], [18, 13],
            [10, 13], [17, 13], [5, 12], [22, 12],
            [7, 11], [20, 11],
        ]

        # A broad legal edge sample.  It includes central, shoulder, and corner
        # lanes so a candidate is not selected from a token two-lane choice.
        self.lane_candidates = [
            [13, 0], [14, 0],
            [11, 2], [16, 2],
            [9, 4], [18, 4],
            [7, 6], [20, 6],
            [5, 8], [22, 8],
            [3, 10], [24, 10],
        ]
        self.last_burst_turn = -999
        self.last_target_x = None

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        turn = game_state.turn_number
        game_state.suppress_warnings(True)

        self._maintain_opening_core(game_state)
        self._grow_shield_corridors(game_state, turn)
        self._add_one_expansion_turret(game_state)

        mp = game_state.get_resource(MP)
        should_burst = (
            turn >= FIRST_BURST_TURN
            and mp >= MIN_BURST_MP
            and turn - self.last_burst_turn >= MIN_BURST_GAP
        )
        if should_burst:
            lane, path, score, risk, shield = self._choose_lane(game_state)
            spawned = game_state.attempt_spawn(SCOUT, lane, 1000)
            self.last_burst_turn = turn
            self.last_target_x = path[-1][0] if path else None
            gamelib.debug_write(
                "REPLAY_SHIELD_STACK turn {} BURST scouts={} lane={} "
                "target={} score={:.3f} risk={:.1f} shield={:.1f}".format(
                    turn,
                    spawned,
                    lane,
                    path[-1] if path else None,
                    score,
                    risk,
                    shield,
                )
            )
        else:
            gamelib.debug_write(
                "REPLAY_SHIELD_STACK turn {} ACCUMULATE mp={:.1f}".format(
                    turn, mp
                )
            )

        game_state.submit_turn()

    def _maintain_opening_core(self, game_state):
        # Preserve the replay's range-density mechanism: base turrets have 4.5
        # range in this config while their nominal upgrade drops range to 3.5.
        game_state.attempt_spawn(TURRET, self.opening_turrets)
        game_state.attempt_spawn(WALL, self.endpoint_walls)
        game_state.attempt_upgrade(self.endpoint_walls)

    def _desired_support_count(self, turn):
        if DISABLE_SUPPORTS:
            return 0
        if turn < 1:
            return 0
        # Add one corridor anchor every other turn.  Building and upgrading a
        # support costs 8 SP total, so the intervening turn naturally completes
        # the upgrade and leaves occasional SP for turret expansion.
        return min(len(self.support_anchors), 1 + (turn - 1) // 2)

    def _grow_shield_corridors(self, game_state, turn):
        anchors = self.support_anchors[: self._desired_support_count(turn)]
        game_state.attempt_spawn(SUPPORT, anchors)
        game_state.attempt_upgrade(anchors)

    def _add_one_expansion_turret(self, game_state):
        for location in self.expansion_turrets:
            if game_state.contains_stationary_unit(location):
                continue
            if game_state.attempt_spawn(TURRET, location):
                return

    def _choose_lane(self, game_state):
        scored = []
        for lane in self.lane_candidates:
            if game_state.contains_stationary_unit(lane):
                continue
            path = game_state.find_path_to_edge(lane)
            if not path:
                continue
            risk = self._projected_turret_damage(game_state, path)
            shield = self._path_shield(game_state, path)

            # Normalize exposure by actual per-Scout effective health.  This is
            # the key distinction from a plain least-turret lane heuristic:
            # accumulated shields can make a nominally busier path safer.
            effective_health = self._scout_health() + shield
            score = risk / max(effective_health, 1.0)
            scored.append((score, risk, -shield, lane, path, shield))

        if not scored:
            fallback = [13, 0]
            return fallback, game_state.find_path_to_edge(fallback) or [], math.inf, math.inf, 0

        scored.sort(key=lambda item: (item[0], item[1], item[3]))
        best_score = scored[0][0]
        band = best_score * (1.0 + LANE_TIE_EPSILON) + 1e-9
        near_best = [item for item in scored if item[0] <= band]

        # On a real near-tie, prefer the target farther from the previous one.
        # This avoids collapsing symmetric boards into a permanently fixed lane
        # while still requiring the alternatives to be essentially equivalent.
        if self.last_target_x is not None and len(near_best) > 1:
            chosen = max(
                near_best,
                key=lambda item: (
                    abs(item[4][-1][0] - self.last_target_x),
                    -item[0],
                ),
            )
        else:
            chosen = near_best[0]
        score, risk, _negative_shield, lane, path, shield = chosen
        return lane, path, score, risk, shield

    def _projected_turret_damage(self, game_state, path):
        # Use each real attacker's configured damage.  This respects the unusual
        # 5-damage/4.5-range base vs 16-damage/3.5-range upgraded tradeoff.
        return sum(
            sum(attacker.damage_i for attacker in game_state.get_attackers(tile, 0))
            for tile in path
        )

    def _path_shield(self, game_state, path):
        total = 0.0
        for location in game_state.game_map:
            for unit in game_state.game_map[location]:
                if (
                    unit.player_index != 0
                    or unit.unit_type != SUPPORT
                    or unit.shieldRange <= 0
                ):
                    continue
                reaches_path = any(
                    game_state.game_map.distance_between_locations(location, tile)
                    <= unit.shieldRange
                    for tile in path
                )
                if reaches_path:
                    total += unit.shieldPerUnit + unit.shieldBonusPerY * unit.y
        return total

    def _scout_health(self):
        return float(self.config["unitInformation"][3].get("startHealth", 0))


if __name__ == "__main__":
    AlgoStrategy().start()
