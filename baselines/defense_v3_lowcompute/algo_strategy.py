import gamelib
import random
import math
import warnings
from sys import maxsize
import json
from collections import defaultdict

"""
CANDIDATE: "defense_v3_lowcompute" -- defense_v2_endgame PLUS a fix for a real,
Verified weakness found while testing the endgame policy: baselines/defense LOSES
0-10 to opponents/turtle_survivor (a purely passive, zero-offense opponent), every
single game ending 40.0-40.0 on health at turn 99 -- i.e. losing purely on the
Verified compute-time tie-break (docs/GAME_SPEC.md 4.3), NOT on any placement/unit
weakness. Directly measured via the replay's `endStats.playerN.total_computation_time`
field (ms): baselines/defense used ~1820-1827ms across a full game vs
turtle_survivor's ~710-730ms. Isolated by a diagnostic probe (disabling
`opportunistic_offense` entirely dropped defense's own compute to ~618ms, matching
turtle_survivor) that essentially ALL of the excess compute comes from
`least_damage_spawn_location`'s per-option `find_path_to_edge`/`get_attackers` calls,
called every other turn from turn 6 onward. See docs/MILESTONE_2_REPORT.md for the
full writeup.

Two changes on top of defense_v2_endgame:

  1. `least_damage_spawn_location` results are now CACHED and only recomputed every
     RECOMPUTE_INTERVAL turns (instead of every eligible turn), and evaluated over
     fewer candidate options -- cuts the number of expensive pathfinding calls by
     roughly an order of magnitude while keeping the same decision *quality* most
     of the time (the cheapest lane rarely flips turn-to-turn against a static
     defense).
  2. STALEMATE_BREAKER: if we have never once been breached by turn
     STALEMATE_CHECK_TURN, periodically commit a real escalating strike (not just a
     cheap probe) using the cached lane choice -- because per the Verified tie-break
     rule, remaining in an exact 40-40 stalemate is a loss for us if we're not
     strictly faster than the opponent (which turtle_survivor already isn't), so
     making ANY real progress (going from tied to ahead) is strictly better than
     staying passive.
"""

