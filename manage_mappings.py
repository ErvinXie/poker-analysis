#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import glob
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from poker_parser import PlayerNameMapper
from language_manager import get_text, set_language

def list_all_mappings():
    """List all existing player mappings with details"""
    mappings_dir = 'player_mappings'
    if not os.path.exists(mappings_dir):
        print(get_text('mappings.no_directory'))
        return
    
    mapping_files = glob.glob(os.path.join(mappings_dir, '*_mapping.json'))
    if not mapping_files:
        print(get_text('mappings.no_files'))
        return
    
    print(get_text('mappings.found_files', count=len(mapping_files)))
    print("="*60)
    
    for mapping_file in sorted(mapping_files):
        log_name = os.path.basename(mapping_file).replace('_mapping.json', '')
        print(f"\n📁 {log_name}")
        
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mappings = json.load(f)
            
            print(get_text('mappings.players_count', count=len(mappings)))
            print(get_text('mappings.file_path', path=mapping_file))
            
            # Show first few mappings as preview
            items = list(mappings.items())
            preview_count = min(3, len(items))
            print("   预览映射:")
            for game_name, real_name in items[:preview_count]:
                print(f"     {game_name[:30]}... -> {real_name}")
            
            if len(items) > preview_count:
                print(get_text('mappings.more_mappings', count=len(items) - preview_count))
                
        except Exception as e:
            print(get_text('mappings.read_error', error=str(e)))

def show_mapping_details(log_name):
    """Show detailed mapping for a specific log file"""
    mapping_file = f'player_mappings/{log_name}_mapping.json'
    
    if not os.path.exists(mapping_file):
        print(f"映射文件不存在: {mapping_file}")
        return
    
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mappings = json.load(f)
        
        print(f"详细映射 - {log_name}")
        print("="*60)
        print(f"总共 {len(mappings)} 个玩家映射:")
        
        for game_name, real_name in sorted(mappings.items()):
            print(f"  {game_name} -> {real_name}")
            
    except Exception as e:
        print(f"读取映射文件失败: {e}")

def create_all_mappings():
    """Create mappings for all log files that don't have mappings yet"""
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        print("No logs directory found.")
        return
    
    log_files = glob.glob(os.path.join(logs_dir, '*.csv'))
    if not log_files:
        print("No CSV log files found.")
        return
    
    unmapped_files = []
    for log_file in log_files:
        log_name = os.path.basename(log_file)
        if log_name.endswith('.csv'):
            log_name = log_name[:-4]
        mapping_file = f'player_mappings/{log_name}_mapping.json'
        
        if not os.path.exists(mapping_file):
            unmapped_files.append(log_file)
    
    if not unmapped_files:
        print("所有日志文件都已有映射！")
        return
    
    print(f"发现 {len(unmapped_files)} 个未映射的日志文件:")
    for i, log_file in enumerate(unmapped_files, 1):
        print(f"  {i}. {os.path.basename(log_file)}")
    
    print(f"\n开始为这些文件创建映射...")
    
    for i, log_file in enumerate(unmapped_files, 1):
        print(f"\n{'='*60}")
        print(f"处理文件 {i}/{len(unmapped_files)}: {os.path.basename(log_file)}")
        print(f"{'='*60}")
        
        if create_mapping_for_log(log_file):
            print("✅ 映射创建成功!")
        else:
            print("❌ 映射创建失败或被取消")
    
    print("\n批量映射创建完成！")

