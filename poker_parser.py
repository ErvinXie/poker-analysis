#!/usr/bin/env python3
import csv
import re
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import json
import tkinter as tk
from tkinter import ttk, messagebox
import os

class PlayerNameMapper:
    def __init__(self, log_file_path: str = None):
        """Initialize mapper for a specific log file"""
        if log_file_path:
            # Extract log file name without path and extension for mapping file name
            log_name = os.path.basename(log_file_path)
            if log_name.endswith('.csv'):
                log_name = log_name[:-4]
            self.mapping_file = f'player_mappings/{log_name}_mapping.json'
        else:
            self.mapping_file = 'player_mappings/default_mapping.json'
        
        self.name_mapping = {}
        self.load_mapping()
    
    def load_mapping(self):
        """Load existing player name mapping from file"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.mapping_file), exist_ok=True)
        
        if os.path.exists(self.mapping_file):
            try:
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    self.name_mapping = json.load(f)
            except:
                self.name_mapping = {}
    
    def save_mapping(self):
        """Save player name mapping to file"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.mapping_file), exist_ok=True)
        
        with open(self.mapping_file, 'w', encoding='utf-8') as f:
            json.dump(self.name_mapping, f, indent=2, ensure_ascii=False)
    
    def get_real_name(self, game_name: str) -> str:
        """Get real name for a game name, return game name if not mapped"""
        return self.name_mapping.get(game_name, game_name)
    
    def show_mapping_dialog(self, player_names: List[str]) -> bool:
        """Show GUI dialog to map player names to real names"""
        # Filter out players that are already mapped
        unmapped_players = [name for name in player_names if name not in self.name_mapping]
        
        if not unmapped_players:
            return True  # All players already mapped
        
        root = tk.Tk()
        root.title("Player Name Mapping")
        root.geometry("600x400")
        
        # Configure font for better Chinese display
        try:
            root.option_add('*Font', 'TkDefaultFont 12')
        except:
            pass
        
        # Create scrollable frame
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Please enter real names for players:", font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Scrollable frame for entries
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Entry widgets for each player
        entries = {}
        for i, player in enumerate(unmapped_players):
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, pady=5)
            
            # Game name label
            game_label = ttk.Label(frame, text=f"Game name: {player}", width=40, anchor="w")
            game_label.pack(side=tk.LEFT)
            
            # Real name entry
            real_name_var = tk.StringVar()
            real_name_entry = ttk.Entry(frame, textvariable=real_name_var, width=20)
            real_name_entry.pack(side=tk.RIGHT, padx=(10, 0))
            
            entries[player] = real_name_var
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        result = {'confirmed': False}
        
        def confirm_mapping():
            # Validate all entries are filled
            for player, var in entries.items():
                real_name = var.get().strip()
                if not real_name:
                    messagebox.showerror("Error", f"Please enter real name for '{player}'")
                    return
                self.name_mapping[player] = real_name
            
            self.save_mapping()
            result['confirmed'] = True
            root.destroy()
        
        def cancel_mapping():
            result['confirmed'] = False
            root.destroy()
        
        # Buttons
        ttk.Button(button_frame, text="Confirm", command=confirm_mapping).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=cancel_mapping).pack(side=tk.RIGHT)
        
        # Center the window
        root.transient()
        root.grab_set()
        root.focus_set()
        
        # Start the GUI
        root.mainloop()
        
        return result['confirmed']

@dataclass
class PlayerAction:
    player: str
    action: str  # fold, call, bet, raise, check, blind
    amount: Optional[int] = None
    timestamp: str = None
    stage: str = "preflop"  # preflop, flop, turn, river

@dataclass
class ShowdownInfo:
    player: str
    hole_cards: List[str]  # Player's hole cards
    hand_rank: Optional[str] = None  # e.g., "pair of tens", "flush", etc.

