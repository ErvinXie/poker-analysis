#!/usr/bin/env python3
"""
Action Frequency Analyzer - 分析每个玩家的行动频率

主要功能:
1. 分析每个玩家的标签化行动频率（open, 3bet, cbet, donk等）
2. 按手牌玩家数量分组统计
3. 生成频率表格：行=玩家，列=玩家数量，值=频率(行动次数/总手数)

输出格式:
- 每个行动类型一个表格
- 包含总手数和行动次数的详细信息
- 支持CSV和控制台输出
"""

import json
import os
import glob
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 使用无GUI后端
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import numpy as np
from typing import Dict, List, Any
from collections import defaultdict

class ActionFrequencyAnalyzer:
    def __init__(self):
        self.player_stats = defaultdict(lambda: defaultdict(lambda: {
            'total_hands': 0,
            'action_counts': defaultdict(int)
        }))
        
    def analyze_enhanced_hands_file(self, enhanced_hands_file: str):
        """分析一个enhanced_hands.json文件"""
        
        with open(enhanced_hands_file, 'r', encoding='utf-8') as f:
            hands = json.load(f)
        
        print(f"分析文件: {os.path.basename(enhanced_hands_file)}")
        print(f"总手牌数: {len(hands)}")
        
        for hand in hands:
            players = hand.get('players', [])
            player_count = len(players)
            
            # 为每个玩家统计总手数
            for player in players:
                self.player_stats[player][player_count]['total_hands'] += 1
            
            # 统计标签化行动
            for stage in ['preflop', 'flop', 'turn', 'river']:
                stage_actions = hand.get(f'{stage}_actions', [])
                
                for action in stage_actions:
                    player = action.get('player')
                    tags = action.get('tags', [])
                    
                    if player and tags:
                        for tag_info in tags:
                            tag = tag_info.get('tag')
                            if tag:
                                self.player_stats[player][player_count]['action_counts'][tag] += 1
    
    def get_all_tags(self) -> List[str]:
        """获取所有出现过的行动标签"""
        all_tags = set()
        
        for player_data in self.player_stats.values():
            for player_count_data in player_data.values():
                all_tags.update(player_count_data['action_counts'].keys())
        
        return sorted(list(all_tags))
    
    def get_all_players(self) -> List[str]:
        """获取所有玩家"""
        return sorted(list(self.player_stats.keys()))
    
    def get_player_counts(self) -> List[int]:
        """获取所有出现过的玩家数量"""
        player_counts = set()
        
        for player_data in self.player_stats.values():
            player_counts.update(player_data.keys())
        
        return sorted(list(player_counts))
    
    def create_frequency_table(self, tag: str) -> pd.DataFrame:
        """为特定标签创建频率表格，包含总频率并按总频率排序"""
        
        players = self.get_all_players()
        player_counts = self.get_player_counts()
        
        # 首先计算每个玩家的总频率用于排序
        player_total_frequencies = {}
        
        for player in players:
            total_tag_count = 0
            total_hands_all = 0
            
            for player_count in player_counts:
                total_hands = self.player_stats[player][player_count]['total_hands']
                action_count = self.player_stats[player][player_count]['action_counts'][tag]
                total_tag_count += action_count
                total_hands_all += total_hands
            
            if total_hands_all > 0 and total_tag_count > 0:
                player_total_frequencies[player] = total_tag_count / total_hands_all
            else:
                player_total_frequencies[player] = 0.0
        
        # 按总频率排序玩家
        sorted_players = sorted(players, key=lambda p: player_total_frequencies[p], reverse=True)
        
        # 创建数据字典
        table_data = {}
        
        for player_count in player_counts:
            column_data = []
            
            for player in sorted_players:
                total_hands = self.player_stats[player][player_count]['total_hands']
                action_count = self.player_stats[player][player_count]['action_counts'][tag]
                
                if total_hands > 0 and action_count > 0:
                    frequency = action_count / total_hands
                    # 格式: frequency (action_count/total_hands)
                    cell_value = f"{frequency:.3f} ({action_count}/{total_hands})"
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
                    self.player_stats[player][pc]['action_counts'][tag] 
                    for pc in player_counts
                )
                total_hands = sum(
                    self.player_stats[player][pc]['total_hands'] 
                    for pc in player_counts
                )
                total_freq_column.append(f"{total_freq:.3f} ({total_count}/{total_hands})")
            else:
                total_freq_column.append("-")
        
        table_data['Total'] = total_freq_column
        
        # 创建DataFrame
        df = pd.DataFrame(table_data, index=sorted_players)
        return df
    
    def create_summary_table(self) -> pd.DataFrame:
        """创建总结表格，显示每个玩家的总体统计，并按总频率排序"""
        
        players = self.get_all_players()
        tags = self.get_all_tags()
        
        summary_data = []
        
        for player in players:
            row_data = {'玩家': player}
            
            # 计算总手数（所有玩家数量的总和）
            total_hands_all = sum(
                data['total_hands'] 
                for data in self.player_stats[player].values()
            )
            row_data['总手数'] = total_hands_all
            
            # 计算每个标签的总频率
            total_frequency_sum = 0.0  # 用于排序的总频率
            
            for tag in tags:
                total_tag_count = sum(
                    data['action_counts'][tag] 
                    for data in self.player_stats[player].values()
                )
                
                if total_hands_all > 0 and total_tag_count > 0:
                    frequency = total_tag_count / total_hands_all
                    row_data[tag] = f"{frequency:.3f} ({total_tag_count})"
                    total_frequency_sum += frequency
                else:
                    row_data[tag] = "-"
            
            # 添加总频率列用于排序
            row_data['总频率'] = f"{total_frequency_sum:.3f}"
            row_data['_sort_key'] = total_frequency_sum  # 临时排序键
            
            summary_data.append(row_data)
        
        # 创建DataFrame并按总频率排序
        df = pd.DataFrame(summary_data)
        df = df.sort_values('_sort_key', ascending=False)
        
        # 移除临时排序键
        df = df.drop('_sort_key', axis=1)
        
        return df
    
    def setup_matplotlib_chinese(self):
        """设置matplotlib支持中文字体"""
        try:
            # 尝试常见的中文字体
            chinese_fonts = [
                'SimHei',           # 黑体 (Windows)
                'Microsoft YaHei',  # 微软雅黑 (Windows)  
                'PingFang SC',      # 苹方 (macOS)
                'Hiragino Sans GB', # 冬青黑体 (macOS)
                'WenQuanYi Micro Hei', # 文泉驿微米黑 (Linux)
                'Noto Sans CJK SC', # 思源黑体 (Linux)
                'DejaVu Sans'       # 备选字体
            ]
            
            for font in chinese_fonts:
                try:
                    plt.rcParams['font.sans-serif'] = [font]
                    plt.rcParams['axes.unicode_minus'] = False
                    # 测试字体是否可用
                    fig, ax = plt.subplots(figsize=(1, 1))
                    ax.text(0.5, 0.5, '中文测试', fontsize=12)
                    plt.close(fig)
                    print(f"使用字体: {font}")
                    return
                except:
                    continue
                    
            # 如果所有字体都失败，使用默认设置
            print("警告: 无法找到中文字体，使用默认字体")
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            
        except Exception as e:
            print(f"字体设置失败: {e}")
    
    def create_frequency_table_image(self, tag: str, output_dir: str):
        """为特定行动创建表格图片"""
        df = self.create_frequency_table(tag)
        
        # 只保留有该行动的玩家
        players_with_action = []
        for player in df.index:
            total_freq = df.loc[player, 'Total']
            if total_freq != '-':
                players_with_action.append(player)
        
        if not players_with_action:
            return
        
        # 过滤DataFrame
        filtered_df = df.loc[players_with_action]
        
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
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # 设置行标签样式
        for i in range(1, n_rows + 1):
            table[(i, -1)].set_facecolor('#E8F5E8')
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
                            # 绿色系，频率越高颜色越深
                            alpha = min(1.0, freq_value * 3)  # 调整透明度
                            table[(i, j)].set_facecolor((0.8, 1.0, 0.8, alpha))
                    except:
                        pass
        
        # 设置标题
        fig.suptitle(f'{tag.upper()} Action Frequency Table\n(Sorted by Total Frequency)', 
                    fontsize=14, fontweight='bold', y=0.95)
        
        # 调整布局
        plt.tight_layout()
        plt.subplots_adjust(top=0.9)
        
        # 保存图片
        img_path = os.path.join(output_dir, f"table_{tag}.png")
        plt.savefig(img_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"Generated table image: {img_path}")
    
    def create_summary_overview_chart(self, output_dir: str):
        """创建总体统计概览图"""
        summary_df = self.create_summary_table()
        tags = self.get_all_tags()
        
        # 提取数据
        players = summary_df['玩家'].tolist()
        
        # 为每个标签提取频率数据
        tag_data = {}
        for tag in tags:
            frequencies = []
            for freq_str in summary_df[tag]:
                if freq_str == '-':
                    frequencies.append(0.0)
                else:
                    try:
                        freq_value = float(freq_str.split(' ')[0])
                        frequencies.append(freq_value)
                    except:
                        frequencies.append(0.0)
            tag_data[tag] = frequencies
        
        # 创建堆叠柱状图
        plt.figure(figsize=(16, 10), dpi=300)
        
        # 设置柱状图位置
        x = np.arange(len(players))
        width = 0.8
        
        # 颜色方案
        colors = plt.cm.Set3(np.linspace(0, 1, len(tags)))
        
        # 创建堆叠柱状图
        bottoms = np.zeros(len(players))
        
        for i, (tag, color) in enumerate(zip(tags, colors)):
            plt.bar(x, tag_data[tag], width, bottom=bottoms, 
                    label=tag, color=color, alpha=0.8, edgecolor='white', linewidth=0.5)
            bottoms += tag_data[tag]
        
        # 设置标题和标签
        plt.title('所有玩家行动频率总览\n(堆叠柱状图 - 按总活跃度排序)', 
                 fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('玩家', fontsize=12, fontweight='bold')
        plt.ylabel('频率', fontsize=12, fontweight='bold')
        
        # 设置x轴标签
        plt.xticks(x, players, rotation=45, ha='right')
        
        # 添加图例
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # 添加网格
        plt.grid(axis='y', alpha=0.3, linestyle='--')
        
        # 调整布局
        plt.tight_layout()
        
        # 保存高清图片
        img_path = os.path.join(output_dir, "overview_stacked_bar.png")
        plt.savefig(img_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"已生成总览图: {img_path}")
    
    def generate_all_visualizations(self, output_dir: str):
        """生成所有可视化图表"""
        
        # 设置中文字体支持
        self.setup_matplotlib_chinese()
        
        print(f"\n🎨 Generating table images...")
        print("-" * 60)
        
        tags = self.get_all_tags()
        
        # 为每个行动标签生成图表
        for tag in tags:
            try:
                print(f"Generating table for {tag}...")
                self.create_frequency_table_image(tag, output_dir)
            except Exception as e:
                print(f"Error generating {tag} table: {e}")
        
        print(f"✅ All table images generated successfully!")

    def export_to_csv(self, output_dir: str):
        """导出所有表格到CSV文件"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        tags = self.get_all_tags()
        
        # 导出每个标签的频率表格
        for tag in tags:
            df = self.create_frequency_table(tag)
            csv_file = os.path.join(output_dir, f"frequency_{tag}.csv")
            df.to_csv(csv_file, encoding='utf-8')
            print(f"已导出: {csv_file}")
        
        # 导出总结表格
        summary_df = self.create_summary_table()
        summary_csv = os.path.join(output_dir, "frequency_summary.csv")
        summary_df.to_csv(summary_csv, index=False, encoding='utf-8')
        print(f"已导出: {summary_csv}")
    
    def display_tables(self):
        """在控制台显示表格"""
        
        tags = self.get_all_tags()
        
        print(f"\n{'='*80}")
        print("行动频率分析结果")
        print(f"{'='*80}")
        
        # 显示总结表格
        print(f"\n📊 总体统计 (所有玩家数量)")
        print("-" * 60)
        summary_df = self.create_summary_table()
        print(summary_df.to_string(index=False))
        
        # 显示每个标签的详细表格
        for tag in tags:
            print(f"\n📈 {tag.upper()} 行动频率 (按玩家数量分组)")
            print("-" * 60)
            df = self.create_frequency_table(tag)
            
            # 检查是否有数据（检查行动次数是否大于0）
            has_data = False
            for player in self.get_all_players():
                for player_count in self.get_player_counts():
                    if self.player_stats[player][player_count]['action_counts'][tag] > 0:
                        has_data = True
                        break
                if has_data:
                    break
            
            if has_data:
                print(df.to_string())
            else:
                print("(无数据)")
        
        print(f"\n💡 说明:")
        print("- 频率格式: 频率值 (行动次数/总手数)")  
        print("- 频率 = 该行动出现次数 / 该玩家数量下的总手数")
        print("- \"-\" 表示该行动出现次数为0")
        print("- 总频率 = 所有行动标签频率的总和")
        print("- 玩家按总频率从高到低排序")
        print("- 例如: 0.150 (3/20) 表示20手牌中出现3次该行动，频率15%")

def process_all_enhanced_files(output_dir: str = "frequency_analysis"):
    """处理所有enhanced_hands.json文件"""
    
    # 查找所有enhanced_hands.json文件
    pattern = "outputs/*/enhanced_hands.json"
    enhanced_files = glob.glob(pattern)
    
    if not enhanced_files:
        print("未找到enhanced_hands.json文件")
        print("请先运行 action_analyzer.py 生成增强数据")
        return None
    
    print(f"找到 {len(enhanced_files)} 个增强数据文件:")
    for file in enhanced_files:
        print(f"  - {file}")
    
    # 创建分析器
    analyzer = ActionFrequencyAnalyzer()
    
    # 分析所有文件
    for enhanced_file in enhanced_files:
        try:
            analyzer.analyze_enhanced_hands_file(enhanced_file)
        except Exception as e:
            print(f"处理文件 {enhanced_file} 时出错: {e}")
            continue
    
    # 显示结果
    analyzer.display_tables()
    
    # 导出CSV
    analyzer.export_to_csv(output_dir)
    
    # 生成可视化图表
    analyzer.generate_all_visualizations(output_dir)
    
    return analyzer

def analyze_specific_file(enhanced_file: str, output_dir: str = "frequency_analysis_single"):
    """分析特定的enhanced_hands.json文件"""
    
    if not os.path.exists(enhanced_file):
        print(f"文件不存在: {enhanced_file}")
        return None
    
    analyzer = ActionFrequencyAnalyzer()
    analyzer.analyze_enhanced_hands_file(enhanced_file)
    
    analyzer.display_tables()
    analyzer.export_to_csv(output_dir)
    analyzer.generate_all_visualizations(output_dir)
    
    return analyzer

def main():
    """主函数"""
    
    print("🎯 Action Frequency Analyzer - 行动频率分析器")
    print("="*60)
    
    # 处理所有enhanced文件
    analyzer = process_all_enhanced_files()
    
    if analyzer:
        print(f"\n📁 结果已导出到: frequency_analysis/")
        print("包含文件:")
        print("📊 CSV数据文件:")
        tags = analyzer.get_all_tags()
        for tag in tags:
            print(f"  - frequency_{tag}.csv")
        print("  - frequency_summary.csv")
        print("\n🎨 Table Images:")
        for tag in tags:
            print(f"  - table_{tag}.png")
        
        print(f"\n🔍 示例用法:")
        print("# 分析特定文件:")
        print("python3 -c \"from action_frequency_analyzer import analyze_specific_file; analyze_specific_file('outputs/某文件/enhanced_hands.json')\"")

if __name__ == "__main__":
    main()