def create_all_mappings_cli():
    """Create mappings for all log files that don't have mappings yet using CLI"""
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        print("No logs directory found.")
        return
    
    log_files = glob.glob(os.path.join(logs_dir, '*.csv'))
    if not log_files:
        print("No CSV log files found.")
        return
    
    # 检查所有日志文件的映射状态
    print("="*60)
    print("检查日志文件映射状态")
    print("="*60)
    
    mapped_files = []
    unmapped_files = []
    
    for log_file in sorted(log_files):
        log_name = os.path.basename(log_file)
        if log_name.endswith('.csv'):
            log_name_base = log_name[:-4]
        else:
            log_name_base = log_name
        mapping_file = f'player_mappings/{log_name_base}_mapping.json'
        
        if os.path.exists(mapping_file):
            mapped_files.append((log_file, mapping_file))
            print(f"✅ {log_name} -> {mapping_file}")
        else:
            unmapped_files.append(log_file)
            print(f"⚠️  {log_name} -> 缺少映射文件")
    
    print(f"\n映射状态总结:")
    print(f"  已映射文件: {len(mapped_files)}")
    print(f"  未映射文件: {len(unmapped_files)}")
    
    # 显示已映射文件的详细信息
    if mapped_files:
        print(f"\n已映射的文件详情:")
        for log_file, mapping_file in mapped_files:
            try:
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    mappings = json.load(f)
                
                # Check if mapping is complete
                all_players, unmapped_players, _ = analyze_mapping_completeness(log_file, mapping_file)
                if unmapped_players:
                    status = f"⚠️  部分映射 ({len(mappings)}/{len(all_players)})"
                    print(f"  {status} {os.path.basename(log_file)}")
                    print(f"      未映射: {', '.join(sorted(list(unmapped_players))[:2])}")
                    if len(unmapped_players) > 2:
                        print(f"      ... 还有 {len(unmapped_players) - 2} 个")
                else:
                    print(f"  ✅ 完全映射 ({len(mappings)} 个) {os.path.basename(log_file)}")
            except Exception as e:
                print(f"  ❌ {os.path.basename(log_file)} -> 读取映射失败: {e}")
    
    # 如果没有未映射文件，直接返回
    if not unmapped_files:
        print("\n🎉 所有日志文件都已有映射！无需创建新映射。")
        return
    
    # 显示需要创建映射的文件
    print(f"\n需要创建映射的文件 ({len(unmapped_files)} 个):")
    for i, log_file in enumerate(unmapped_files, 1):
        print(f"  {i}. {os.path.basename(log_file)}")
    
    # 询问用户是否继续
    try:
        print(f"\n是否要为这 {len(unmapped_files)} 个文件创建映射？")
        confirm = input("输入 'y' 或 'yes' 继续，其他键退出: ").lower().strip()
        
        if confirm not in ['y', 'yes']:
            print("已取消映射创建。")
            return
    except (EOFError, KeyboardInterrupt):
        print("\n已取消映射创建。")
        return
    
    print(f"\n开始为这些文件创建映射...")
    
    success_count = 0
    failed_count = 0
    
    for i, log_file in enumerate(unmapped_files, 1):
        print(f"\n{'='*60}")
        print(f"处理文件 {i}/{len(unmapped_files)}: {os.path.basename(log_file)}")
        print(f"{'='*60}")
        
        if create_mapping_for_log(log_file, use_cli=True):
            print("✅ 映射创建成功!")
            success_count += 1
        else:
            print("❌ 映射创建失败或被取消")
            failed_count += 1
    
    print(f"\n{'='*60}")
    print("批量映射创建完成！")
    print(f"✅ 成功创建: {success_count} 个")
    print(f"❌ 失败/取消: {failed_count} 个")
    print("="*60)

