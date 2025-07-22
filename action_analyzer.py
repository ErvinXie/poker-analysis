#!/usr/bin/env python3
"""
Action Analyzer - 为poker行动添加标签和生成行动线

主要功能:
1. 为每个action添加poker术语标签（open, 3bet, 4bet, donk, etc.）  
2. 生成每个玩家在每手牌中的行动线（X=check, B=bet, F=fold, C=call）

支持的标签:
- open: 首个主动加注行动
- 3bet: 第三次下注/加注
- 4bet: 第四次下注/加注  
- donk: flop上抢攻（不是preflop aggressor）
- cbet: 持续下注
- check-raise: 先check后raise
- limp: 跛入（只call大盲注）
"""

import json
import os
import glob
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class ActionTag:
    """行动标签"""
    tag: str
    description: str
    confidence: float = 1.0  # 标签置信度 (0-1)

class ActionAnalyzer:
    def __init__(self):
        # 行动线符号映射
        self.action_symbols = {
            'check': 'X',
            'bet': 'B', 
            'call': 'C',
            'fold': 'F',
            'raise': 'R',
            'all-in': 'A',
            'blind': ''  # 盲注不计入行动线
        }
        
    def analyze_hand_actions(self, hand: Dict[str, Any]) -> Dict[str, Any]:
        """分析一手牌的所有行动，添加标签和生成行动线"""
        
        # 创建增强版hand数据
        enhanced_hand = hand.copy()
        
        # 1. 为每个action添加标签
        enhanced_hand = self._add_action_tags(enhanced_hand)
        
        # 2. 生成每个玩家的行动线
        enhanced_hand['action_lines'] = self._generate_action_lines(enhanced_hand)
        
        # 3. 分析关键信息
        enhanced_hand['analysis'] = self._analyze_hand_summary(enhanced_hand)
        
        return enhanced_hand
    
    def _add_action_tags(self, hand: Dict[str, Any]) -> Dict[str, Any]:
        """为每个action添加poker术语标签"""
        
        # 跟踪每个阶段的行动状态
        preflop_aggressor = None
        preflop_raise_count = 0
        stage_first_actions = {}  # 每个阶段第一个行动的玩家
        
        # 处理preflop actions
        non_blind_actions = []
        for action in hand['preflop_actions']:
            if action['action'] != 'blind':
                non_blind_actions.append(action)
        
        # 为preflop行动添加标签
        for i, action in enumerate(non_blind_actions):
            tags = []
            
            if action['action'] == 'raise':
                preflop_raise_count += 1
                if preflop_raise_count == 1:
                    tags.append(ActionTag('open', '首次加注开池'))
                    preflop_aggressor = action['player']
                elif preflop_raise_count == 2:
                    tags.append(ActionTag('3bet', '三次下注'))
                elif preflop_raise_count == 3:
                    tags.append(ActionTag('4bet', '四次下注'))
                elif preflop_raise_count >= 4:
                    tags.append(ActionTag(f'{preflop_raise_count + 1}bet', f'{preflop_raise_count + 1}次下注'))
                    
            elif action['action'] == 'call' and i == 0:
                # 第一个行动是call，可能是limp
                if action['amount'] and action['amount'] <= 100:  # 假设大盲注通常不超过100
                    tags.append(ActionTag('limp', '跛入（平跟大盲注）'))
            
            # 添加标签到action
            action['tags'] = [{'tag': tag.tag, 'description': tag.description, 'confidence': tag.confidence} 
                             for tag in tags]
        
        # 处理postflop stages
        for stage in ['flop', 'turn', 'river']:
            stage_actions = hand[f'{stage}_actions']
            if not stage_actions:
                continue
                
            stage_first_actions[stage] = stage_actions[0]['player']
            check_raise_candidates = {}  # 跟踪可能的check-raise
            
            for i, action in enumerate(stage_actions):
                tags = []
                
                if action['action'] == 'bet':
                    if i == 0:
                        # 第一个行动是bet
                        if action['player'] == preflop_aggressor:
                            tags.append(ActionTag('cbet', '持续下注'))
                        else:
                            tags.append(ActionTag('donk', '抢攻下注'))
                    else:
                        # 检查是否是check-raise的第二部分
                        if action['player'] in check_raise_candidates:
                            tags.append(ActionTag('check-raise', '过牌加注'))
                            del check_raise_candidates[action['player']]
                
                elif action['action'] == 'raise':
                    # 检查是否是check-raise
                    if action['player'] in check_raise_candidates:
                        tags.append(ActionTag('check-raise', '过牌加注'))
                        del check_raise_candidates[action['player']]
                
                elif action['action'] == 'check':
                    # 标记为check-raise候选
                    check_raise_candidates[action['player']] = i
                
                # 添加标签到action
                action['tags'] = [{'tag': tag.tag, 'description': tag.description, 'confidence': tag.confidence} 
                                 for tag in tags]
        
        return hand
    
    def _generate_action_lines(self, hand: Dict[str, Any]) -> Dict[str, str]:
        """为每个玩家生成行动线"""
        
        action_lines = {}
        
        # 获取所有参与的玩家
        all_players = set()
        for stage in ['preflop', 'flop', 'turn', 'river']:
            for action in hand[f'{stage}_actions']:
                if action['action'] != 'blind':  # 排除盲注
                    all_players.add(action['player'])
        
        # 为每个玩家构建行动线
        for player in all_players:
            line_parts = []
            
            for stage in ['preflop', 'flop', 'turn', 'river']:
                stage_actions = hand[f'{stage}_actions']
                player_actions = [a for a in stage_actions if a['player'] == player and a['action'] != 'blind']
                
                if player_actions:
                    # 将该阶段的行动转换为符号
                    stage_symbols = []
                    for action in player_actions:
                        symbol = self.action_symbols.get(action['action'], '?')
                        if symbol:  # 排除空符号（如盲注）
                            stage_symbols.append(symbol)
                    
                    if stage_symbols:
                        line_parts.append(''.join(stage_symbols))
                elif stage_actions:  # 该阶段有行动但玩家没参与，可能已fold
                    # 检查玩家是否在前面阶段fold了
                    folded = False
                    for prev_stage in ['preflop', 'flop', 'turn', 'river']:
                        if prev_stage == stage:
                            break
                        prev_actions = [a for a in hand[f'{prev_stage}_actions'] 
                                      if a['player'] == player and a['action'] == 'fold']
                        if prev_actions:
                            folded = True
                            break
                    
                    if not folded and stage_actions:  # 玩家还在牌局中但该阶段没行动
                        continue  # 可能在等待其他玩家行动
            
            action_lines[player] = '/'.join(line_parts) if line_parts else ''
        
        return action_lines
    
    def _analyze_hand_summary(self, hand: Dict[str, Any]) -> Dict[str, Any]:
        """分析手牌的关键信息"""
        
        analysis = {
            'preflop_aggressor': None,
            'preflop_callers': [],
            'postflop_aggressor': None,
            'showdown_players': len(hand.get('showdown', [])),
            'total_pot': hand.get('pot_size', 0),
            'winner': hand.get('winner'),
            'stages_played': []
        }
        
        # 找到preflop aggressor
        for action in hand['preflop_actions']:
            if action['action'] == 'raise' and 'open' in [t['tag'] for t in action.get('tags', [])]:
                analysis['preflop_aggressor'] = action['player']
                break
        
        # 找到preflop callers
        for action in hand['preflop_actions']:
            if action['action'] == 'call':
                analysis['preflop_callers'].append(action['player'])
        
        # 找到postflop aggressor（第一个bet/raise的玩家）
        for stage in ['flop', 'turn', 'river']:
            for action in hand[f'{stage}_actions']:
                if action['action'] in ['bet', 'raise']:
                    analysis['postflop_aggressor'] = action['player']
                    break
            if analysis['postflop_aggressor']:
                break
        
        # 统计进行到哪些阶段
        for stage in ['preflop', 'flop', 'turn', 'river']:
            if hand[f'{stage}_actions']:
                analysis['stages_played'].append(stage)
        
        return analysis

