import gamelib
import random
import math
import warnings
from sys import maxsize
import json
from collections import defaultdict

"""
CANDIDATE: "defense_v12_corner_box" -- defense_v6_encryptor_fix (milestone5-champion)
PLUS ONE narrow, bounded, DEPTH-ONLY structural change at the two corner
anchors, per the user's explicit Milestone 7 follow-up instruction: after
`defense_v10_lockdown` (4 sub-iterations) and `defense_v11_econ_offense`
both failed to reverse the `travelling_salesmen_v33` loss -- and
`v11_econ_offense` additionally introduced 4 new regressions specifically
via its OFFENSE-posture changes (docs/MILESTONE_7_REPORT.md sec 3 bisection)
-- this candidate makes ZERO changes to offense/MP spending of any kind.
`opportunistic_offense`, `desperation_offense`, `all_in_tied_strike`,
`_stalemate_breaker`, `stall_with_interceptors`, and `_get_cached_lane` are
all IDENTICAL to `defense_v6_encryptor_fix`, byte-for-byte, specifically so
any effect (positive or negative) observed against ANY opponent can be
attributed cleanly to the one structural change below, not confounded with
an offense change the way every prior patch attempt (Milestone 6's 5, and
`v11_econ_offense`'s Finding 3) was.

THE ONE CHANGE (Verified from `game-configs.json` `unitInformation`, not
assumed): a WALL (`FF`) costs 1 SP for 40 startHealth, upgrades to 120
startHealth for (no override in its `upgrade` dict, so it defaults to) 1
more SP -- 60 HP per total SP spent, fully upgraded. A TURRET (`DF`) costs 2
SP for 75 startHealth and its upgrade grants ZERO additional startHealth
(only attackRange 4.5->3.5 and attackDamageWalker 5.0->16.0) -- 37.5 HP per
SP spent, unchanged by upgrading. WALL is the more HP-efficient structure by
a wide margin; this candidate spends the SAME total SP as `v6` at each
corner but shifts a larger share of it toward WALL, which several prior
Milestone 6 patch attempts already showed helps somewhat (patch #5,
`docs/MILESTONE_6_REPORT.md` sec 4) but never in true isolation from an
offense change, and never combined with a genuine second layer at a
Verified-non-edge tile (`[3,11]`/`[24,11]`, `docs/MILESTONE_6_REPORT.md`
patch #2) AND with the near-corner wall row upgraded to priority-1 (ahead of
the corner TURRET's own upgrade) rather than left at whatever the shared
`upgrade_core` priority order happened to give it. Concretely, added to
`core_wall_front`'s existing coverage:
  - `[2, 12]`/`[25, 12]`: a WALL "shoulder" one tile inland of each corner
    turret along the same row (Verified NOT an edge tile: `2+12=14`/
    `25-12=13`, neither matches the `x+y=13`/`x-y=14` scoring-edge
    diagonals) -- narrows the gap a Demolisher can walk through once the
    corner TURRET dies, without itself being another "instantly re-openable
    scoring tile" the way the Milestone 6 patch #1 mistake was.
  - `[3, 11]`/`[24, 11]`: a genuine second-layer TURRET, reusing the exact
    tile Milestone 6 patch #2 already Verified is both a true non-edge
    depth tile AND within a corner TURRET's attack range (so it isn't dead
    weight sitting out of range) -- kept as a TURRET (not WALL) specifically
    for its DPS contribution, since the WALL-heavy allocation above is
    already covering the "pure blocking" role.
  - Upgrade priority: originally the corner-adjacent WALL tiles were
    upgraded FIRST, ahead of `core_turret_anchors` -- a full regression run
    showed this alone caused 2 new regressions
    (`travelling_salesmen_frumblesnatch`, `travelling_salesmen_adapdef`),
    isolated and fixed by reverting to v6's original upgrade order (see the
    `CORRECTION` comment in `upgrade_core` below for the full honest
    writeup, same discipline as `defense_v11_econ_offense`'s own corrected
    comment). The new corner structures are upgraded in their natural
    place in the priority order, not jumped to the front.
This is intentionally the LAST attempt at a `v33`-specific structural fix
per the user's explicit instruction to stop after one bounded, honest retry
regardless of outcome -- see docs/MILESTONE_7_REPORT.md sec 4 for the result.

--- Original defense_v6_encryptor_fix docstring (SUPPORT/Encryptor fix, unchanged below) ---

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
        gamelib.debug_write('Configuring DEFENSE_V12_CORNER_BOX candidate...')
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
        # Milestone 4 Encryptor fix: moved forward from [[13,3],[14,3]] to
        # [[13,9],[14,9]] -- see build_core_defense/module docstring.
        self.core_support_anchors = [[13, 9], [14, 9]]

        # Milestone 7 corner-box fix (module docstring): WALL shoulders one
        # tile inland of each corner turret (Verified non-edge tiles), plus a
        # genuine second-layer TURRET at the Milestone-6-Verified non-edge
        # depth tile within range of the corner.
        self.corner_wall_shoulders = [[2, 12], [25, 12]]
        self.corner_depth_turrets = [[3, 11], [24, 11]]
        # Upgrade-priority set: the wall tiles directly on/adjacent to the two
        # vulnerable corners, upgraded FIRST (module docstring) -- includes
        # the tip (`[0,13]`/`[27,13]`), the near-corner front row
        # (`[1,13]`/`[26,13]`), and the new shoulders above.
        self.corner_priority_walls = [[0, 13], [1, 13], [2, 12], [27, 13], [26, 13], [25, 12]]

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
        continuing to conserve (prior-art hypothesis #4, docs/GAME_SPEC.md 4.3).

        Milestone 5 fix: this used to hardcode "spawn exactly 2 demolishers,
        dump the rest on scouts" regardless of how much MP was actually
        available. That was already a fairly arbitrary allocation, but the
        corrected config's DEMOLISHER MP cost (3 -> 2) makes it worse: 2
        demolishers is now only 4 MP, a shrinking (and, at any real late-game
        MP total, tiny) fraction of what's on hand, so nearly everything ends
        up as scouts no matter the actual budget. Switched to the same
        fraction-of-current-MP demolisher budget as all_in_tied_strike (same
        "we're spending everything, every remaining turn" intent, so the same
        offensive mix logic applies) -- confirmed via a synthetic on_turn
        probe (mocked GameState, no real match needed since this branch has
        never been observed to trigger in 5 milestones of benchmarking -- see
        docs/MILESTONE_5_REPORT.md) that this now produces the same
        demolisher:scout ratio as all_in_tied_strike for the same MP total,
        instead of an almost-fixed demolisher count."""
        best = self._get_cached_lane(game_state)
        mp = game_state.get_resource(MP)
        demolisher_cost = game_state.type_cost(DEMOLISHER)[MP]
        demolisher_budget = mp * ALL_IN_DEMOLISHER_MP_FRACTION
        num_demolishers = int(demolisher_budget // demolisher_cost)
        if num_demolishers > 0:
            game_state.attempt_spawn(DEMOLISHER, best, num_demolishers)
        game_state.attempt_spawn(SCOUT, best, 1000)

    def _decay_breach_history(self):
        for loc in list(self.breach_history.keys()):
            self.breach_history[loc] *= 0.6
            if self.breach_history[loc] < 0.05:
                del self.breach_history[loc]

    def build_core_defense(self, game_state):
        game_state.attempt_spawn(TURRET, self.core_turret_anchors)
        game_state.attempt_spawn(WALL, self.core_wall_front)
        # Milestone 7 corner-box fix (module docstring): the WALL shoulders +
        # second-layer depth TURRETs are placed right after the existing
        # core, at the same defensive priority as everything else here --
        # this candidate does not reorder anything relative to v6 other than
        # adding these two new placements and the upgrade-priority change
        # below.
        game_state.attempt_spawn(WALL, self.corner_wall_shoulders)
        game_state.attempt_spawn(TURRET, self.corner_depth_turrets)
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
        # CORRECTION (logged honestly rather than silently fixed, same
        # discipline as v11_econ_offense's own corrected comment): this
        # method originally upgraded `corner_priority_walls`/
        # `corner_depth_turrets` FIRST, ahead of `core_turret_anchors` --
        # the stated reasoning was "a 120-HP wall right at the corner buys
        # more survival than a damage upgrade elsewhere does this early."
        # A full regression run (`docs/MILESTONE_7_REPORT.md` sec 4) showed
        # this was a real mistake: it introduced 2 new regressions
        # (`travelling_salesmen_frumblesnatch` 10->0/10,
        # `travelling_salesmen_adapdef` 10->7/10) that a follow-up isolated
        # diagnostic (same section) proved were caused SPECIFICALLY by this
        # reordering, not by the new `corner_wall_shoulders`/
        # `corner_depth_turrets` structures themselves -- reverting ONLY
        # this reorder (restoring the original v6 priority: turret damage
        # upgrade first) fixed both regressions completely (4/4 each,
        # isolated test) while keeping the new structures in place. Upgrade
        # order below is now back to v6's original order; the new corner
        # structures are upgraded in their natural place alongside
        # everything else, not jumped to the front of the queue.
        #
        # Upgrading a TURRET is a big power jump (dmg 5->16) for a marginal SP
        # cost -- prioritize this over raw width once the core anchors are down.
        # NOTE (Milestone 4, Verified from game-configs.json directly): under the
        # corrected config, upgrading a TURRET changes attackRange from 4.5 DOWN
        # to 3.5 -- a real range-for-damage tradeoff, not a strict upgrade, unlike
        # the old config where upgrading increased both. Still worth it here since
        # our anchors are spaced closely enough that the range loss rarely opens a
        # gap (see docs/MILESTONE_4_REPORT.md for the regression numbers), but this
        # is no longer a "free" upgrade the way it was under the old config.
        game_state.attempt_upgrade(self.core_turret_anchors)
        game_state.attempt_upgrade(self.core_wall_front)
        # Milestone 7 corner-box fix: the new corner structures, upgraded
        # right after the original core -- same relative position the
        # `corner_wall_shoulders`/`corner_depth_turrets` tiles would have
        # had if they'd simply been appended to `core_wall_front`/
        # `core_turret_anchors` in the first place.
        game_state.attempt_upgrade(self.corner_priority_walls)
        game_state.attempt_upgrade(self.corner_depth_turrets)
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