def analyze_mapping_completeness(log_file, mapping_file):
    """Analyze mapping completeness for a single log file"""
    if not os.path.exists(log_file):
        return None, None, None
    
    # Collect all players from log file
    from poker_parser import PokerLogParser
    import csv
    import re
    
    all_players = set()
    
    with open(log_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            entry = row['entry']
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
                    all_players.add(match)
    
    # Load existing mappings
    existing_mappings = {}
    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                existing_mappings = json.load(f)
        except Exception as e:
            print(f"Warning: Could not read mapping file {mapping_file}: {e}")
    
    # Find mapped and unmapped players
    mapped_players = set(existing_mappings.keys())
    unmapped_players = all_players - mapped_players
    extra_mappings = mapped_players - all_players  # mappings for players not in this log
    
    return all_players, unmapped_players, existing_mappings

def supplement_mapping_cli(log_file, mapping_file):
    """Supplement missing mappings for a log file using CLI"""
    all_players, unmapped_players, existing_mappings = analyze_mapping_completeness(log_file, mapping_file)
    
    if all_players is None:
        print(f"❌ 无法分析日志文件: {log_file}")
        return False
    
    log_name = os.path.basename(log_file)
    
    print(f"\n{'='*60}")
    print(f"映射完整性分析: {log_name}")
    print(f"{'='*60}")
    print(f"日志中总玩家数: {len(all_players)}")
    print(f"已映射玩家数: {len(existing_mappings)}")
    print(f"未映射玩家数: {len(unmapped_players)}")
    
    if not unmapped_players:
        print("✅ 所有玩家都已映射！")
        return True
    
    print(f"\n未映射的玩家 ({len(unmapped_players)} 个):")
    for i, player in enumerate(sorted(unmapped_players), 1):
        print(f"  {i}. {player}")
    
    # Ask user if they want to supplement mappings
    try:
        confirm = input(f"\n是否要为这 {len(unmapped_players)} 个未映射玩家添加映射？(y/n): ").lower().strip()
        if confirm not in ['y', 'yes']:
            print("已取消映射补充。")
            return False
    except (EOFError, KeyboardInterrupt):
        print("\n已取消映射补充。")
        return False
    
    # Supplement mappings
    new_mappings = existing_mappings.copy()
    added_count = 0
    
    print(f"\n开始补充映射...")
    print("-" * 60)
    
    for i, player in enumerate(sorted(unmapped_players), 1):
        while True:
            print(f"\n[{i}/{len(unmapped_players)}] 游戏用户名: {player}")
            real_name = input("真实姓名 (或按Enter跳过): ").strip()
            
            if real_name.lower() == 'quit':
                print("映射补充已取消")
                return False
            elif real_name == '':
                print(f"跳过玩家: {player}")
                break
            elif real_name in new_mappings.values():
                print(f"警告: '{real_name}' 已经映射给其他玩家")
                confirm = input("是否继续使用此名字? (y/n): ").lower()
                if confirm in ['y', 'yes']:
                    new_mappings[player] = real_name
                    print(f"已添加映射: {player} -> {real_name}")
                    added_count += 1
                    break
            else:
                new_mappings[player] = real_name
                print(f"已添加映射: {player} -> {real_name}")
                added_count += 1
                break
    
    if added_count == 0:
        print("\n没有添加任何新映射")
        return False
    
    # Save updated mappings
    try:
        os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(new_mappings, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 映射更新成功: {mapping_file}")
        print(f"新增映射: {added_count} 个")
        print(f"总映射数: {len(new_mappings)} 个")
        return True
    
    except Exception as e:
        print(f"\n❌ 保存映射失败: {e}")
        return False

def check_all_mappings_completeness():
    """Check mapping completeness for all log files"""
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        print("No logs directory found.")
        return
    
    log_files = glob.glob(os.path.join(logs_dir, '*.csv'))
    if not log_files:
        print("No CSV log files found.")
        return
    
    print("=" * 70)
    print("检查所有映射的完整性")
    print("=" * 70)
    
    incomplete_files = []
    
    for log_file in sorted(log_files):
        log_name = os.path.basename(log_file)
        log_name_base = log_name[:-4] if log_name.endswith('.csv') else log_name
        mapping_file = f'player_mappings/{log_name_base}_mapping.json'
        
        all_players, unmapped_players, existing_mappings = analyze_mapping_completeness(log_file, mapping_file)
        
        if all_players is None:
            print(f"❌ {log_name}: 无法分析文件")
            continue
        
        mapped_count = len(existing_mappings) if existing_mappings else 0
        total_count = len(all_players)
        unmapped_count = len(unmapped_players) if unmapped_players else 0
        
        if unmapped_count > 0:
            incomplete_files.append((log_file, mapping_file, unmapped_players))
            status = f"⚠️  未完成 ({mapped_count}/{total_count})"
        else:
            status = f"✅ 完整 ({mapped_count}/{total_count})"
        
        print(f"{status} {log_name}")
        
        if unmapped_count > 0:
            print(f"    未映射玩家: {', '.join(sorted(list(unmapped_players))[:3])}")
            if len(unmapped_players) > 3:
                print(f"    ... 还有 {len(unmapped_players) - 3} 个")
    
    print(f"\n{'='*70}")
    print(f"映射完整性总结:")
    print(f"  总日志文件: {len(log_files)}")
    print(f"  映射完整: {len(log_files) - len(incomplete_files)}")
    print(f"  映射不完整: {len(incomplete_files)}")
    
    return incomplete_files

def supplement_all_mappings_cli():
    """Supplement missing mappings for all log files using CLI"""
    incomplete_files = check_all_mappings_completeness()
    
    if not incomplete_files:
        print("\n🎉 所有映射都已完整！")
        return
    
    print(f"\n发现 {len(incomplete_files)} 个文件的映射不完整")
    
    # Ask user if they want to supplement all mappings
    try:
        confirm = input(f"\n是否要为所有不完整的映射文件补充缺失的玩家映射？(y/n): ").lower().strip()
        if confirm not in ['y', 'yes']:
            print("已取消映射补充。")
            return
    except (EOFError, KeyboardInterrupt):
        print("\n已取消映射补充。")
        return
    
    success_count = 0
    failed_count = 0
    total_added = 0
    
    for i, (log_file, mapping_file, unmapped_players) in enumerate(incomplete_files, 1):
        log_name = os.path.basename(log_file)
        
        print(f"\n{'='*70}")
        print(f"补充映射 {i}/{len(incomplete_files)}: {log_name}")
        print(f"需要补充 {len(unmapped_players)} 个玩家")
        print(f"{'='*70}")
        
        # Show current progress
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                existing_mappings = json.load(f)
            existing_count = len(existing_mappings)
        except:
            existing_count = 0
        
        if supplement_mapping_cli(log_file, mapping_file):
            print("✅ 映射补充成功!")
            success_count += 1
            
            # Calculate how many were actually added
            try:
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    updated_mappings = json.load(f)
                added = len(updated_mappings) - existing_count
                total_added += added
            except:
                pass
        else:
            print("❌ 映射补充失败或被取消")
            failed_count += 1
    
    print(f"\n{'='*70}")
    print("批量映射补充完成！")
    print(f"✅ 成功补充: {success_count} 个文件")
    print(f"❌ 失败/取消: {failed_count} 个文件")
    print(f"📊 总计新增映射: {total_added} 个")
    print("="*70)

def create_mapping_for_log(log_file, use_cli=False):
    """Create a new mapping for a specific log file interactively"""
    if not os.path.exists(log_file):
        print(f"日志文件不存在: {log_file}")
        return False
    
    print(f"为日志文件创建玩家映射: {log_file}")
    
    # Create parser and collect player names
    from poker_parser import PokerLogParser
    import csv
    import re
    
    parser = PokerLogParser(log_file)
    
    print("收集玩家名单...")
    with open(log_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            entry = row['entry']
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
                    parser.all_players.add(match)
    
    print(f"发现 {len(parser.all_players)} 个玩家")
    
    if use_cli:
        # Use command-line interface for mapping
        return create_mapping_cli(list(parser.all_players), parser.name_mapper.mapping_file)
    else:
        # Show mapping dialog
        if parser.name_mapper.show_mapping_dialog(list(parser.all_players)):
            mapping_file = parser.name_mapper.mapping_file
            print(f"映射保存在: {mapping_file}")
            return True
        else:
            print("❌ 用户取消了映射创建")
            return False

def create_mapping_cli(players, mapping_file):
    """Create player mapping using command-line interface"""
    print("\n" + "="*60)
    print("命令行玩家映射创建")
    print("="*60)
    print("为每个玩家输入真实姓名，或按Enter跳过")
    print("输入 'quit' 退出映射创建")
    print("-"*60)
    
    mappings = {}
    
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
            elif real_name in mappings.values():
                print(f"警告: '{real_name}' 已经映射给其他玩家")
                confirm = input("是否继续使用此名字? (y/n): ").lower()
                if confirm in ['y', 'yes']:
                    mappings[player] = real_name
                    print(f"已映射: {player} -> {real_name}")
                    break
            else:
                mappings[player] = real_name
                print(f"已映射: {player} -> {real_name}")
                break
    
    if not mappings:
        print("\n没有创建任何映射")
        return False
    
    # Save mappings
    try:
        os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 映射保存成功: {mapping_file}")
        print(f"创建了 {len(mappings)} 个玩家映射")
        return True
    
    except Exception as e:
        print(f"\n❌ 保存映射失败: {e}")
        return False

def list_log_files():
    """List all available log files"""
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        print("No logs directory found.")
        return []
    
    log_files = glob.glob(os.path.join(logs_dir, '*.csv'))
    
    if not log_files:
        print("No CSV log files found.")
        return []
    
    print(f"找到 {len(log_files)} 个日志文件:")
    for i, log_file in enumerate(sorted(log_files), 1):
        log_name = os.path.basename(log_file)
        mapping_file = f'player_mappings/{log_name[:-4]}_mapping.json'
        status = "✅ 已映射" if os.path.exists(mapping_file) else "⚠️ 未映射"
        print(f"  {i}. {log_name} {status}")
    
    return log_files

class MappingManagerGUI:
    def __init__(self):
        # Set language to English by default
        set_language('en')
        
        self.root = tk.Tk()
        self.root.title(get_text('app.title'))
        self.root.geometry("800x600")
        
        # 设置中文字体支持
        import tkinter.font as tkFont
        
        # 在Linux/WSL环境下设置中文字体
        try:
            # 获取系统可用字体
            available_fonts = list(tkFont.families())
            
            # 按优先级尝试中文字体
            chinese_fonts = [
                'WenQuanYi Zen Hei',  # 文泉驿正黑
                'WenQuanYi Micro Hei', # 文泉驿微米黑
                'Droid Sans Fallback', # Droid回退字体
                'DejaVu Sans',         # DejaVu字体
                'Arial'                # Arial作为最后备选
            ]
            
            selected_font = 'TkDefaultFont'  # 默认字体
            for font in chinese_fonts:
                if font in available_fonts:
                    selected_font = font
                    break
            
            # 设置默认字体
            default_font = tkFont.nametofont("TkDefaultFont")
            default_font.configure(family=selected_font, size=10)
            
            print(f"使用字体: {selected_font}")
            
        except Exception as e:
            print(f"字体设置失败: {e}")
            pass
        
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the GUI interface"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text=get_text('app.title'))
        title_label.pack(pady=(0, 20))
        
        # Notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Log Files Overview
        self.logs_frame = ttk.Frame(notebook)
        notebook.add(self.logs_frame, text=get_text('tabs.log_files'))
        self.setup_logs_tab()
        
        # Tab 2: Mappings Overview
        self.mappings_frame = ttk.Frame(notebook)
        notebook.add(self.mappings_frame, text=get_text('tabs.mappings'))
        self.setup_mappings_tab()
        
        # Tab 3: Batch Operations
        self.batch_frame = ttk.Frame(notebook)
        notebook.add(self.batch_frame, text=get_text('tabs.batch_ops'))
        self.setup_batch_tab()
        
    def setup_logs_tab(self):
        """Setup the log files tab"""
        # Header
        header_frame = ttk.Frame(self.logs_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text=get_text('log_files.header')).pack(side=tk.LEFT)
        
        ttk.Button(header_frame, text=get_text('log_files.buttons.refresh'), 
                  command=self.refresh_logs).pack(side=tk.RIGHT)
        
        # Logs treeview
        columns = (get_text('log_files.columns.filename'), get_text('log_files.columns.status'), 
                  get_text('log_files.columns.players'), get_text('log_files.columns.mapping_file'))
        self.logs_tree = ttk.Treeview(self.logs_frame, columns=columns, show='headings')
        
        column_widths = {get_text('log_files.columns.filename'): 250, get_text('log_files.columns.status'): 100, 
                        get_text('log_files.columns.players'): 80, get_text('log_files.columns.mapping_file'): 250}
        for col in columns:
            self.logs_tree.heading(col, text=col)
            self.logs_tree.column(col, width=column_widths.get(col, 150))
        
        # Scrollbar for logs tree
        logs_scrollbar = ttk.Scrollbar(self.logs_frame, orient=tk.VERTICAL, 
                                      command=self.logs_tree.yview)
        self.logs_tree.configure(yscrollcommand=logs_scrollbar.set)
        
        # Pack logs tree and scrollbar
        tree_frame = ttk.Frame(self.logs_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.logs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        logs_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.logs_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(buttons_frame, text=get_text('log_files.buttons.create_mapping'), 
                  command=self.create_selected_mapping).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text=get_text('log_files.buttons.edit_mapping'), 
                  command=self.edit_selected_mapping).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text=get_text('log_files.buttons.view_details'), 
                  command=self.view_mapping_details).pack(side=tk.LEFT)
        
        # Load initial data
        self.refresh_logs()
    
    def setup_mappings_tab(self):
        """Setup the mappings overview tab"""
        # Header
        header_frame = ttk.Frame(self.mappings_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text=get_text('mappings.header')).pack(side=tk.LEFT)
        
        ttk.Button(header_frame, text=get_text('log_files.buttons.refresh'), 
                  command=self.refresh_mappings).pack(side=tk.RIGHT)
        
        # Mappings display
        self.mappings_text = scrolledtext.ScrolledText(self.mappings_frame, 
                                                      wrap=tk.WORD, height=20)
        self.mappings_text.pack(fill=tk.BOTH, expand=True)
        
        # Load initial mappings
        self.refresh_mappings()
    
    def setup_batch_tab(self):
        """Setup the batch operations tab"""
        # Title
        ttk.Label(self.batch_frame, text=get_text('batch_ops.header')).pack(pady=(0, 20))
        
        # Operations frame
        ops_frame = ttk.LabelFrame(self.batch_frame, text=get_text('batch_ops.frame_title'))
        ops_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Create all mappings button
        create_all_frame = ttk.Frame(ops_frame)
        create_all_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(create_all_frame, text=get_text('batch_ops.create_all.button'), 
                  command=self.create_all_mappings).pack(side=tk.LEFT)
        ttk.Label(create_all_frame, 
                 text=get_text('batch_ops.create_all.description')).pack(side=tk.LEFT, padx=(10, 0))
        
        # Batch parse button
        parse_all_frame = ttk.Frame(ops_frame)
        parse_all_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(parse_all_frame, text=get_text('batch_ops.parse_all.button'), 
                  command=self.batch_parse_logs).pack(side=tk.LEFT)
        ttk.Label(parse_all_frame, 
                 text=get_text('batch_ops.parse_all.description')).pack(side=tk.LEFT, padx=(10, 0))
        
        # Status text
        status_frame = ttk.LabelFrame(self.batch_frame, text=get_text('batch_ops.status_title'))
        status_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.status_text = scrolledtext.ScrolledText(status_frame, wrap=tk.WORD, height=10)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
    def refresh_logs(self):
        """Refresh the logs treeview"""
        # Clear existing items
        for item in self.logs_tree.get_children():
            self.logs_tree.delete(item)
        
        # Get log files
        logs_dir = 'logs'
        if not os.path.exists(logs_dir):
            return
        
        log_files = glob.glob(os.path.join(logs_dir, '*.csv'))
        
        for log_file in sorted(log_files):
            log_name = os.path.basename(log_file)
            base_name = log_name[:-4] if log_name.endswith('.csv') else log_name
            mapping_file = f'player_mappings/{base_name}_mapping.json'
            
            if os.path.exists(mapping_file):
                status = get_text('log_files.status.mapped')
                try:
                    with open(mapping_file, 'r', encoding='utf-8') as f:
                        mappings = json.load(f)
                    players_count = len(mappings)
                except:
                    players_count = get_text('log_files.status.error')
            else:
                status = get_text('log_files.status.not_mapped')
                players_count = get_text('common.na')
            
            self.logs_tree.insert('', tk.END, values=(
                log_name, status, players_count, mapping_file if os.path.exists(mapping_file) else get_text('common.na')
            ))
    
    def refresh_mappings(self):
        """Refresh the mappings display"""
        self.mappings_text.delete(1.0, tk.END)
        
        mappings_dir = 'player_mappings'
        if not os.path.exists(mappings_dir):
            self.mappings_text.insert(tk.END, get_text('mappings.no_directory'))
            return
        
        mapping_files = glob.glob(os.path.join(mappings_dir, '*_mapping.json'))
        if not mapping_files:
            self.mappings_text.insert(tk.END, get_text('mappings.no_files'))
            return
        
        self.mappings_text.insert(tk.END, get_text('mappings.found_files', count=len(mapping_files)) + "\n\n")
        
        for mapping_file in sorted(mapping_files):
            log_name = os.path.basename(mapping_file).replace('_mapping.json', '')
            self.mappings_text.insert(tk.END, f"📁 {log_name}\n")
            
            try:
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    mappings = json.load(f)
                
                self.mappings_text.insert(tk.END, get_text('mappings.players_count', count=len(mappings)) + "\n")
                self.mappings_text.insert(tk.END, get_text('mappings.file_path', path=mapping_file) + "\n")
                
                # Show first few mappings
                items = list(mappings.items())[:3]
                for game_name, real_name in items:
                    self.mappings_text.insert(tk.END, f"     {game_name[:30]}... -> {real_name}\n")
                
                if len(mappings) > 3:
                    self.mappings_text.insert(tk.END, get_text('mappings.more_mappings', count=len(mappings) - 3) + "\n")
                    
            except Exception as e:
                self.mappings_text.insert(tk.END, get_text('mappings.read_error', error=str(e)) + "\n")
            
            self.mappings_text.insert(tk.END, "\n")
    
    def create_selected_mapping(self):
        """Create mapping for selected log file"""
        selected = self.logs_tree.selection()
        if not selected:
            messagebox.showwarning(get_text('dialogs.warning'), get_text('dialogs.select_file_first'))
            return
        
        item = self.logs_tree.item(selected[0])
        log_name = item['values'][0]
        log_file = f'logs/{log_name}'
        
        if create_mapping_for_log(log_file):
            messagebox.showinfo(get_text('dialogs.success'), get_text('dialogs.mapping_created'))
            self.refresh_logs()
            self.refresh_mappings()
        else:
            messagebox.showwarning(get_text('dialogs.cancelled'), get_text('dialogs.mapping_cancelled'))
    
    def edit_selected_mapping(self):
        """Edit mapping for selected log file"""
        selected = self.logs_tree.selection()
        if not selected:
            messagebox.showwarning(get_text('dialogs.warning'), get_text('dialogs.select_file_first'))
            return
        
        item = self.logs_tree.item(selected[0])
        log_name = item['values'][0]
        base_name = log_name[:-4] if log_name.endswith('.csv') else log_name
        mapping_file = f'player_mappings/{base_name}_mapping.json'
        
        if not os.path.exists(mapping_file):
            messagebox.showwarning(get_text('dialogs.warning'), get_text('dialogs.no_mapping_exists'))
            return
        
        # For now, just show the mapping details
        # In a full implementation, you could create an edit dialog
        self.view_mapping_details()
    
    def view_mapping_details(self):
        """View details of selected mapping"""
        selected = self.logs_tree.selection()
        if not selected:
            messagebox.showwarning(get_text('dialogs.warning'), get_text('dialogs.select_file_first'))
            return
        
        item = self.logs_tree.item(selected[0])
        log_name = item['values'][0]
        base_name = log_name[:-4] if log_name.endswith('.csv') else log_name
        mapping_file = f'player_mappings/{base_name}_mapping.json'
        
        if not os.path.exists(mapping_file):
            messagebox.showwarning(get_text('dialogs.warning'), get_text('dialogs.no_mapping_exists'))
            return
        
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mappings = json.load(f)
            
            # Create details window
            details_window = tk.Toplevel(self.root)
            details_window.title(get_text('details.window_title', name=base_name))
            details_window.geometry("600x400")
            
            # Title
            ttk.Label(details_window, text=get_text('details.header', name=base_name)).pack(pady=10)
            
            # Mappings display
            text_widget = scrolledtext.ScrolledText(details_window, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text_widget.insert(tk.END, get_text('details.total_mappings', count=len(mappings)) + "\n\n")
            for game_name, real_name in sorted(mappings.items()):
                text_widget.insert(tk.END, f"{game_name} -> {real_name}\n")
            
            text_widget.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror(get_text('dialogs.error'), get_text('dialogs.read_mapping_failed', error=str(e)))
    
    def create_all_mappings(self):
        """Create mappings for all unmapped log files"""
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(tk.END, get_text('batch_ops.starting') + "\n")
        self.status_text.update()
        
        result = messagebox.askyesno(get_text('batch_ops.confirm_title'), 
                                   get_text('batch_ops.confirm_message'))
        if result:
            create_all_mappings()
            self.refresh_logs()
            self.refresh_mappings()
            self.status_text.insert(tk.END, get_text('batch_ops.complete') + "\n")
    
    def batch_parse_logs(self):
        """Batch parse all logs with existing mappings"""
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(tk.END, get_text('batch_ops.not_implemented') + "\n")
        self.status_text.insert(tk.END, get_text('batch_ops.use_command') + "\n")
    
    def run(self):
        """Run the GUI"""
        self.root.mainloop()

def run_gui():
    """Launch the GUI application"""
    app = MappingManagerGUI()
    app.run()

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Poker玩家映射管理工具")
        print("="*40)
        print("用法:")
        print("  python3 manage_mappings.py gui               - 启动GUI界面")
        print("  python3 manage_mappings.py list              - 列出所有映射")
        print("  python3 manage_mappings.py logs              - 列出所有日志文件")
        print("  python3 manage_mappings.py show <log>        - 显示特定日志的映射")
        print("  python3 manage_mappings.py create <log>      - 为日志创建映射(GUI)")
        print("  python3 manage_mappings.py createcli <log>   - 为日志创建映射(命令行)")
        print("  python3 manage_mappings.py createall         - 为所有日志创建映射")
        print("  python3 manage_mappings.py createallcli      - 为所有日志创建映射(命令行)")
        print("  python3 manage_mappings.py check             - 检查所有映射的完整性")
        print("  python3 manage_mappings.py supplement <log>  - 补充单个日志的缺失映射")
        print("  python3 manage_mappings.py supplementall     - 补充所有日志的缺失映射")
        print("")
        print("示例:")
        print("  python3 manage_mappings.py gui")
        print("  python3 manage_mappings.py check")
        print("  python3 manage_mappings.py supplement logs/poker_log.csv")
        print("  python3 manage_mappings.py supplementall")
        print("  python3 manage_mappings.py show poker_now_log_pgl3Rc9zEebTOvy_wTLZXDzsf")
        return
    
    command = sys.argv[1]
    
    if command == 'gui':
        run_gui()
    
    elif command == 'list':
        list_all_mappings()
    
    elif command == 'logs':
        list_log_files()
    
    elif command == 'show':
        if len(sys.argv) < 3:
            print("请提供日志名称")
            return
        log_name = sys.argv[2]
        show_mapping_details(log_name)
    
    elif command == 'create':
        if len(sys.argv) < 3:
            print("请提供日志文件路径")
            return
        log_file = sys.argv[2]
        create_mapping_for_log(log_file)
    
    elif command == 'createcli':
        if len(sys.argv) < 3:
            print("请提供日志文件路径")
            return
        log_file = sys.argv[2]
        create_mapping_for_log(log_file, use_cli=True)
    
    elif command == 'createall':
        create_all_mappings()
    
    elif command == 'createallcli':
        create_all_mappings_cli()
    
    elif command == 'check':
        check_all_mappings_completeness()
    
    elif command == 'supplement':
        if len(sys.argv) < 3:
            print("请提供日志文件路径")
            return
        log_file = sys.argv[2]
        log_name_base = os.path.basename(log_file)
        if log_name_base.endswith('.csv'):
            log_name_base = log_name_base[:-4]
        mapping_file = f'player_mappings/{log_name_base}_mapping.json'
        supplement_mapping_cli(log_file, mapping_file)
    
    elif command == 'supplementall':
        supplement_all_mappings_cli()
    
    else:
        print(f"未知命令: {command}")
        print("使用 'python3 manage_mappings.py' 查看帮助")

if __name__ == "__main__":
    main()