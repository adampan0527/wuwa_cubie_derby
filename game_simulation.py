# -*- coding: utf-8 -*-
import random
from character import (CHARACTER_NAMES, JINHSI_SKILL_CHANCE, CHANGLI_SKILL_CHANCE, 
                       CAMELLYA_SKILL_CHANCE, CARLOTTA_SKILL_CHANCE, Character, 
                       find_character_by_id, update_stack_info_for_cell)

def roll_dice(character_name):
    if character_name == "Shorekeeper":
        return random.choice([2, 3])
    return random.randint(1, 3)

def game_simulation():
    print("欢迎来到 Wuthering Waves 团子赛跑模拟器!\n")

    # 获取重复模拟次数
    while True:
        try:
            num_simulations_input = input("请输入重复模拟次数 (至少为1): ")
            num_simulations = int(num_simulations_input)
            if num_simulations <= 0:
                print("重复模拟次数必须大于0，请重新输入。")
                continue
            break
        except ValueError:
            print("输入无效，请输入一个整数。")

    # --- 让我手动填写参与的角色 --- (User customization section)
    # 请在此处输入参与角色的数字编号，用逗号分隔，例如: 1,2,3
    # 可用角色编号及其对应名称:
    # 1: Jinhsi, 2: Changli, 3: Calcharo, 4: Shorekeeper, 5: Camellya, 6: Carlotta
    # 7: Roccia, 8: Brant, 9: Cantarella, 10: Zani, 11: Cartethya, 12: Phoebe
    # -----------------------------------
    while True:
        try:
            player_input_ids_str = input("请输入参与角色的数字编号 (例如 1,2,5): ")
            participating_character_ids = [int(id_str.strip()) for id_str in player_input_ids_str.split(',')]
            if not participating_character_ids:
                print("未选择任何角色，请至少选择一个角色。")
                continue
            valid_ids = True
            for char_id in participating_character_ids:
                if char_id not in CHARACTER_NAMES:
                    print(f"错误：角色编号 {char_id} 无效。可用编号为: {list(CHARACTER_NAMES.keys())}")
                    valid_ids = False
                    break
            if valid_ids:
                break
        except ValueError:
            print("输入格式错误，请输入数字编号并用逗号分隔。")

    # 设置总里程
    total_mileage = 23
    # max_rounds = 0 # 无回合限制 (Implicitly handled by game_ended logic)
    print(f"游戏总里程设置为: {total_mileage} 步，无回合数限制。")

    ranking_stats = {}
    # 初始化排名统计字典
    for i in range(1, len(participating_character_ids) + 1):
        ranking_stats[i] = {name: 0 for id, name in CHARACTER_NAMES.items() if id in participating_character_ids}

    for sim_num in range(num_simulations):
        characters = [Character(id, CHARACTER_NAMES[id]) for id in participating_character_ids]
        game_board = {0: participating_character_ids[:]}
        for char in characters:
            char.position = 0 # Initialize all at position 0
        update_stack_info_for_cell(0, game_board, characters)

        round_num = 1
        game_ended = False
        turn_order = [] # Will be set at the start of each round
        changli_effect_pending_from_last_round = {} # Stores if Changli's skill triggered last round

        # 主游戏循环
        while not game_ended:
            # 每个轮次开始时，随机重置角色的行动顺序，除非长离技能生效
            if round_num == 1 or not changli_effect_pending_from_last_round:
                turn_order = random.sample(characters, len(characters))
            else:
                # Apply Changli's effect from previous round
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

                # Changli's skill check
                if current_char.name == "Changli" and current_char.stacked_below:
                    if random.random() < CHANGLI_SKILL_CHANCE:
                        changli_effect_this_round[current_char.id] = True

                # 里程胜利条件检查
                if total_mileage != 0 and current_char.position >= total_mileage:
                    game_ended = True
                    break # Exit inner for-loop (character turns)

            if game_ended:
                break # Exit while-loop (rounds)
            
            changli_effect_pending_from_last_round = changli_effect_this_round # Carry over to next round
            round_num += 1

        # 单次模拟结束后的排名统计
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

    # 所有模拟结束后的总结
    print("\n--- 所有模拟完成 ---")
    print("\n--- 最终排名统计 --- (名次: {角色: 次数})")
    final_display_stats = {}
    for rank, char_counts in ranking_stats.items():
        filtered_counts = {char_name: count for char_name, count in char_counts.items() if count > 0}
        if filtered_counts:
            final_display_stats[rank] = filtered_counts
    
    for rank, char_counts in sorted(final_display_stats.items()):
        print(f"第 {rank} 名: {char_counts}")

    print("\n感谢游玩!")

if __name__ == "__main__":
    game_simulation()