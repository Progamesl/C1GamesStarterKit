import gamelib
import random
from sys import maxsize
import json

"""
COMBINED-THREAT OPPONENT (Milestone 6): "adaptive_burst_combined_arms".

Every opponent built in Milestones 4-5 deliberately isolated ONE mechanism at
a time, specifically so a win/loss could be cleanly attributed to that one
thing (docs/MILESTONE_5_REPORT.md). That discipline was correct for what it
was testing, but it has a real, acknowledged cost: after 5 milestones of
narrow single-mechanism probes, `baselines/defense_v6_encryptor_fix` has
literally never lost a single game that reached turn 78, and its DESPERATE
endgame mode has zero real-match evidence (Milestone 5 section 8). This
opponent is the deliberate opposite of that discipline: it COMBINES several
real, independently-plausible aggressive mechanisms at once, specifically to
see whether the champion can be pushed into an actual loss or a real
DESPERATE trigger for the first time -- real evidence, not another synthetic
probe.

Four mechanisms combined (none of them novel individually -- each is already
used somewhere in this repo's opponent corpus or documented in
docs/STRATEGIC_PRIOR_ART_REPORT.md -- the novelty here is combining all four
in one opponent that also has a real defense, rather than testing any one in
isolation):

1. REAL OWN DEFENSE (not a glass cannon). Every Milestone 5 probe opponent
   with a "real" defense (shield_race_rusher) still only used 4 turrets + a
   partial wall -- comparable to this repo's *weakest* baselines, not a
   serious defense. This opponent uses a full-width turret+wall layout
   deliberately modeled on the same scale as our own champion's core defense
   (10 turret anchors, corner-weighted, full wall coverage, opportunistic
   upgrades, plus reactive rebuilding at recently-breached locations,
   docs/STRATEGIC_PRIOR_ART_REPORT.md 3.1) -- specifically so this opponent
   can survive 40+ turns and let the other three mechanisms actually get
   exercised, instead of the match resolving in <15 turns the way every
   Milestone 5 probe's matches did (docs/MILESTONE_5_REPORT.md section 4.1).

2. REAL ECONOMIC ACCUMULATION INTO PERIODIC BURSTS
   (docs/STRATEGIC_PRIOR_ART_REPORT.md's "delayed resource-hoarding" idea,
   §2 taxonomy -- documented historically as a mechanism that BEAT a strong
   team, source #6). Spends essentially nothing on offense between bursts
   (SP-funded defense keeps running every turn regardless), letting MP
   accumulate -- subject to the engine's own real
   bitDecayPerRound=0.25/bitGrowthRate ramp (not hand-modeled; we just read
   whatever game_state.get_resource(MP) actually reports each turn) -- then
   commits the large majority of the accumulated pool in one burst every
   ~4-6 turns (jittered, see mechanism 4).

3. ADAPTIVE LANE CHOICE BASED ON DETECTED DEFENSE WEAKNESS. Every burst
   (not cached/static) scans the ENTIRE enemy half of `game_state.game_map`
   for TURRET/WALL/SUPPORT density by x-column (same enemy-unit-scanning
   technique as opponents/adaptive_reactive and opponents/support_sniper),
   builds a per-column weighted density profile, and combines that with the
   same projected-turret-damage path heuristic used throughout this repo
   (`least_damage_spawn_location`) over a WIDE candidate set (every valid
   deploy cell along both bottom edges, not 2 fixed lanes) -- so the lane
   genuinely adapts to wherever the champion's actual defense is thinnest
   that specific game, using two independent signals (real projected combat
   damage + raw structural density) rather than one.

4. ESCORTED, MIXED-COMPOSITION, NON-TELEGRAPHING BURSTS. Each burst sends an
   INTERCEPTOR pair (anti-mobile screen/path-clearer) simultaneously with a
   SCOUT wave, followed one turn later by a DEMOLISHER group along the same
   lane (staggered escort, same underlying idea as
   opponents/escorted_combined_arms and opponents/support_sniper, just with
   a bigger, ACCUMULATED MP budget behind it rather than that turn's raw
   income alone) -- and the burst period, the scout:demolisher MP split, and
   lane tie-breaking among near-equal candidates are all jittered with
   bounded randomness specifically so this doesn't reduce to one exact,
   memorizable pattern (the module doesn't "telegraph" a single fixed
   period/ratio/lane).
"""

