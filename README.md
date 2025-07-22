# Poker Log Analysis Tool

一个用于解析和分析pokernow游戏日志的Python工具，支持多日志文件管理和玩家真名映射。此项目完全使用claude code编写。

## 📁 项目结构

```
poker-analysis/
├── logs/                                    # 原始poker日志文件
│   ├── poker_now_log_pgl3Rc9zEebTOvy_wTLZXDzsf.csv
│   └── poker_now_log_pglAFi9Mg7aYIU-MhLeQmJjlW.csv
├── player_mappings/                         # 玩家真名映射文件
│   └── poker_now_log_pgl3Rc9zEebTOvy_wTLZXDzsf_mapping.json
├── outputs/                                 # 解析结果输出
│   └── poker_now_log_pgl3Rc9zEebTOvy_wTLZXDzsf/
│       ├── parsed_hands.json              # 详细手牌数据
│       ├── game_statistics.json           # 游戏统计数据
│       └── game_summary.txt               # 可读性报告
└── 脚本文件/
    ├── poker_parser.py                     # 主解析器
    ├── batch_process.py                    # 批量处理脚本
    ├── manage_mappings.py                  # 映射管理工具
    └── demo_mapping.py                     # 演示脚本
```

## 🚀 主要功能

### 🃏 游戏阶段解析
- **Preflop**: 翻牌前动作
- **Flop**: 翻牌后动作（3张公共牌）
- **Turn**: 转牌动作（第4张公共牌）
- **River**: 河牌动作（第5张公共牌）

### 👥 玩家管理
- 每个日志文件独立的玩家真名映射
- 支持GUI和CLI两种映射输入方式
- 智能映射补充（只为未映射玩家创建映射）
- 自动保存和加载映射配置

### 🎯 详细数据
- 玩家手牌（showdown时）
- 按阶段划分的动作
- 底池大小和赢家信息
- 完整的社区牌记录

### 📊 统计分析
- 玩家胜率统计
- 动作频率分析
- 底池大小分析
- 可读性报告生成

## 📖 使用方法

### 1. 单文件处理
```bash
python3 poker_parser.py
```
- 处理默认日志文件
- 弹出GUI设置玩家真名映射
- 生成完整的解析结果

### 2. 批量处理
```bash
python3 batch_process.py
```
- 自动处理logs/目录下所有CSV文件
- **CLI命令行界面**设置玩家映射（非GUI）
- 智能检测未映射玩家，仅为需要的玩家创建映射
- 支持跳过（Enter）和退出（quit）操作
- 并行生成所有输出

### 3. 映射管理

#### GUI界面（推荐）
```bash
python3 manage_mappings.py gui
```
- **中文界面**，友好易用
- **三个标签页**：日志文件、映射管理、批量操作
- **可视化管理**所有映射
- **实时状态显示**：✅已映射 / ⚠️未映射
- **一键操作**：创建、编辑、查看详情
- **批量处理**支持

#### 命令行界面
```bash
# 查看所有日志文件和映射状态
python3 manage_mappings.py logs

# 查看所有现有映射
python3 manage_mappings.py list

# 查看特定日志的详细映射
python3 manage_mappings.py show <log_name>

# 为特定日志创建映射（CLI界面）
python3 manage_mappings.py createcli <log_file_path>

# 补充现有映射中缺少的玩家
python3 manage_mappings.py supplement <log_file_path>

# 批量创建所有日志的映射
python3 manage_mappings.py createallcli

# 检查所有映射的完整性
python3 manage_mappings.py check
```

## 📋 输出文件说明

### parsed_hands.json
包含所有手牌的详细数据：
```json
{
  "hand_id": "8v46qz5acokg",
  "hand_number": 221,
  "dealer": "李四",
  "players": ["小刚", "李四", "雷"],
  "flop_cards": ["8♥", "9♣", "9♠"],
  "turn_card": "5♠",
  "river_card": "9♥",
  "preflop_actions": [...],
  "flop_actions": [...],
  "showdown": [
    {
      "player": "小刚",
      "hole_cards": ["7♠", "10♥"]
    }
  ]
}
```

