import gamelib
import random
import math
import warnings
from sys import maxsize
import json


class AlgoStrategy(gamelib.AlgoCore):
    """
    Main algorithmic strategy class for the C1Games Terminal competition.
    Designed for high performance and agile computation.
    """

    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """
        Initializes the game state, extracts unit constants, and sets up
        tracking variables for attack and defense logic.
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
        
        # -------------------------------------------------------------
        # STATE TRACKING
        # Tracks the game state across turns to implement alternating
        # attacks and reactive defensive deployments.
        # -------------------------------------------------------------
        self.last_attack_side = 'right'  # Start by attacking left first turn
        self.enemy_attacked_left = False # Default assumption
        self.scored_on_locations = []

    def on_turn(self, turn_state):
        """
        Triggered each turn to execute the core game logic.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        game_state.suppress_warnings(True)
        
        # Reset tracker for the frame analysis
        self.scored_on_locations = []
        
        # Execute customized strategy steps
        self.execute_custom_strategy(game_state)
        
        # Always submit your turn once logic is resolved
        game_state.submit_turn()

    def execute_custom_strategy(self, game_state):
        """
        Executes the overall strategic flow broken down into specific
        defensive and offensive steps.
        """
        # STEP 1: Build Defenses 
        # Strategy: Highly Optimized, No Walls, No Turret Upgrades
        self.build_defences(game_state)
        
        # STEP 2: Execute Offense
        # Strategy: Alternating Sides, 5 Scouts, Y <= 10
        self.execute_attack(game_state)

    def build_defences(self, game_state):
        """
        Deploys all defensive structures (Supports and Turrets) according
        to the predefined strategy blueprint.
        """
        # ---------------------------------------------------------------------
        # a) Supports: Initially place at (12-15, 11)
        # Place 4 supports at specific coordinates. Upgrade any 3, then the last.
        # The game engine handles upgrading sequentially based on available SP.
        # ---------------------------------------------------------------------
        support_locations = [[12, 11], [13, 11], [14, 11], [15, 11]]
        game_state.attempt_spawn(SUPPORT, support_locations)
        game_state.attempt_upgrade(support_locations)

        # ---------------------------------------------------------------------
        # b) Turrets: Base Structure
        # ---------------------------------------------------------------------
        base_turrets = [[12, 12], [11, 11], [15, 12], [16, 11]]
        game_state.attempt_spawn(TURRET, base_turrets)

        # ---------------------------------------------------------------------
        # Reactive Turret Phasing
        # Deploy phases conditionally based on where the opponent attacked last.
        # ---------------------------------------------------------------------
        phase_left_turrets = [
            [0, 13], [2, 13], [3, 12],                      # Phase 1
            [4, 13], [5, 13], [4, 12],                      # Phase 2
            [6, 13], [7, 13], [8, 13], [9, 13], [10, 13]    # Phase 3 (Center gaps)
        ]
        
        phase_right_turrets = [
            [25, 13], [27, 13], [24, 12],                   # Phase 1
            [22, 13], [23, 13], [23, 12],                   # Phase 2
            [21, 13], [20, 13], [19, 13], [18, 13], [17, 13]# Phase 3 (Center gaps)
        ]

        # Prioritize defending the side the enemy heavily attacked
        if self.enemy_attacked_left:
            game_state.attempt_spawn(TURRET, phase_left_turrets)
            game_state.attempt_spawn(TURRET, phase_right_turrets) # If points remain
        else:
            game_state.attempt_spawn(TURRET, phase_right_turrets)
            game_state.attempt_spawn(TURRET, phase_left_turrets)  # If points remain

    def execute_attack(self, game_state):
        """
        Deploys offensive units based on available MP. Continually re-evaluates 
        attack vector dynamically for maximum unpredictability.
        """
        # Always attack exclusively in chunks of 5 scouts
        if game_state.get_resource(MP) >= 5:
            
            # Alternate attack side from the prior attack to avoid static algorithm traps
            attack_side = 'left' if self.last_attack_side == 'right' else 'right'
            
            # Formulate spawn options ensuring Y <= 10
            if attack_side == 'left':
                spawn_options = [
                    [12, 1], [6, 7], [11, 2], [10, 3], 
                    [9, 4], [8, 5], [7, 6]
                ]
            else:
                spawn_options = [
                    [15, 1], [21, 7], [16, 2], [17, 3], 
                    [18, 4], [19, 5], [20, 6]
                ]

            # Vet locations to ensure nothing is obstructed by our own defenses
            spawn_options = self.filter_blocked_locations(spawn_options, game_state)
            
            if not spawn_options:
                return  # No valid spawns available

            # Identify the path that minimizes risk profile/damage intake
            best_location = self.least_damage_spawn_location(game_state, spawn_options)
            
            # Spawn exactly 5 scouts
            spawn_success = game_state.attempt_spawn(SCOUT, best_location, 5)
            
            # Register successful assault logic for alternating side check
            if spawn_success > 0:
                self.last_attack_side = attack_side

    def least_damage_spawn_location(self, game_state, location_options):
        """
        Calculates expected structural resistance along all potential paths.
        Optimized to calculate damage efficiently.
        """
        best_loc = location_options[0]
        min_damage = float('inf')
        
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            
            for path_location in path:
                # Fast assessment: Expected damage = number of attackers * 6 (base turret damage)
                attackers = game_state.get_attackers(path_location, 0)
                damage += len(attackers) * 6
            
            if damage < min_damage:
                min_damage = damage
                best_loc = location
                
            # If we find a path with 0 resistance, take it immediately to save compute time
            if min_damage == 0:
                break
                
        return best_loc

    def filter_blocked_locations(self, locations, game_state):
        """
        Evaluates a set of raw locations and strips out any that overlap 
        with existing defensive units.
        """
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        Fast JSON parsing on the live action feed to accurately profile 
        incoming enemy attack vectors.
        Records self.enemy_attacked_left based directly on breach instances 
        or damage receipts.
        """
        state = json.loads(turn_string)
        events = state.get("events", {})
        
        # Check breaches
        breaches = events.get("breach", [])
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            
            if not unit_owner_self:
                if location[0] < 14:
                    self.enemy_attacked_left = True
                else:
                    self.enemy_attacked_left = False
                return  # Exit early to save compute

        # Fallback: check where our units took damage
        damage_events = events.get("damage", [])
        for dmg in damage_events:
            location = dmg[0]
            unit_owner_self = True if dmg[4] == 1 else False
            
            if unit_owner_self:  # If our structures took damage
                if location[0] < 14:
                    self.enemy_attacked_left = True
                else:
                    self.enemy_attacked_left = False
                return  # Exit early to save compute

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()