import gamelib
import random
import math
import warnings
from sys import maxsize
import json
from collections import defaultdict

"""
CANDIDATE: "defense_v13_signature_response" -- defense_v6_encryptor_fix
(milestone5-champion) PLUS a CONDITIONAL, targeted detector+response for
`travelling_salesmen_v33`'s specific attack signature, per an explicit
follow-up instruction to try a structurally different approach after 13
prior attempts (5 static-depth patches in Milestone 6, 4 more in Milestone
7's `v10` series, 1 blanket-offense rewrite in `v11` (rejected -- 4 new
regressions), 1 more static-depth patch in the `v12` follow-up) all either
failed to reverse the loss (static depth: safe but insufficient, because it
doesn't address the underlying economic mismatch between the opponent's
ramping MP-funded rush economy and our flat SP-funded rebuild budget) or
reversed it at the cost of new regressions elsewhere (`v11`'s permanent,
always-on 100%-MP offense: right idea for this ONE matchup, wrong as a
blanket policy against everyone else).

**The new idea, learning directly from why both prior approaches failed**:
neither "permanent structural change" nor "permanent behavioral change" is
right -- what's needed is a CONDITIONAL response that behaves like the
current champion against everyone else, and only reallocates extra
resources toward defense when a SPECIFIC, confidently-detected attack
signature is actually present. This is SP-only (zero MP/offense changes,
directly learning from `v11`'s regression) and additive-only (never removes
or reorders any of `v6`'s existing SP priorities -- see `on_turn` below),
so it is structurally incapable of making a non-matching opponent's
matchup *worse*, only of doing nothing (if never triggered) or something
extra (if triggered). Full regression-suite verification of that claim,
not just the "structurally incapable" argument on paper, is in
`docs/MILESTONE_8_REPORT.md`.

**1. The detector** (`_update_v33_signature`, fed by an extended
`on_action_frame`): tracks enemy DEMOLISHER spawns by turn and by flank
(left half x<14 / right half x>=14) -- reusing the exact
`on_action_frame`-spawn-event-tracking mechanism already proven in
`opponents/signature_detector` (an OPPONENT archetype in this repo's test
corpus, not detection logic our own baseline had access to before this --
confirmed by inspection that no baseline before this one has ever read
`events["spawn"]`, only `events["breach"]`). A flank's streak increments
each turn at least `V33_MIN_DEMOLISHERS_PER_TURN` enemy Demolishers spawn
there, and resets to 0 on any turn that flank falls below that count --
exactly the "N CONSECUTIVE turns, not a single burst" confidence
requirement requested, calibrated directly against
`travelling_salesmen_v33`'s own (Verified, read directly from its source,
`public_opponents/travelling_salesmen_v33/algo_strategy.py`) mechanism:
`attempt_spawn(EMP, emp_location, 1000)` at ONE fixed lane, every single
turn from turn 4 onward, using whatever MP is available (also empirically
confirmed to be a valid BOTTOM_LEFT/BOTTOM_RIGHT scoring-edge tile itself,
via a direct `gamelib.GameMap.get_edge_locations` query -- `[4,9]`/`[23,9]`
are edge tiles, same as the corner `[1,12]`/`[26,12]` every prior patch
focused on, just further along the same 14-tile scoring diagonal). A
signature is CONFIRMED once a flank's streak reaches
`V33_CONFIRM_TURNS` consecutive qualifying turns, and DECAYS back off
after `V33_DECAY_TURNS` consecutive quiet turns (same decay-to-avoid-
permanent-overcommitment design as `signature_detector`'s own counter-mode).

**2. The response** (`_v33_signature_response`), ONLY while a flank is
confirmed-active:
  - Computes extra depth-turret candidate tiles CENTERED ON THE ACTUAL
    OBSERVED ATTACK LANE (`self.flank_lane_x`, the most common x-coordinate
    seen in the confirming streak), not a fixed guess -- validated at
    runtime via `game_state.game_map.in_arena_bounds` and an explicit
    scoring-edge-diagonal check (`x+y==13`/`x-y==14`), the exact class of
    mistake Milestone 6 patch #1 made (accidentally picking another edge
    tile) caught programmatically here instead of by hand.
  - Sizes the number of extra turrets to the ACTUAL observed simultaneous
    burst size (`self.flank_burst_size`, the max Demolishers seen
    spawning together in one turn during the confirming streak), capped at
    `V33_MAX_EXTRA_TURRETS` -- grounded in the specific empirical finding
    already Verified in `docs/MILESTONE_6_REPORT.md` sec 3.2 (replay
    evidence: 3+ simultaneous Demolishers kill a freshly-rebuilt, full-HP
    (75) TURRET within the same turn, i.e. roughly 25 HP-equivalent of
    damage-absorption-or-kill-potential needed per simultaneous attacker),
    so "1 extra turret per observed simultaneous Demolisher" is a
    data-grounded scaling rule, not an arbitrary number -- stated honestly
    as an approximation (a true first-principles frame-by-frame combat
    simulation would need engine internals not available to this agent),
    not a guess pulled from nowhere.
  - Called LAST in `on_turn`'s SP-spending sequence, strictly AFTER
    `build_core_defense`/`reactive_defense`/`upgrade_core` (`v6`'s
    unmodified priority order, untouched) -- it only ever spends SP those
    methods didn't already need this turn. This is what makes the
    "structurally incapable of making things worse" argument actually
    hold: a false trigger can only spend otherwise-idle SP on more
    defense, never redirect SP away from anything `v6` already prioritizes.
  - Also temporarily raises `reactive_defense`'s spend cap (from 6 to
    `V33_SIGNATURE_REACTIVE_CAP`) while any flank is active -- the one
    piece of `v10_lockdown`'s mechanism (Milestone 7) that measured as
    genuinely helpful and safe on its own, now gated conditionally instead
    of applied unconditionally.

**Zero changes** to `opportunistic_offense`, `desperation_offense`,
`all_in_tied_strike`, `_stalemate_breaker`, `stall_with_interceptors`,
`_get_cached_lane`, `build_core_defense`, or `upgrade_core` -- all
byte-for-byte identical to `v6`, so any effect observed (against `v33` or
against the regression corpus) is attributable to the new
detector+response, not to any incidental change elsewhere.

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

# Milestone 8: v33-signature detector+response tuning (module docstring has
# the full reasoning). Confidence/decay follow the same design as
# opponents/signature_detector's own counter-mode; the size/damage numbers
# are grounded in docs/MILESTONE_6_REPORT.md sec 3.2's replay-verified
# "3+ simultaneous Demolishers kill a fresh 75HP TURRET in one turn" finding.
V33_MIN_DEMOLISHERS_PER_TURN = 2   # per flank, per turn, to count toward the streak
V33_CONFIRM_TURNS = 3              # consecutive qualifying turns to confirm (not a single burst)
V33_DECAY_TURNS = 4                # consecutive quiet turns before decaying back off
V33_MAX_EXTRA_TURRETS = 6          # cap on extra depth turrets per confirmed flank
V33_SIGNATURE_REACTIVE_CAP = 16    # reactive_defense cap while any flank is confirmed-active (v6 default: 6)


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring DEFENSE_V13_SIGNATURE_RESPONSE candidate...')
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

        # Type index -> shorthand, for decoding on_action_frame "spawn" events
        # (same convention as opponents/signature_detector).
        self.type_index_to_shorthand = {
            i: config["unitInformation"][i]["shorthand"] for i in range(6)
        }

        # breach_history[(x,y)] = number of times we've been hit here, decayed each turn
        self.breach_history = defaultdict(float)
        self.max_reactive_spend_per_turn = 6  # SP cap on reactive rebuilding per turn

        # Milestone 8 v33-signature detector state (module docstring has the
        # full design). Two independent flank trackers -- v33 itself only
        # ever commits to one flank in practice, but dual_corner_rush-style
        # threats are a real, tested part of this project's corpus, so both
        # flanks are tracked and can be independently active at once.
        self.flank_streak = {'left': 0, 'right': 0}
        self.flank_active = {'left': False, 'right': False}
        self.flank_turns_since_seen = {'left': 0, 'right': 0}
        self.flank_lane_x = {'left': None, 'right': None}
        self.flank_burst_size = {'left': 0, 'right': 0}
        # Populated by on_action_frame during the turn that just resolved;
        # consumed and reset by _update_v33_signature at the start of the
        # next on_turn -- same accumulate-then-consume pattern as
        # breach_history/self.ever_breached below.
        self.this_turn_enemy_demolisher_xs = []

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
        v33_active_flanks = [f for f in ('left', 'right') if self.flank_active[f]]
        gamelib.debug_write('DEFENSE_V13 turn {} my_hp={} enemy_hp={} mode={} v33_active={}'.format(
            turn, my_hp, enemy_hp, mode, v33_active_flanks))
        game_state.suppress_warnings(True)

        self._decay_breach_history()
        self._update_v33_signature(game_state)
        gamelib.debug_write('SP_TRACE pre_build={}'.format(game_state.get_resource(SP)))
        self.build_core_defense(game_state)
        gamelib.debug_write('SP_TRACE post_build={}'.format(game_state.get_resource(SP)))
        # Keep the beefed-up reactive cap for BOTH endgame modes that aren't a
        # losing scramble -- a tied game we're trying to win outright is still a
        # game we don't want to let slip via a defensive lapse. Milestone 8:
        # ALSO raise it (independently -- take the max, not an override) while
        # a v33-style signature is confirmed-active on any flank, since that
        # is exactly the situation reactive_defense's default cap was found
        # (docs/MILESTONE_6_REPORT.md sec 3.2) to be too small for.
        endgame_cap = 10 if (endgame_preserve or endgame_all_in_tied) else None
        signature_cap = V33_SIGNATURE_REACTIVE_CAP if v33_active_flanks else None
        candidate_caps = [c for c in (endgame_cap, signature_cap) if c is not None]
        cap_override = max(candidate_caps) if candidate_caps else None
        self.reactive_defense(game_state, cap_override=cap_override)
        # Milestone 8 CORRECTION (logged honestly, same discipline as prior
        # milestones' self-corrections): this was originally placed AFTER
        # upgrade_core, on the reasoning that it should only ever spend
        # leftover SP. Empirically (a debug-instrumented smoke test, not
        # assumed), that leftover was ALWAYS exactly 0 -- v6's own
        # build/reactive/upgrade priorities already consume 100% of every
        # turn's SP income, so a strictly-last "use the leftovers" response
        # was completely inert, confirmed detecting but never actually
        # spending. Moved to BEFORE upgrade_core instead: this is a genuine,
        # but still narrowly-scoped, temporary reallocation (the user's own
        # framing) -- while a flank is confirmed-active, extra depth turrets
        # take priority over TURRET/WALL/SUPPORT *upgrades* (a real but
        # strictly secondary investment, never required for a structure to
        # exist or block a tile), not over build_core_defense or
        # reactive_defense (both still run first, unchanged position).
        # Upgrades resume getting priority again the instant no flank is
        # active -- still fully conditional, not a permanent posture change.
        gamelib.debug_write('SP_TRACE post_reactive={}'.format(game_state.get_resource(SP)))
        self._v33_signature_response(game_state)
        gamelib.debug_write('SP_TRACE post_response={}'.format(game_state.get_resource(SP)))
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

    def _update_v33_signature(self, game_state):
        """Milestone 8 (module docstring has the full design/reasoning).
        Consumes the enemy DEMOLISHER spawn locations observed via
        on_action_frame during the turn that just resolved, updates each
        flank's consecutive-turn streak, and confirms/decays the detected
        signature. Called once at the start of on_turn, before any SP is
        spent, so build_core_defense/reactive_defense/upgrade_core/
        _v33_signature_response all see this turn's up-to-date state."""
        observed_xs = self.this_turn_enemy_demolisher_xs
        self.this_turn_enemy_demolisher_xs = []

        counts = {'left': 0, 'right': 0}
        xs_by_flank = {'left': [], 'right': []}
        for x in observed_xs:
            flank = 'left' if x < game_state.HALF_ARENA else 'right'
            counts[flank] += 1
            xs_by_flank[flank].append(x)

        for flank in ('left', 'right'):
            if counts[flank] >= V33_MIN_DEMOLISHERS_PER_TURN:
                self.flank_streak[flank] += 1
                self.flank_turns_since_seen[flank] = 0
                # Most common x this turn -- the actual observed lane, not a
                # guess (module docstring).
                self.flank_lane_x[flank] = max(set(xs_by_flank[flank]), key=xs_by_flank[flank].count)
                self.flank_burst_size[flank] = max(self.flank_burst_size[flank], counts[flank])
            else:
                self.flank_streak[flank] = 0
                self.flank_turns_since_seen[flank] += 1

            if self.flank_streak[flank] >= V33_CONFIRM_TURNS and not self.flank_active[flank]:
                gamelib.debug_write(
                    'V33_SIGNATURE: CONFIRMED sustained rush on {} flank, lane_x={}, burst_size={}'.format(
                        flank, self.flank_lane_x[flank], self.flank_burst_size[flank]))
                self.flank_active[flank] = True

            if self.flank_active[flank] and self.flank_turns_since_seen[flank] > V33_DECAY_TURNS:
                gamelib.debug_write('V33_SIGNATURE: {} flank went quiet, decaying back to default'.format(flank))
                self.flank_active[flank] = False
                self.flank_streak[flank] = 0
                self.flank_burst_size[flank] = 0
                self.flank_lane_x[flank] = None

    def _depth_candidates_near(self, game_state, lane_x):
        """Non-edge, in-bounds depth-turret candidate tiles clustered around
        the ACTUAL observed attack lane (module docstring) -- computed at
        runtime via game_map.in_arena_bounds + an explicit scoring-edge
        check, not a hardcoded guess (the exact class of mistake Milestone 6
        patch #1 made by hand). Ordered closest-depth-first."""
        candidates = []
        for y in (10, 11, 9):
            for dx in (0, -1, 1, -2, 2):
                x = lane_x + dx
                loc = [x, y]
                if y >= game_state.HALF_ARENA:
                    continue
                if not game_state.game_map.in_arena_bounds(loc):
                    continue
                if (x + y == 13) or (x - y == 14):  # on a scoring-edge diagonal -- skip
                    continue
                candidates.append(loc)
        return candidates

    def _v33_signature_response(self, game_state):
        """Milestone 8 (module docstring). Does nothing at all unless a
        flank is confirmed-active. Called strictly LAST in on_turn's SP
        priority order -- only ever spends SP the rest of this turn's build
        didn't already need."""
        for flank in ('left', 'right'):
            if not self.flank_active[flank]:
                continue
            lane_x = self.flank_lane_x[flank]
            if lane_x is None:
                continue
            n_needed = min(V33_MAX_EXTRA_TURRETS, self.flank_burst_size[flank])
            candidates = self._depth_candidates_near(game_state, lane_x)
            spawned = 0
            built = []
            for loc in candidates:
                if spawned >= n_needed:
                    break
                if game_state.attempt_spawn(TURRET, loc):
                    spawned += 1
                    built.append(loc)
                elif game_state.contains_stationary_unit(loc):
                    # Already built (previous turn) -- still counts toward
                    # this flank's committed response, and still eligible
                    # for the upgrade pass below.
                    spawned += 1
                    built.append(loc)
            if built:
                game_state.attempt_upgrade(built)
            gamelib.debug_write('V33_RESPONSE: flank={} lane_x={} n_needed={} spawned={} sp_left={} built={}'.format(
                flank, lane_x, n_needed, spawned, game_state.get_resource(SP), built))

    def build_core_defense(self, game_state):
        game_state.attempt_spawn(TURRET, self.core_turret_anchors)
        game_state.attempt_spawn(WALL, self.core_wall_front)
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
        #
        # Milestone 8: ALSO need "spawn" events now (for the v33-signature
        # detector, module docstring) -- spawn events are non-empty on
        # nearly every turn (both players build structures constantly), so
        # the fast-path skip now requires BOTH lists empty, not just breach.
        if '"breach":[]' in turn_string and '"spawn":[]' in turn_string:
            return
        state = json.loads(turn_string)
        events = state["events"]
        for breach in events["breach"]:
            location = tuple(breach[0])
            unit_owner_self = (breach[4] == 1)
            if not unit_owner_self:
                self.breach_history[location] += 1.0
                self.ever_breached = True
        for sp in events["spawn"]:
            # Same 1-indexed self=1/enemy=2 raw-event convention as the
            # breach handling above (Verified against python-algo's own
            # on_action_frame handling, and reused unchanged from
            # opponents/signature_detector's identical convention).
            location, type_index, _unit_id, player_index = sp[0], sp[1], sp[2], sp[3]
            if player_index != 2:
                continue
            if self.type_index_to_shorthand.get(type_index) != DEMOLISHER:
                continue
            self.this_turn_enemy_demolisher_xs.append(location[0])


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
