import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):

    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))
        self.delete_cost = 0
        self.attack_this_turn = False
        self.just_attacked = False
        self.SP_save_constraint = 0
        self.build_state = 0
        self.num_additional_upgraded_supports_placed = 0

        self.mid_pressure_level = 0
        self.last_mid_reinforce_turn = -5
        self.mid_block_established = False

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
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

        self.scored_on_locations = []

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        gamelib.debug_write('Build State: {}'.format(self.build_state))
        game_state.suppress_warnings(True)
        
        self.well_strategy(game_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def well_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """

        self.delete_cost = 0
        self.SP_save_constraint = 0
        
        if (self.attack_this_turn and self.enemy_left_corner_covered(game_state)):
            game_state.attempt_spawn(TURRET, [2, 13])

        if (self.just_attacked):
            game_state.attempt_spawn(TURRET, [[1, 12], [2, 12]])

        self.rebuild_structures(game_state)
        self.delete_low_structures(game_state)

        self.reinforce_middle(game_state)

        if (self.should_prepare_attack(game_state)):
            self.prepare_attack(game_state)

        if (self.attack_this_turn):
            self.attack(game_state)

        self.build(game_state)

        if (self.just_attacked):
            self.just_attacked = False
        elif (self.attack_this_turn):
            self.attack_this_turn = False
            self.just_attacked = True
        elif (self.should_prepare_attack(game_state)):
            self.attack_this_turn = True

    def should_prepare_attack(self, game_state):
        return game_state.get_resource(1, 0) >= 13

    def delete_low_structures(self, game_state):
        for location in game_state.game_map:

            save_amount = 0
            if (self.attack_this_turn):
                save_amount = 2
            elif (self.should_prepare_attack(game_state) and self.enemy_left_corner_covered(game_state)):
                save_amount = 1
            if (self.delete_cost >= game_state.get_resource(0, 0) + 5 - save_amount):
                break
            
            if (game_state.contains_stationary_unit(location)):
                curr_unit = game_state.contains_stationary_unit(location)

                if (curr_unit.unit_type != SUPPORT):
                    if ((not (curr_unit.unit_type == WALL and curr_unit.health == 60)) and (curr_unit.health / curr_unit.max_health) <= 0.50): 
                        self.delete_cost += curr_unit.cost[0]
                    
                        game_state.attempt_remove(location)
    
    def rebuild_structures(self, game_state):
        upgraded_wall_locations = [[27, 13], [0, 13]]
        long_wall_locations_excluding_opening = [[x, 12] for x in range(3, 18)]
        right_reinforcement_locations = [[25, 11], [24, 11], [23, 11], [23, 10], [23, 9]]
        specific_important_locations_late = [[23, 13], [26, 12], [4, 13], [18, 11], [21, 7], [20, 6]]
        specific_important_locations_early = [[26, 12], [18, 11], [21, 7]]
        short_wall_locations = [[x, 12] for x in range(22, 26)]
        right_pillar_locations = [[22, y] for y in range(8, 12)]
        left_pillar_locations = [[19, y] for y in range(5, 12)]
        less_important_locations = [[20, 9], [21, 11], [19, 12]]

        if (self.build_state >= 2):
            game_state.attempt_spawn(WALL, upgraded_wall_locations)
            if (self.build_state >= 3):
                game_state.attempt_upgrade(upgraded_wall_locations)

        game_state.attempt_spawn(TURRET, long_wall_locations_excluding_opening)

        if (not self.attack_this_turn):
            game_state.attempt_spawn(TURRET, [[1, 12], [2, 12]])

        if (self.build_state >= 5):
            game_state.attempt_spawn(TURRET, right_reinforcement_locations)

        if (self.build_state >= 4):
            game_state.attempt_spawn(TURRET, specific_important_locations_late)
        else:
            game_state.attempt_spawn(TURRET, specific_important_locations_early)

        if (self.build_state < 5):
            game_state.attempt_spawn(TURRET, short_wall_locations)
            game_state.attempt_spawn(TURRET, right_pillar_locations)
        else:
            game_state.attempt_spawn(TURRET, [22, 8])

        game_state.attempt_spawn(TURRET, left_pillar_locations)
        
        if (self.build_state >= 6):
            game_state.attempt_upgrade([26, 12])
        if (self.build_state >= 7):
            game_state.attempt_upgrade([25, 12])
        if (self.build_state >= 9):
            game_state.attempt_upgrade([3, 12])
        if (self.build_state >= 10):
            game_state.attempt_upgrade([25, 11])
        if (self.build_state >= 11):
            game_state.attempt_upgrade([22, 11])

        if (self.build_state >= 5):
            game_state.attempt_spawn(TURRET, short_wall_locations)
            game_state.attempt_spawn(TURRET, right_pillar_locations)

        game_state.attempt_spawn(TURRET, less_important_locations)

        if (self.build_state >= 4):
            game_state.attempt_spawn(TURRET, [18, 12])

    def prepare_attack(self, game_state):
        game_state.attempt_remove([2, 12])
        game_state.attempt_remove([1, 12])

        if (self.enemy_left_corner_covered(game_state)):
            self.SP_save_constraint = 4
        else:
            self.SP_save_constraint = 3

    def enemy_left_corner_covered(self, game_state):
        #for x in range(0, 2):
        #    if (not game_state.contains_stationary_unit([x, 14])):
        #        return False
        return True

    def attack(self, game_state):
        if (self.enemy_left_corner_covered(game_state)):
            game_state.attempt_remove([2, 13])

        x = 12
        if (game_state.get_resource(0, 0) >= 8):
            while ((x > 5) and (game_state.attempt_spawn(SUPPORT, [x, 11]) == 0)):
                x -= 1
            if (x != 5):
                game_state.attempt_upgrade([x, 11])

        MP_int = math.floor(game_state.get_resource(1, 0))
        game_state.attempt_spawn(SCOUT, [10, 3], MP_int // 3)
        game_state.attempt_spawn(SCOUT, [14, 0], MP_int - (MP_int // 3))

    def build(self, game_state):
        subtracted_save_constraint = False
        if (game_state.get_resource(0, 0) >= self.SP_save_constraint):
            game_state._GameState__set_resource(SP, 0 - self.SP_save_constraint)
            subtracted_save_constraint = True

        if (self.build_state == 0):
            build_locs = [[x, 12] for x in range(0, 18)] + [[19, 12]] + [[x, 12] for x in range(22, 27)]
            build_locs += [[19, y] for y in range(5, 12)] + [[22, y] for y in range(8, 12)]
            build_locs += [[18, 11], [21, 7], [20, 9], [21, 11]]
            game_state.attempt_spawn(TURRET, build_locs)
            self.build_state = 1
        elif (self.build_state < 2):
            game_state.attempt_spawn(WALL, [[27, 13], [0, 13]])
            left_wall_unit = game_state.contains_stationary_unit([0, 13])
            right_wall_unit = game_state.contains_stationary_unit([27, 13])
            if (left_wall_unit and right_wall_unit):
                self.build_state = 2
            else:
                self.build_state = 1.1
        elif (self.build_state < 3):
            game_state.attempt_upgrade([[27, 13], [0, 13]])
            left_wall_unit = game_state.contains_stationary_unit([0, 13])
            right_wall_unit = game_state.contains_stationary_unit([27, 13])
            if (left_wall_unit and right_wall_unit):
                if (left_wall_unit.upgraded and right_wall_unit.upgraded):
                    self.build_state = 3
                else:
                    self.build_state = 2.1
        elif (self.build_state < 4):
            build_locs = [[23, 13], [20, 6], [4, 13], [18, 12]]
            game_state.attempt_spawn(TURRET, build_locs)
            all_structures_built = True
            for loc in build_locs:
                if (not game_state.contains_stationary_unit(loc)):
                    all_structures_built = False
                    break
            if (all_structures_built):
                self.build_state = 4
            else:
                self.build_state = 3.1
        elif (self.build_state < 5):
            build_locs = [[25, 11], [24, 11], [23, 10], [23, 9], [23, 11]]
            game_state.attempt_spawn(TURRET, build_locs)
            all_structures_built = True
            for loc in build_locs:
                if (not game_state.contains_stationary_unit(loc)):
                    all_structures_built = False
                    break
            if (all_structures_built):
                self.build_state = 5
            else:
                self.build_state = 4.1
        elif (self.build_state < 6):
            game_state.attempt_upgrade([26, 12])
            right_upgraded_turret_unit = game_state.contains_stationary_unit([26, 12])

            if (right_upgraded_turret_unit and right_upgraded_turret_unit.upgraded):
                self.build_state = 6
            else:
                self.build_state = 5.1
        elif (self.build_state < 7):
            game_state.attempt_upgrade([25, 12])
            additional_right_upgraded_turret_unit = game_state.contains_stationary_unit([25, 12])
            if (additional_right_upgraded_turret_unit and additional_right_upgraded_turret_unit.upgraded):
                self.build_state = 7
            else:
                self.build_state = 6.1
        elif (self.build_state < 8):
            if (game_state.get_resource(0, 0) >= 8):
                x = 12
                while ((x > 5) and (game_state.attempt_spawn(SUPPORT, [x, 11]) == 0)):
                    x -= 1
                if (x != 5):
                    self.num_additional_upgraded_supports_placed += game_state.attempt_upgrade([x, 11])
                if (x == 5 or self.num_additional_upgraded_supports_placed == 2):
                    self.build_state = 8
                else:
                    self.build_state = 7.1
        elif (self.build_state < 9):
            game_state.attempt_upgrade([3, 12])
            well_upgraded_turret_unit = game_state.contains_stationary_unit([3, 12])
            if (well_upgraded_turret_unit and well_upgraded_turret_unit.upgraded):
                self.build_state = 9
            else:
                self.build_state = 8.1
        elif (self.build_state < 10):
            game_state.attempt_upgrade([25, 11])
            well_upgraded_turret_unit = game_state.contains_stationary_unit([25, 11])
            if (well_upgraded_turret_unit and well_upgraded_turret_unit.upgraded):
                self.build_state = 10
            else:
                self.build_state = 9.1
        elif (self.build_state < 11):
            game_state.attempt_upgrade([22, 11])
            lower_right_upgraded_turret_unit = game_state.contains_stationary_unit([22, 11])
            if (lower_right_upgraded_turret_unit and lower_right_upgraded_turret_unit.upgraded):
                self.build_state = 11
            else:
                self.build_state = 10.1

        if (subtracted_save_constraint):
            game_state._GameState__set_resource(SP, self.SP_save_constraint)

    def reinforce_middle(self, game_state):
        turn = game_state.turn_number
        enemy_MP = game_state.get_resource(MP, 1)

        mid_breaches = sum(1 for (x, y) in self.scored_on_locations if 11 <= x <= 16)

        pressure_score = 0
        pressure_score += mid_breaches        
        if turn >= 10: pressure_score += 1    
        if enemy_MP >= 15: pressure_score += 1
        if mid_breaches >= 3: pressure_score += 2 

        target_level = min(4, pressure_score)
        if target_level > self.mid_pressure_level:
            self.mid_pressure_level = target_level

        if self.mid_pressure_level == 0 and self.mid_block_established:
            return

        if turn - self.last_mid_reinforce_turn < 2:
            return

        front_plugs = [[12, 12], [13, 12], [14, 12], [15, 12]]
        back_turrets = [[12, 11], [14, 11]]
        back_extra = [[13, 11], [15, 11]]
        deep_turrets = [[13, 10], [14, 10]]
        support_line = [[11, 11], [16, 11]]

        if self.mid_pressure_level >= 1:
            game_state.attempt_spawn(WALL, front_plugs)
            self.mid_block_established = True
        if self.mid_pressure_level >= 2:
            game_state.attempt_spawn(TURRET, back_turrets)
        if self.mid_pressure_level >= 3:
            game_state.attempt_spawn(TURRET, back_extra)
            game_state.attempt_spawn(TURRET, deep_turrets)
            game_state.attempt_upgrade([loc for loc in back_turrets + deep_turrets if game_state.contains_stationary_unit(loc)])
        if self.mid_pressure_level >= 4:
            game_state.attempt_spawn(SUPPORT, support_line)
            game_state.attempt_upgrade([loc for loc in back_extra if game_state.contains_stationary_unit(loc)])

        self.last_mid_reinforce_turn = turn

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))
                if 11 <= location[0] <= 16:
                    self.mid_pressure_level = max(self.mid_pressure_level, 2)


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
