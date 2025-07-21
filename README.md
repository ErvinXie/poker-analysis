# Poker Log Analysis Tool

一个用于解析和分析poker游戏日志的Python工具，支持多日志文件管理和玩家真名映射。

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
- GUI界面输入玩家真名
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
- 为每个文件分别设置映射
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

# 为特定日志创建映射
python3 manage_mappings.py create <log_file_path>

# 批量为所有日志创建映射
python3 manage_mappings.py createall
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

- **独立映射**: 每个日志文件有独立的玩家映射
- **阶段解析**: 准确识别游戏的4个阶段
- **Showdown识别**: 解析玩家亮牌信息
- **GUI友好**: 简单易用的映射设置界面
- **批量处理**: 支持一次处理多个日志文件
- **结构化输出**: 每个日志对应独立的输出目录

## 📝 示例

处理日志文件后，你将得到：
- 玩家"bb @ iwr6u9zGyq"映射为"小红"
- 解析221手牌局
- 小红获胜33次，排名第一
- 详细的动作统计和分析报告

## 🛠️ 依赖要求

- Python 3.7+
- tkinter (GUI界面)
- 标准库: json, csv, re, os, glob

## 📄 许可证

此项目仅供学习和分析使用。