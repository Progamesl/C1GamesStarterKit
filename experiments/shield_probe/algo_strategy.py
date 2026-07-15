import gamelib
import json

"""
Milestone 4 SUPPORT/Encryptor shield-mechanism probe (docs/MILESTONE_4_REPORT.md
section on the Encryptor logic fix). Purpose-built, not a real baseline: places a
SUPPORT next to a "near" WALL/TURRET/SCOUT-spawn-point and control "far" copies of
the same units well outside shieldRange, then leaves everything alone (the
opponent, experiments/shield_probe_passive, never attacks) so any health
difference between near/far copies in the resulting replay is attributable ONLY
to the shield mechanic, not combat damage. Upgrades the SUPPORT partway through
to also observe the effect of the range/shieldPerUnit/shieldBonusPerY upgrade.
"""


class AlgoStrategy(gamelib.AlgoCore):
    def on_game_start(self, config):
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

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        turn = game_state.turn_number
        game_state.suppress_warnings(True)
        gamelib.debug_write('SHIELD_PROBE turn {}'.format(turn))

        if turn == 0:
            # Row y=8 has valid x in [5,22] (diamond geometry, see game_map.py
            # in_arena_bounds) -- wide enough to place a near AND a far
            # structure pair on the exact same row, controlling for y entirely.
            # SUPPORT at (13,8), unupgraded: shieldRange 2.5, shieldPerUnit 2.0.
            game_state.attempt_spawn(SUPPORT, [13, 8])
            # "Near" structures: within 2.5 tiles of the SUPPORT.
            game_state.attempt_spawn(WALL, [12, 8])     # dist 1.0
            game_state.attempt_spawn(TURRET, [11, 8])   # dist 2.0
            # "Far" control structures on the SAME row: 7-8 tiles away, out of
            # range both before AND after the shieldRange-7 upgrade.
            game_state.attempt_spawn(WALL, [6, 8])      # dist 7.0
            game_state.attempt_spawn(TURRET, [5, 8])    # dist 8.0

        if turn == 5:
            # Upgrade to shieldRange 7 / shieldPerUnit 4 / shieldBonusPerY 0.3 --
            # if the far structures (dist 7-8) are still unaffected post-upgrade,
            # that's strong evidence range 7 is a real, enforced cap.
            game_state.attempt_upgrade([13, 8])

        if turn == 0:
            # Second, pre-upgraded SUPPORT at a DIFFERENT y (y=3 instead of 8)
            # to test whether shieldBonusPerY scales with the SUPPORT's own y
            # position (hypothesis: shield = shieldPerUnit + shieldBonusPerY *
            # support_y). Row y=3 has valid x in [10,17] (game_map.py
            # in_arena_bounds), and (10,3) is exactly the BOTTOM_LEFT edge
            # deploy point for that row.
            game_state.attempt_spawn(SUPPORT, [11, 3])
            game_state.attempt_upgrade([11, 3])

        # Every turn: one scout spawned at (13,0) (a valid BOTTOM_LEFT-edge
        # deploy point -- see game_map.py get_edge_locations) whose path runs
        # straight up column x~13, passing directly through the SUPPORT's
        # (13,8) radius on its way to the enemy edge -- vs one at (0,13), the
        # far corner of the SAME edge, deployed on a lane that stays away from
        # (13,8) far longer. Repeated every turn for many independent samples.
        if turn >= 1:
            game_state.attempt_spawn(SCOUT, [13, 0], 1)
            game_state.attempt_spawn(SCOUT, [0, 13], 1)
            # Near-lane scout for the y=3 SUPPORT (predicted shield if the
            # y-scaling hypothesis is right: 4.0 + 0.3*3 = 4.9 -> 19.9 HP).
            game_state.attempt_spawn(SCOUT, [10, 3], 1)

        game_state.submit_turn()


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