@dataclass 
class PokerHand:
    hand_id: str
    hand_number: int
    dealer: str
    players: List[str]
    player_stacks: Dict[str, int]
    
    # Actions organized by stage
    preflop_actions: List[PlayerAction] = None
    flop_actions: List[PlayerAction] = None
    turn_actions: List[PlayerAction] = None
    river_actions: List[PlayerAction] = None
    
    # Community cards by stage
    flop_cards: List[str] = None
    turn_card: str = None
    river_card: str = None
    
    # Showdown information
    showdown: List[ShowdownInfo] = None
    
    # Results
    pot_size: int = 0
    winner: str = None
    winning_amount: int = 0
    timestamp: str = None
    
    def __post_init__(self):
        if self.preflop_actions is None:
            self.preflop_actions = []
        if self.flop_actions is None:
            self.flop_actions = []
        if self.turn_actions is None:
            self.turn_actions = []
        if self.river_actions is None:
            self.river_actions = []
        if self.showdown is None:
            self.showdown = []
    
    @property
    def all_actions(self) -> List[PlayerAction]:
        """Get all actions across all stages"""
        return self.preflop_actions + self.flop_actions + self.turn_actions + self.river_actions
    
    @property
    def community_cards(self) -> List[str]:
        """Get all community cards"""
        cards = []
        if self.flop_cards:
            cards.extend(self.flop_cards)
        if self.turn_card:
            cards.append(self.turn_card)
        if self.river_card:
            cards.append(self.river_card)
        return cards

