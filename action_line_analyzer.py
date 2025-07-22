#!/usr/bin/env python3
"""
Action Line Analyzer - 分析玩家行动线频率

主要功能:
1. 分析每个玩家的行动线出现频率
2. 按桌子玩家数量分组统计
3. 生成频率表格和可视化图表
4. 支持完整行动线和部分匹配

行动线格式说明:
- X=Check, B=Bet, C=Call, F=Fold, R=Raise, A=All-in
- 格式: preflop/flop/turn/river
- 例如: "R/B/X/R" = 翻牌前raise，flop下bet，turn过check，river加raise
"""

import json
import os
import glob
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 使用无GUI后端
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Any, Set
from collections import defaultdict, Counter
import re

class ActionLineAnalyzer:
    def __init__(self):
        self.player_action_lines = defaultdict(lambda: defaultdict(lambda: {
            'total_hands': 0,
            'action_lines': defaultdict(int)
        }))
        
    def analyze_enhanced_hands_file(self, enhanced_hands_file: str):
        """分析一个enhanced_hands.json文件"""
        
        with open(enhanced_hands_file, 'r', encoding='utf-8') as f:
            hands = json.load(f)
        
        print(f"Analyzing file: {os.path.basename(enhanced_hands_file)}")
        print(f"Total hands: {len(hands)}")
        
        for hand in hands:
            players = hand.get('players', [])
            player_count = len(players)
            action_lines = hand.get('action_lines', {})
            
            # 为每个玩家统计总手数和行动线
            for player in players:
                self.player_action_lines[player][player_count]['total_hands'] += 1
                
                # 获取该玩家的行动线
                if player in action_lines:
                    action_line = action_lines[player]
                    self.player_action_lines[player][player_count]['action_lines'][action_line] += 1
                    
    def get_all_players(self) -> List[str]:
        """获取所有玩家"""
        return sorted(list(self.player_action_lines.keys()))
    
    def get_player_counts(self) -> List[int]:
        """获取所有出现过的玩家数量"""
        player_counts = set()
        for player_data in self.player_action_lines.values():
            player_counts.update(player_data.keys())
        return sorted(list(player_counts))
    
    def get_all_action_lines(self, min_occurrences: int = 1) -> List[str]:
        """获取所有出现过的行动线，按出现频率排序"""
        action_line_counts = defaultdict(int)
        
        for player_data in self.player_action_lines.values():
            for player_count_data in player_data.values():
                for action_line, count in player_count_data['action_lines'].items():
                    action_line_counts[action_line] += count
        
        # 过滤出现次数少的行动线，并按频率排序
        filtered_lines = [
            line for line, count in action_line_counts.items() 
            if count >= min_occurrences
        ]
        
        return sorted(filtered_lines, key=lambda x: action_line_counts[x], reverse=True)
    
    def get_top_action_lines(self, top_n: int = 20) -> List[str]:
        """获取最常见的N个行动线"""
        action_line_counts = defaultdict(int)
        
        for player_data in self.player_action_lines.values():
            for player_count_data in player_data.values():
                for action_line, count in player_count_data['action_lines'].items():
                    action_line_counts[action_line] += count
        
        # 按出现频率排序，取前N个
        sorted_lines = sorted(action_line_counts.items(), key=lambda x: x[1], reverse=True)
        return [line for line, _ in sorted_lines[:top_n]]
    
    def create_action_line_frequency_table(self, action_line: str) -> pd.DataFrame:
        """为特定行动线创建频率表格"""
        
        players = self.get_all_players()
        player_counts = self.get_player_counts()
        
        # 计算每个玩家的总频率用于排序
        player_total_frequencies = {}
        
        for player in players:
            total_line_count = 0
            total_hands_all = 0
            
            for player_count in player_counts:
                total_hands = self.player_action_lines[player][player_count]['total_hands']
                line_count = self.player_action_lines[player][player_count]['action_lines'][action_line]
                total_line_count += line_count
                total_hands_all += total_hands
            
            if total_hands_all > 0 and total_line_count > 0:
                player_total_frequencies[player] = total_line_count / total_hands_all
            else:
                player_total_frequencies[player] = 0.0
        
        # 按总频率排序玩家
        sorted_players = sorted(players, key=lambda p: player_total_frequencies[p], reverse=True)
        
        # 创建数据字典
        table_data = {}
        
        for player_count in player_counts:
            column_data = []
            
            for player in sorted_players:
                total_hands = self.player_action_lines[player][player_count]['total_hands']
                line_count = self.player_action_lines[player][player_count]['action_lines'][action_line]
                
                if total_hands > 0 and line_count > 0:
                    frequency = line_count / total_hands
                    cell_value = f"{frequency:.3f} ({line_count}/{total_hands})"
                else:
                    cell_value = "-"
                
                column_data.append(cell_value)
            
            table_data[f"{player_count}P"] = column_data
        
        # 添加总频率列
        total_freq_column = []
        for player in sorted_players:
            total_freq = player_total_frequencies[player]
            if total_freq > 0:
                # 计算总次数
                total_count = sum(
                    self.player_action_lines[player][pc]['action_lines'][action_line] 
                    for pc in player_counts
                )
                total_hands = sum(
                    self.player_action_lines[player][pc]['total_hands'] 
                    for pc in player_counts
                )
                total_freq_column.append(f"{total_freq:.3f} ({total_count}/{total_hands})")
            else:
                total_freq_column.append("-")
        
        table_data['Total'] = total_freq_column
        
        # 创建DataFrame
        df = pd.DataFrame(table_data, index=sorted_players)
        return df
    
    def create_summary_table(self, top_n: int = 15) -> pd.DataFrame:
        """创建最常见行动线的总结表格"""
        
        top_action_lines = self.get_top_action_lines(top_n)
        players = self.get_all_players()
        
        summary_data = []
        
        for player in players:
            row_data = {'Player': player}
            
            # 计算总手数
            total_hands_all = sum(
                data['total_hands'] 
                for data in self.player_action_lines[player].values()
            )
            row_data['Total Hands'] = total_hands_all
            
            # 计算每个行动线的总频率
            total_frequency_sum = 0.0
            
            for action_line in top_action_lines:
                total_line_count = sum(
                    data['action_lines'][action_line] 
                    for data in self.player_action_lines[player].values()
                )
                
                if total_hands_all > 0 and total_line_count > 0:
                    frequency = total_line_count / total_hands_all
                    row_data[action_line] = f"{frequency:.3f} ({total_line_count})"
                    total_frequency_sum += frequency
                else:
                    row_data[action_line] = "-"
            
            # 添加总频率用于排序
            row_data['Total Freq'] = f"{total_frequency_sum:.3f}"
            row_data['_sort_key'] = total_frequency_sum
            
            summary_data.append(row_data)
        
        # 创建DataFrame并按总频率排序
        df = pd.DataFrame(summary_data)
        df = df.sort_values('_sort_key', ascending=False)
        
        # 移除临时排序键
        df = df.drop('_sort_key', axis=1)
        
        return df
    
    def create_action_line_table_image(self, action_line: str, output_dir: str):
        """为特定行动线创建表格图片"""
        df = self.create_action_line_frequency_table(action_line)
        
        # 只保留有该行动线的玩家
        players_with_line = []
        for player in df.index:
            total_freq = df.loc[player, 'Total']
            if total_freq != '-':
                players_with_line.append(player)
        
        if not players_with_line:
            print(f"No players found with action line: {action_line}")
            return
        
        # 过滤DataFrame
        filtered_df = df.loc[players_with_line]
        
        # 计算表格尺寸
        n_rows = len(filtered_df)
        n_cols = len(filtered_df.columns)
        
        # 创建图片
        fig, ax = plt.subplots(figsize=(max(12, n_cols * 1.2), max(6, n_rows * 0.5)), dpi=300)
        ax.axis('tight')
        ax.axis('off')
        
        # 创建表格
        table = ax.table(cellText=filtered_df.values,
                        rowLabels=filtered_df.index,
                        colLabels=filtered_df.columns,
                        cellLoc='center',
                        loc='center',
                        bbox=[0, 0, 1, 1])
        
        # 设置表格样式
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)
        
        # 设置表头样式
        for i in range(n_cols):
            table[(0, i)].set_facecolor('#2196F3')  # 蓝色
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # 设置行标签样式
        for i in range(1, n_rows + 1):
            table[(i, -1)].set_facecolor('#E3F2FD')  # 浅蓝色
            table[(i, -1)].set_text_props(weight='bold')
        
        # 设置数据单元格样式
        for i in range(1, n_rows + 1):
            for j in range(n_cols):
                cell_value = filtered_df.iloc[i-1, j]
                if cell_value == '-':
                    table[(i, j)].set_facecolor('#F5F5F5')
                    table[(i, j)].set_text_props(color='gray')
                else:
                    # 根据频率值设置颜色深度
                    try:
                        freq_value = float(cell_value.split(' ')[0])
                        if freq_value > 0:
                            # 蓝色系，频率越高颜色越深
                            alpha = min(1.0, freq_value * 5)  # 调整透明度
                            table[(i, j)].set_facecolor((0.8, 0.9, 1.0, alpha))
                    except:
                        pass
        
        # 设置标题
        fig.suptitle(f'Action Line "{action_line}" Frequency Table\n(Sorted by Total Frequency)', 
                    fontsize=14, fontweight='bold', y=0.95)
        
        # 调整布局
        plt.tight_layout()
        plt.subplots_adjust(top=0.9)
        
        # 保存图片
        safe_filename = action_line.replace('/', '_').replace('\\', '_')
        img_path = os.path.join(output_dir, f"action_line_{safe_filename}.png")
        plt.savefig(img_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"Generated action line table: {img_path}")
    
    def create_summary_table_image(self, output_dir: str, top_n: int = 15):
        """创建行动线总结表格图片"""
        df = self.create_summary_table(top_n)
        
        # 计算表格尺寸
        n_rows = len(df)
        n_cols = len(df.columns)
        
        # 创建图片
        fig, ax = plt.subplots(figsize=(max(16, n_cols * 1.0), max(8, n_rows * 0.4)), dpi=300)
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
        table.set_fontsize(8)
        table.scale(1, 1.5)
        
        # 设置表头样式
        for i in range(n_cols):
            table[(0, i)].set_facecolor('#FF9800')  # 橙色
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # 设置数据单元格样式
        for i in range(1, n_rows + 1):
            for j in range(n_cols):
                cell_value = df.iloc[i-1, j]
                
                # 玩家名称列
                if j == 0:
                    table[(i, j)].set_facecolor('#FFF3E0')  # 浅橙色
                    table[(i, j)].set_text_props(weight='bold')
                # 总手数列
                elif j == 1:
                    table[(i, j)].set_facecolor('#F5F5F5')
                # 行动线频率列
                elif cell_value == '-':
                    table[(i, j)].set_facecolor('#F5F5F5')
                    table[(i, j)].set_text_props(color='gray')
                else:
                    # 根据频率值设置颜色深度
                    try:
                        freq_value = float(str(cell_value).split(' ')[0])
                        if freq_value > 0:
                            # 橙色系，频率越高颜色越深
                            alpha = min(1.0, freq_value * 8)  # 调整透明度
                            table[(i, j)].set_facecolor((1.0, 0.9, 0.8, alpha))
                    except:
                        pass
        
        # 设置标题
        fig.suptitle(f'Top {top_n} Action Lines Frequency Summary\n(Sorted by Total Activity)', 
                    fontsize=14, fontweight='bold', y=0.95)
        
        # 调整布局
        plt.tight_layout()
        plt.subplots_adjust(top=0.9)
        
        # 保存图片
        img_path = os.path.join(output_dir, f"action_line_summary_top{top_n}.png")
        plt.savefig(img_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"Generated action line summary: {img_path}")
    
    def export_to_csv(self, output_dir: str, top_n: int = 20):
        """导出所有表格到CSV文件"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        top_action_lines = self.get_top_action_lines(top_n)
        
        # 导出每个行动线的频率表格
        for action_line in top_action_lines:
            df = self.create_action_line_frequency_table(action_line)
            safe_filename = action_line.replace('/', '_').replace('\\', '_')
            csv_file = os.path.join(output_dir, f"action_line_{safe_filename}.csv")
            df.to_csv(csv_file, encoding='utf-8')
            print(f"Exported: {csv_file}")
        
        # 导出总结表格
        summary_df = self.create_summary_table(top_n)
        summary_csv = os.path.join(output_dir, f"action_line_summary_top{top_n}.csv")
        summary_df.to_csv(summary_csv, index=False, encoding='utf-8')
        print(f"Exported: {summary_csv}")
    
    def generate_all_visualizations(self, output_dir: str, top_n: int = 15):
        """生成所有可视化图表"""
        
        print(f"\n🎨 Generating action line visualizations...")
        print("-" * 60)
        
        top_action_lines = self.get_top_action_lines(top_n)
        
        # 为每个行动线生成表格图片
        for i, action_line in enumerate(top_action_lines, 1):
            try:
                print(f"[{i}/{len(top_action_lines)}] Generating table for: {action_line}")
                self.create_action_line_table_image(action_line, output_dir)
            except Exception as e:
                print(f"Error generating table for {action_line}: {e}")
        
        # 生成总结表格
        try:
            print("Generating summary table...")
            self.create_summary_table_image(output_dir, top_n)
        except Exception as e:
            print(f"Error generating summary table: {e}")
        
        print(f"✅ All action line visualizations generated successfully!")
    
    def display_summary(self, top_n: int = 10):
        """显示行动线分析摘要"""
        
        print(f"\n{'='*80}")
        print("Action Line Analysis Summary")
        print(f"{'='*80}")
        
        # 显示最常见的行动线
        top_action_lines = self.get_top_action_lines(top_n)
        action_line_counts = defaultdict(int)
        
        for player_data in self.player_action_lines.values():
            for player_count_data in player_data.values():
                for action_line, count in player_count_data['action_lines'].items():
                    action_line_counts[action_line] += count
        
        print(f"\n📊 Top {top_n} Most Common Action Lines:")
        print("-" * 50)
        for i, action_line in enumerate(top_action_lines, 1):
            count = action_line_counts[action_line]
            print(f"{i:2d}. {action_line:<15} - {count:4d} occurrences")
        
        # 显示玩家统计
        total_players = len(self.get_all_players())
        total_hands = sum(
            sum(data['total_hands'] for data in player_data.values())
            for player_data in self.player_action_lines.values()
        )
        
        print(f"\n📈 Statistics:")
        print(f"  - Total Players: {total_players}")
        print(f"  - Total Hands Analyzed: {total_hands}")
        print(f"  - Unique Action Lines: {len(action_line_counts)}")
        print(f"  - Action Lines with 3+ occurrences: {len(self.get_all_action_lines(3))}")

def process_all_enhanced_files(output_dir: str = "action_line_analysis", top_n: int = 15):
    """处理所有enhanced_hands.json文件"""
    
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
    analyzer = ActionLineAnalyzer()
    
    # 分析所有文件
    for enhanced_file in enhanced_files:
        try:
            analyzer.analyze_enhanced_hands_file(enhanced_file)
        except Exception as e:
            print(f"Error processing file {enhanced_file}: {e}")
            continue
    
    # 显示摘要
    analyzer.display_summary(top_n)
    
    # 导出CSV
    analyzer.export_to_csv(output_dir, top_n)
    
    # 生成可视化图表
    analyzer.generate_all_visualizations(output_dir, top_n)
    
    return analyzer

def main():
    """主函数"""
    
    print("🎯 Action Line Analyzer - 行动线频率分析器")
    print("="*60)
    
    # 处理所有enhanced文件
    analyzer = process_all_enhanced_files()
    
    if analyzer:
        print(f"\n📁 Results exported to: action_line_analysis/")
        print("Files include:")
        print("📊 CSV data files:")
        top_action_lines = analyzer.get_top_action_lines(15)
        for action_line in top_action_lines:
            safe_filename = action_line.replace('/', '_').replace('\\', '_')
            print(f"  - action_line_{safe_filename}.csv")
        print("  - action_line_summary_top15.csv")
        print("\n🎨 Table Images:")
        for action_line in top_action_lines:
            safe_filename = action_line.replace('/', '_').replace('\\', '_')
            print(f"  - action_line_{safe_filename}.png")
        print("  - action_line_summary_top15.png")
        
        print(f"\n💡 Action Line Format:")
        print("  - X=Check, B=Bet, C=Call, F=Fold, R=Raise, A=All-in")
        print("  - Format: preflop/flop/turn/river")
        print("  - Example: 'R/B/X/R' = Raise preflop, Bet flop, Check turn, Raise river")

if __name__ == "__main__":
    main()