def process_parsed_hands_file(input_file: str, output_file: str = None) -> str:
    """处理一个parsed_hands.json文件，添加标签和行动线"""
    
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"文件不存在: {input_file}")
    
    # 读取原始数据
    with open(input_file, 'r', encoding='utf-8') as f:
        hands = json.load(f)
    
    # 初始化分析器
    analyzer = ActionAnalyzer()
    
    # 分析每手牌
    enhanced_hands = []
    for hand in hands:
        enhanced_hand = analyzer.analyze_hand_actions(hand)
        enhanced_hands.append(enhanced_hand)
    
    # 确定输出文件名
    if output_file is None:
        base_dir = os.path.dirname(input_file)
        output_file = os.path.join(base_dir, 'enhanced_hands.json')
    
    # 保存增强后的数据
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enhanced_hands, f, indent=2, ensure_ascii=False)
    
    return output_file

def process_all_outputs():
    """处理所有outputs目录下的parsed_hands.json文件"""
    
    outputs_dir = 'outputs'
    if not os.path.exists(outputs_dir):
        print("未找到outputs目录")
        return
    
    # 查找所有parsed_hands.json文件
    pattern = os.path.join(outputs_dir, '*', 'parsed_hands.json')
    input_files = glob.glob(pattern)
    
    if not input_files:
        print("未找到任何parsed_hands.json文件")
        return
    
    print(f"找到 {len(input_files)} 个文件待处理:")
    
    processed_files = []
    for input_file in input_files:
        try:
            print(f"\n处理: {input_file}")
            output_file = process_parsed_hands_file(input_file)
            print(f"✅ 生成: {output_file}")
            processed_files.append(output_file)
            
            # 显示简单统计
            with open(output_file, 'r', encoding='utf-8') as f:
                hands = json.load(f)
            
            total_hands = len(hands)
            hands_with_tags = 0
            total_tagged_actions = 0
            
            # 统计含标签的手牌和标签总数
            for hand in hands:
                hand_has_tags = False
                for stage in ['preflop', 'flop', 'turn', 'river']:
                    for action in hand.get(f'{stage}_actions', []):
                        if action.get('tags', []):
                            hand_has_tags = True
                            total_tagged_actions += len(action['tags'])
                
                if hand_has_tags:
                    hands_with_tags += 1
            
            print(f"   - 总手牌数: {total_hands}")
            print(f"   - 含标签手牌: {hands_with_tags}")
            print(f"   - 标签总数: {total_tagged_actions}")
            
        except Exception as e:
            print(f"❌ 处理失败 {input_file}: {e}")
    
    print(f"\n处理完成! 共处理了 {len(processed_files)} 个文件")
    return processed_files

