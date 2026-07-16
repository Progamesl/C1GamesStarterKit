import gamelib
import random
from sys import maxsize
import json

"""
ADVERSARIAL COUNTERSEARCH OPPONENT (Milestone 4->5): "shield_race_rusher".

Targets a THIRD, distinct `baselines/defense_v6_encryptor_fix` weakness from
`opponents/support_sniper` (direct structural sniping) and
`opponents/corner_lane_baiter` (routing around the shield radius): the
UPGRADE-TIMING window itself. Read directly from the champion's
`upgrade_core`: SUPPORT is the LAST thing upgraded every turn, strictly after
ALL 10 `core_turret_anchors` and ALL 12 `core_wall_front` cells are already
upgraded. With a finite per-turn SP income, that ordering means many, many
turns can pass with SUPPORT sitting at its unupgraded stats (shieldRange 2.5,
shieldPerUnit 2.0 -- a much smaller, weaker shield than the upgraded 7/4.0)
even though it was already spawned and exposed.

Hypothesis: unlike `baselines/rush` (which is *unfocused* aggression, already
in the regression corpus and already beaten 100% of the time), a rush that is
specifically SUSTAINED (not just an opening burst) and specifically AIMED at
the central lane (where SUPPORT lives) for the whole early/mid game should
maximize time spent inside the pre-SUPPORT-upgrade window, and should also
keep partially re-testing hypothesis 3 from `support_sniper` (does sustained,
undirected pressure on the same lane, even without adaptive detection, keep
knocking SUPPORT down before it escapes the back of the upgrade queue?) via
a completely different, non-adaptive, "dumb but persistent" mechanism, as a
robustness cross-check on that same underlying question.

Unlike `support_sniper` (minimal defense, fully offense-committed) and
`corner_lane_baiter` (zero offense, pure static bait), this opponent carries
a REAL defense of its own (dense enough to survive a long game, upgraded
opportunistically) so it also represents "a fairly complete, competitively
serious opponent applies sustained pressure early" rather than a
deliberately one-dimensional probe -- the version of this test closest to a
real competitive matchup.
"""

RUSH_START_TURN = 3
DEMOLISHER_PERIOD = 3


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring SHIELD_RACE_RUSHER opponent...')
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

        # A real (if modest) defense of its own -- corner turrets plus a
        # partial front wall, upgraded with whatever SP the rush doesn't
        # need, so this opponent can survive a long game rather than being a
        # pure glass-cannon probe.
        self.defense_turrets = [[1, 12], [26, 12], [4, 12], [23, 12]]
        self.defense_walls = [[x, 13] for x in [0, 1, 2, 3, 24, 25, 26, 27]]

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        turn = game_state.turn_number
        gamelib.debug_write('SHIELD_RACE_RUSHER turn {}'.format(turn))
        game_state.suppress_warnings(True)

        game_state.attempt_spawn(TURRET, self.defense_turrets)
        game_state.attempt_spawn(WALL, self.defense_walls)
        game_state.attempt_upgrade(self.defense_turrets)
        game_state.attempt_upgrade(self.defense_walls)

        if turn < RUSH_START_TURN:
            self.stall_with_interceptors(game_state, max_spend=2)
        else:
            self.sustained_central_rush(game_state)

        game_state.submit_turn()

    def sustained_central_rush(self, game_state):
        """Every turn from RUSH_START_TURN onward (not just a one-off burst):
        commit essentially all available MP to the central lane specifically
        -- maximizing exposure of any turn where SUPPORT is unupgraded or
        recently destroyed, and cross-checking (via a non-adaptive mechanism)
        whether sustained central pressure alone, without detection, is
        enough to matter."""
        turn = game_state.turn_number
        options = [[13, 0], [14, 0]]
        best = self.least_damage_spawn_location(game_state, options)

        demolisher_cost = game_state.type_cost(DEMOLISHER)[MP]
        if turn % DEMOLISHER_PERIOD == 0 and game_state.get_resource(MP) >= demolisher_cost * 2:
            game_state.attempt_spawn(DEMOLISHER, best, 2)

        game_state.attempt_spawn(SCOUT, best, 1000)

    def stall_with_interceptors(self, game_state, max_spend=2):
        friendly_edges = (game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) +
                          game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT))
        deploy_locations = [loc for loc in friendly_edges if not game_state.contains_stationary_unit(loc)]
        spent = 0
        while (game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP]
               and len(deploy_locations) > 0 and spent < max_spend):
            deploy_location = deploy_locations[random.randint(0, len(deploy_locations) - 1)]
            if game_state.attempt_spawn(INTERCEPTOR, deploy_location):
                spent += 1

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
