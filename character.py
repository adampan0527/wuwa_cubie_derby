# -*- coding: utf-8 -*-
import random

# 角色技能常量
JINHSI_SKILL_CHANCE = 0.4
CHANGLI_SKILL_CHANCE = 0.65
CAMELLYA_SKILL_CHANCE = 0.5
CARLOTTA_SKILL_CHANCE = 0.28
ROCCIA_SKILL_CHANCE = 1.0 # Roccia: 总是触发（如果条件满足）
BRANT_SKILL_CHANCE = 1.0  # Brant: 总是触发（如果条件满足）
CANTARELLA_SKILL_CHANCE = 1.0 # Cantarella: 总是触发（如果条件满足，每场一次）
ZANI_STACKED_BONUS_CHANCE = 0.4
CARTETHYA_LAST_POS_BONUS_CHANCE = 0.6
PHOEBE_EXTRA_STEP_CHANCE = 0.5

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
        # 新增技能相关属性
        self.cantarella_skill_used_this_game = False
        self.cartethya_skill_activated_this_game = False # 标记Cartethya的“最后一名”条件是否已在本局游戏中触发过一次
        self.cartethya_permanent_bonus_active = False  # 标记Cartethya的永久额外前进效果是否已激活
        self.zani_next_turn_bonus_pending = False

    def __repr__(self):
        return f"{self.name}(ID:{self.id}) at {self.position}"

    def move(self, steps, game_board, all_characters, turn_order_for_round=None, current_char_index_in_turn_order=None, first_round_move_individually=False):
        # print(f"{self.name} 掷骰子 {steps}。") # 已移除打印
        current_pos = self.position
        original_steps = steps # 保存原始骰子点数
        new_pos = self.position + steps

        # Cartethya: 后续回合奖励如果技能已激活
        if self.name == "Cartethya" and self.cartethya_permanent_bonus_active:
            if random.random() < CARTETHYA_LAST_POS_BONUS_CHANCE:
                # print(f"Cartethya技能：后续回合奖励触发！额外前进2格。")
                new_pos += 2

        # Zani 下回合奖励生效
        if self.name == "Zani" and self.zani_next_turn_bonus_pending:
            # print(f"Zani技能：上回合堆叠奖励触发！额外前进2格。")
            new_pos += 2
            self.zani_next_turn_bonus_pending = False # 重置奖励

        # Phoebe技能：50%概率额外前进1格
        if self.name == "Phoebe" and random.random() < PHOEBE_EXTRA_STEP_CHANCE:
            # print(f"Phoebe技能触发！额外前进1格。")
            new_pos += 1

        # Camellya技能：单独移动并获得额外步数 (不受 first_round_move_individually 影响，因为她总是单独移动)
        if self.name == "Camellya" and random.random() < CAMELLYA_SKILL_CHANCE:
            extra_steps_camellya = 0
            if current_pos in game_board:
                for char_id_in_cell in game_board[current_pos]:
                    if char_id_in_cell != self.id:
                        extra_steps_camellya += 1
            new_pos += extra_steps_camellya
            # print(f"Camellya技能触发！额外 {extra_steps_camellya} 步。单独移动。") # 已移除打印

            # 从旧位置移除Camellya（如果存在）
            if current_pos in game_board and self.id in game_board[current_pos]:
                game_board[current_pos].remove(self.id)
                if not game_board[current_pos]:
                    del game_board[current_pos]

            # 更新Camellya的位置
            self.position = new_pos
            if new_pos not in game_board:
                game_board[new_pos] = []
            game_board[new_pos].append(self.id)
            # Camellya单独移动，因此无需更新堆叠角色
            self.stacked_on_top = []
            if self.stacked_below:
                char_below = find_character_by_id(self.stacked_below, all_characters)
                if char_below and self.id in char_below.stacked_on_top:
                    char_below.stacked_on_top.remove(self.id)
            self.stacked_below = None
            # Camellya单独移动，因此之前在她上方的角色不再堆叠在她身上
            for top_char_id in self.stacked_on_top:
                top_char = find_character_by_id(top_char_id, all_characters)
                if top_char:
                    top_char.stacked_below = None # 他们现在位于新（或如果未移动则为旧）堆叠的底部
            self.stacked_on_top = []
            return

        # Brant技能：如果是第一个移动，则额外前进2格
        if self.name == "Brant" and turn_order_for_round and current_char_index_in_turn_order == 0:
            # print(f"Brant技能触发！第一个移动，额外前进2格。")
            new_pos += 2

        # Calcharo技能：如果最后一名，额外移动3步
        if self.name == "Calcharo":
            min_overall_position = min(c.position for c in all_characters)
            # Calcharo处于绝对最后位置并且位于其堆叠的底部 (如果第一轮不堆叠，则 self.stacked_below 总是 None)
            if self.position == min_overall_position and (self.stacked_below is None or first_round_move_individually):
                # print(f"Calcharo技能触发！额外3步。") # 已移除打印
                new_pos += 3

        # Carlotta技能：移动两次
        if self.name == "Carlotta" and random.random() < CARLOTTA_SKILL_CHANCE:
            # print(f"Carlotta技能触发！移动两次。") # 已移除打印
            self._perform_move_with_stack(steps, game_board, all_characters, find_character_by_id, update_stack_info_for_cell, first_round_move_individually=first_round_move_individually) # 传递辅助函数
            # 第二次移动
            # print(f"{self.name} (Carlotta第二次移动) 掷骰子 {steps}。") # 已移除打印
            self._perform_move_with_stack(steps, game_board, all_characters, find_character_by_id, update_stack_info_for_cell, first_round_move_individually=first_round_move_individually) # 传递辅助函数
            return

        self._perform_move_with_stack(original_steps, game_board, all_characters, find_character_by_id, update_stack_info_for_cell, new_pos_override=new_pos, turn_order_for_round=turn_order_for_round, current_char_index_in_turn_order=current_char_index_in_turn_order, first_round_move_individually=first_round_move_individually) # 传递辅助函数

    def _perform_move_with_stack(self, steps, game_board, all_characters, find_char_func, update_stack_func, new_pos_override=None, turn_order_for_round=None, current_char_index_in_turn_order=None, first_round_move_individually=False):
        current_pos = self.position
        target_pos = new_pos_override if new_pos_override is not None else self.position + steps

        # 一起移动的角色（此角色以及堆叠在其上方的角色）
        chars_to_move_ids = [self.id]
        if not first_round_move_individually:
            chars_to_move_ids.extend(self.stacked_on_top[:])
        # else: 如果 first_round_move_individually 为 True, 则只移动当前角色 self.id
        chars_to_move_objects = [find_char_func(cid, all_characters) for cid in chars_to_move_ids]

        # 与下方角色分离（如果有）
        if self.stacked_below and not first_round_move_individually:
            char_below = find_char_func(self.stacked_below, all_characters)
            if char_below:
                char_below.stacked_on_top = [cid for cid in char_below.stacked_on_top if cid not in chars_to_move_ids]

        # 从game_board的当前单元格中移除所有移动中的角色
        if current_pos in game_board:
            for char_id in chars_to_move_ids:
                if char_id in game_board[current_pos]:
                    game_board[current_pos].remove(char_id)
            if not game_board[current_pos]:
                del game_board[current_pos]

        # 更新所有移动中角色的位置
        for char_obj in chars_to_move_objects:
            if char_obj:
                char_obj.position = target_pos
                char_obj.stacked_below = None # 重置，如果落在某人身上则会设置

        # 添加到新单元格并处理堆叠
        if target_pos not in game_board:
            game_board[target_pos] = []

        # 如果新单元格不为空，则堆叠在现有角色之上
        if game_board[target_pos] and not first_round_move_individually:
            bottom_char_in_new_cell_id = game_board[target_pos][-1] # 最后一个是现有堆叠的顶部
            bottom_char_in_new_cell = find_char_func(bottom_char_in_new_cell_id, all_characters)
            if bottom_char_in_new_cell:
                bottom_char_in_new_cell.stacked_on_top.extend(chars_to_move_ids)
                # self (the current character moving) is the first in chars_to_move_objects
                if chars_to_move_objects[0]: # Ensure self exists
                    chars_to_move_objects[0].stacked_below = bottom_char_in_new_cell_id
                
                # 更新堆叠中其他已移动角色的stacked_below (if they moved as a stack)
                for i in range(1, len(chars_to_move_objects)):
                    if chars_to_move_objects[i] and chars_to_move_objects[i-1]: # 检查对象是否存在
                        chars_to_move_objects[i].stacked_below = chars_to_move_objects[i-1].id
        elif game_board[target_pos] and first_round_move_individually:
            # 如果是第一轮单独移动，并且目标格子有其他角色，则当前角色堆叠在最上面
            # 但不改变其他角色的堆叠关系，也不形成新的堆叠（因为是单独移动）
            # 仅在 update_stack_info_for_cell 在回合结束时调用时，才会正式形成堆叠
            pass # 堆叠逻辑将在回合结束时由 update_stack_info_for_cell 处理

        game_board[target_pos].extend(chars_to_move_ids) # 将移动中的角色添加到新单元格

        # Cantarella技能：移动过程中遇到角色时，会和该格子中所有角色堆叠，并在本回合中一起移动，每场比赛最多触发一次
        if self.name == "Cantarella" and not self.cantarella_skill_used_this_game:
            encountered_chars_in_path = False
            # 检查路径上是否有其他角色 (不包括起点和终点，只检查中间的格子)
            # 注意：这是一个简化的检查，假设角色是“跳跃”移动，而不是逐格移动。
            # 如果需要精确的逐格碰撞检测，这里的逻辑会更复杂。
            # 目前，我们检查目标位置在移动前是否有角色。
            if target_pos != current_pos and target_pos in game_board and game_board[target_pos]:
                # 检查目标格子是否是自己移动前所在的格子（不太可能，但以防万一）
                # 并且目标格子里有其他角色
                is_encounter = any(char_id != self.id for char_id in game_board[target_pos])
                if is_encounter:
                    encountered_chars_in_path = True
            
            if encountered_chars_in_path:
                # print(f"Cantarella技能触发！在 {target_pos} 遇到角色，将堆叠并一起移动。")
                self.cantarella_skill_used_this_game = True
                # 将目标格子中的所有角色（除了Cantarella自己，如果她不知何故已经在那里的话）添加到chars_to_move_ids
                # 并且他们需要从旧的堆叠中正确移除
                original_target_cell_chars = list(game_board.get(target_pos, []))
                for char_id_in_target_cell in original_target_cell_chars:
                    if char_id_in_target_cell != self.id and char_id_in_target_cell not in chars_to_move_ids:
                        char_to_add = find_char_func(char_id_in_target_cell, all_characters)
                        if char_to_add:
                            # 从旧位置的game_board中移除 (如果他们是从其他地方来的)
                            if char_to_add.position in game_board and char_to_add.id in game_board[char_to_add.position]:
                                game_board[char_to_add.position].remove(char_to_add.id)
                                if not game_board[char_to_add.position]:
                                    del game_board[char_to_add.position]
                                # 更新旧位置的堆叠
                                update_stack_func(char_to_add.position, game_board, all_characters)

                            # 从他们之前的堆叠关系中移除
                            if char_to_add.stacked_below:
                                char_below_obj = find_char_func(char_to_add.stacked_below, all_characters)
                                if char_below_obj and char_to_add.id in char_below_obj.stacked_on_top:
                                    char_below_obj.stacked_on_top.remove(char_to_add.id)
                            for char_above_id in char_to_add.stacked_on_top:
                                char_above_obj = find_char_func(char_above_id, all_characters)
                                if char_above_obj:
                                    char_above_obj.stacked_below = None # 他们现在是新堆叠的底部（如果Cantarella在他们下面）
                            
                            chars_to_move_ids.append(char_to_add.id)
                            chars_to_move_objects.append(char_to_add)
                            # Cantarella将成为这个新形成堆叠的底部
                            char_to_add.stacked_below = self.id 
                            # Cantarella的stacked_on_top将在之后由update_stack_func更新
                # 清空目标格子，因为所有角色都将随Cantarella移动
                if target_pos in game_board:
                    game_board[target_pos] = [] 
                    if not game_board[target_pos]:
                        del game_board[target_pos]

        # Jinhsi的技能现在在game_simulation.py的回合结束时处理

        # 所有移动结束后重新评估整个单元格的堆叠情况
        # 如果是第一轮且不应用初始堆叠，则不在每次移动后更新堆叠，而是在回合结束时统一更新
        if not first_round_move_individually:
            update_stack_func(target_pos, game_board, all_characters)
            if current_pos != target_pos and current_pos in game_board and game_board[current_pos]: # 确保旧格子还有角色
                 update_stack_func(current_pos, game_board, all_characters)

        # Roccia技能：如果是最后一个移动，则额外前进2格
        if self.name == "Roccia" and turn_order_for_round and current_char_index_in_turn_order == len(turn_order_for_round) - 1:
            # print(f"Roccia技能触发！最后一个移动，额外前进2格。")
            # 这个技能是在完成常规移动后触发的，所以需要再次移动
            # 注意：这可能导致Roccia移动两次。如果意图是修改原始移动，则逻辑需要调整。
            # 假设是完成移动后再额外移动。
            # 从当前位置（target_pos）再移动2格
            roc_current_pos = self.position # 已经是 target_pos
            roc_new_pos = roc_current_pos + 2
            self._perform_move_with_stack(2, game_board, all_characters, find_char_func, update_stack_func, new_pos_override=roc_new_pos, first_round_move_individually=first_round_move_individually)

        # Cartethya技能激活：自身移动结束后，若处于最后一名，则激活永久奖励效果（每场比赛仅一次激活机会）
        if self.name == "Cartethya" and not self.cartethya_skill_activated_this_game:
            is_last = True
            current_cartethya_pos = self.position # 移动后的位置
            for char_obj in all_characters:
                if char_obj.id == self.id: continue # 跳过自己
                if char_obj.position < current_cartethya_pos:
                    is_last = False
                    break
                # 如果位置相同，Cartethya必须是堆叠的底部才算最后
                if char_obj.position == current_cartethya_pos:
                    # 如果Cartethya不是当前格子堆叠的第一个（底部），那她就不是最后
                    if game_board.get(current_cartethya_pos) and game_board[current_cartethya_pos][0] != self.id:
                        is_last = False
                        break
            if is_last:
                # print(f"Cartethya技能激活！处于最后一名，后续回合永久获得额外前进机会。")
                self.cartethya_permanent_bonus_active = True
                self.cartethya_skill_activated_this_game = True # 标记技能已在本局激活过，不再检查激活条件

        # Zani技能：开始移动时，如果处于堆叠状态，下回合有40%概率额外前进2格
        # 这个检查需要在角色实际移动之前，基于移动开始时的状态
        # 我们在移动开始时（move方法顶部）处理生效，在这里设置标记
        if self.name == "Zani" and (self.stacked_on_top or self.stacked_below) and not first_round_move_individually:
            if random.random() < ZANI_STACKED_BONUS_CHANCE:
                # print(f"Zani技能：堆叠状态下移动，下回合可能额外前进。")
                self.zani_next_turn_bonus_pending = True

# 先前是全局的辅助函数，现在可能Character类需要，或者保留在game_simulation中
# 目前，假设它们被传递，或者如果它们在game_simulation.py中保持全局，则修改Character类以不直接调用它们

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