def show_hand_example(enhanced_hands_file: str, hand_number: int = 1):
    """显示一个手牌的分析结果示例"""
    
    with open(enhanced_hands_file, 'r', encoding='utf-8') as f:
        hands = json.load(f)
    
    if not hands:
        print("文件中没有手牌数据")
        return
    
    # 找到指定的手牌
    target_hand = None
    for hand in hands:
        if hand.get('hand_number') == hand_number:
            target_hand = hand
            break
    
    if not target_hand:
        target_hand = hands[0]
        print(f"未找到手牌#{hand_number}，显示第一手牌...")
    
    print(f"\n{'='*60}")
    print(f"手牌 #{target_hand['hand_number']} (ID: {target_hand['hand_id']}) 分析结果")
    print(f"{'='*60}")
    
    print(f"玩家: {', '.join(target_hand['players'])}")
    print(f"庄家: {target_hand['dealer']}")
    
    # 显示行动线
    print(f"\n📊 行动线:")
    action_lines = target_hand.get('action_lines', {})
    for player, line in action_lines.items():
        print(f"  {player}: {line}")
    
    # 显示带标签的关键行动
    print(f"\n🏷️ 标签化行动:")
    for stage in ['preflop', 'flop', 'turn', 'river']:
        stage_actions = target_hand.get(f'{stage}_actions', [])
        tagged_actions = [a for a in stage_actions if a.get('tags', [])]
        
        if tagged_actions:
            print(f"  {stage.capitalize()}:")
            for action in tagged_actions:
                tags_str = ', '.join([t['tag'] for t in action['tags']])
                amount_str = f" ({action['amount']})" if action.get('amount') else ""
                print(f"    {action['player']}: {action['action']}{amount_str} [{tags_str}]")
    
    # 显示分析总结
    analysis = target_hand.get('analysis', {})
    print(f"\n📈 分析总结:")
    print(f"  Preflop Aggressor: {analysis.get('preflop_aggressor', 'N/A')}")
    print(f"  Postflop Aggressor: {analysis.get('postflop_aggressor', 'N/A')}")
    print(f"  Stages Played: {', '.join(analysis.get('stages_played', []))}")
    print(f"  Winner: {analysis.get('winner', 'N/A')}")
    print(f"  Pot Size: {analysis.get('total_pot', 0)}")

def show_tag_statistics(enhanced_hands_file: str):
    """显示标签统计"""
    
    with open(enhanced_hands_file, 'r', encoding='utf-8') as f:
        hands = json.load(f)
    
    tag_counts = {}
    
    # 统计各种标签出现次数
    for hand in hands:
        for stage in ['preflop', 'flop', 'turn', 'river']:
            for action in hand.get(f'{stage}_actions', []):
                for tag in action.get('tags', []):
                    tag_name = tag['tag']
                    tag_counts[tag_name] = tag_counts.get(tag_name, 0) + 1
    
    if tag_counts:
        print(f"\n📊 标签统计 (来自 {os.path.basename(enhanced_hands_file)}):")
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        for tag, count in sorted_tags:
            print(f"  {tag}: {count}次")

def main():
    """主函数 - 处理所有文件并显示示例"""
    
    print("🃏 Action Analyzer - Poker行动标签和行动线分析器")
    print("="*60)
    
    # 处理所有文件
    processed_files = process_all_outputs()
    
    if processed_files:
        # 显示第一个文件的示例
        print(f"\n📝 示例分析结果:")
        show_hand_example(processed_files[0])
        
        # 显示标签统计
        show_tag_statistics(processed_files[0])
        
        print(f"\n💡 使用说明:")
        print(f"- X=Check, B=Bet, C=Call, F=Fold, R=Raise, A=All-in")
        print(f"- 行动线格式: preflop/flop/turn/river")
        print(f"- 标签包括: open, 3bet, 4bet, cbet, donk, check-raise, limp等")
        print(f"\n📁 输出文件:")
        for pf in processed_files:
            print(f"  - {pf}")
        
        print(f"\n🔍 查看特定手牌:")
        print(f"  python3 -c \"from action_analyzer import show_hand_example; show_hand_example('{processed_files[0]}', 手牌编号)\"")
        print(f"\n📈 查看标签统计:")
        print(f"  python3 -c \"from action_analyzer import show_tag_statistics; show_tag_statistics('{processed_files[0]}')\"\"")

if __name__ == "__main__":
    main()