class PokerLogParser:
    def __init__(self, log_file_path: str = None):
        self.hands: List[PokerHand] = []
        self.current_hand: Optional[PokerHand] = None
        self.current_stage: str = "preflop"
        self.name_mapper = PlayerNameMapper(log_file_path)
        self.all_players = set()
        self.log_file_path = log_file_path
        
        # Setup output directory
        if log_file_path:
            log_name = os.path.basename(log_file_path)
            if log_name.endswith('.csv'):
                log_name = log_name[:-4]
            self.output_dir = f'outputs/{log_name}'
        else:
            self.output_dir = 'outputs/default'
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
    def clean_player_name(self, name: str) -> str:
        """Extract clean player name from quoted format"""
        if '"' in name:
            match = re.search(r'"([^"]+)"', name)
            game_name = match.group(1) if match else name
        else:
            game_name = name
        
        # Add to all players set for mapping later
        self.all_players.add(game_name)
        
        # Return real name if mapped, otherwise game name
        return self.name_mapper.get_real_name(game_name)
    
    def parse_amount(self, text: str) -> Optional[int]:
        """Extract amount from action text"""
        numbers = re.findall(r'\d+', text)
        return int(numbers[0]) if numbers else None
    
    def parse_cards(self, text: str) -> List[str]:
        """Extract cards from flop/turn/river text"""
        card_pattern = r'[AKQJT2-9][♠♥♦♣]'
        return re.findall(card_pattern, text)
    
    def parse_flop_cards(self, text: str) -> List[str]:
        """Parse flop cards from text like 'Flop: [Q♥, 6♠, 8♣]'"""
        # Extract cards within brackets
        bracket_match = re.search(r'\[(.*?)\]', text)
        if bracket_match:
            cards_str = bracket_match.group(1)
            return self.parse_cards(cards_str)
        return []
    
    def parse_turn_river_card(self, text: str) -> str:
        """Parse turn/river card from text like 'Turn: Q♥, 6♠, 8♣ [9♥]' """
        # Find the card in the final bracket
        bracket_match = re.search(r'\[([^]]+)\]', text)
        if bracket_match:
            card_str = bracket_match.group(1)
            cards = self.parse_cards(card_str)
            return cards[0] if cards else None
        return None
    
    def parse_hole_cards(self, text: str) -> List[str]:
        """Parse hole cards from showdown text like 'shows a 7♠, 10♥' or 'shows a K♥'"""
        # Find cards after "shows a"
        match = re.search(r'shows a (.+)', text)
        if match:
            cards_str = match.group(1).rstrip('.')
            return self.parse_cards(cards_str)
        return []
    
    def parse_player_stacks(self, text: str) -> Dict[str, int]:
        """Parse player stacks from stack line"""
        stacks = {}
        # Pattern: "Player Name @ id" (amount)
        pattern = r'"([^"]+)"\s*\((\d+)\)'
        matches = re.findall(pattern, text)
        for name, amount in matches:
            real_name = self.clean_player_name(f'"{name}"')
            stacks[real_name] = int(amount)
        return stacks
    
    def parse_log_file(self, file_path: str):
        """Parse the poker log CSV file"""
        # First read all rows and sort by order (ascending to get chronological order)
        rows = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        
        # Sort by order column in ascending order to get chronological sequence
        # The log file is in reverse chronological order, so we need to reverse it
        rows.sort(key=lambda x: int(x['order']) if x['order'].isdigit() else 0)
        
        # Now process entries in chronological order
        for row in rows:
            entry = row['entry']
            timestamp = row['at']
            
            self.process_entry(entry, timestamp)
        
        # Finalize the last hand if exists
        if self.current_hand:
            self.hands.append(self.current_hand)
    
    def process_entry(self, entry: str, timestamp: str):
        """Process a single log entry"""
        
        # Start of new hand
        if "-- starting hand #" in entry:
            if self.current_hand:
                self.hands.append(self.current_hand)
            
            # Extract hand info
            hand_match = re.search(r'hand #(\d+) \(id: (\w+)\).*dealer: "([^"]+)"', entry)
            if hand_match:
                hand_num = int(hand_match.group(1))
                hand_id = hand_match.group(2)
                dealer = self.clean_player_name(f'"{hand_match.group(3)}"')
                
                self.current_hand = PokerHand(
                    hand_id=hand_id,
                    hand_number=hand_num,
                    dealer=dealer,
                    players=[],
                    player_stacks={},
                    timestamp=timestamp
                )
                self.current_stage = "preflop"
        
        # End of hand
        elif "-- ending hand #" in entry:
            if self.current_hand:
                # Hand is complete, will be added to list when next hand starts
                pass
        
        # Player stacks
        elif "Player stacks:" in entry:
            if self.current_hand:
                stacks = self.parse_player_stacks(entry)
                self.current_hand.player_stacks = stacks
                self.current_hand.players = list(stacks.keys())
        
        # Community cards - Flop
        elif "Flop:" in entry:
            if self.current_hand:
                self.current_stage = "flop"
                self.current_hand.flop_cards = self.parse_flop_cards(entry)
        
        # Turn
        elif "Turn:" in entry:
            if self.current_hand:
                self.current_stage = "turn"
                self.current_hand.turn_card = self.parse_turn_river_card(entry)
        
        # River
        elif "River:" in entry:
            if self.current_hand:
                self.current_stage = "river"
                self.current_hand.river_card = self.parse_turn_river_card(entry)
        
        # Showdown - player shows cards
        elif " shows a " in entry:
            if self.current_hand:
                match = re.search(r'"([^"]+)" shows a', entry)
                if match:
                    player = self.clean_player_name(f'"{match.group(1)}"')
                    hole_cards = self.parse_hole_cards(entry)
                    showdown_info = ShowdownInfo(player=player, hole_cards=hole_cards)
                    self.current_hand.showdown.append(showdown_info)
        
        # Player actions
        elif self.current_hand:
            action_patterns = [
                # More specific patterns first to avoid incorrect matching  
                (r'"([^"]+)" posts a small blind of (\d+)', 'blind'),
                (r'"([^"]+)" posts a big blind of (\d+)', 'blind'),
                (r'"([^"]+)" raises to (\d+)', 'raise'),
                (r'"([^"]+)" raises by (\d+)', 'raise'),
                (r'"([^"]+)" bets (\d+)', 'bet'),
                (r'"([^"]+)" calls (\d+)', 'call'),
                (r'"([^"]+)" goes all-in with (\d+)', 'all-in'),
                (r'"([^"]+)" folds', 'fold'),
                (r'"([^"]+)" checks', 'check'),
                (r'"([^"]+)" collected (\d+) from pot', 'win'),
                (r'Uncalled bet of (\d+) returned to "([^"]+)"', 'return')
            ]
            
            for pattern, action_type in action_patterns:
                match = re.search(pattern, entry)
                if match:
                    if action_type == 'win':
                        player = self.clean_player_name(f'"{match.group(1)}"')
                        amount = int(match.group(2))
                        self.current_hand.winner = player
                        self.current_hand.winning_amount = amount
                        self.current_hand.pot_size = amount
                    elif action_type == 'return':
                        # Skip uncalled bets for now
                        pass
                    else:
                        player = self.clean_player_name(f'"{match.group(1)}"')
                        amount = None
                        if len(match.groups()) > 1 and match.group(2).isdigit():
                            amount = int(match.group(2))
                        
                        action = PlayerAction(
                            player=player,
                            action=action_type,
                            amount=amount,
                            timestamp=timestamp,
                            stage=self.current_stage
                        )
                        
                        # Add to appropriate stage
                        if self.current_stage == "preflop":
                            self.current_hand.preflop_actions.append(action)
                        elif self.current_stage == "flop":
                            self.current_hand.flop_actions.append(action)
                        elif self.current_stage == "turn":
                            self.current_hand.turn_actions.append(action)
                        elif self.current_stage == "river":
                            self.current_hand.river_actions.append(action)
                    break
    
    def get_statistics(self) -> Dict:
        """Get basic statistics from parsed hands"""
        stats = {
            'total_hands': len(self.hands),
            'players': set(),
            'total_pot': 0,
            'biggest_pot': 0,
            'player_wins': {},
            'player_actions': {}
        }
        
        for hand in self.hands:
            # Collect all players
            stats['players'].update(hand.players)
            
            # Pot statistics
            if hand.pot_size:
                stats['total_pot'] += hand.pot_size
                stats['biggest_pot'] = max(stats['biggest_pot'], hand.pot_size)
            
            # Winner statistics
            if hand.winner:
                stats['player_wins'][hand.winner] = stats['player_wins'].get(hand.winner, 0) + 1
            
            # Action statistics
            for action in hand.all_actions:
                player = action.player
                if player not in stats['player_actions']:
                    stats['player_actions'][player] = {'fold': 0, 'call': 0, 'bet': 0, 'raise': 0, 'check': 0, 'all-in': 0, 'blind': 0}
                if action.action in stats['player_actions'][player]:
                    stats['player_actions'][player][action.action] += 1
        
        stats['players'] = list(stats['players'])
        return stats
    
    def export_to_json(self, output_file: str = None):
        """Export parsed hands to JSON"""
        if output_file is None:
            output_file = os.path.join(self.output_dir, 'parsed_hands.json')
        hands_dict = []
        for hand in self.hands:
            def actions_to_dict(actions):
                return [
                    {
                        'player': action.player,
                        'action': action.action,
                        'amount': action.amount,
                        'timestamp': action.timestamp,
                        'stage': action.stage
                    }
                    for action in actions
                ]
            
            hand_dict = {
                'hand_id': hand.hand_id,
                'hand_number': hand.hand_number,
                'dealer': hand.dealer,
                'players': hand.players,
                'player_stacks': hand.player_stacks,
                
                # Community cards by stage
                'flop_cards': hand.flop_cards,
                'turn_card': hand.turn_card,
                'river_card': hand.river_card,
                'community_cards': hand.community_cards,  # All cards combined
                
                # Actions by stage
                'preflop_actions': actions_to_dict(hand.preflop_actions),
                'flop_actions': actions_to_dict(hand.flop_actions),
                'turn_actions': actions_to_dict(hand.turn_actions),
                'river_actions': actions_to_dict(hand.river_actions),
                'all_actions': actions_to_dict(hand.all_actions),  # All actions combined
                
                # Showdown info
                'showdown': [
                    {
                        'player': sd.player,
                        'hole_cards': sd.hole_cards,
                        'hand_rank': sd.hand_rank
                    }
                    for sd in hand.showdown
                ],
                
                # Results
                'pot_size': hand.pot_size,
                'winner': hand.winner,
                'winning_amount': hand.winning_amount,
                'timestamp': hand.timestamp
            }
            hands_dict.append(hand_dict)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(hands_dict, f, indent=2, ensure_ascii=False)
    
    def export_statistics(self, output_file: str = None):
        """Export game statistics to JSON"""
        if output_file is None:
            output_file = os.path.join(self.output_dir, 'game_statistics.json')
        
        stats = self.get_statistics()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
    
    def export_summary_report(self, output_file: str = None):
        """Export a human-readable summary report"""
        if output_file is None:
            output_file = os.path.join(self.output_dir, 'game_summary.txt')
        
        stats = self.get_statistics()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Poker Game Analysis Report\n")
            f.write(f"========================\n\n")
            
            if self.log_file_path:
                f.write(f"Log File: {os.path.basename(self.log_file_path)}\n")
            
            f.write(f"Total Hands: {stats['total_hands']}\n")
            f.write(f"Total Players: {len(stats['players'])}\n")
            f.write(f"Total Pot Amount: {stats['total_pot']}\n")
            f.write(f"Biggest Pot: {stats['biggest_pot']}\n\n")
            
            f.write(f"Players: {', '.join(stats['players'])}\n\n")
            
            f.write("Player Win Counts:\n")
            f.write("-" * 20 + "\n")
            for player, wins in sorted(stats['player_wins'].items(), 
                                     key=lambda x: x[1], reverse=True):
                f.write(f"{player}: {wins} wins\n")
            
            f.write("\nPlayer Actions Summary:\n")
            f.write("-" * 25 + "\n")
            for player, actions in stats['player_actions'].items():
                total_actions = sum(actions.values())
                f.write(f"{player}: {total_actions} total actions\n")
                for action, count in actions.items():
                    if count > 0:
                        f.write(f"  {action}: {count}\n")
                f.write("\n")

