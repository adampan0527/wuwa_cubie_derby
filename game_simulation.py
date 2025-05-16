# -*- coding: utf-8 -*-
import random
from prettytable import PrettyTable # 导入PrettyTable
from character import (CHARACTER_NAMES, JINHSI_SKILL_CHANCE, CHANGLI_SKILL_CHANCE, 
                       CAMELLYA_SKILL_CHANCE, CARLOTTA_SKILL_CHANCE, Character, 
                       find_character_by_id, update_stack_info_for_cell)

def roll_dice(character_name):
    if character_name == "Shorekeeper":
        return random.choice([2, 3])
    if character_name == "Zani":
        return random.choice([1, 3])
    return random.randint(1, 3)

def game_simulation():
    print("Welcome to the Wuthering Waves Cubie Derby Simulator!\n")

    # 获取模拟次数
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

    # --- 选择参赛角色 --- (用户自定义部分)
    print("\n--- Select Participating Characters ---")
    print("Available characters and their IDs:")
    for char_id, char_name in CHARACTER_NAMES.items():
        print(f"{char_id}: {char_name}")
    print("-----------------------------------")
    # 输入参赛角色的数字ID，用逗号分隔，例如：1,2,3
    # 可用角色及其ID：
    # 1: 今汐, 2: 长离, 3: 卡卡罗, 4: 巡岸者, 5: Camellya, 6: Carlotta
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

    # --- 设置参赛角色的初始位置 ---
    initial_positions = {}
    print("\n--- Set Initial Positions (can be negative) ---")
    for char_id in participating_character_ids:
        char_name = CHARACTER_NAMES[char_id]
        while True:
            try:
                pos_input = input(f"Enter initial position for {char_name} (ID: {char_id}): ")
                initial_positions[char_id] = int(pos_input)
                break
            except ValueError:
                print("Invalid input. Please enter an integer for the position.")

    # 设置总里程
    original_total_mileage = 23
    print(f"Original game mileage (before adjustments for negative starts): {original_total_mileage} steps.")

    # 如果存在负数起始位置，则调整位置和里程
    min_initial_position = 0
    if initial_positions:
        min_initial_position = min(initial_positions.values())
    
    position_offset = 0
    if min_initial_position < 0:
        position_offset = abs(min_initial_position)
        print(f"Negative start detected. Adjusting all positions and total mileage by {position_offset}.")

    adjusted_total_mileage = original_total_mileage + position_offset
    print(f"Adjusted total game mileage: {adjusted_total_mileage} steps, with no round limit.")

    ranking_stats = {}
    # 初始化排名统计字典
    for i in range(1, len(participating_character_ids) + 1):
        ranking_stats[i] = {name: 0 for id, name in CHARACTER_NAMES.items() if id in participating_character_ids}

    # --- 模拟前：一次性确定初始角色设置和堆叠顺序 --- 
    initial_characters_by_pos = {}
    for char_id in participating_character_ids:
        adjusted_pos = initial_positions[char_id] + position_offset
        if adjusted_pos not in initial_characters_by_pos:
            initial_characters_by_pos[adjusted_pos] = []
        initial_characters_by_pos[adjusted_pos].append(char_id)

    # 此字典将存储每个起始位置的最终有序角色ID列表
    final_initial_character_order_at_pos = {}

    # 询问是否在第一轮应用初始堆叠
    apply_initial_stack_in_round_one = True # 默认为True
    # 仅当存在多个角色在同一初始位置时才询问
    if any(len(ids) > 1 for ids in initial_characters_by_pos.values()):
        while True:
            apply_stack_input = input("\nApply initial character stacking in the first round? (yes/no, default yes): ").strip().lower()
            if apply_stack_input in ["yes", "y", ""]:
                apply_initial_stack_in_round_one = True
                break
            elif apply_stack_input in ["no", "n"]:
                apply_initial_stack_in_round_one = False
                print("Initial stacking will NOT be applied in the first round. Characters will move individually. Stack order input will be skipped.")
                break
            else:
                print("Invalid input. Please enter 'yes' or 'no'.")

    sorted_initial_positions_for_setup = sorted(initial_characters_by_pos.keys())

    if apply_initial_stack_in_round_one:
        for pos_setup in sorted_initial_positions_for_setup:
            char_ids_at_pos_setup = initial_characters_by_pos[pos_setup]
            
            if len(char_ids_at_pos_setup) > 1:
                print(f"\n--- Specify Stack Order at Position {pos_setup - position_offset} (Adjusted: {pos_setup}) ---")
                print(f"Characters at this position: {[CHARACTER_NAMES[cid] for cid in char_ids_at_pos_setup]}")
                
                ordered_char_ids_for_this_pos = []
                temp_char_ids_for_prompt_setup = list(char_ids_at_pos_setup) # 用于提示的可变副本

                for i in range(len(char_ids_at_pos_setup)):
                    while True:
                        try:
                            remaining_display = [f"{CHARACTER_NAMES[cid]} (ID: {cid})" for cid in temp_char_ids_for_prompt_setup]
                            prompt_msg = f"Enter ID of character for stack level {i+1} (bottom is 1) from remaining: [{', '.join(remaining_display)}]: "
                            chosen_id_str = input(prompt_msg)
                            chosen_id = int(chosen_id_str.strip())
                            if chosen_id in temp_char_ids_for_prompt_setup:
                                ordered_char_ids_for_this_pos.append(chosen_id)
                                temp_char_ids_for_prompt_setup.remove(chosen_id)
                                break
                            else:
                                print("Invalid ID or ID already selected for this position. Please choose from the remaining list.")
                        except ValueError:
                            print("Invalid input. Please enter a numerical ID.")
                final_initial_character_order_at_pos[pos_setup] = ordered_char_ids_for_this_pos
            else:
                # 如果只有一个角色，则无需排序，直接存储
                final_initial_character_order_at_pos[pos_setup] = char_ids_at_pos_setup
    else:
        # 如果不应用初始堆叠，则直接使用 initial_characters_by_pos 作为基础
        # 角色将单独移动，堆叠顺序将在第一轮后确定
        for pos_setup in sorted_initial_positions_for_setup:
            final_initial_character_order_at_pos[pos_setup] = initial_characters_by_pos[pos_setup]
            # 注意：这里的顺序可能不重要，因为它们将单独移动，并且堆叠将在之后更新
            # 但为了保持数据结构一致，我们仍然填充它。

    # --- 模拟循环 --- 
    for sim_num in range(num_simulations):
        characters = []
        game_board = {}

        # 根据预先确定的初始顺序初始化角色和game_board
        for pos_init, ordered_ids_in_cell in final_initial_character_order_at_pos.items():
            game_board[pos_init] = [] # 初始化game_board中的单元格
            for char_id in ordered_ids_in_cell:
                char = Character(char_id, CHARACTER_NAMES[char_id])
                char.position = pos_init
                # 重置每场游戏技能状态
                char.cantarella_skill_used_this_game = False
                char.cartethya_skill_activated_this_game = False # Cartethya: 重置“最后一名”条件是否已触发的标记
                char.cartethya_permanent_bonus_active = False  # Cartethya: 重置永久额外前进效果是否已激活的标记
                char.zani_next_turn_bonus_pending = False
                characters.append(char)
                game_board[pos_init].append(char.id)
        
        # 如果其他地方需要（例如打破平局），则按ID对主“characters”列表进行排序以保持一致性，尽管回合顺序是随机的
        characters.sort(key=lambda c: c.id)

        # 排序和角色对象创建后，更新所有初始位置的堆叠信息
        if apply_initial_stack_in_round_one:
            for pos_val_update in game_board.keys():
                update_stack_info_for_cell(pos_val_update, game_board, characters)
        # else: 如果不应用初始堆叠，则 Character 对象的 stacked_on_top 和 stacked_below 初始为空列表/None

        round_num = 1
        game_ended = False
        turn_order = [] #将在每轮开始时设置
        changli_effect_pending_from_last_round = {} # 存储长离的技能是否在上一轮触发

        # 主游戏循环
        while not game_ended:
            # 每轮开始时，随机化角色回合顺序，除非长离的技能生效
            if round_num == 1 or not changli_effect_pending_from_last_round:
                turn_order = random.sample(characters, len(characters))
            else:
                # 应用上一轮长离的效果
                # 首先，为每个人建立一个随机的回合顺序。
                current_round_turn_order = random.sample(characters, len(characters))
                
                # 然后，如果任何长离的技能处于激活状态，则将其移至末尾 
                # 而不改变其他角色的相对顺序。
                final_turn_order_this_round = []
                changlis_to_move_to_end = []

                for char_obj in current_round_turn_order:
                    if char_obj.id in changli_effect_pending_from_last_round:
                        changlis_to_move_to_end.append(char_obj)
                    else:
                        final_turn_order_this_round.append(char_obj)
                
                # 将触发技能的长离添加到最后
                turn_order = final_turn_order_this_round + changlis_to_move_to_end
            
            changli_effect_this_round = {} # 重置当前回合的触发器

            for current_char in turn_order:
                if not current_char: continue # 在正确的列表管理下不应发生

                steps = roll_dice(current_char.name)
                first_round_move_individually = (round_num == 1 and not apply_initial_stack_in_round_one)
                current_char_index = turn_order.index(current_char) if current_char in turn_order else -1
                current_char.move(steps, game_board, characters, turn_order_for_round=turn_order, current_char_index_in_turn_order=current_char_index, first_round_move_individually=first_round_move_individually)

                # 里程胜利条件检查
                if adjusted_total_mileage != 0 and current_char.position >= adjusted_total_mileage:
                    game_ended = True
                    break # 退出内部for循环（角色回合）

            if game_ended:
                break # 退出while循环（回合）

            # 回合结束技能检查
            # 长离技能：影响下一轮的行动顺序
            changli_effect_this_round_temp = {}
            for char_obj in characters: # 遍历所有角色以检查长离的技能
                if char_obj.name == "Changli" and char_obj.stacked_below: # 长离的条件
                    if random.random() < CHANGLI_SKILL_CHANCE:
                        changli_effect_this_round_temp[char_obj.id] = True
            changli_effect_pending_from_last_round = changli_effect_this_round_temp

            # 今汐技能：移动到堆叠顶部
            for char_obj in characters: # 遍历所有角色以检查今汐的技能
                if char_obj.name == "Jinhsi" and char_obj.stacked_on_top and random.random() < JINHSI_SKILL_CHANCE:
                    # print(f"今汐的技能在回合结束时触发！移动到当前堆叠的顶部。") # 可选打印
                    current_cell_stack = game_board.get(char_obj.position, [])
                    if char_obj.id in current_cell_stack and len(current_cell_stack) > 1:
                        current_cell_stack.remove(char_obj.id)
                        current_cell_stack.append(char_obj.id)
                        game_board[char_obj.position] = current_cell_stack # 更新game_board
                        # 更新今汐的内部堆叠信息以及她下方的角色
                        update_stack_info_for_cell(char_obj.position, game_board, characters)
            
            # 如果第一轮未应用堆叠，则在第一轮结束后更新堆叠信息
            if round_num == 1 and not apply_initial_stack_in_round_one:
                # print("\n--- End of Round 1: Establishing stacking for subsequent rounds ---") # 可选提示
                for pos_val_update in game_board.keys():
                    if game_board.get(pos_val_update): # 确保格子里有角色
                        update_stack_info_for_cell(pos_val_update, game_board, characters)
            
            round_num += 1

        # 单次模拟结束后的排名统计
        def get_stack_order_in_cell(char_obj, game_board_state):
            # 确保char_obj.position是有效键且char_obj.id在列表中
            if char_obj.position in game_board_state and game_board_state[char_obj.position] and char_obj.id in game_board_state[char_obj.position]:
                return game_board_state[char_obj.position].index(char_obj.id)
            return -1 # 表示未找到角色或单元格为空，排名应较低

        sorted_characters_for_ranking = sorted(
            characters, 
            key=lambda c: (c.position, get_stack_order_in_cell(c, game_board)), 
            reverse=True
        )
        
        current_simulation_ranks = {}
        for rank_idx, char_obj in enumerate(sorted_characters_for_ranking):
            actual_rank = rank_idx + 1
            # 根据位置和精确的堆叠顺序检查平局（已由排序键处理）
            # 如果需要更复杂的排名数字分配打破平局规则，则应在此处添加。
            # 目前，排序顺序决定唯一的排名数字，除非位置和堆叠顺序完全相同（对于不同角色而言不太可能）。
            if rank_idx > 0:
                prev_char_obj = sorted_characters_for_ranking[rank_idx-1]
                if char_obj.position == prev_char_obj.position and \
                   get_stack_order_in_cell(char_obj, game_board) == get_stack_order_in_cell(prev_char_obj, game_board):
                    actual_rank = current_simulation_ranks[prev_char_obj.name]
            
            current_simulation_ranks[char_obj.name] = actual_rank
            
            if actual_rank not in ranking_stats:
                 # 如果ranking_stats已为所有可能的排名预先初始化，则理想情况下不应发生此情况
                 # 但是，为安全起见，如果出现新的排名（例如，由于平局导致 > 参与者数量），则进行初始化
                ranking_stats[actual_rank] = {name: 0 for id, name in CHARACTER_NAMES.items() if id in participating_character_ids}

            if char_obj.name in ranking_stats[actual_rank]:
                 ranking_stats[actual_rank][char_obj.name] += 1
            # else: # 这个else意味着角色不在该排名的初始设置中，这是一个问题
                 # ranking_stats[actual_rank][char_obj.name] = 1 # 应预先初始化为0

    # 所有模拟完成后的摘要
    print("\n--- All Simulations Complete ---")
    print("\n--- Final Ranking Statistics ---")

    participating_character_names = [CHARACTER_NAMES[id] for id in participating_character_ids]

    # 使用PrettyTable创建表格
    table = PrettyTable()
    table.field_names = ["Rank"] + participating_character_names

    # 表格内容
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