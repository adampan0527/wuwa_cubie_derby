# -*- coding: utf-8 -*-
import random
from prettytable import PrettyTable # Import PrettyTable
from character import (CHARACTER_NAMES, JINHSI_SKILL_CHANCE, CHANGLI_SKILL_CHANCE, 
                       CAMELLYA_SKILL_CHANCE, CARLOTTA_SKILL_CHANCE, Character, 
                       find_character_by_id, update_stack_info_for_cell)

def roll_dice(character_name):
    if character_name == "Shorekeeper":
        return random.choice([2, 3])
    return random.randint(1, 3)

def game_simulation():
    print("Welcome to the Wuthering Waves Cubie Derby Simulator!\n")

    # Get the number of simulations to run
    while True:
        try:
            num_simulations_input = input("Enter the number of simulations to run (at least 1): ")
            num_simulations = int(num_simulations_input)
            if num_simulations <= 0:
                print("Number of simulations must be greater than 0. Please re-enter.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter an integer.")

    # --- Select participating characters --- (User customization section)
    print("\n--- Select Participating Characters ---")
    print("Available characters and their IDs:")
    for char_id, char_name in CHARACTER_NAMES.items():
        print(f"{char_id}: {char_name}")
    print("-----------------------------------")
    # Enter the numerical IDs of the participating characters, separated by commas, e.g.: 1,2,3
    # Available characters and their IDs:
    # 1: Jinhsi, 2: Changli, 3: Calcharo, 4: Shorekeeper, 5: Camellya, 6: Carlotta
    # 7: Roccia, 8: Brant, 9: Cantarella, 10: Zani, 11: Cartethya, 12: Phoebe
    # -----------------------------------
    while True:
        try:
            player_input_ids_str = input("Enter the numerical IDs of the participating characters (e.g., 1,2,5): ")
            participating_character_ids = [int(id_str.strip()) for id_str in player_input_ids_str.split(',')]
            if not participating_character_ids:
                print("No characters selected. Please select at least one character.")
                continue
            valid_ids = True
            for char_id in participating_character_ids:
                if char_id not in CHARACTER_NAMES:
                    print(f"Error: Character ID {char_id} is invalid. Available IDs are: {list(CHARACTER_NAMES.keys())}")
                    valid_ids = False
                    break
            if valid_ids:
                break
        except ValueError:
            print("Invalid input format. Please enter numerical IDs separated by commas.")

    # Set total mileage
    total_mileage = 23
    # max_rounds = 0 # No round limit (Implicitly handled by game_ended logic)
    print(f"Total game mileage set to: {total_mileage} steps, with no round limit.")

    ranking_stats = {}
    # Initialize ranking statistics dictionary
    for i in range(1, len(participating_character_ids) + 1):
        ranking_stats[i] = {name: 0 for id, name in CHARACTER_NAMES.items() if id in participating_character_ids}

    for sim_num in range(num_simulations):
        characters = [Character(id, CHARACTER_NAMES[id]) for id in participating_character_ids]
        game_board = {0: participating_character_ids[:] # Initialize all characters at position 0 on the game board
        }
        for char in characters:
            char.position = 0 # Initialize all at position 0
        update_stack_info_for_cell(0, game_board, characters)

        round_num = 1
        game_ended = False
        turn_order = [] # Will be set at the start of each round
        changli_effect_pending_from_last_round = {} # Stores if Changli's skill triggered last round

        # Main game loop
        while not game_ended:
            # At the start of each round, randomize character turn order, unless Changli's skill is in effect
            if round_num == 1 or not changli_effect_pending_from_last_round:
                turn_order = random.sample(characters, len(characters))
            else:
                # Apply Changli's effect from the previous round
                temp_order_for_changli = []
                changlis_to_move_last_for_changli = []
                # Use the order from the end of the previous round as a base if available, or a fresh sample
                # For simplicity, let's re-sample and then move Changli if the effect is pending
                # This ensures randomness even if Changli's skill is active multiple times
                current_round_base_order = random.sample(characters, len(characters))
                for char_obj in current_round_base_order:
                    if char_obj.id in changli_effect_pending_from_last_round:
                        changlis_to_move_last_for_changli.append(char_obj)
                    else:
                        temp_order_for_changli.append(char_obj)
                turn_order = temp_order_for_changli + changlis_to_move_last_for_changli
            
            changli_effect_this_round = {} # Reset for current round's triggers

            for current_char in turn_order:
                if not current_char: continue # Should not happen with proper list management

                steps = roll_dice(current_char.name)
                current_char.move(steps, game_board, characters)

                # Mileage victory condition check
                if total_mileage != 0 and current_char.position >= total_mileage:
                    game_ended = True
                    break # Exit inner for-loop (character turns)

            if game_ended:
                break # Exit while-loop (rounds)

            # End of round skill checks
            # Changli's skill: Affects next round's turn order
            changli_effect_this_round_temp = {}
            for char_obj in characters: # Iterate through all characters to check for Changli's skill
                if char_obj.name == "Changli" and char_obj.stacked_below: # Changli's condition
                    if random.random() < CHANGLI_SKILL_CHANCE:
                        changli_effect_this_round_temp[char_obj.id] = True
            changli_effect_pending_from_last_round = changli_effect_this_round_temp

            # Jinhsi's skill: Move to top of stack
            for char_obj in characters: # Iterate through all characters to check for Jinhsi's skill
                if char_obj.name == "Jinhsi" and char_obj.stacked_on_top and random.random() < JINHSI_SKILL_CHANCE:
                    # print(f"Jinhsi's skill triggers at end of round! Moves to the top of the current stack.") # Optional print
                    current_cell_stack = game_board.get(char_obj.position, [])
                    if char_obj.id in current_cell_stack and len(current_cell_stack) > 1:
                        current_cell_stack.remove(char_obj.id)
                        current_cell_stack.append(char_obj.id)
                        game_board[char_obj.position] = current_cell_stack # Update game_board
                        # Update Jinhsi's internal stack info and the character below her
                        update_stack_info_for_cell(char_obj.position, game_board, characters)
            
            round_num += 1

        # Ranking statistics after a single simulation ends
        def get_stack_order_in_cell(char_obj, game_board_state):
            # Ensure char_obj.position is a valid key and char_obj.id is in the list
            if char_obj.position in game_board_state and game_board_state[char_obj.position] and char_obj.id in game_board_state[char_obj.position]:
                return game_board_state[char_obj.position].index(char_obj.id)
            return -1 # Indicates character not found or cell empty, should rank lower

        sorted_characters_for_ranking = sorted(
            characters, 
            key=lambda c: (c.position, get_stack_order_in_cell(c, game_board)), 
            reverse=True
        )
        
        current_simulation_ranks = {}
        for rank_idx, char_obj in enumerate(sorted_characters_for_ranking):
            actual_rank = rank_idx + 1
            # Check for ties based on position and exact stack order (already handled by sort key)
            # If a more complex tie-breaking for rank number assignment is needed, it would go here.
            # For now, the sort order determines unique rank numbers unless positions AND stack order are identical (unlikely for different chars).
            if rank_idx > 0:
                prev_char_obj = sorted_characters_for_ranking[rank_idx-1]
                if char_obj.position == prev_char_obj.position and \
                   get_stack_order_in_cell(char_obj, game_board) == get_stack_order_in_cell(prev_char_obj, game_board):
                    actual_rank = current_simulation_ranks[prev_char_obj.name]
            
            current_simulation_ranks[char_obj.name] = actual_rank
            
            if actual_rank not in ranking_stats:
                 # This case should ideally not happen if ranking_stats is pre-initialized for all possible ranks
                 # However, to be safe, initialize if a new rank appears (e.g. > num_participants due to ties)
                ranking_stats[actual_rank] = {name: 0 for id, name in CHARACTER_NAMES.items() if id in participating_character_ids}

            if char_obj.name in ranking_stats[actual_rank]:
                 ranking_stats[actual_rank][char_obj.name] += 1
            # else: # This else implies the character was not in the initial setup for that rank, which is an issue
                 # ranking_stats[actual_rank][char_obj.name] = 1 # Should be pre-initialized to 0

    # Summary after all simulations are complete
    print("\n--- All Simulations Complete ---")
    print("\n--- Final Ranking Statistics ---")

    participating_character_names = [CHARACTER_NAMES[id] for id in participating_character_ids]

    # Create table using PrettyTable
    table = PrettyTable()
    table.field_names = ["Rank"] + participating_character_names

    # Table content
    for rank_num in range(1, len(participating_character_ids) + 1):
        row_data = [f"Rank {rank_num}"]
        for char_name in participating_character_names:
            count = 0
            if rank_num in ranking_stats and char_name in ranking_stats[rank_num]:
                count = ranking_stats[rank_num][char_name]
            
            probability = (count / num_simulations) * 100 if num_simulations > 0 else 0
            row_data.append(f"{count} / {probability:.2f}%")
        table.add_row(row_data)

    print(table)

    print("\nThanks for playing!")

if __name__ == "__main__":
    game_simulation()