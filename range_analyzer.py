#!/usr/bin/env python3
"""
Range Analyzer - 玩家范围分析器

主要功能:
1. 分析玩家在不同行动/行动线下实际持有的牌型
2. 基于showdown数据推断玩家的范围
3. 按行动标签和行动线分类统计牌型分布
4. 生成范围分析报告和可视化图表

牌型分类:
- Premium Pairs: AA, KK, QQ, JJ
- Medium Pairs: TT, 99, 88, 77
- Small Pairs: 66, 55, 44, 33, 22
- Strong Aces: AK, AQ, AJ
- Medium Aces: AT, A9, A8, A7
- Weak Aces: A6, A5, A4, A3, A2
- Suited Connectors: KQ, QJ, JT, etc.
- Broadway: High cards T-A
- Others: 其他牌型
"""

import json
import os
import glob
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 使用无GUI后端
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter
import re

class RangeAnalyzer:
    def __init__(self):
        # 存储每个玩家在不同条件下的牌型数据
        self.player_ranges = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        # action_tag -> player -> hand_category -> [hands]
        self.tag_ranges = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        # action_line -> player -> hand_category -> [hands]
        self.line_ranges = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        
    def categorize_hand(self, hole_cards: List[str]) -> str:
        """将底牌分类到不同的牌型类别"""
        if len(hole_cards) != 2:
            return "Unknown"
        
        # 解析牌型
        card1, card2 = hole_cards
        rank1 = self.get_rank_value(card1[0])
        rank2 = self.get_rank_value(card2[0])
        suit1 = card1[1] if len(card1) > 1 else card1[-1]
        suit2 = card2[1] if len(card2) > 1 else card2[-1]
        
        # 确保rank1 >= rank2 用于标准化
        if rank1 < rank2:
            rank1, rank2 = rank2, rank1
        
        is_suited = suit1 == suit2
        is_pair = rank1 == rank2
        
        # 对子分类
        if is_pair:
            if rank1 >= 11:  # JJ+
                return "Premium Pairs"
            elif rank1 >= 7:  # 77-TT
                return "Medium Pairs"
            else:  # 22-66
                return "Small Pairs"
        
        # Ace牌分类
        if rank1 == 14:  # A开头
            if rank2 >= 11:  # AK, AQ, AJ
                return "Strong Aces"
            elif rank2 >= 7:  # A7-AT
                return "Medium Aces"
            else:  # A2-A6
                return "Weak Aces"
        
        # 连牌和高牌
        if rank1 >= 10 and rank2 >= 10:  # Broadway cards
            if abs(rank1 - rank2) <= 3 and is_suited:  # 连牌同花
                return "Suited Connectors"
            elif abs(rank1 - rank2) <= 1:  # 连牌
                return "Broadway"
            else:
                return "Broadway"
        
        # 同花连牌
        if is_suited and abs(rank1 - rank2) <= 3:
            return "Suited Connectors"
        
        # 连牌
        if abs(rank1 - rank2) <= 1:
            return "Connectors"
        
        # 其他
        return "Others"
    
    def get_rank_value(self, rank: str) -> int:
        """获取牌面大小的数值"""
        rank_values = {
            '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 
            'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
        }
        return rank_values.get(rank, 0)
    
    def normalize_hand(self, hole_cards: List[str]) -> str:
        """标准化牌型表示 (如AKo, AKs, 77等)"""
        if len(hole_cards) != 2:
            return "Unknown"
        
        card1, card2 = hole_cards
        rank1 = card1[0]
        rank2 = card2[0]
        suit1 = card1[1] if len(card1) > 1 else card1[-1]
        suit2 = card2[1] if len(card2) > 1 else card2[-1]
        
        # 标准化rank顺序
        rank_order = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        if rank_order.index(rank1) < rank_order.index(rank2):
            rank1, rank2 = rank2, rank1
        
        if rank1 == rank2:
            return f"{rank1}{rank2}"  # 对子
        elif suit1 == suit2:
            return f"{rank1}{rank2}s"  # 同花
        else:
            return f"{rank1}{rank2}o"  # 非同花
    
    def analyze_enhanced_hands_file(self, enhanced_hands_file: str):
        """分析一个enhanced_hands.json文件中的showdown数据"""
        
        with open(enhanced_hands_file, 'r', encoding='utf-8') as f:
            hands = json.load(f)
        
        print(f"Analyzing showdown data from: {os.path.basename(enhanced_hands_file)}")
        
        showdown_count = 0
        
        for hand in hands:
            showdown = hand.get('showdown', [])
            if not showdown:
                continue
                
            showdown_count += 1
            action_lines = hand.get('action_lines', {})
            
            # 分析每个亮牌的玩家
            for show_info in showdown:
                player = show_info.get('player')
                hole_cards = show_info.get('hole_cards', [])
                
                if not player or not hole_cards or len(hole_cards) != 2:
                    continue
                
                # 分类牌型
                hand_category = self.categorize_hand(hole_cards)
                normalized_hand = self.normalize_hand(hole_cards)
                
                # 获取该玩家的行动线
                player_action_line = action_lines.get(player, "Unknown")
                
                # 存储到范围数据中
                self.player_ranges[player][hand_category]['hands'].append({
                    'cards': hole_cards,
                    'normalized': normalized_hand,
                    'action_line': player_action_line,
                    'hand_id': hand.get('hand_id', 'unknown')
                })
                
                # 获取该手牌中玩家的标签行动
                for stage in ['preflop', 'flop', 'turn', 'river']:
                    stage_actions = hand.get(f'{stage}_actions', [])
                    for action in stage_actions:
                        if action.get('player') == player:
                            tags = action.get('tags', [])
                            for tag_info in tags:
                                tag = tag_info.get('tag')
                                if tag:
                                    self.tag_ranges[tag][player][hand_category].append({
                                        'cards': hole_cards,
                                        'normalized': normalized_hand,
                                        'action_line': player_action_line,
                                        'stage': stage,
                                        'action': action.get('action'),
                                        'hand_id': hand.get('hand_id', 'unknown')
                                    })
                
                # 按行动线分类
                self.line_ranges[player_action_line][player][hand_category].append({
                    'cards': hole_cards,
                    'normalized': normalized_hand,
                    'hand_id': hand.get('hand_id', 'unknown')
                })
        
        print(f"Found {showdown_count} hands with showdown data")
    
    def create_player_range_summary(self) -> pd.DataFrame:
        """创建玩家范围总结表"""
        
        data = []
        categories = [
            "Premium Pairs", "Medium Pairs", "Small Pairs",
            "Strong Aces", "Medium Aces", "Weak Aces", 
            "Suited Connectors", "Broadway", "Connectors", "Others"
        ]
        
        for player, ranges in self.player_ranges.items():
            row = {'Player': player}
            total_hands = 0
            
            for category in categories:
                count = len(ranges.get(category, {}).get('hands', []))
                row[category] = count
                total_hands += count
            
            row['Total'] = total_hands
            data.append(row)
        
        df = pd.DataFrame(data)
        return df.sort_values('Total', ascending=False)
    
    def create_tag_range_summary(self, tag: str) -> pd.DataFrame:
        """创建特定标签的范围分析表"""
        
        if tag not in self.tag_ranges:
            return pd.DataFrame()
        
        data = []
        categories = [
            "Premium Pairs", "Medium Pairs", "Small Pairs",
            "Strong Aces", "Medium Aces", "Weak Aces", 
            "Suited Connectors", "Broadway", "Connectors", "Others"
        ]
        
        for player, ranges in self.tag_ranges[tag].items():
            row = {'Player': player}
            total_hands = 0
            
            for category in categories:
                count = len(ranges.get(category, []))
                row[category] = count
                total_hands += count
            
            row['Total'] = total_hands
            if total_hands > 0:  # 只包含有数据的玩家
                data.append(row)
        
        df = pd.DataFrame(data)
        if not df.empty:
            return df.sort_values('Total', ascending=False)
        return df
    
    def create_range_table_image(self, df: pd.DataFrame, title: str, output_path: str):
        """创建范围分析表格图片"""
        
        if df.empty:
            print(f"No data for {title}")
            return
        
        # 计算表格尺寸
        n_rows = len(df)
        n_cols = len(df.columns)
        
        # 创建图片
        fig, ax = plt.subplots(figsize=(max(14, n_cols * 1.0), max(6, n_rows * 0.5)), dpi=300)
        ax.axis('tight')
        ax.axis('off')
        
        # 创建表格
        table = ax.table(cellText=df.values,
                        colLabels=df.columns,
                        cellLoc='center',
                        loc='center',
                        bbox=[0, 0, 1, 1])
        
        # 设置表格样式
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.8)
        
        # 设置表头样式
        for i in range(n_cols):
            table[(0, i)].set_facecolor('#8E24AA')  # 紫色
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # 设置数据单元格样式
        for i in range(1, n_rows + 1):
            for j in range(n_cols):
                cell_value = df.iloc[i-1, j]
                
                # 玩家名称列
                if j == 0:
                    table[(i, j)].set_facecolor('#F3E5F5')  # 浅紫色
                    table[(i, j)].set_text_props(weight='bold')
                # 数值列
                else:
                    try:
                        value = int(cell_value)
                        if value > 0:
                            # 根据数量设置颜色深度
                            alpha = min(1.0, value / 10)  # 调整透明度
                            table[(i, j)].set_facecolor((0.9, 0.8, 1.0, alpha))
                            table[(i, j)].set_text_props(weight='bold')
                        else:
                            table[(i, j)].set_facecolor('#F5F5F5')
                            table[(i, j)].set_text_props(color='gray')
                    except:
                        pass
        
        # 设置标题
        fig.suptitle(title, fontsize=14, fontweight='bold', y=0.95)
        
        # 调整布局
        plt.tight_layout()
        plt.subplots_adjust(top=0.9)
        
        # 保存图片
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"Generated range analysis: {output_path}")
    
    def get_specific_hands_for_tag(self, tag: str, player: str = None) -> List[Dict]:
        """获取特定标签下的具体牌型数据"""
        
        hands_data = []
        
        if tag not in self.tag_ranges:
            return hands_data
        
        players_to_check = [player] if player else self.tag_ranges[tag].keys()
        
        for p in players_to_check:
            if p not in self.tag_ranges[tag]:
                continue
                
            for category, hands in self.tag_ranges[tag][p].items():
                for hand_info in hands:
                    hands_data.append({
                        'player': p,
                        'category': category,
                        'cards': hand_info['cards'],
                        'normalized': hand_info['normalized'],
                        'action_line': hand_info['action_line'],
                        'stage': hand_info['stage'],
                        'action': hand_info['action'],
                        'hand_id': hand_info['hand_id']
                    })
        
        return hands_data
    
    def export_detailed_range_data(self, output_dir: str):
        """导出详细的范围数据"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 导出每个标签的详细数据
        for tag in self.tag_ranges.keys():
            hands_data = self.get_specific_hands_for_tag(tag)
            if hands_data:
                df = pd.DataFrame(hands_data)
                csv_file = os.path.join(output_dir, f"range_detail_{tag}.csv")
                df.to_csv(csv_file, index=False, encoding='utf-8')
                print(f"Exported detailed range data: {csv_file}")
    
    def generate_all_visualizations(self, output_dir: str):
        """生成所有可视化图表"""
        
        print(f"\n🎨 Generating range analysis visualizations...")
        print("-" * 60)
        
        # 生成玩家总体范围分析
        player_summary = self.create_player_range_summary()
        if not player_summary.empty:
            self.create_range_table_image(
                player_summary, 
                "Player Range Analysis - All Showdowns",
                os.path.join(output_dir, "player_range_summary.png")
            )
        
        # 生成每个标签的范围分析
        common_tags = ['open', '3bet', 'cbet', 'check-raise', 'donk']
        
        for tag in common_tags:
            if tag in self.tag_ranges:
                tag_summary = self.create_tag_range_summary(tag)
                if not tag_summary.empty:
                    self.create_range_table_image(
                        tag_summary, 
                        f"Range Analysis - {tag.upper()} Action",
                        os.path.join(output_dir, f"range_{tag}.png")
                    )
        
        print(f"✅ All range analysis visualizations generated!")
    
    def display_summary(self):
        """显示范围分析摘要"""
        
        print(f"\n{'='*80}")
        print("Range Analysis Summary")
        print(f"{'='*80}")
        
        # 总体统计
        total_showdowns = sum(
            len(ranges.get(cat, {}).get('hands', []))
            for ranges in self.player_ranges.values()
            for cat in ranges.keys()
        )
        
        total_players_with_showdowns = len([
            player for player, ranges in self.player_ranges.items()
            if any(ranges.get(cat, {}).get('hands', []) for cat in ranges.keys())
        ])
        
        print(f"\n📊 Overall Statistics:")
        print(f"  - Players with showdown data: {total_players_with_showdowns}")
        print(f"  - Total showdown samples: {total_showdowns}")
        
        # 标签统计
        print(f"\n🏷️ Action Tags with Range Data:")
        for tag, players in self.tag_ranges.items():
            sample_count = sum(
                len(hands) 
                for player_data in players.values()
                for hands in player_data.values()
            )
            if sample_count > 0:
                print(f"  - {tag}: {sample_count} samples")
        
        # 玩家统计
        print(f"\n👥 Players with Most Showdown Data:")
        player_counts = []
        for player, ranges in self.player_ranges.items():
            count = sum(
                len(ranges.get(cat, {}).get('hands', []))
                for cat in ranges.keys()
            )
            if count > 0:
                player_counts.append((player, count))
        
        player_counts.sort(key=lambda x: x[1], reverse=True)
        for player, count in player_counts[:5]:
            print(f"  - {player}: {count} showdown samples")

def process_all_enhanced_files(output_dir: str = "range_analysis"):
    """处理所有enhanced_hands.json文件进行范围分析"""
    
    # 查找所有enhanced_hands.json文件
    pattern = "outputs/*/enhanced_hands.json"
    enhanced_files = glob.glob(pattern)
    
    if not enhanced_files:
        print("No enhanced_hands.json files found")
        print("Please run action_analyzer.py first to generate enhanced data")
        return None
    
    print(f"Found {len(enhanced_files)} enhanced data files:")
    for file in enhanced_files:
        print(f"  - {file}")
    
    # 创建分析器
    analyzer = RangeAnalyzer()
    
    # 分析所有文件
    for enhanced_file in enhanced_files:
        try:
            analyzer.analyze_enhanced_hands_file(enhanced_file)
        except Exception as e:
            print(f"Error processing file {enhanced_file}: {e}")
            continue
    
    # 显示摘要
    analyzer.display_summary()
    
    # 导出详细数据
    analyzer.export_detailed_range_data(output_dir)
    
    # 生成可视化图表
    analyzer.generate_all_visualizations(output_dir)
    
    return analyzer

def main():
    """主函数"""
    
    print("🎯 Range Analyzer - 玩家范围分析器")
    print("="*60)
    
    # 处理所有enhanced文件
    analyzer = process_all_enhanced_files()
    
    if analyzer:
        print(f"\n📁 Results exported to: range_analysis/")
        print("Files include:")
        print("📊 Detailed CSV data files:")
        for tag in analyzer.tag_ranges.keys():
            print(f"  - range_detail_{tag}.csv")
        print("\n🎨 Range Analysis Images:")
        print("  - player_range_summary.png")
        common_tags = ['open', '3bet', 'cbet', 'check-raise', 'donk']
        for tag in common_tags:
            if tag in analyzer.tag_ranges:
                print(f"  - range_{tag}.png")
        
        print(f"\n💡 Hand Categories:")
        print("  - Premium Pairs: AA, KK, QQ, JJ")
        print("  - Medium Pairs: TT, 99, 88, 77")
        print("  - Small Pairs: 66, 55, 44, 33, 22")
        print("  - Strong Aces: AK, AQ, AJ")
        print("  - Medium Aces: AT, A9, A8, A7")
        print("  - Weak Aces: A6, A5, A4, A3, A2")
        print("  - Suited Connectors: Connected suited cards")
        print("  - Broadway: High cards T-A")

if __name__ == "__main__":
    main()