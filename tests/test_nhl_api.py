#!/usr/bin/env python3
"""
Tests for the NHL API module

This module tests the NHL API functionality of the Ovechkin Goal Tracker.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import pytz
import requests

from ovechkin_tracker.nhl_api import (
    _make_api_request,
    get_ovechkin_stats,
    get_capitals_games_played,
    get_remaining_games,
    clear_cache
)


class TestNHLAPI:
    """Test cases for the NHL API module"""
    
    @patch('ovechkin_tracker.nhl_api.requests.get')
    def test_make_api_request_success(self, mock_requests_get):
        """Test making a successful API request"""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {'test': 'data'}
        mock_requests_get.return_value = mock_response
        
        # Call the function
        result = _make_api_request('https://example.com/api')
        
        # Verify the result and function calls
        assert result == {'test': 'data'}
        mock_requests_get.assert_called_once_with('https://example.com/api', timeout=3)
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()
    
    @patch('ovechkin_tracker.nhl_api.requests.get')
    def test_make_api_request_timeout(self, mock_requests_get):
        """Test API request with timeout"""
        # Setup mock to raise a timeout exception
        mock_requests_get.side_effect = requests.exceptions.Timeout('Connection timed out')
        
        # Call the function
        result = _make_api_request('https://example.com/api', retries=2)
        
        # Verify the result and function calls
        assert result is None
        assert mock_requests_get.call_count == 3  # Initial call + 2 retries
    
    @patch('ovechkin_tracker.nhl_api.requests.get')
    def test_make_api_request_http_error(self, mock_requests_get):
        """Test API request with HTTP error"""
        # Setup mock to raise an HTTP error
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError('404 Client Error')
        mock_response.status_code = 404
        mock_requests_get.return_value = mock_response
        
        # Call the function
        result = _make_api_request('https://example.com/api')
        
        # Verify the result
        assert result is None
    
    @patch('ovechkin_tracker.nhl_api._make_api_request')
    def test_get_ovechkin_stats(self, mock_make_request):
        """Test getting Ovechkin's stats"""
        # Setup mock
        mock_make_request.return_value = {'test': 'data'}
        
        # Clear the cache to ensure a fresh request
        get_ovechkin_stats.cache_clear()
        
        # Call the function
        result = get_ovechkin_stats()
        
        # Verify the result and function calls
        assert result == {'test': 'data'}
        mock_make_request.assert_called_once_with('https://api-web.nhle.com/v1/player/8471214/landing')
    
    @patch('ovechkin_tracker.nhl_api._make_api_request')
    def test_get_ovechkin_stats_failed_request(self, mock_make_request):
        """Test getting Ovechkin's stats when the request fails"""
        # Setup mock to return None (failed request)
        mock_make_request.return_value = None
        
        # Clear the cache to ensure a fresh request
        get_ovechkin_stats.cache_clear()
        
        # Call the function
        result = get_ovechkin_stats()
        
        # Verify the result
        assert result == {}
    
    @patch('ovechkin_tracker.nhl_api._make_api_request')
    def test_get_capitals_games_played(self, mock_make_request):
        """Test getting Capitals' games played"""
        # Setup mock
        mock_make_request.return_value = {
            'standings': [
                {'teamAbbrev': {'default': 'WSH'}, 'gamesPlayed': 25},
                {'teamAbbrev': {'default': 'PIT'}, 'gamesPlayed': 26}
            ]
        }
        
        # Clear the cache to ensure a fresh request
        get_capitals_games_played.cache_clear()
        
        # Call the function
        result = get_capitals_games_played()
        
        # Verify the result and function calls
        assert result == 25
        mock_make_request.assert_called_once_with('https://api-web.nhle.com/v1/standings/now')
    
    @patch('ovechkin_tracker.nhl_api._make_api_request')
    def test_get_capitals_games_played_team_not_found(self, mock_make_request):
        """Test getting Capitals' games played when team is not found"""
        # Setup mock with no Capitals team
        mock_make_request.return_value = {
            'standings': [
                {'teamAbbrev': {'default': 'PIT'}, 'gamesPlayed': 26},
                {'teamAbbrev': {'default': 'NYR'}, 'gamesPlayed': 27}
            ]
        }
        
        # Clear the cache to ensure a fresh request
        get_capitals_games_played.cache_clear()
        
        # Call the function
        result = get_capitals_games_played()
        
        # Verify the result
        assert result == 0
    
    @patch('ovechkin_tracker.nhl_api._make_api_request')
    def test_get_capitals_games_played_failed_request(self, mock_make_request):
        """Test getting Capitals' games played when the request fails"""
        # Setup mock to return None (failed request)
        mock_make_request.return_value = None
        
        # Clear the cache to ensure a fresh request
        get_capitals_games_played.cache_clear()
        
        # Call the function
        result = get_capitals_games_played()
        
        # Verify the result
        assert result == 0
    
    @patch('ovechkin_tracker.nhl_api._make_api_request')
    @patch('ovechkin_tracker.nhl_api.datetime')
    def test_get_remaining_games(self, mock_datetime, mock_make_request):
        """Test getting remaining games"""
        # Setup datetime mock
        mock_now = datetime(2025, 3, 14, 8, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.utcnow.return_value = mock_now
        mock_datetime.fromisoformat.side_effect = lambda x: datetime.fromisoformat(x.replace('Z', '+00:00'))
        
        # Setup API response mock
        future_date = (mock_now + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
        mock_make_request.return_value = {
            'games': [
                {
                    'gameDate': '2025-03-15',
                    'startTimeUTC': future_date,
                    'homeTeam': {
                        'abbrev': 'WSH',
                        'placeName': {'default': 'Washington'},
                        'commonName': {'default': 'Capitals'}
                    },
                    'awayTeam': {
                        'abbrev': 'PIT',
                        'placeName': {'default': 'Pittsburgh'},
                        'commonName': {'default': 'Penguins'}
                    }
                }
            ]
        }
        
        # Clear the cache to ensure a fresh request
        get_remaining_games.cache_clear()
        
        # Call the function
        result = get_remaining_games()
        
        # Verify the result and function calls
        assert len(result) == 1
        assert result[0]['opponent'] == 'Pittsburgh Penguins'
        assert result[0]['location'] == 'Home'
        assert '2025-03-15' in result[0]['date']
        mock_make_request.assert_called_once_with('https://api-web.nhle.com/v1/club-schedule-season/WSH/now')
    
    @patch('ovechkin_tracker.nhl_api._make_api_request')
    def test_get_remaining_games_failed_request(self, mock_make_request):
        """Test getting remaining games when the request fails"""
        # Setup mock to return None (failed request)
        mock_make_request.return_value = None
        
        # Clear the cache to ensure a fresh request
        get_remaining_games.cache_clear()
        
        # Call the function
        result = get_remaining_games()
        
        # Verify the result
        assert result == []
    
    @patch('ovechkin_tracker.nhl_api.get_ovechkin_stats.cache_clear')
    @patch('ovechkin_tracker.nhl_api.get_capitals_games_played.cache_clear')
    @patch('ovechkin_tracker.nhl_api.get_remaining_games.cache_clear')
    def test_clear_cache(self, mock_clear_remaining, mock_clear_games, mock_clear_stats):
        """Test clearing all caches"""
        # Call the function
        clear_cache()
        
        # Verify all cache_clear methods were called
        mock_clear_stats.assert_called_once()
        mock_clear_games.assert_called_once()
        mock_clear_remaining.assert_called_once()