ENDGAME_TURN_THRESHOLD = 80
RECOMPUTE_INTERVAL = 12
STALEMATE_CHECK_TURN = 40
STALEMATE_STRIKE_PERIOD = 10


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring DEFENSE_V3_LOWCOMPUTE candidate...')
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

        # breach_history[(x,y)] = number of times we've been hit here, decayed each turn
        self.breach_history = defaultdict(float)
        self.max_reactive_spend_per_turn = 6  # SP cap on reactive rebuilding per turn

        # Full-width core defense line locations (front row) and the corner-weighted
        # turret anchors placed one row back, out of enemy demolisher's direct line.
        self.core_turret_anchors = [
            [1, 12], [26, 12],      # corners: highest priority
            [4, 12], [23, 12],
            [7, 11], [20, 11],
            [10, 10], [17, 10],
            [13, 10], [14, 10],
        ]
        self.core_wall_front = [[x, 13] for x in [0, 1, 2, 3, 4, 5, 22, 23, 24, 25, 26, 27]]

        self._cached_lane = None
        self._cached_lane_turn = -999
        self.ever_breached = False

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        turn = game_state.turn_number

        near_cap = turn > ENDGAME_TURN_THRESHOLD
        ahead = game_state.my_health >= game_state.enemy_health
        endgame_preserve = near_cap and ahead
        endgame_desperate = near_cap and not ahead

        gamelib.debug_write('DEFENSE_V2 turn {} my_hp={} enemy_hp={} mode={}'.format(
            turn, game_state.my_health, game_state.enemy_health,
            'PRESERVE' if endgame_preserve else ('DESPERATE' if endgame_desperate else 'NORMAL')))
        game_state.suppress_warnings(True)

        self._decay_breach_history()
        self.build_core_defense(game_state)
        self.reactive_defense(game_state, cap_override=(10 if endgame_preserve else None))
        self.upgrade_core(game_state)

        if endgame_preserve:
            # Lock in the lead: no offense, spend any remaining MP stalling with
            # interceptors instead (cheap, defensive-only, never leaves our own
            # side of the board).
            self.stall_with_interceptors(game_state, max_spend=3)
        elif endgame_desperate:
            self.desperation_offense(game_state)
        else:
            self.opportunistic_offense(game_state)

        game_state.submit_turn()

    def desperation_offense(self, game_state):
        """Behind on health near the turn cap: normal play is losing this game on
        its current trajectory, so spend everything offensively rather than
        continuing to conserve (prior-art hypothesis #4, docs/GAME_SPEC.md 4.3)."""
        best = self._get_cached_lane(game_state)
        demolisher_cost = game_state.type_cost(DEMOLISHER)[MP]
        if game_state.get_resource(MP) >= demolisher_cost * 2:
            game_state.attempt_spawn(DEMOLISHER, best, 2)
        game_state.attempt_spawn(SCOUT, best, 1000)

    def _decay_breach_history(self):
        for loc in list(self.breach_history.keys()):
            self.breach_history[loc] *= 0.6
            if self.breach_history[loc] < 0.05:
                del self.breach_history[loc]

    def build_core_defense(self, game_state):
        game_state.attempt_spawn(TURRET, self.core_turret_anchors)
        game_state.attempt_spawn(WALL, self.core_wall_front)
        # Cheap SUPPORT behind the middle to hedge our bets on the (partially
        # unverified, see GAME_SPEC.md 2.1 gap note) shield mechanic, but only once
        # the SP core exists -- never before turret/wall coverage.
        if game_state.get_resource(SP) > 10:
            game_state.attempt_spawn(SUPPORT, [[13, 3], [14, 3]])

    def upgrade_core(self, game_state):
        # Upgrading a TURRET is a big power jump (dmg 5->15, range 2.5->3.5) for a
        # marginal +3.0 SP over its base cost -- prioritize this over raw width once
        # the core anchors are down.
        game_state.attempt_upgrade(self.core_turret_anchors)
        game_state.attempt_upgrade(self.core_wall_front)

    def reactive_defense(self, game_state, cap_override=None):
        """Reinforce a neighborhood around recently-breached cells, weighted by
        recency+frequency, capped in total SP spend so a repeated-feint opponent
        can't bait us into overspending on a decoy lane (prior-art hypothesis #1).
        `cap_override` raises the cap in endgame-preserve mode (see on_turn)."""
        if not self.breach_history:
            return
        cap = cap_override if cap_override is not None else self.max_reactive_spend_per_turn
        ranked = sorted(self.breach_history.items(), key=lambda kv: -kv[1])
        spent = 0
        for (bx, by), weight in ranked:
            if spent >= cap:
                break
            neighborhood = [[bx, by + 1], [bx - 1, by + 1], [bx + 1, by + 1]]
            for loc in neighborhood:
                if spent >= cap:
                    break
                if loc[1] >= game_state.HALF_ARENA:
                    continue
                cost = game_state.type_cost(TURRET)[SP]
                if game_state.attempt_spawn(TURRET, loc):
                    spent += cost

    def opportunistic_offense(self, game_state):
        """Only spend MP we can genuinely spare; never touch SP set aside for
        defense. Simple least-damage scout probe, reusing the same path-risk
        heuristic idea as the starter bot but gated on turn parity + a higher MP
        floor so this archetype doesn't behave like a rush.

        Compute-time fix (see module docstring): the lane choice is now cached and
        only recomputed every RECOMPUTE_INTERVAL turns instead of every eligible
        turn, cutting the number of expensive pathfinding calls roughly 10x versus
        baselines/defense while keeping the same decision quality most of the time.
        """
        turn = game_state.turn_number
        if turn < 6:
            self.stall_with_interceptors(game_state)
            return

        mp = game_state.get_resource(MP)
        if mp >= 9 and turn % 2 == 0:
            best = self._get_cached_lane(game_state)
            game_state.attempt_spawn(SCOUT, best, 1000)

        self._stalemate_breaker(game_state)

    def _get_cached_lane(self, game_state):
        turn = game_state.turn_number
        if self._cached_lane is None or (turn - self._cached_lane_turn) >= RECOMPUTE_INTERVAL:
            # Only 2 options (not 4): halves the already-throttled pathfinding cost
            # again. [13,0] represents a middle lane, [3,10] a near-corner lane --
            # still a meaningful choice, just cheaper to evaluate every time.
            options = [[13, 0], [3, 10]]
            self._cached_lane = self.least_damage_spawn_location(game_state, options)
            self._cached_lane_turn = turn
        return self._cached_lane

    def _stalemate_breaker(self, game_state):
        """If the opponent has never once broken through our defense by
        STALEMATE_CHECK_TURN, a passive 40-40 result at turn 100 is a loss for us
        via the compute-time tie-break (Verified, GAME_SPEC.md 4.3) unless we're
        strictly faster -- so periodically commit real force to try to actually
        gain ground rather than staying tied indefinitely."""
        turn = game_state.turn_number
        if self.ever_breached or turn < STALEMATE_CHECK_TURN or turn % STALEMATE_STRIKE_PERIOD != 0:
            return
        best = self._get_cached_lane(game_state)
        demolisher_cost = game_state.type_cost(DEMOLISHER)[MP]
        if game_state.get_resource(MP) >= demolisher_cost * 2:
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
        # Compute-time fix (see module docstring): hoist the GameUnit(TURRET, ...)
        # construction out of the innermost loop -- it was previously reconstructed
        # once per path tile (often 10-15+ times per option) for a value that never
        # changes within a single call. This alone was a meaningful chunk of
        # defense's excess per-turn compute time relative to a much simpler
        # opponent (see docs/MILESTONE_2_REPORT.md for the measured numbers).
        turret_damage = gamelib.GameUnit(TURRET, game_state.config).damage_i
        damages = []
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            if path:
                for path_location in path:
                    damage += len(game_state.get_attackers(path_location, 0)) * turret_damage
            else:
                damage = float('inf')
            damages.append(damage)
        return location_options[damages.index(min(damages))]

    def on_action_frame(self, turn_string):
        # Compute-time fix (see module docstring): gamelib.AlgoCore.start() already
        # does one full json.loads(...) on every action frame just to route it here
        # -- our own second, independent json.loads(...) on the same string was
        # pure duplicate work. Most frames have zero breach events (`"breach":[]`,
        # a fixed, whitespace-free substring the engine always emits for an empty
        # list), so a cheap substring check lets us skip the second full parse
        # entirely on the common case.
        if '"breach":[]' in turn_string:
            return
        state = json.loads(turn_string)
        breaches = state["events"]["breach"]
        for breach in breaches:
            location = tuple(breach[0])
            unit_owner_self = (breach[4] == 1)
            if not unit_owner_self:
                self.breach_history[location] += 1.0
                self.ever_breached = True


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
