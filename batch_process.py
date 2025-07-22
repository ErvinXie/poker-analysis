#!/usr/bin/env python3
import os
import glob
from poker_parser import PokerLogParser
import csv
import re
import json

def create_mapping_cli(players, mapping_file):
    """Create or supplement player mapping using command-line interface"""
    # Load existing mappings if they exist
    existing_mappings = {}
    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                existing_mappings = json.load(f)
        except:
            pass
    
    print("\n" + "="*60)
    print("命令行玩家映射创建/补充")
    print("="*60)
    print("为每个玩家输入真实姓名，或按Enter跳过")
    print("输入 'quit' 退出映射创建")
    if existing_mappings:
        print(f"注意: 将补充现有的 {len(existing_mappings)} 个映射")
    print("-"*60)
    
    new_mappings = existing_mappings.copy()
    added_count = 0
    
    for i, player in enumerate(sorted(players), 1):
        while True:
            print(f"\n[{i}/{len(players)}] 游戏用户名: {player}")
            real_name = input("真实姓名 (或按Enter跳过): ").strip()
            
            if real_name.lower() == 'quit':
                print("映射创建已取消")
                return False
            elif real_name == '':
                print(f"跳过玩家: {player}")
                break
            elif real_name in new_mappings.values():
                print(f"警告: '{real_name}' 已经映射给其他玩家")
                confirm = input("是否继续使用此名字? (y/n): ").lower()
                if confirm in ['y', 'yes']:
                    new_mappings[player] = real_name
                    print(f"已映射: {player} -> {real_name}")
                    added_count += 1
                    break
            else:
                new_mappings[player] = real_name
                print(f"已映射: {player} -> {real_name}")
                added_count += 1
                break
    
    if added_count == 0:
        print("\n没有添加任何新映射")
        return len(existing_mappings) > 0  # Return True if there were existing mappings
    
    # Save mappings
    try:
        os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(new_mappings, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 映射保存成功: {mapping_file}")
        print(f"新增映射: {added_count} 个")
        print(f"总映射数: {len(new_mappings)} 个")
        return True
    
    except Exception as e:
        print(f"\n❌ 保存映射失败: {e}")
        return False

def get_unmapped_players(players, mapping_file):
    """Get list of players that don't have mappings yet"""
    if not os.path.exists(mapping_file):
        return players  # No mapping file exists, all players are unmapped
    
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            existing_mappings = json.load(f)
    except:
        return players  # Can't read mapping file, treat all as unmapped
    
    return [player for player in players if player not in existing_mappings]

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
            
            # Read and sort rows by order (chronological)
            rows = []
            with open(log_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)
            
            # Sort by order to get chronological sequence
            rows.sort(key=lambda x: int(x['order']) if x['order'].isdigit() else 0)
            
            # Extract player names from entries in chronological order
            for row in rows:
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
            
            # Check for unmapped players and create CLI mapping
            log_name = os.path.basename(log_file)
            log_name_base = log_name[:-4] if log_name.endswith('.csv') else log_name
            mapping_file = f'player_mappings/{log_name_base}_mapping.json'
            
            unmapped_players = get_unmapped_players(list(parser_temp.all_players), mapping_file)
            
            print(f"发现 {len(parser_temp.all_players)} 个玩家")
            
            if unmapped_players:
                print(f"需要为 {len(unmapped_players)} 个未映射玩家创建映射")
                if not create_mapping_cli(unmapped_players, mapping_file):
                    print("用户取消了映射设置，跳过此文件")
                    continue
            else:
                print("所有玩家已有映射，直接处理")
            
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