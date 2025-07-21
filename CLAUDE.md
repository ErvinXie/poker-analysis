# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a comprehensive poker log analysis system that parses PokerNow CSV log files and provides detailed analysis including hand-by-hand breakdowns, player statistics, and real name mapping management. The system supports both Chinese and English interfaces with full internationalization.

## Core Architecture

### Data Flow Architecture
The system follows a three-stage pipeline:
1. **Log Ingestion** → Raw CSV files from PokerNow
2. **Player Mapping** → Anonymous game names to real names via JSON mapping files 
3. **Analysis & Export** → Structured JSON output with hand details, statistics, and summaries

### Key Components

**poker_parser.py** - Core parsing engine containing:
- `PokerLogParser`: Main parser class that processes CSV logs into structured poker hands
- `PlayerNameMapper`: Manages per-log-file player name mappings with GUI dialogs
- Data classes: `PokerHand`, `PlayerAction`, `ShowdownInfo` for structured hand representation
- Exports: JSON hand data, statistics, and human-readable summaries

**manage_mappings.py** - Comprehensive mapping management tool with:
- Full CLI interface with 11 commands (gui, check, supplement, createallcli, etc.)
- tkinter GUI with internationalized interface (tabs: Log Files, Mappings, Batch Operations)
- Mapping completeness analysis - identifies unmapped players within existing mapping files
- Batch operations for creating and supplementing mappings across multiple log files

**language_manager.py** - i18n system:
- Loads JSON language files from `locales/` directory
- Supports dot notation keys (e.g., 'dialogs.warning')
- Fallback mechanism: current language → default language → key itself
- Used throughout GUI components for Chinese/English text

## File Structure & Data Organization

```
├── logs/                          # Raw poker CSV files (gitignored)
├── player_mappings/              # JSON mapping files (one per log file)
│   └── {log_name}_mapping.json   # Game usernames → Real names
├── outputs/                      # Analysis results (gitignored)  
│   └── {log_name}/
│       ├── parsed_hands.json    # Structured hand data
│       ├── game_statistics.json # Player stats & analytics
│       └── game_summary.txt     # Human-readable report
└── locales/                     # Language files
    ├── en.json                  # English UI text
    └── zh.json                  # Chinese UI text
```

**Critical Design Pattern**: Each log file gets its own isolated mapping file and output directory. This enables processing multiple poker games independently without name conflicts.

## Essential Commands

### Main Processing Commands
```bash
# Core single-file processing (with GUI mapping dialog)
python3 poker_parser.py

# Batch process all logs with GUI dialogs for each
python3 batch_process.py

# Launch comprehensive mapping management GUI
python3 manage_mappings.py gui
```

### CLI Mapping Management
```bash
# Check completeness of ALL mappings (shows unmapped players)
python3 manage_mappings.py check

# Create mappings via command-line interface (no GUI)
python3 manage_mappings.py createcli logs/filename.csv
python3 manage_mappings.py createallcli

# Supplement existing mappings with missing players
python3 manage_mappings.py supplement logs/filename.csv
python3 manage_mappings.py supplementall

# View current mapping status and details
python3 manage_mappings.py logs
python3 manage_mappings.py list
python3 manage_mappings.py show log_name
```

## Key Technical Details

### Player Name Mapping System
- Each CSV log gets a corresponding `{log_name}_mapping.json` file
- Mapping files store `{"Game Username @ ID": "Real Name"}` pairs
- The system can detect unmapped players by comparing log file contents to mapping file keys
- GUI and CLI interfaces both support creating/supplementing mappings

### Poker Hand Parsing
- Parses 4 game stages: preflop, flop, turn, river
- Extracts community cards, player actions, bet amounts, and showdown information
- Uses regex patterns to parse PokerNow's specific log format
- Handles dealer rotation, blinds, and multiple betting rounds per stage

### Internationalization Architecture
- English is the default language (`language_manager.py` sets 'en' default)
- GUI components use `get_text('key.subkey')` instead of hardcoded strings  
- Language files use nested JSON structure for organized text management
- All user-facing text in manage_mappings.py is internationalized

### Output Generation
The parser generates three complementary output files:
1. **parsed_hands.json**: Complete structured data with all hand details, actions, and cards
2. **game_statistics.json**: Aggregated player metrics, win rates, and behavioral analysis  
3. **game_summary.txt**: Human-readable report with rankings and key insights

## Development Workflow

When adding new features:
1. Consider whether it affects single files vs. batch processing
2. For UI changes, update both GUI (tkinter) and CLI interfaces in manage_mappings.py
3. For new text, add entries to both `locales/en.json` and `locales/zh.json`  
4. Test with both complete and incomplete mapping scenarios
5. Ensure new functionality works across the 3-stage data pipeline

The codebase emphasizes user experience with both power-user CLI tools and approachable GUI interfaces, while maintaining data isolation between different poker games/logs.