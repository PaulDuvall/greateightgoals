#!/usr/bin/env python3
"""NHL API Module for Ovechkin Goal Tracker

This module handles all interactions with the NHL API to fetch
Ovechkin's stats and the Capitals' schedule.

Optimized for AWS Lambda with caching and improved error handling.
"""

import requests
import json
import logging
from datetime import datetime, timedelta
import pytz
from functools import lru_cache

# Set up logging
logger = logging.getLogger(__name__)

# Constants
OVECHKIN_ID = '8471214'
CAPITALS_TEAM_ID = 15  # Washington Capitals team ID
CAPITALS_TEAM_ABBREV = "WSH"  # Washington Capitals abbreviation
SEASON_END_DATE = '2025-04-17'

# Request timeout and retry configuration
REQUEST_TIMEOUT = 3  # Reduced timeout for Lambda environment
MAX_RETRIES = 2

# Cache configuration
CACHE_EXPIRY = 3600  # Cache expiry in seconds (1 hour)


def _make_api_request(url, timeout=REQUEST_TIMEOUT, retries=MAX_RETRIES):
    """Make an API request with retries and error handling
    
    Args:
        url (str): The API URL to request
        timeout (int): Request timeout in seconds
        retries (int): Number of retry attempts
        
    Returns:
        dict: JSON response or None if request failed
    """
    attempt = 0
    last_error = None
    
    while attempt <= retries:
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout as e:
            last_error = f"Request timed out: {e}"
            logger.warning(f"API request timed out (attempt {attempt+1}/{retries+1}): {url}")
        except requests.exceptions.HTTPError as e:
            last_error = f"HTTP error: {e}"
            # Don't retry 4xx errors, only 5xx
            if response.status_code >= 500:
                logger.warning(f"API server error (attempt {attempt+1}/{retries+1}): {url}, status: {response.status_code}")
            else:
                logger.error(f"API client error: {url}, status: {response.status_code}")
                break
        except requests.exceptions.RequestException as e:
            last_error = f"Request error: {e}"
            logger.warning(f"API request error (attempt {attempt+1}/{retries+1}): {url}")
        
        attempt += 1
    
    logger.error(f"Failed to make API request after {retries+1} attempts: {url}, error: {last_error}")
    return None


@lru_cache(maxsize=1)
def get_ovechkin_stats():
    """Fetch Ovechkin's current season and team stats from NHL API
    
    Returns:
        dict: Ovechkin's stats or empty dict if request failed
    """
    url = f"https://api-web.nhle.com/v1/player/{OVECHKIN_ID}/landing"
    data = _make_api_request(url)
    
    if not data:
        logger.error("Failed to fetch Ovechkin stats")
        return {}
    
    return data


@lru_cache(maxsize=1)
def get_capitals_games_played():
    """Fetch Washington Capitals' games played from NHL API
    
    Returns:
        int: Number of games played or 0 if request failed
    """
    url = "https://api-web.nhle.com/v1/standings/now"
    data = _make_api_request(url)
    
    if not data:
        logger.error("Failed to fetch standings data")
        return 0
    
    # Find the Capitals in the standings data
    for team in data.get('standings', []):
        if team.get('teamAbbrev', {}).get('default') == 'WSH':
            return team.get('gamesPlayed', 0)
    
    logger.warning("Could not find Capitals in standings data")
    return 0


@lru_cache(maxsize=1)
def get_remaining_games():
    """Fetch the remaining schedule for the Washington Capitals using the NHL API.
    
    Returns:
        list: List of remaining games or empty list if request failed
    """
    # Build the API URL using the working api-web.nhle.com endpoint
    schedule_url = f"https://api-web.nhle.com/v1/club-schedule-season/{CAPITALS_TEAM_ABBREV}/now"

    data = _make_api_request(schedule_url)
    if not data:
        logger.error("Failed to fetch schedule data")
        return []

    remaining_games = []
    today = datetime.now().date()
    
    # Parse the games data from the API format
    for game in data.get("games", []):
        # Get the game date and time
        game_date_str = game.get("gameDate", "")
        game_time_str = game.get("startTimeUTC", "")
        
        # Skip games that have already been played
        if not game_date_str or not game_time_str:
            continue
            
        try:
            # Create a datetime object from the UTC time
            utc_game_datetime = datetime.fromisoformat(game_time_str.replace("Z", "+00:00"))
            
            # Skip games that have already been played
            if utc_game_datetime.replace(tzinfo=None) < datetime.utcnow():
                continue
                
            # Convert to Eastern Time
            eastern = pytz.timezone('America/New_York')
            local_game_datetime = utc_game_datetime.astimezone(eastern)
            
            # US format (YYYY-MM-DD)
            us_date = local_game_datetime.strftime('%Y-%m-%d')
            
            # European format (DD.MM.YYYY)
            eu_date = local_game_datetime.strftime('%d.%m.%Y')
            
            # Time with timezone
            local_time = local_game_datetime.strftime('%I:%M %p ET')
            
            # Day of week
            day_of_week = local_game_datetime.strftime('%A')
            
            # Format for display with day of week
            display_date = f"{day_of_week}, {us_date} ({eu_date})"
            
            # Determine the opponent and location
            is_home_game = game.get("homeTeam", {}).get("abbrev") == CAPITALS_TEAM_ABBREV
            opponent_team = game.get("awayTeam" if is_home_game else "homeTeam", {})
            
            place_name = opponent_team.get("placeName", {}).get("default", "")
            common_name = opponent_team.get("commonName", {}).get("default", "")
            opponent = f"{place_name} {common_name}".strip() or "Unknown"
            location = "Home" if is_home_game else "Away"
            
            remaining_games.append({
                "date": display_date,
                "time": local_time,
                "opponent": opponent,
                "location": location
            })
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing game datetime: {e}")
            continue

    return remaining_games


def clear_cache():
    """Clear all function caches
    
    This is useful when you need to force a refresh of data
    """
    get_ovechkin_stats.cache_clear()
    get_capitals_games_played.cache_clear()
    get_remaining_games.cache_clear()
    logger.info("NHL API caches cleared")