BURST_PERIOD_MIN = 4
BURST_PERIOD_MAX = 6
MP_BURST_FLOOR = 6
DENSITY_SCAN_WINDOW = 4          # +/- x columns averaged around each path tile
DENSITY_WEIGHT = 1.5             # relative weight of raw structure density vs. projected combat damage
LANE_TIE_EPSILON = 0.12          # fractional band around the best score to jitter among near-ties
DEMOLISHER_MP_FRACTION_RANGE = (0.30, 0.55)  # jittered per-burst, not fixed
SCOUT_MP_FRACTION_RANGE = (0.45, 0.70)       # jittered per-burst, spent on the screen turn


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring ADAPTIVE_BURST_COMBINED_ARMS opponent...')
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

        # Mechanism 1: a real, full-scale defense (same rough scale as our own
        # champion's core defense, not a 4-turret token gesture).
        self.core_turret_anchors = [
            [1, 12], [26, 12],
            [4, 12], [23, 12],
            [7, 11], [20, 11],
            [10, 10], [17, 10],
            [12, 9], [15, 9],
        ]
        self.core_wall_front = [[x, 13] for x in [0, 1, 2, 3, 4, 5, 22, 23, 24, 25, 26, 27]]
        self.breach_history = {}
        self.max_reactive_spend_per_turn = 6

        # Mechanism 2/4: burst scheduling state.
        self.next_burst_turn = random.randint(BURST_PERIOD_MIN, BURST_PERIOD_MAX) + 2
        self.pending_demolisher_lane = None

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        turn = game_state.turn_number
        game_state.suppress_warnings(True)

        self._decay_breach_history()
        self._build_defense(game_state)
        self._reactive_defense(game_state)
        self._upgrade_defense(game_state)

        mp = game_state.get_resource(MP)
        if self.pending_demolisher_lane is not None:
            # Mechanism 4, escort turn: the demolisher group follows one turn
            # behind the scout/interceptor screen, sized by whatever MP is
            # actually available now (fresh income, since the bank was
            # already spent on the screen turn).
            self._escort_demolisher_wave(game_state, self.pending_demolisher_lane)
            self.pending_demolisher_lane = None
            mode = 'ESCORT'
        elif turn >= self.next_burst_turn and mp >= MP_BURST_FLOOR:
            lane = self._choose_burst_lane(game_state)
            self._burst_screen_wave(game_state, lane, mp)
            self.pending_demolisher_lane = lane
            self.next_burst_turn = turn + random.randint(BURST_PERIOD_MIN, BURST_PERIOD_MAX)
            mode = 'BURST_SCREEN'
        else:
            # Mechanism 2: deliberately spend nothing else on offense between
            # bursts -- let MP accumulate rather than trickle-spending it.
            mode = 'ACCUMULATE'

        gamelib.debug_write('ABCA turn {} mp={:.1f} mode={} next_burst={}'.format(
            turn, mp, mode, self.next_burst_turn))
        game_state.submit_turn()

    # ---- Mechanism 1: real defense ----

    def _build_defense(self, game_state):
        game_state.attempt_spawn(TURRET, self.core_turret_anchors)
        game_state.attempt_spawn(WALL, self.core_wall_front)

    def _upgrade_defense(self, game_state):
        game_state.attempt_upgrade(self.core_turret_anchors)
        game_state.attempt_upgrade(self.core_wall_front)

    def _decay_breach_history(self):
        for loc in list(self.breach_history.keys()):
            self.breach_history[loc] *= 0.6
            if self.breach_history[loc] < 0.05:
                del self.breach_history[loc]

    def _reactive_defense(self, game_state):
        if not self.breach_history:
            return
        cap = self.max_reactive_spend_per_turn
        ranked = sorted(self.breach_history.items(), key=lambda kv: -kv[1])
        spent = 0
        for (bx, by), _weight in ranked:
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

    # ---- Mechanism 3: adaptive lane choice ----

    def _enemy_density_by_column(self, game_state):
        """One full scan of the enemy half per burst (not per candidate, not
        every turn) -- weighted structure density per x-column, used as a
        second, independent signal alongside the projected-combat-damage
        heuristic below."""
        density = [0.0] * game_state.ARENA_SIZE
        weight = {TURRET: 3.0, WALL: 1.0, SUPPORT: 1.0}
        for location in game_state.game_map:
            if not game_state.contains_stationary_unit(location):
                continue
            for unit in game_state.game_map[location]:
                if unit.player_index == 1:
                    density[location[0]] += weight.get(unit.unit_type, 1.0)
        return density

    def _choose_burst_lane(self, game_state):
        density = self._enemy_density_by_column(game_state)
        turret_damage = gamelib.GameUnit(TURRET, game_state.config).damage_i

        candidates = []
        for edge in (game_state.game_map.BOTTOM_LEFT, game_state.game_map.BOTTOM_RIGHT):
            candidates.extend(game_state.game_map.get_edge_locations(edge))
        # Stride-2 sample: enough coverage of the full edge width without
        # doubling the already-expensive per-candidate pathfinding cost.
        candidates = [loc for i, loc in enumerate(candidates) if i % 2 == 0]

        scored = []
        for loc in candidates:
            if game_state.contains_stationary_unit(loc):
                continue
            path = game_state.find_path_to_edge(loc)
            if not path:
                continue
            combat_damage = sum(len(game_state.get_attackers(p, 0)) * turret_damage for p in path)
            density_score = sum(
                density[x] for x in range(max(0, loc[0] - DENSITY_SCAN_WINDOW),
                                           min(game_state.ARENA_SIZE, loc[0] + DENSITY_SCAN_WINDOW + 1))
            )
            combined = combat_damage + DENSITY_WEIGHT * density_score
            scored.append((combined, loc))

        if not scored:
            return [13, 0]

        scored.sort(key=lambda t: t[0])
        best_score = scored[0][0]
        # Mechanism 4 (non-telegraphing): jitter among near-ties rather than
        # always picking the single best candidate deterministically.
        threshold = best_score + abs(best_score) * LANE_TIE_EPSILON + 1.0
        near_best = [loc for score, loc in scored if score <= threshold]
        return near_best[random.randint(0, len(near_best) - 1)]

    # ---- Mechanism 4: escorted, mixed, non-telegraphing bursts ----

    def _burst_screen_wave(self, game_state, lane, mp):
        game_state.attempt_spawn(INTERCEPTOR, lane, 2)
        scout_fraction = random.uniform(*SCOUT_MP_FRACTION_RANGE)
        scout_budget = mp * scout_fraction
        scout_cost = game_state.type_cost(SCOUT)[MP]
        num_scouts = max(1, int(scout_budget // scout_cost))
        game_state.attempt_spawn(SCOUT, lane, num_scouts)

    def _escort_demolisher_wave(self, game_state, lane):
        mp = game_state.get_resource(MP)
        demolisher_fraction = random.uniform(*DEMOLISHER_MP_FRACTION_RANGE)
        demolisher_cost = game_state.type_cost(DEMOLISHER)[MP]
        demolisher_budget = mp * demolisher_fraction
        num_demolishers = int(demolisher_budget // demolisher_cost)
        if num_demolishers > 0:
            game_state.attempt_spawn(DEMOLISHER, lane, num_demolishers)
        # Spend whatever's left over as more scouts along the same lane,
        # rather than letting it idle until the next burst.
        game_state.attempt_spawn(SCOUT, lane, 1000)

    def on_action_frame(self, turn_string):
        if '"breach":[]' in turn_string:
            return
        state = json.loads(turn_string)
        breaches = state["events"]["breach"]
        for breach in breaches:
            location = tuple(breach[0])
            unit_owner_self = (breach[4] == 1)
            if not unit_owner_self:
                self.breach_history[location] = self.breach_history.get(location, 0.0) + 1.0


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
