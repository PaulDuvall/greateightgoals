#!/usr/bin/env python3
"""
OvechkinData Class Module

This module provides a Python class that encapsulates Ovechkin's statistics and projections,
including goals needed to break Gretzky's record.

The class follows PEP8 style guidelines and includes detailed documentation.
"""

import logging
import json
from datetime import datetime, timedelta
import pytz
from functools import lru_cache
from typing import Dict, List, Any, Optional, Union

from ovechkin_tracker.nhl_api import get_ovechkin_stats, get_capitals_games_played, get_remaining_games

# Set up logging
logger = logging.getLogger(__name__)


class OvechkinData:
    """A class to encapsulate Ovechkin's statistics and projections.
    
    This class provides a structured way to access and manipulate Ovechkin's data,
    including current stats, projections, and record-breaking information.
    
    Attributes:
        GRETZKY_RECORD (int): Wayne Gretzky's career goals record (894)
        SEASON_END_DATE (str): The end date of the current NHL season
    """
    
    # Class constants
    GRETZKY_RECORD = 894
    SEASON_END_DATE = '2025-04-17'
    
    def __init__(self):
        """Initialize the OvechkinData class.
        
        Upon initialization, the class fetches the latest data from the NHL API
        and calculates all relevant statistics.
        """
        # Initialize data containers
        self._raw_data = {}
        self._flat_stats = {}
        self._nested_stats = {}
        self._record_game = None
        self._record_game_dict = {}
        
        # Initialize stat fields with default values
        self._ovechkin_games_played = 0
        self._games_ovie_missed = 0
        self._total_season_games = 82
        self._team_games_played = 0
        self._remaining_games = 0
        self._goals_this_season = 0
        self._goals_at_season_start = 0
        self._total_goals = 0
        self._goals_per_game = 0
        self._goals_to_beat_gretzky = 0
        self._projected_remaining_goals = 0
        self._projected_date_str = "N/A"
        self._record_game_info = "No game information available"
        self._last_updated = ""
        
        # Fetch and calculate the stats
        self._fetch_and_calculate_stats()
    
    def _fetch_and_calculate_stats(self) -> None:
        """Fetch data from NHL API and calculate all statistics.
        
        This private method is called during initialization to populate
        all the class attributes with the latest data.
        """
        try:
            # Get player and team stats
            self._raw_data = get_ovechkin_stats()
            if not self._raw_data:
                logger.error("Failed to calculate stats: No data returned from NHL API")
                return
            
            # Get career totals
            career = self._raw_data.get('careerTotals', {}).get('regularSeason', {})
            self._total_goals = career.get('goals', 0)
            
            # Get current season stats from featuredStats
            current_season = self._raw_data.get('featuredStats', {}).get('regularSeason', {})
            player_stats = current_season.get('subSeason', {})
            
            # Get Capitals games played dynamically
            self._team_games_played = get_capitals_games_played()
            
            self._ovechkin_games_played = player_stats.get('gamesPlayed', 0)
            self._goals_this_season = player_stats.get('goals', 0)
            
            # Calculate derived stats
            self._goals_at_season_start = self._total_goals - self._goals_this_season
            self._total_season_games = 82
            self._remaining_games = self._total_season_games - self._team_games_played
            self._games_ovie_missed = self._team_games_played - self._ovechkin_games_played
            
            # Avoid division by zero
            self._goals_per_game = self._goals_this_season / max(self._ovechkin_games_played, 1)
            self._projected_remaining_goals = round(self._goals_per_game * self._remaining_games)
            self._goals_to_beat_gretzky = self.GRETZKY_RECORD - self._total_goals + 1  # +1 to break record, not just tie
            
            # Calculate projected record-breaking date
            projected_date_obj = None
            if self._goals_per_game > 0:
                games_needed = self._goals_to_beat_gretzky / self._goals_per_game
                games_remaining_needed = round(games_needed)
                
                # Convert end date string to datetime
                end_date = datetime.strptime(self.SEASON_END_DATE, '%Y-%m-%d')
                now = datetime.now(pytz.timezone('America/New_York'))
                days_remaining = (end_date - now.replace(tzinfo=None)).days
                
                # Avoid division by zero
                days_per_game = days_remaining / max(self._remaining_games, 1)
                projected_days = days_per_game * games_remaining_needed
                projected_date_obj = now + timedelta(days=projected_days)
                self._projected_date_str = projected_date_obj.strftime('%m/%d/%Y')
            else:
                self._projected_date_str = "N/A"
            
            # Pre-fetch remaining games to avoid redundant API calls
            remaining_games_list = get_remaining_games()
            
            # Find the game on or closest to the projected record-breaking date
            self._record_game = self._find_game_on_projected_date(projected_date_obj, remaining_games_list) if projected_date_obj else None
            
            # Create record game info string
            self._record_game_info = "No game information available"
            self._record_game_dict = {}
            if self._record_game:
                # Get day of week for the game date
                game_date = datetime.strptime(self._record_game['date'].split(', ')[1].split(' (')[0], '%Y-%m-%d')
                day_of_week = game_date.strftime('%A')
                
                # Format dates in both US and European formats
                us_date = game_date.strftime('%Y-%m-%d')
                eu_date = game_date.strftime('%d.%m.%Y')
                
                self._record_game_info = f"{day_of_week}, {us_date} ({eu_date}), {self._record_game['time']} vs {self._record_game['opponent']} ({self._record_game['location']})"
                
                # Create record game dictionary
                self._record_game_dict = {
                    "full_string": self._record_game_info,
                    "date": f"{day_of_week}, {us_date} ({eu_date})",
                    "time": self._record_game['time'],
                    "opponent": self._record_game['opponent'],
                    "location": self._record_game['location'],
                    "raw_date": us_date
                }
            
            now = datetime.now(pytz.timezone('America/New_York'))
            self._last_updated = now.strftime("%Y-%m-%d %I:%M:%S %p ET")
            
            # Create the stats dictionaries
            self._build_stats_dictionaries()
            
        except Exception as e:
            logger.error(f"Error calculating stats: {e}", exc_info=True)
    
    def _find_game_on_projected_date(self, projected_date, games_cache=None):
        """Find the Capitals game on or closest to the projected record-breaking date.
        
        Args:
            projected_date: Date object or string in format '%m/%d/%Y'
            games_cache: Optional pre-fetched games list to avoid redundant API calls
            
        Returns:
            dict: Game information or None if no game is found
        """
        # Get all remaining games (use cache if provided)
        remaining_games = games_cache if games_cache is not None else get_remaining_games()
        
        if not remaining_games:
            logger.warning("No remaining games found when looking for projected date game")
            return None
        
        # Convert projected_date to date object for comparison
        if isinstance(projected_date, str):
            try:
                projected_date = datetime.strptime(projected_date, '%m/%d/%Y').date()
            except ValueError as e:
                logger.error(f"Invalid date format: {e}")
                return None
        elif isinstance(projected_date, datetime):
            projected_date = projected_date.date()
        
        # Find the game on or AFTER the projected date (never before)
        closest_game = None
        min_days_diff = float('inf')
        
        for game in remaining_games:
            # Extract the US date format from the display_date
            # Format is "Saturday, 2025-03-01 (01.03.2025)"
            try:
                # Extract the date part between the comma and the parenthesis
                date_str = game['date'].split(', ')[1].split(' (')[0]
                game_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                # Only consider games on or after the projected date
                if game_date >= projected_date:
                    days_diff = (game_date - projected_date).days
                    
                    if days_diff < min_days_diff:
                        min_days_diff = days_diff
                        closest_game = game
            except (ValueError, IndexError) as e:
                logger.error(f"Error processing date: {e}")
                continue
        
        # If no game is found on or after the projected date, find the last game of the season
        if closest_game is None and remaining_games:
            # Sort games by date
            try:
                sorted_games = sorted(remaining_games, 
                                     key=lambda g: datetime.strptime(g['date'].split(', ')[1].split(' (')[0], '%Y-%m-%d'))
                closest_game = sorted_games[-1]  # Get the last game
            except (ValueError, IndexError) as e:
                logger.error(f"Error sorting games: {e}")
                closest_game = remaining_games[-1]  # Fallback to the last game in the list
        
        return closest_game
    
    def _build_stats_dictionaries(self) -> None:
        """Build the flat and nested stats dictionaries.
        
        This private method is called during initialization to create
        the structured data dictionaries for easy access.
        """
        # Create the flat stats dictionary
        self._flat_stats = {
            "Games Ovie Played": self._ovechkin_games_played,
            "Games Ovie Missed": self._games_ovie_missed,
            "Games in Season": self._total_season_games,
            "Games Caps Played": self._team_games_played,
            "Remaining Games": self._remaining_games,
            "Goals Scored 24-25": self._goals_this_season,
            "Total Number of Goals at Beginning of Season": self._goals_at_season_start,
            "Total Number of Goals": self._total_goals,
            "Ovie # of Goals per game": round(self._goals_per_game, 2),
            "Gretzy Goals Record": self.GRETZKY_RECORD,
            "Goals to Beat Gretzy": self._goals_to_beat_gretzky,
            "Projected Remaining Goals this Season": self._projected_remaining_goals,
            "Last game of Season": self.SEASON_END_DATE,
            "Projected Date of Record-Breaking Goal": self._projected_date_str,
            "Projected Record-Breaking Game": self._record_game_info,
            "Last Updated": self._last_updated
        }
        
        # Create the nested stats dictionary
        remaining_games_list = get_remaining_games()
        self._nested_stats = {
            "player": {
                "name": "Alex Ovechkin",
                "goals": self._total_goals,
                "gretzky_record": self.GRETZKY_RECORD,
                "games_played": 1470,  # Career games played
                "team": "Washington Capitals",
                "goals_needed": self._goals_to_beat_gretzky,
                "goals_per_game": round(self._total_goals / 1470, 3)  # Career goals per game
            },
            "season": {
                "goals_this_season": self._goals_this_season,
                "games_played": self._ovechkin_games_played,
                "games_missed": self._games_ovie_missed,
                "total_games": self._total_season_games,
                "remaining_games": self._remaining_games,
                "goals_per_game": round(self._goals_per_game, 3)
            },
            "team": {
                "name": "Washington Capitals",
                "record": "N/A",
                "upcoming_games": remaining_games_list[:5]  # Only include next 5 games to reduce payload size
            },
            "record": {
                "current_holder": "Wayne Gretzky",
                "record_goals": self.GRETZKY_RECORD,
                "projected_date": self._projected_date_str,
                "projected_game": self._record_game_dict
            },
            "progress": {
                "percentage": round((self._total_goals / self.GRETZKY_RECORD) * 100, 1),
                "goals_needed": self._goals_to_beat_gretzky,
                "goals_per_game_needed": round(self._goals_to_beat_gretzky / max(self._remaining_games, 1), 2)
            },
            "meta": {
                "last_updated": self._last_updated,
                "data_source": "NHL API",
                "season_end": self.SEASON_END_DATE
            }
        }
    
    # Getter methods for all properties
    def get_ovechkin_games_played(self) -> int:
        """Get the number of games Ovechkin has played this season."""
        return self._ovechkin_games_played
    
    def get_games_ovie_missed(self) -> int:
        """Get the number of games Ovechkin has missed this season."""
        return self._games_ovie_missed
    
    def get_total_season_games(self) -> int:
        """Get the total number of games in an NHL season."""
        return self._total_season_games
    
    def get_team_games_played(self) -> int:
        """Get the number of games the Capitals have played this season."""
        return self._team_games_played
    
    def get_remaining_games(self) -> int:
        """Get the number of games remaining in the season."""
        return self._remaining_games
    
    def get_goals_this_season(self) -> int:
        """Get the number of goals Ovechkin has scored this season."""
        return self._goals_this_season
    
    def get_goals_at_season_start(self) -> int:
        """Get the number of goals Ovechkin had at the start of the season."""
        return self._goals_at_season_start
    
    def get_total_goals(self) -> int:
        """Get the total number of goals Ovechkin has scored in his career."""
        return self._total_goals
    
    def get_goals_per_game(self) -> float:
        """Get Ovechkin's goals per game this season."""
        return round(self._goals_per_game, 2)
    
    def get_gretzky_record(self) -> int:
        """Get Wayne Gretzky's career goals record."""
        return self.GRETZKY_RECORD
    
    def get_goals_to_beat_gretzky(self) -> int:
        """Get the number of goals Ovechkin needs to break Gretzky's record."""
        return self._goals_to_beat_gretzky
    
    def get_projected_remaining_goals(self) -> int:
        """Get the projected number of goals Ovechkin will score in the remaining games."""
        return self._projected_remaining_goals
    
    def get_season_end_date(self) -> str:
        """Get the end date of the current NHL season."""
        return self.SEASON_END_DATE
    
    def get_projected_date_str(self) -> str:
        """Get the projected date when Ovechkin will break Gretzky's record."""
        return self._projected_date_str
    
    def get_record_game_info(self) -> str:
        """Get information about the game when Ovechkin is projected to break the record."""
        return self._record_game_info
    
    def get_last_updated(self) -> str:
        """Get the timestamp when the data was last updated."""
        return self._last_updated
    
    def get_flat_stats(self) -> Dict[str, Any]:
        """Get all stats in a flat dictionary format."""
        return self._flat_stats
    
    def get_nested_stats(self) -> Dict[str, Any]:
        """Get all stats in a nested dictionary format."""
        return self._nested_stats
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get both flat and nested stats dictionaries."""
        return {
            "flat_stats": self._flat_stats,
            "nested_stats": self._nested_stats
        }
    
    # Setter methods for properties that might need updating
    def set_ovechkin_games_played(self, value: int) -> None:
        """Set the number of games Ovechkin has played this season."""
        self._ovechkin_games_played = value
        # Update games missed calculation
        self._games_ovie_missed = self._team_games_played - value
        self._build_stats_dictionaries()
    
    def set_goals_this_season(self, value: int) -> None:
        """Set the number of goals Ovechkin has scored this season."""
        self._goals_this_season = value
        # Update total goals accordingly
        self._total_goals = self._goals_at_season_start + value
        self._build_stats_dictionaries()
    
    def set_total_goals(self, value: int) -> None:
        """Set the total number of goals Ovechkin has scored in his career."""
        self._total_goals = value
        # Update goals this season accordingly
        self._goals_this_season = value - self._goals_at_season_start
        self._build_stats_dictionaries()
    
    def refresh_data(self) -> None:
        """Refresh all data from the NHL API and recalculate stats."""
        self._fetch_and_calculate_stats()
    
    def display_stats(self) -> None:
        """Print the current Ovechkin statistics."""
        print("Ovechkin Goal Tracker - NHL Record Watch")
        print(f"Total Goals: {self._total_goals}")
        print(f"Goals This Season: {self._goals_this_season}")
        print(f"Goals to Beat Gretzky: {self._goals_to_beat_gretzky}")
        print(f"Projected Record Date: {self._projected_date_str}")
        print(f"Record game info: {self._record_game_info}")
        print(f"Last Updated: {self._last_updated}")
    
    def to_json(self) -> str:
        """Convert all stats to a JSON string."""
        return json.dumps(self.get_all_stats(), indent=2)
    
    def to_html(self) -> str:
        """Generate an HTML representation of the stats."""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ovechkin Goal Tracker</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        h1 {
            color: #C8102E; /* Capitals red */
            border-bottom: 2px solid #041E42; /* Capitals blue */
            padding-bottom: 10px;
        }
        .stats-container {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }
        .stats-section {
            flex: 1;
            min-width: 300px;
            background-color: #f9f9f9;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .stats-item {
            margin-bottom: 10px;
        }
        .stats-label {
            font-weight: bold;
        }
        .highlight {
            color: #C8102E;
            font-weight: bold;
        }
        .footer {
            margin-top: 20px;
            font-size: 0.8em;
            color: #666;
            text-align: center;
        }
    </style>
</head>
<body>
    <h1>Ovechkin Goal Tracker - NHL Record Watch</h1>
    
    <div class="stats-container">
        <div class="stats-section">
            <h2>Current Status</h2>
"""
        
        # Add current status stats
        status_items = [
            ("Total Goals", self._total_goals),
            ("Gretzky Record", self.GRETZKY_RECORD),
            ("Goals Needed to Break Record", self._goals_to_beat_gretzky),
            ("Goals This Season", self._goals_this_season),
            ("Goals Per Game", round(self._goals_per_game, 2))
        ]
        
        for label, value in status_items:
            html += f"""            <div class="stats-item">
                <span class="stats-label">{label}:</span> 
                <span class="highlight">{value}</span>
            </div>
"""
        
        html += """        </div>
        
        <div class="stats-section">
            <h2>Season Information</h2>
"""
        
        # Add season information stats
        season_items = [
            ("Games Played", self._ovechkin_games_played),
            ("Games Missed", self._games_ovie_missed),
            ("Team Games Played", self._team_games_played),
            ("Remaining Games", self._remaining_games),
            ("Season End Date", self.SEASON_END_DATE)
        ]
        
        for label, value in season_items:
            html += f"""            <div class="stats-item">
                <span class="stats-label">{label}:</span> {value}
            </div>
"""
        
        html += """        </div>
        
        <div class="stats-section">
            <h2>Record Projection</h2>
"""
        
        # Add projection stats
        projection_items = [
            ("Projected Remaining Goals", self._projected_remaining_goals),
            ("Projected Record Date", self._projected_date_str),
            ("Projected Record Game", self._record_game_info)
        ]
        
        for label, value in projection_items:
            html += f"""            <div class="stats-item">
                <span class="stats-label">{label}:</span> {value}
            </div>
"""
        
        html += f"""        </div>
    </div>
    
    <div class="footer">
        Last Updated: {self._last_updated} | Data Source: NHL API
    </div>
</body>
</html>
"""
        
        return html
