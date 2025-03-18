#!/usr/bin/env python3
"""
Unit tests for the OvechkinData class

This module contains comprehensive unit tests for the OvechkinData class,
validating its functionality, getters, setters, and data processing methods.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime
import pytz

# Import the class to test
from ovechkin_tracker.ovechkin_data import OvechkinData


class TestOvechkinData(unittest.TestCase):
    """Test suite for the OvechkinData class"""

    @patch('ovechkin_tracker.ovechkin_data.get_ovechkin_stats')
    @patch('ovechkin_tracker.ovechkin_data.get_capitals_games_played')
    @patch('ovechkin_tracker.ovechkin_data.get_remaining_games')
    def setUp(self, mock_get_remaining_games, mock_get_capitals_games_played, mock_get_ovechkin_stats):
        """Set up test fixtures and mocks"""
        # Mock the NHL API responses
        mock_get_ovechkin_stats.return_value = {
            'careerTotals': {
                'regularSeason': {
                    'goals': 886
                }
            },
            'featuredStats': {
                'regularSeason': {
                    'subSeason': {
                        'gamesPlayed': 50,
                        'goals': 33
                    }
                }
            }
        }
        
        mock_get_capitals_games_played.return_value = 66
        
        # Mock the remaining games
        mock_get_remaining_games.return_value = [
            {
                'date': 'Saturday, 2025-04-12 (12.04.2025)',
                'time': '12:30 PM ET',
                'opponent': 'Columbus Blue Jackets',
                'location': 'Away'
            },
            {
                'date': 'Monday, 2025-04-14 (14.04.2025)',
                'time': '7:00 PM ET',
                'opponent': 'New York Rangers',
                'location': 'Home'
            }
        ]
        
        # Create an instance of OvechkinData with mocked data
        self.ovechkin_data = OvechkinData()
        
        # Reset the mocks for subsequent tests
        mock_get_ovechkin_stats.reset_mock()
        mock_get_capitals_games_played.reset_mock()
        mock_get_remaining_games.reset_mock()

    def test_initialization(self):
        """Test that the OvechkinData class initializes correctly"""
        # Verify that the class constants are set correctly
        self.assertEqual(self.ovechkin_data.GRETZKY_RECORD, 894)
        self.assertEqual(self.ovechkin_data.SEASON_END_DATE, '2025-04-17')
        
        # Verify that the data was fetched and calculated
        self.assertIsNotNone(self.ovechkin_data.get_flat_stats())
        self.assertIsNotNone(self.ovechkin_data.get_nested_stats())

    def test_getters(self):
        """Test all getter methods"""
        # Test basic getters
        self.assertEqual(self.ovechkin_data.get_ovechkin_games_played(), 50)
        self.assertEqual(self.ovechkin_data.get_games_ovie_missed(), 16)
        self.assertEqual(self.ovechkin_data.get_total_season_games(), 82)
        self.assertEqual(self.ovechkin_data.get_team_games_played(), 66)
        self.assertEqual(self.ovechkin_data.get_remaining_games(), 16)
        self.assertEqual(self.ovechkin_data.get_goals_this_season(), 33)
        self.assertEqual(self.ovechkin_data.get_goals_at_season_start(), 853)
        self.assertEqual(self.ovechkin_data.get_total_goals(), 886)
        self.assertAlmostEqual(self.ovechkin_data.get_goals_per_game(), 0.66)
        self.assertEqual(self.ovechkin_data.get_gretzky_record(), 894)
        self.assertEqual(self.ovechkin_data.get_goals_to_beat_gretzky(), 9)
        self.assertEqual(self.ovechkin_data.get_projected_remaining_goals(), 11)
        self.assertEqual(self.ovechkin_data.get_season_end_date(), '2025-04-17')
        
        # Test dictionary getters
        flat_stats = self.ovechkin_data.get_flat_stats()
        self.assertIsInstance(flat_stats, dict)
        self.assertIn('Games Ovie Played', flat_stats)
        
        nested_stats = self.ovechkin_data.get_nested_stats()
        self.assertIsInstance(nested_stats, dict)
        self.assertIn('player', nested_stats)
        
        all_stats = self.ovechkin_data.get_all_stats()
        self.assertIsInstance(all_stats, dict)
        self.assertIn('flat_stats', all_stats)
        self.assertIn('nested_stats', all_stats)

    def test_setters(self):
        """Test setter methods and verify they update related values"""
        # Test setting games played
        self.ovechkin_data.set_ovechkin_games_played(55)
        self.assertEqual(self.ovechkin_data.get_ovechkin_games_played(), 55)
        self.assertEqual(self.ovechkin_data.get_games_ovie_missed(), 11)  # 66 - 55
        
        # Test setting goals this season
        self.ovechkin_data.set_goals_this_season(40)
        self.assertEqual(self.ovechkin_data.get_goals_this_season(), 40)
        self.assertEqual(self.ovechkin_data.get_total_goals(), 893)  # 853 + 40
        
        # Test setting total goals
        self.ovechkin_data.set_total_goals(890)
        self.assertEqual(self.ovechkin_data.get_total_goals(), 890)
        self.assertEqual(self.ovechkin_data.get_goals_this_season(), 37)  # 890 - 853

    @patch('ovechkin_tracker.ovechkin_data.get_ovechkin_stats')
    @patch('ovechkin_tracker.ovechkin_data.get_capitals_games_played')
    @patch('ovechkin_tracker.ovechkin_data.get_remaining_games')
    def test_refresh_data(self, mock_get_remaining_games, mock_get_capitals_games_played, mock_get_ovechkin_stats):
        """Test that refresh_data updates all data"""
        # Set up new mock data
        mock_get_ovechkin_stats.return_value = {
            'careerTotals': {
                'regularSeason': {
                    'goals': 888
                }
            },
            'featuredStats': {
                'regularSeason': {
                    'subSeason': {
                        'gamesPlayed': 52,
                        'goals': 35
                    }
                }
            }
        }
        
        mock_get_capitals_games_played.return_value = 68
        
        # Call refresh_data
        self.ovechkin_data.refresh_data()
        
        # Verify that the data was updated
        self.assertEqual(self.ovechkin_data.get_ovechkin_games_played(), 52)
        self.assertEqual(self.ovechkin_data.get_team_games_played(), 68)
        self.assertEqual(self.ovechkin_data.get_total_goals(), 888)
        self.assertEqual(self.ovechkin_data.get_goals_this_season(), 35)

    def test_to_json(self):
        """Test that to_json returns valid JSON"""
        json_str = self.ovechkin_data.to_json()
        
        # Verify that the result is a string
        self.assertIsInstance(json_str, str)
        
        # Verify that the string can be parsed as JSON
        try:
            json_data = json.loads(json_str)
            self.assertIsInstance(json_data, dict)
            self.assertIn('flat_stats', json_data)
            self.assertIn('nested_stats', json_data)
        except json.JSONDecodeError:
            self.fail("to_json() did not return valid JSON")

    def test_to_html(self):
        """Test that to_html returns valid HTML"""
        html = self.ovechkin_data.to_html()
        
        # Verify that the result is a string
        self.assertIsInstance(html, str)
        
        # Verify that the HTML contains expected elements
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('<html', html)
        self.assertIn('Ovechkin Goal Tracker', html)
        self.assertIn(str(self.ovechkin_data.get_total_goals()), html)
        self.assertIn(str(self.ovechkin_data.get_goals_to_beat_gretzky()), html)

    @patch('builtins.print')
    def test_display_stats(self, mock_print):
        """Test that display_stats prints the expected output"""
        self.ovechkin_data.display_stats()
        
        # Verify that print was called
        mock_print.assert_called()
        
        # Verify that the header was printed
        mock_print.assert_any_call("Ovechkin Goal Tracker - NHL Record Watch")

    def test_find_game_on_projected_date(self):
        """Test the _find_game_on_projected_date method"""
        # Create a test date
        test_date = datetime(2025, 4, 12).date()
        
        # Create test games
        test_games = [
            {
                'date': 'Saturday, 2025-04-12 (12.04.2025)',
                'time': '12:30 PM ET',
                'opponent': 'Columbus Blue Jackets',
                'location': 'Away'
            },
            {
                'date': 'Monday, 2025-04-14 (14.04.2025)',
                'time': '7:00 PM ET',
                'opponent': 'New York Rangers',
                'location': 'Home'
            }
        ]
        
        # Call the method
        result = self.ovechkin_data._find_game_on_projected_date(test_date, test_games)
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result['opponent'], 'Columbus Blue Jackets')

    def test_build_stats_dictionaries(self):
        """Test that _build_stats_dictionaries creates the expected dictionaries"""
        # Call the method
        self.ovechkin_data._build_stats_dictionaries()
        
        # Verify the flat stats
        flat_stats = self.ovechkin_data.get_flat_stats()
        self.assertEqual(flat_stats['Games Ovie Played'], 50)
        self.assertEqual(flat_stats['Total Number of Goals'], 886)
        self.assertEqual(flat_stats['Goals to Beat Gretzy'], 9)
        
        # Verify the nested stats
        nested_stats = self.ovechkin_data.get_nested_stats()
        self.assertEqual(nested_stats['player']['goals'], 886)
        self.assertEqual(nested_stats['player']['goals_needed'], 9)
        self.assertEqual(nested_stats['season']['goals_this_season'], 33)


if __name__ == '__main__':
    unittest.main()
