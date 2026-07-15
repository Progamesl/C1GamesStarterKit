import gamelib
import random
from sys import maxsize
import json

"""
ADVERSARIAL COUNTERSEARCH OPPONENT (Milestone 4->5): "corner_lane_baiter".

Targets a DIFFERENT `baselines/defense_v6_encryptor_fix` weakness than
`opponents/support_sniper`: not a direct attack on the SUPPORT structure, but
an attempt to make the champion's OWN offense never benefit from it in the
first place.

Read directly from the champion's source: `_get_cached_lane` (and every mode
that calls it -- `opportunistic_offense`, `desperation_offense`,
`all_in_tied_strike`, `_stalemate_breaker`) chooses between exactly two fixed
lane options, `[[13, 0], [3, 10]]`, via `least_damage_spawn_location` (a pure
projected-damage-along-path heuristic with NO awareness of the SUPPORT's
shield radius at all). The SUPPORT pair sits at `[[13, 9], [14, 9]]` with
`shieldRange` 2.5 unupgraded / 7 upgraded (Verified, Milestone 4 probe). The
distance from `[3, 10]` to `[13, 9]` is `sqrt(10^2 + 1^2) ~= 10.05` -- OUTSIDE
even the fully-upgraded 7-range shield radius. So: any turn the champion's own
heuristic picks the `[3, 10]` lane instead of `[13, 0]`, its own
scouts/demolishers get ZERO shield bonus, no matter how upgraded SUPPORT is.

Hypothesis: a static defense that is deliberately DENSE across the center
columns (where `[13, 0]`'s path runs) but deliberately WEAK at the near-left
corner (where `[3, 10]`'s path runs) should make the corner lane look
consistently cheaper to the champion's own damage-projection heuristic,
reliably routing its own offense away from the SUPPORT's shield radius on
every turn it attacks -- specifically negating the Milestone 4 fix's whole
margin advantage over `defense_v4_tiebreak` (control) in exactly the kind of
long/grinding matchup where that advantage was shown to matter
(docs/MILESTONE_4_REPORT.md section 3, the three "leak/turtle" opponents).

Pure static defense, zero offense (like opponents/turtle_survivor) --
isolates the routing question cleanly, without a counter-offense confound.
"""


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring CORNER_LANE_BAITER opponent...')
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

        # Dense wall + turret coverage across the CENTER columns only
        # (x in [6,21]) -- exactly where the champion's [13,0] lane runs, and
        # near-symmetric on both sides so it can't just walk around it via
        # the *other* side's near-corner instead.
        self.center_wall_front = [[x, 13] for x in range(6, 22)]
        self.center_wall_second = [[x, 12] for x in range(7, 21)]
        self.center_turret_line = [[x, 11] for x in range(6, 22, 2)]
        # Deliberately WEAK/minimal at both corners -- x in [0,5] and
        # [22,27] -- so the [3,10]-style lanes look cheap by comparison.
        self.corner_turrets = [[1, 12], [26, 12]]

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        turn = game_state.turn_number
        gamelib.debug_write('CORNER_LANE_BAITER turn {}'.format(turn))
        game_state.suppress_warnings(True)

        game_state.attempt_spawn(TURRET, self.center_turret_line)
        game_state.attempt_spawn(WALL, self.center_wall_front)
        game_state.attempt_spawn(WALL, self.center_wall_second)
        game_state.attempt_spawn(TURRET, self.corner_turrets)

        game_state.attempt_upgrade(self.center_turret_line)
        game_state.attempt_upgrade(self.center_wall_front)
        game_state.attempt_upgrade(self.center_wall_second)
        game_state.attempt_upgrade(self.corner_turrets)

        # No offense, ever -- pure static bait, isolating the routing
        # question from any counter-offense confound (same rationale as
        # opponents/turtle_survivor).

        game_state.submit_turn()


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
