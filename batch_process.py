#!/usr/bin/env python3
import os
import glob
from poker_parser import PokerLogParser
import csv
import re

def process_all_logs():
    """Process all CSV log files in the logs directory"""
    logs_dir = 'logs'
    
    # Main output directory will be created automatically by individual parsers
    
    # Find all CSV files in logs directory
    log_files = glob.glob(os.path.join(logs_dir, '*.csv'))
    
    if not log_files:
        print(f"No CSV files found in {logs_dir}/")
        return
    
    print(f"Found {len(log_files)} log files to process:")
    for log_file in log_files:
        print(f"  - {os.path.basename(log_file)}")
    
    processed_files = []
    
    for log_file in log_files:
        try:
            print(f"\n{'='*60}")
            print(f"Processing: {os.path.basename(log_file)}")
            print(f"{'='*60}")
            
            # First pass: collect player names
            parser_temp = PokerLogParser(log_file)
            print("收集玩家名单...")
            
            with open(log_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    entry = row['entry']
                    # Extract player names from various patterns
                    patterns = [
                        r'"([^"]+)" folds',
                        r'"([^"]+)" calls',
                        r'"([^"]+)" bets',
                        r'"([^"]+)" raises',
                        r'"([^"]+)" checks',
                        r'"([^"]+)" posts',
                        r'"([^"]+)" collected',
                        r'dealer: "([^"]+)"',
                        r'Player stacks:.*?"([^"]+)"'
                    ]
                    for pattern in patterns:
                        matches = re.findall(pattern, entry)
                        for match in matches:
                            parser_temp.all_players.add(match)
            
            # Show mapping dialog for this log file
            print(f"发现 {len(parser_temp.all_players)} 个玩家")
            if not parser_temp.name_mapper.show_mapping_dialog(list(parser_temp.all_players)):
                print("用户取消了映射设置，跳过此文件")
                continue
            
            # Parse with mappings
            parser = PokerLogParser(log_file)
            print(f"解析 {os.path.basename(log_file)}...")
            parser.parse_log_file(log_file)
            
            print(f"解析了 {len(parser.hands)} 手牌")
            
            # Export all outputs to the parser's output directory
            parser.export_to_json()
            parser.export_statistics()
            parser.export_summary_report()
            
            print(f"导出到目录: {parser.output_dir}/")
            print("生成的文件:")
            print(f"  - {parser.output_dir}/parsed_hands.json")
            print(f"  - {parser.output_dir}/game_statistics.json")
            print(f"  - {parser.output_dir}/game_summary.txt")
            
            # Get quick stats
            stats = parser.get_statistics()
            print(f"统计: {stats['total_hands']} 手牌, {len(stats['players'])} 玩家")
            
            processed_files.append({
                'log_file': log_file,
                'output_dir': parser.output_dir,
                'hands': len(parser.hands),
                'players': len(stats['players'])
            })
            
        except Exception as e:
            print(f"处理文件 {log_file} 时出错: {e}")
            continue
    
    # Summary
    print(f"\n{'='*60}")
    print("处理完成总结:")
    print(f"{'='*60}")
    print(f"处理了 {len(processed_files)}/{len(log_files)} 个文件")
    
    total_hands = 0
    for pf in processed_files:
        total_hands += pf['hands']
        log_name = os.path.basename(pf['log_file'])
        print(f"✅ {log_name}: {pf['hands']} 手牌, {pf['players']} 玩家")
        print(f"   输出目录: {pf['output_dir']}/")
    
    print(f"\n总计解析了 {total_hands} 手牌")
    print(f"所有输出保存在: outputs/ 文件夹下")
    print(f"玩家映射保存在: player_mappings/ 文件夹下")

def list_existing_mappings():
    """List all existing player mappings"""
    mappings_dir = 'player_mappings'
    if not os.path.exists(mappings_dir):
        print("No player mappings directory found.")
        return
    
    mapping_files = glob.glob(os.path.join(mappings_dir, '*_mapping.json'))
    if not mapping_files:
        print("No mapping files found.")
        return
    
    print("现有的玩家映射文件:")
    for mapping_file in mapping_files:
        log_name = os.path.basename(mapping_file).replace('_mapping.json', '')
        print(f"  - {log_name}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'list':
        list_existing_mappings()
    else:
        process_all_logs()