# -*- coding: utf-8 -*-
import random

# 角色技能常量
JINHSI_SKILL_CHANCE = 0.4
CHANGLI_SKILL_CHANCE = 0.65
CAMELLYA_SKILL_CHANCE = 0.5
CARLOTTA_SKILL_CHANCE = 0.28

# 角色ID映射
CHARACTER_NAMES = {
    1: "Jinhsi",
    2: "Changli",
    3: "Calcharo",
    4: "Shorekeeper",
    5: "Camellya",
    6: "Carlotta",
    7: "Roccia",
    8: "Brant",
    9: "Cantarella",
    10: "Zani",
    11: "Cartethya",
    12: "Phoebe"
}


class Character:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.position = 0
        self.stacked_on_top = []  # 存储堆叠在该角色上方的角色ID
        self.stacked_below = None # 存储该角色下方的角色ID

    def __repr__(self):
        return f"{self.name}(ID:{self.id}) at {self.position}"

    def move(self, steps, game_board, all_characters):
        # print(f"{self.name} rolls {steps}.") # Removed print
        current_pos = self.position
        new_pos = self.position + steps

        # Camellya's skill: move alone and extra steps
        if self.name == "Camellya" and random.random() < CAMELLYA_SKILL_CHANCE:
            extra_steps_camellya = 0
            if current_pos in game_board:
                for char_id_in_cell in game_board[current_pos]:
                    if char_id_in_cell != self.id:
                        extra_steps_camellya += 1
            new_pos += extra_steps_camellya
            # print(f"Camellya's skill triggers! Extra {extra_steps_camellya} steps. Moves alone.") # Removed print

            # Remove Camellya from old position (if exists)
            if current_pos in game_board and self.id in game_board[current_pos]:
                game_board[current_pos].remove(self.id)
                if not game_board[current_pos]:
                    del game_board[current_pos]

            # Update Camellya's position
            self.position = new_pos
            if new_pos not in game_board:
                game_board[new_pos] = []
            game_board[new_pos].append(self.id)
            # Camellya moves alone, so no need to update stacked characters
            self.stacked_on_top = []
            if self.stacked_below:
                char_below = find_character_by_id(self.stacked_below, all_characters)
                if char_below and self.id in char_below.stacked_on_top:
                    char_below.stacked_on_top.remove(self.id)
            self.stacked_below = None
            # Camellya moves alone, so characters previously on top of her are no longer stacked on her
            for top_char_id in self.stacked_on_top:
                top_char = find_character_by_id(top_char_id, all_characters)
                if top_char:
                    top_char.stacked_below = None # They are now at the bottom of their new (or old if not moved) stack
            self.stacked_on_top = []
            return

        # Calcharo's skill: extra 3 steps if last
        if self.name == "Calcharo":
            min_overall_position = min(c.position for c in all_characters)
            # Calcharo is at the absolute last position and is at the bottom of his stack
            if self.position == min_overall_position and self.stacked_below is None:
                # print(f"Calcharo's skill triggers! Extra 3 steps.") # Removed print
                new_pos += 3

        # Carlotta's skill: move twice
        if self.name == "Carlotta" and random.random() < CARLOTTA_SKILL_CHANCE:
            # print(f"Carlotta's skill triggers! Moves twice.") # Removed print
            self._perform_move_with_stack(steps, game_board, all_characters, find_character_by_id, update_stack_info_for_cell) # Pass helper functions
            # Second move
            # print(f"{self.name} (Carlotta's second move) rolls {steps}.") # Removed print
            self._perform_move_with_stack(steps, game_board, all_characters, find_character_by_id, update_stack_info_for_cell) # Pass helper functions
            return

        self._perform_move_with_stack(steps, game_board, all_characters, find_character_by_id, update_stack_info_for_cell, new_pos_override=new_pos) # Pass helper functions

    def _perform_move_with_stack(self, steps, game_board, all_characters, find_char_func, update_stack_func, new_pos_override=None):
        current_pos = self.position
        target_pos = new_pos_override if new_pos_override is not None else self.position + steps

        # Characters to move together (this character and those stacked on top)
        chars_to_move_ids = [self.id] + self.stacked_on_top[:]
        chars_to_move_objects = [find_char_func(cid, all_characters) for cid in chars_to_move_ids]

        # Detach from character below (if any)
        if self.stacked_below:
            char_below = find_char_func(self.stacked_below, all_characters)
            if char_below:
                char_below.stacked_on_top = [cid for cid in char_below.stacked_on_top if cid not in chars_to_move_ids]

        # Remove all moving characters from their current cell in game_board
        if current_pos in game_board:
            for char_id in chars_to_move_ids:
                if char_id in game_board[current_pos]:
                    game_board[current_pos].remove(char_id)
            if not game_board[current_pos]:
                del game_board[current_pos]

        # Update positions of all moving characters
        for char_obj in chars_to_move_objects:
            if char_obj:
                char_obj.position = target_pos
                char_obj.stacked_below = None # Reset, will be set if lands on someone

        # Add to new cell and handle stacking
        if target_pos not in game_board:
            game_board[target_pos] = []

        # If new cell is not empty, stack on top of existing characters
        if game_board[target_pos]:
            bottom_char_in_new_cell_id = game_board[target_pos][-1] # Last one is the top of the existing stack
            bottom_char_in_new_cell = find_char_func(bottom_char_in_new_cell_id, all_characters)
            if bottom_char_in_new_cell:
                bottom_char_in_new_cell.stacked_on_top.extend(chars_to_move_ids)
                self.stacked_below = bottom_char_in_new_cell_id
                # Update stacked_below for other moved characters in the stack
                for i in range(1, len(chars_to_move_objects)):
                    if chars_to_move_objects[i]: # Check if object exists
                        chars_to_move_objects[i].stacked_below = chars_to_move_objects[i-1].id

        game_board[target_pos].extend(chars_to_move_ids) # Add moving characters to the new cell

        # Jinhsi's skill is now handled at the end of the round in game_simulation.py

        # Re-evaluate stacking for the entire cell after all moves
        update_stack_func(target_pos, game_board, all_characters)
        if current_pos != target_pos and current_pos in game_board:
             update_stack_func(current_pos, game_board, all_characters)

# Helper functions that were previously global, now might be needed by Character class or remain in game_simulation
# For now, let's assume they are passed or Character class is modified to not directly call them if they remain global in game_simulation.py

def find_character_by_id(char_id, characters_list):
    for char in characters_list:
        if char.id == char_id:
            return char
    return None

def update_stack_info_for_cell(position, game_board, all_characters):
    if position not in game_board or not game_board[position]:
        return

    cell_char_ids = game_board[position]
    for i, char_id in enumerate(cell_char_ids):
        char_obj = find_character_by_id(char_id, all_characters)
        if not char_obj: continue

        char_obj.stacked_on_top = cell_char_ids[i+1:]
        char_obj.stacked_below = cell_char_ids[i-1] if i > 0 else None