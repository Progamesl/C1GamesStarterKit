import gamelib
import random
import math
import warnings
from sys import maxsize
import json
from collections import defaultdict

"""
CANDIDATE: "defense_v7_range_leverage" -- defense_v6_encryptor_fix PLUS a rebalanced
core defense that leans on the corrected config's Destructor/TURRET range increase
and Filter/WALL health cut, instead of the old 10-anchor/no-second-layer layout
tuned for the old 2.5-range, 75-HP-wall config (Milestone 4, section 4,
docs/MILESTONE_4_REPORT.md -- "test at least one alternative construction that
reflects the new balance").

Two concrete, Verified-from-config changes from defense_v6_encryptor_fix:
  1. `core_turret_anchors` cut from 10 to 6 (drops the 4 anchors that existed
     mainly to close gaps at the old 2.5 range) -- Verified via game-configs.json
     that base attackRange is now 4.5 (+80%), so the same 6 corner/mid/center
     anchors plausibly cover similar ground with less overlap/redundancy.
  2. The freed SP goes to a `core_wall_second` layer (behind the corners) and to
     WALL upgrades specifically, NOT turret upgrades -- Verified via
     game-configs.json that upgrading a TURRET now trades attackRange 4.5->3.5
     for damage (a real cost with this sparser layout), while upgrading a WALL
     is unambiguously better value now than under the old config (its base HP
     was cut nearly in half, 75->40, so the same ~1.0 SP upgrade cost now buys a
     3x HP multiplier, 40->120, instead of the old 2x, 75->150).

This is a genuine, testable hypothesis, not an assumed improvement -- see
docs/MILESTONE_4_REPORT.md section 4 for the actual regression numbers this was
benchmarked against before any champion decision was made. SUPPORT/Encryptor fix
carried over unchanged from defense_v6_encryptor_fix (see below).

--- defense_v6_encryptor_fix docstring (Encryptor fix, unchanged here) ---

CANDIDATE: "defense_v6_encryptor_fix" -- defense_v4_tiebreak PLUS a corrected-config
SUPPORT/Encryptor fix (Milestone 4, docs/MILESTONE_4_REPORT.md).

Carries over defense_v4_tiebreak's tie-break/all-in-tied-endgame logic UNCHANGED
(see below for that original rationale) -- that logic is about compute-time and
turn-cap tie-break mechanics, which the config correction did not touch (Verified,
docs/GAME_SPEC.md 4.3). What DID change is SUPPORT ("Encryptor"): under the config
all of Milestones 1-3 (and defense_v4_tiebreak's own design) were built against,
SUPPORT had `shieldRange: 0` -- i.e. its shield mechanic was a complete, verified
no-op no matter where you placed it, and its only real effect was
`generatesResource1/2` (a flat per-turn resource generator). Under the corrected
"High School Terminal 2026" config, SUPPORT has NO generatesResource fields at all
(confirmed absent) but a real, working shield: `shieldRange: 2.5` (7 on upgrade),
`shieldPerUnit: 2.0` (4 on upgrade), `shieldBonusPerY: 0.0` (0.3 on upgrade).

Milestone 4 finding (Verified via a purpose-built controlled probe experiment,
experiments/shield_probe/, not assumed from field names -- see
docs/MILESTONE_4_REPORT.md for the full methodology and replay-derived numbers):
  1. SUPPORT shields ONLY mobile units passing within shieldRange at any point
     along their path -- NOT stationary structures. A WALL and a TURRET placed
     directly adjacent to an upgraded SUPPORT for 30 turns showed ZERO health
     change (stayed at exactly base HP the entire game); a SCOUT passing through
     the same SUPPORT's radius gained a Verified, reproducible flat HP bonus.
  2. The bonus exactly matches `shieldPerUnit + shieldBonusPerY * support_y`
     (support's OWN y-coordinate, not the shielded unit's) -- e.g. an upgraded
     SUPPORT at y=8 produced a scout HP bonus of exactly 4.0 + 0.3*8 = 6.4 (15.0
     -> 21.4 HP, a 42% health increase for that scout), matching the formula to
     one decimal place across multiple independent samples.
  3. Multiple SUPPORTs' shields STACK on a unit that passes through more than one
     radius.
  4. `defense_v4_tiebreak`'s old placement, `[[13, 3], [14, 3]]`, was already
     (correctly, if only by a hedge) framed as "for the shield mechanic" rather
     than economy -- but (a) it was a complete no-op under the old config since
     shieldRange was 0 there, and (b) even now that the mechanic is real, y=3 is
     needlessly far back: shieldBonusPerY specifically rewards forward
     placement, and the position is not reliably on-path for the corner attack
     lanes ([3,10]/[24,10]) used elsewhere in this same file's offense logic.
  5. THE FIX: move the SUPPORT pair forward to `[[13, 9], [14, 9]]` -- one row
     behind the `core_turret_anchors` at y=10, i.e. still fully shielded by our
     own front line, not newly exposed -- and actually UPGRADE it once the core
     is stable (previously never upgraded at all). This both raises the
     shieldBonusPerY payout (0.3*9=2.7 vs 0.3*3=0.9) and keeps it squarely on
     the central `[13,0]`/`[14,0]` attack lane our own scouts/demolishers
     already launch from, so our own offense gets measurably tougher units for
     the same MP spend -- see docs/MILESTONE_4_REPORT.md for the regression
     numbers this change was actually tested against.

--- Original defense_v4_tiebreak docstring (tie-break logic, unchanged here) ---

CANDIDATE: "defense_v4_tiebreak" -- defense_v3_lowcompute PLUS a fix for a second,
deeper root cause behind the residual turtle_survivor loss rate (defense_v3_lowcompute
only won 3/16, ~19%, see docs/MILESTONE_2_REPORT.md).

Milestone 3 root-cause finding (Verified via turn-by-turn/frame-by-frame replay
inspection, not just aggregate win/loss -- see docs/MILESTONE_3_REPORT.md):
defense_v3_lowcompute DOES commit real, substantial force against turtle_survivor
throughout the game (confirmed via replay unit-health tracking: several of
turtle_survivor's front-row WALLs were driven from 75 HP down to single digits and
even fully destroyed-then-rebuilt multiple times), so the residual loss is NOT "we
never attack." It IS, however, a genuine mode-transition bug: `ahead = my_health >=
enemy_health` treats an exact TIE as "ahead," which triggers endgame-preserve mode
(all offense suppressed) for the entire turn 81-99 window even when the game is
merely tied, not actually won. Verified directly from replay MP-stat tracking: this
leaves ~55-57 MP sitting completely unspent at turn 99 in every single
defense_v3_lowcompute-vs-turtle_survivor game we checked -- a large, wasted,
completely idle resource, right when it matters most.

The fix: split the old single "ahead" (>=) check into a strict "ahead" (>) and a
new explicit TIED-near-cap mode. Only a strict lead triggers preserve-mode
passivity. An exact tie near the cap instead triggers ALL_IN_TIED_MODE: commit
100% of available MP every remaining turn (not gated by the normal turn-parity/MP-
floor heuristics, since there is nothing left to save MP for once the game is about
to end tied) to a concentrated demolisher+scout strike at the cached lane, on the
theory (directly requested to be tested, not just assumed) that an explicit
"opponent isn't attacking and we're tied near the cap -> commit to a decisive
breach" rule is what was missing, separate from the compute-time work already done
in defense_v3_lowcompute.
"""