### game_statistics.json
游戏统计数据（JSON格式）

### game_summary.txt
可读性报告，包含：
- 基本统计信息
- 玩家胜率排名
- 详细动作分析

## 🔧 技术特点

- **时间顺序解析**: 自动处理PokerNow的倒序日志，确保手牌按正确时间顺序解析
- **完整行动识别**: 支持所有poker行动类型
  - ✅ `call` (跟注) - 含金额信息
  - ✅ `bet` (下注) 
  - ✅ `raise` (加注到/加注)
  - ✅ `fold` (弃牌)
  - ✅ `check` (过牌)
  - ✅ `all-in` (全押)
  - ✅ `blind` (小/大盲注)
- **独立映射**: 每个日志文件有独立的玩家映射
- **阶段解析**: 准确识别游戏的4个阶段（preflop/flop/turn/river）
- **Showdown识别**: 解析玩家亮牌信息
- **双界面支持**: GUI（单文件）+ CLI（批量处理）
- **智能映射补充**: 只为未映射玩家创建新映射
- **结构化输出**: 每个日志对应独立的输出目录

## 📝 示例

### 批量处理示例
```bash
python3 batch_process.py
```
```
============================================================
批量处理CLI映射功能演示
============================================================
发现 4 个日志文件:
  - poker_now_log_pgl3Rc9zEebTOvy_wTLZXDzsf.csv
  - poker_now_log_pglAFi9Mg7aYIU-MhLeQmJjlW.csv
  - poker_now_log_pglJMYVieA7X-ALkm1NjY4lbj.csv
  - poker_now_log_pgldHXSOe84InI8eDhQOANXkX.csv

处理: poker_now_log_pgl3Rc9zEebTOvy_wTLZXDzsf.csv
发现 3 个玩家
需要为 3 个未映射玩家创建映射

[1/3] 游戏用户名: Ray @ kvtFT6s9zr
真实姓名 (或按Enter跳过): Ray
已映射: Ray @ kvtFT6s9zr -> Ray

[2/3] 游戏用户名: 只玩AA @ oqITwo4YrW  
真实姓名 (或按Enter跳过): 小王
已映射: 只玩AA @ oqITwo4YrW -> 小王

✅ 映射保存成功
解析了 221 手牌
```

### 解析结果示例
处理日志文件后，你将得到：
- 玩家"Ray @ kvtFT6s9zr"映射为"Ray"
- 解析221手牌（按正确时间顺序：#1 → #221）
- 所有行动类型正确识别（call、bet、raise、fold、check等）
- 完整的阶段解析（preflop → flop → turn → river）

## 🛠️ 依赖要求

- Python 3.7+
- tkinter (GUI界面)
- 标准库: json, csv, re, os, glob

## ⚠️ 常见问题

### Q: 为什么解析的手牌顺序很重要？
**A**: PokerNow的CSV日志文件是倒序的（最新条目在前），但poker分析需要按时间顺序。本工具自动处理这个问题，确保手牌按正确顺序解析（#1 → #221）。

### Q: batch_process.py和单文件处理有什么区别？
**A**: 
- **单文件** (`poker_parser.py`): GUI界面输入玩家映射
- **批量处理** (`batch_process.py`): CLI命令行界面输入玩家映射，适合处理多个文件

### Q: 如何确认所有行动都被正确解析？
**A**: 查看输出的`parsed_hands.json`文件，确认每个action都有正确的`player`、`action`类型和`amount`（如适用）。

### Q: 映射文件在哪里？
**A**: 每个日志文件对应一个映射文件，保存在`player_mappings/`目录下，格式为`{log_name}_mapping.json`。

## 📄 许可证

此项目仅供学习和分析使用。