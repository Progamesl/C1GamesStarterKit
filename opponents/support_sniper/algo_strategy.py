import gamelib
import random
from sys import maxsize
import json

"""
ADVERSARIAL COUNTERSEARCH OPPONENT (Milestone 4->5): "support_sniper".

Purpose-built to close the one honest gap flagged in docs/MILESTONE_4_REPORT.md
section 6: no opponent has yet specifically targeted `baselines/defense_v6_encryptor_fix`'s
new SUPPORT (Encryptor) placement/upgrade behavior under the corrected config.

Read directly from `baselines/defense_v6_encryptor_fix/algo_strategy.py`:
SUPPORT is placed at a FIXED pair of coordinates (`[[13, 9], [14, 9]]`), only
spawned once `SP > 10` (build_core_defense), and only UPGRADED after both the
full turret-anchor line AND the full wall-front line are already upgraded
(upgrade_core's call order: turrets, then walls, then support). Its base
health is only 30 (WALL: 40/120, TURRET: 75 -- SUPPORT is the single most
fragile structure type in the corrected config, per docs/GAME_SPEC.md 2.5) and
its shield-mechanic itself does nothing to protect the SUPPORT unit's own
health (Verified in the Milestone 4 probe: SUPPORT shields only MOBILE units
passing through its radius, never stationary structures, not even itself).

Three hypotheses this opponent tests simultaneously, by direct attack rather
than by argument:
  1. **Fixed placement is a fixed target.** A known/detectable x~13-14 column
     is a much narrower, more predictable target than the full-width wall
     front, so a lane-optimized attack can consistently reach it.
  2. **Upgrade-timing window.** Because SUPPORT upgrades dead last in
     `upgrade_core`, it likely spends a large fraction of the early/mid game
     at its unupgraded stats (shieldRange 2.5, shieldPerUnit 2.0) even though
     it's already exposed -- attacking early (not waiting for a "mature"
     defense) specifically probes this window.
  3. **Squishy and re-buildable, not permanently gone.** `build_core_defense`
     re-spawns SUPPORT every turn it's missing (as long as SP>10), so
     destroying it once is not a permanent breach -- the real test is whether
     SUSTAINED pressure can keep it perpetually destroyed/unupgraded (a
     standing MP/SP drain and a standing loss of the shield bonus for the
     champion's own offense), not just a one-off kill.

Mechanism: rather than hardcode the exact champion coordinates (which would
only test this one file, and stop working the moment placement changes),
this opponent ADAPTIVELY detects enemy SUPPORT structures every turn via
`game_state.game_map` (the same enemy-unit-scanning technique already used by
`opponents/adaptive_reactive` and `opponents/escorted_combined_arms`), then
biases its attack lane toward whichever detected SUPPORT x-column exists,
falling back to the known central lane ([13,0]/[14,0], the only two valid
BOTTOM edge cells at y=0) if none has been spawned yet. Uses a scout screen
one turn ahead of a following demolisher group (re-using the
`escorted_combined_arms` staggering idea, since DEMOLISHER is the unit type
that reliably damages structures at range) to help the demolishers actually
survive long enough to reach the SUPPORT's row, sent continuously and early
(starting turn 3), not just once.
"""

WAVE_PERIOD = 4


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring SUPPORT_SNIPER opponent...')
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

        # Minimal own defense -- this opponent exists to test the attack side
        # of the matchup, not to be a strong defensive fixture in its own
        # right (same design choice as opponents/middle_rush_exploit and
        # opponents/escorted_combined_arms).
        self.min_defense = [[0, 13], [27, 13], [1, 12], [26, 12]]
        self.pending_lane = None

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        turn = game_state.turn_number
        gamelib.debug_write('SUPPORT_SNIPER turn {}'.format(turn))
        game_state.suppress_warnings(True)

        game_state.attempt_spawn(TURRET, self.min_defense)

        cycle_pos = turn % WAVE_PERIOD
        if turn >= 2 and cycle_pos == 0:
            best = self._choose_support_lane(game_state)
            game_state.attempt_spawn(SCOUT, best, 3)
            self.pending_lane = best
        elif self.pending_lane is not None and cycle_pos == 1:
            demolisher_budget_mp = game_state.get_resource(MP)
            demolisher_cost = game_state.type_cost(DEMOLISHER)[MP]
            num_demolishers = max(1, min(4, int(demolisher_budget_mp // demolisher_cost)))
            game_state.attempt_spawn(DEMOLISHER, self.pending_lane, num_demolishers)
            self.pending_lane = None
        elif turn >= 2 and game_state.get_resource(MP) >= 3:
            # Between organized waves, still keep some steady pressure on the
            # detected support lane rather than letting MP idle.
            best = self._choose_support_lane(game_state)
            game_state.attempt_spawn(SCOUT, best, 2)

        game_state.submit_turn()

    def _choose_support_lane(self, game_state):
        """Adaptively bias toward whichever x-column an enemy SUPPORT has
        actually been detected on; fall back to the known central lane
        ([13,0]/[14,0], the two BOTTOM-edge cells at the tip of the diamond)
        if none is up yet -- SUPPORT under the corrected config is a
        high-value, low-HP target either way."""
        support_locs = self._detect_enemy_unit_locations(game_state, SUPPORT)
        candidates = [[13, 0], [14, 0], [12, 1], [15, 1]]
        if support_locs:
            target_x = support_locs[0][0]
            # Prefer whichever candidate is on the same x column (mod the
            # left/right symmetry of the diamond) as the detected support.
            candidates = sorted(
                candidates,
                key=lambda loc: min(abs(loc[0] - target_x), abs(loc[0] - (27 - target_x))),
            )
        return self.least_damage_spawn_location(game_state, candidates)

    def _detect_enemy_unit_locations(self, game_state, unit_type):
        locations = []
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and unit.unit_type == unit_type:
                        locations.append(list(location))
        return locations

    def least_damage_spawn_location(self, game_state, location_options):
        turret_damage = gamelib.GameUnit(TURRET, game_state.config).damage_i
        damages = []
        for location in location_options:
            if game_state.contains_stationary_unit(location):
                damages.append(float('inf'))
                continue
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