ENDGAME_TURN_THRESHOLD = 80
RECOMPUTE_INTERVAL = 12
STALEMATE_CHECK_TURN = 40
STALEMATE_STRIKE_PERIOD = 10
ALL_IN_DEMOLISHER_MP_FRACTION = 0.4  # rest goes to scouts, same $/dmg ratio but faster/more bodies


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring DEFENSE_V7_RANGE_LEVERAGE candidate...')
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

        # Milestone 4 rebalance experiment (docs/MILESTONE_4_REPORT.md section 4):
        # defense_v4_tiebreak/v6's 10-anchor turret line was spaced for the OLD
        # config's 2.5 attackRange, which needed tight overlap to avoid gaps.
        # Under the corrected config, base attackRange is 4.5 (+80%) -- Verified
        # via game-configs.json directly -- so this variant tests a SPARSER,
        # 6-anchor line that leans on the wider range for coverage, freeing SP
        # for wall upgrades instead (see upgrade_core: also Verified via
        # game-configs.json that upgrading a TURRET now costs range, 4.5->3.5,
        # while upgrading a WALL is still a strict, cheap improvement, 40->120 HP
        # for the same ~1.0 SP base cost -- a much better rebalanced trade than
        # before, since WALL startHealth was cut nearly in half, 75->40).
        self.core_turret_anchors = [
            [1, 12], [26, 12],      # corners: highest priority
            [7, 11], [20, 11],
            [13, 10], [14, 10],
        ]
        self.core_wall_front = [[x, 13] for x in [0, 1, 2, 3, 4, 5, 22, 23, 24, 25, 26, 27]]
        # Second wall layer (one row back from core_wall_front) -- cheap
        # (1.0 SP each) given WALL's now-lower base HP, and upgrading it is an
        # even better trade than before (see upgrade_core). Only spans the
        # width behind the corner turret anchors, not the full board, to keep
        # SP spend bounded.
        self.core_wall_second = [[x, 12] for x in [2, 3, 24, 25]]
        # Milestone 4 Encryptor fix: moved forward from [[13,3],[14,3]] to
        # [[13,9],[14,9]] -- see build_core_defense/module docstring.
        self.core_support_anchors = [[13, 9], [14, 9]]

        self._cached_lane = None
        self._cached_lane_turn = -999
        self.ever_breached = False

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        turn = game_state.turn_number

        near_cap = turn > ENDGAME_TURN_THRESHOLD
        my_hp, enemy_hp = game_state.my_health, game_state.enemy_health
        strictly_ahead = my_hp > enemy_hp
        tied = my_hp == enemy_hp
        endgame_preserve = near_cap and strictly_ahead
        endgame_all_in_tied = near_cap and tied
        endgame_desperate = near_cap and not strictly_ahead and not tied

        mode = ('PRESERVE' if endgame_preserve else
                'ALL_IN_TIED' if endgame_all_in_tied else
                'DESPERATE' if endgame_desperate else 'NORMAL')
        gamelib.debug_write('DEFENSE_V6 turn {} my_hp={} enemy_hp={} mode={}'.format(
            turn, my_hp, enemy_hp, mode))
        game_state.suppress_warnings(True)

        self._decay_breach_history()
        self.build_core_defense(game_state)
        # Keep the beefed-up reactive cap for BOTH endgame modes that aren't a
        # losing scramble -- a tied game we're trying to win outright is still a
        # game we don't want to let slip via a defensive lapse.
        self.reactive_defense(game_state, cap_override=(10 if (endgame_preserve or endgame_all_in_tied) else None))
        self.upgrade_core(game_state)

        if endgame_preserve:
            # Lock in a REAL (strict) lead: no offense, spend any remaining MP
            # stalling with interceptors instead (cheap, defensive-only, never
            # leaves our own side of the board).
            self.stall_with_interceptors(game_state, max_spend=3)
        elif endgame_all_in_tied:
            self.all_in_tied_strike(game_state)
        elif endgame_desperate:
            self.desperation_offense(game_state)
        else:
            self.opportunistic_offense(game_state)

        game_state.submit_turn()

    def all_in_tied_strike(self, game_state):
        """Milestone 3 fix: an exact health tie near the turn cap is NOT a secured
        win -- per the Verified tie-break (docs/GAME_SPEC.md 4.3) it's a loss for us
        unless we're strictly faster than the opponent, which turtle-style
        opponents already aren't beating us on. Verified via replay MP tracking
        that the old (>=) "ahead" check let ~55-57 MP sit completely idle by turn
        99 in every observed loss -- there is nothing left to save it for, so
        commit ALL of it, every remaining turn, unconditionally (no turn-parity or
        MP-floor gating -- those exist to pace ourselves through a long game we're
        not in the closing turns of anymore)."""
        best = self._get_cached_lane(game_state)
        mp = game_state.get_resource(MP)
        demolisher_cost = game_state.type_cost(DEMOLISHER)[MP]
        demolisher_budget = mp * ALL_IN_DEMOLISHER_MP_FRACTION
        num_demolishers = int(demolisher_budget // demolisher_cost)
        if num_demolishers > 0:
            game_state.attempt_spawn(DEMOLISHER, best, num_demolishers)
        game_state.attempt_spawn(SCOUT, best, 1000)

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
        game_state.attempt_spawn(WALL, self.core_wall_second)
        # Milestone 4 Encryptor fix (see module docstring + docs/MILESTONE_4_REPORT.md
        # for the probe experiment this is based on): SUPPORT now has a real,
        # Verified shield mechanic under the corrected config. Placed one row
        # BEHIND core_turret_anchors (y=9, vs the anchors' y=10) -- still fully
        # screened by our own front line, not newly exposed to enemy fire -- and
        # squarely on the central [13,0]/[14,0] attack lane, so our own
        # scouts/demolishers reliably pick up the shield right as they launch.
        # Still gated on "core SP exists first," same defensive-priority order
        # as before.
        if game_state.get_resource(SP) > 10:
            game_state.attempt_spawn(SUPPORT, self.core_support_anchors)

    def upgrade_core(self, game_state):
        # Milestone 4 rebalance experiment (docs/MILESTONE_4_REPORT.md section 4):
        # unlike defense_v6_encryptor_fix, this variant deliberately does NOT
        # upgrade TURRETs. Verified from game-configs.json: upgrading now trades
        # attackRange 4.5->3.5 for +11 damage -- with this variant's sparser
        # 6-anchor layout (chosen specifically to lean on the wider BASE range
        # for coverage), giving that range back up is a worse trade than it was
        # for the denser v4/v6 layout. Instead, prioritize WALL upgrades: cheap
        # (~1.0 SP, since WALL's upgrade cost1 is unset and falls back to the
        # base cost) and now a much bigger relative HP swing (40->120, 3x) than
        # under the old config (75->150, 2x) -- a strictly better SP-for-HP
        # trade than before, precisely because WALL's base HP was cut so much.
        game_state.attempt_upgrade(self.core_wall_front)
        game_state.attempt_upgrade(self.core_wall_second)
        # Milestone 4 Encryptor fix: actually upgrade SUPPORT once it exists --
        # defense_v4_tiebreak (and every earlier "defense" family baseline) never
        # did this. Upgrading roughly doubles shieldPerUnit (2.0->4.0) and nearly
        # triples shieldRange (2.5->7), which our own probe experiment confirmed
        # produces a real, substantial HP bonus (docs/MILESTONE_4_REPORT.md).
        # Gated behind turret/wall upgrades (attempt_upgrade only spends SP on
        # units that exist and aren't already upgraded, so this naturally waits
        # its turn in the priority order without extra bookkeeping).
        game_state.attempt_upgrade(self.core_support_anchors)

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