def main():
    log_file = 'logs/poker_now_log_pgl3Rc9zEebTOvy_wTLZXDzsf.csv'
    
    # First pass: collect all player names
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
    
    # Show mapping dialog
    print(f"发现 {len(parser_temp.all_players)} 个玩家")
    if not parser_temp.name_mapper.show_mapping_dialog(list(parser_temp.all_players)):
        print("用户取消了映射设置")
        return
    
    # Now parse with mappings
    parser = PokerLogParser(log_file)
    print(f"解析 {log_file}...")
    parser.parse_log_file(log_file)
    
    print(f"Parsed {len(parser.hands)} hands")
    
    # Get statistics
    stats = parser.get_statistics()
    print("\n=== Game Statistics ===")
    print(f"Total hands: {stats['total_hands']}")
    print(f"Players: {', '.join(stats['players'])}")
    print(f"Total pot amount: {stats['total_pot']}")
    print(f"Biggest pot: {stats['biggest_pot']}")
    
    print("\n=== Player Win Counts ===")
    for player, wins in sorted(stats['player_wins'].items(), key=lambda x: x[1], reverse=True):
        print(f"{player}: {wins} wins")
    
    # Export all outputs
    print(f"\n导出到目录: {parser.output_dir}/")
    parser.export_to_json()
    parser.export_statistics() 
    parser.export_summary_report()
    
    print("生成的文件:")
    print(f"  - {parser.output_dir}/parsed_hands.json")
    print(f"  - {parser.output_dir}/game_statistics.json") 
    print(f"  - {parser.output_dir}/game_summary.txt")
    
    # Show sample hand with detailed stages
    if parser.hands:
        print("\n=== Sample Hand (Detailed) ===")
        # Find a hand with showdown for better example
        sample = None
        for hand in parser.hands:
            if hand.showdown:
                sample = hand
                break
        if not sample:
            sample = parser.hands[0]
            
        print(f"Hand #{sample.hand_number} (ID: {sample.hand_id})")
        print(f"Dealer: {sample.dealer}")
        print(f"Players: {', '.join(sample.players)}")
        
        # Show community cards by stage
        if sample.flop_cards:
            print(f"Flop: {', '.join(sample.flop_cards)}")
        if sample.turn_card:
            print(f"Turn: {sample.turn_card}")
        if sample.river_card:
            print(f"River: {sample.river_card}")
        
        # Show actions by stage
        if sample.preflop_actions:
            print(f"Preflop actions ({len(sample.preflop_actions)}):")
            for action in sample.preflop_actions[:5]:  # Show first 5
                amount_str = f" {action.amount}" if action.amount else ""
                print(f"  {action.player}: {action.action}{amount_str}")
        
        if sample.flop_actions:
            print(f"Flop actions ({len(sample.flop_actions)}):")
            for action in sample.flop_actions:
                amount_str = f" {action.amount}" if action.amount else ""
                print(f"  {action.player}: {action.action}{amount_str}")
        
        if sample.turn_actions:
            print(f"Turn actions ({len(sample.turn_actions)}):")
            for action in sample.turn_actions:
                amount_str = f" {action.amount}" if action.amount else ""
                print(f"  {action.player}: {action.action}{amount_str}")
        
        if sample.river_actions:
            print(f"River actions ({len(sample.river_actions)}):")
            for action in sample.river_actions:
                amount_str = f" {action.amount}" if action.amount else ""
                print(f"  {action.player}: {action.action}{amount_str}")
        
        # Show showdown
        if sample.showdown:
            print("Showdown:")
            for sd in sample.showdown:
                cards_str = ', '.join(sd.hole_cards) if sd.hole_cards else "folded"
                print(f"  {sd.player}: {cards_str}")
        
        print(f"Winner: {sample.winner} ({sample.winning_amount})")

if __name__ == "__main__":
    main()