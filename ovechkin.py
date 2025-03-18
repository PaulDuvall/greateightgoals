#!/usr/bin/env python3
"""Ovechkin Goal Tracker

A simplified application to track Alex Ovechkin's progress toward breaking
Wayne Gretzky's NHL goal record and send email notifications with projections.

Follows the twelve-factor app methodology with configuration from AWS Parameter Store.
"""

import requests
import json
import boto3
import logging
import os
import sys
import io
from datetime import datetime, timedelta
import pytz
from botocore.exceptions import ClientError
import getpass

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
OVECHKIN_ID = '8471214'
SEASON_END_DATE = '2025-04-17'
GRETZKY_RECORD = 894
CAPITALS_TEAM_ID = 15  # Washington Capitals team ID
CAPITALS_TEAM_ABBREV = "WSH"  # Washington Capitals abbreviation

# ===== NHL API Functions =====

def get_ovechkin_stats():
    """Fetch Ovechkin's current season and team stats from NHL API"""
    url = f"https://api-web.nhle.com/v1/player/{OVECHKIN_ID}/landing"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()

def get_capitals_games_played():
    """Fetch Washington Capitals' games played from NHL API"""
    url = "https://api-web.nhle.com/v1/standings/now"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    # Find the Capitals in the standings data
    for team in data.get('standings', []):
        if team.get('teamAbbrev', {}).get('default') == 'WSH':
            return team.get('gamesPlayed', 0)
    
    # Fallback value if we can't find the Capitals
    return 0

def get_remaining_games():
    """Fetch the remaining schedule for the Washington Capitals using the NHL API."""
    # Set the current date in the proper format
    today = datetime.now().date()
    
    # Build the API URL using the working api-web.nhle.com endpoint
    schedule_url = f"https://api-web.nhle.com/v1/club-schedule-season/{CAPITALS_TEAM_ABBREV}/now"

    try:
        response = requests.get(schedule_url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching schedule data: {e}")
        return []

    remaining_games = []
    # Parse the games data from the new API format
    for game in data.get("games", []):
        # Get the game date and time
        game_date_str = game.get("gameDate", "")
        game_time_str = game.get("startTimeUTC", "")
        
        # Skip games that have already been played
        if not game_date_str or not game_time_str:
            continue
            
        # Create a datetime object from the UTC time
        try:
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
            
            # Determine the opponent
            if game.get("homeTeam", {}).get("abbrev") == CAPITALS_TEAM_ABBREV:
                # Capitals are the home team, so the opponent is the away team
                opponent_team = game.get("awayTeam", {})
                place_name = opponent_team.get("placeName", {}).get("default", "")
                common_name = opponent_team.get("commonName", {}).get("default", "")
                opponent = f"{place_name} {common_name}".strip()
                if not opponent:
                    opponent = "Unknown"
                location = "Home"
            else:
                # Capitals are the away team, so the opponent is the home team
                opponent_team = game.get("homeTeam", {})
                place_name = opponent_team.get("placeName", {}).get("default", "")
                common_name = opponent_team.get("commonName", {}).get("default", "")
                opponent = f"{place_name} {common_name}".strip()
                if not opponent:
                    opponent = "Unknown"
                location = "Away"
            
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

# ===== Stats Calculation Functions =====

def find_game_on_projected_date(projected_date):
    """Find the Capitals game on or closest to the projected record-breaking date"""
    # Get all remaining games
    remaining_games = get_remaining_games()
    
    if not remaining_games:
        return None
    
    # Convert projected_date to date object for comparison
    if isinstance(projected_date, str):
        try:
            projected_date = datetime.strptime(projected_date, '%m/%d/%Y').date()
        except ValueError:
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
            sorted_games = sorted(remaining_games, key=lambda g: datetime.strptime(g['date'].split(', ')[1].split(' (')[0], '%Y-%m-%d'))
            closest_game = sorted_games[-1]  # Get the last game
        except (ValueError, IndexError) as e:
            logger.error(f"Error sorting games: {e}")
            closest_game = remaining_games[-1]  # Fallback to the last game in the list
    
    return closest_game

def calculate_stats(return_dict=False):
    """Calculate Ovechkin's stats and projections"""
    try:
        # Get player and team stats
        data = get_ovechkin_stats()
        
        # Get career totals
        career = data.get('careerTotals', {}).get('regularSeason', {})
        total_goals = career.get('goals', 0)
        
        # Get current season stats from featuredStats
        current_season = data.get('featuredStats', {}).get('regularSeason', {})
        player_stats = current_season.get('subSeason', {})
        
        # Get Capitals games played dynamically
        team_games_played = get_capitals_games_played()
        
        ovechkin_games_played = player_stats.get('gamesPlayed', 0)
        goals_this_season = player_stats.get('goals', 0)
        
        # Calculate derived stats
        goals_at_season_start = total_goals - goals_this_season
        total_season_games = 82
        remaining_games = total_season_games - team_games_played
        games_ovie_missed = team_games_played - ovechkin_games_played
        goals_per_game = goals_this_season / ovechkin_games_played if ovechkin_games_played > 0 else 0
        projected_remaining_goals = round(goals_per_game * remaining_games)
        goals_to_beat_gretzky = GRETZKY_RECORD - total_goals + 1  # +1 to break record, not just tie
        
        # Calculate projected record-breaking date
        projected_date_obj = None
        if goals_per_game > 0:
            games_needed = goals_to_beat_gretzky / goals_per_game
            games_remaining_needed = round(games_needed)
            
            # Convert end date string to datetime
            end_date = datetime.strptime(SEASON_END_DATE, '%Y-%m-%d')
            now = datetime.now(pytz.timezone('America/New_York'))
            days_remaining = (end_date - now.replace(tzinfo=None)).days
            days_per_game = days_remaining / remaining_games if remaining_games > 0 else 0
            projected_days = days_per_game * games_remaining_needed
            projected_date_obj = now + timedelta(days=projected_days)
            projected_date_str = projected_date_obj.strftime('%m/%d/%Y')
        else:
            projected_date_str = "N/A"
        
        # Find the game on or closest to the projected record-breaking date
        record_game = find_game_on_projected_date(projected_date_obj) if projected_date_obj else None
        
        # Create record game info string
        record_game_info = "No game information available"
        record_game_dict = {}
        if record_game:
            # Get day of week for the game date
            game_date = datetime.strptime(record_game['date'].split(', ')[1].split(' (')[0], '%Y-%m-%d')
            day_of_week = game_date.strftime('%A')
            
            # Format dates in both US and European formats
            us_date = game_date.strftime('%Y-%m-%d')
            eu_date = game_date.strftime('%d.%m.%Y')
            
            record_game_info = f"{day_of_week}, {us_date} ({eu_date}), {record_game['time']} vs {record_game['opponent']} ({record_game['location']})"
            
            # Create record game dictionary
            record_game_dict = {
                "full_string": record_game_info,
                "date": f"{day_of_week}, {us_date} ({eu_date})",
                "time": record_game['time'],
                "opponent": record_game['opponent'],
                "location": record_game['location'],
                "raw_date": us_date
            }
        
        now = datetime.now(pytz.timezone('America/New_York'))
        now_str = now.strftime("%Y-%m-%d %I:%M:%S %p ET")
        
        # Create the stats dictionary
        stats = {
            "flat_stats": {
                "Games Ovie Played": ovechkin_games_played,
                "Games Ovie Missed": games_ovie_missed,
                "Games in Season": total_season_games,
                "Games Caps Played": team_games_played,
                "Remaining Games": remaining_games,
                "Goals Scored 24-25": goals_this_season,
                "Total Number of Goals at Beginning of Season": goals_at_season_start,
                "Total Number of Goals": total_goals,
                "Ovie # of Goals per game": round(goals_per_game, 2),
                "Gretzy Goals Record": GRETZKY_RECORD,
                "Goals to Beat Gretzy": goals_to_beat_gretzky,
                "Projected Remaining Goals this Season": projected_remaining_goals,
                "Last game of Season": SEASON_END_DATE,
                "Projected Date of Record-Breaking Goal": projected_date_str,
                "Projected Record-Breaking Game": record_game_info,
                "Last Updated": now_str
            },
            "nested_stats": {
                "player": {
                    "name": "Alex Ovechkin",
                    "goals": total_goals,
                    "gretzky_record": GRETZKY_RECORD,
                    "games_played": 1470,  # Career games played
                    "team": "Washington Capitals",
                    "goals_needed": goals_to_beat_gretzky,
                    "goals_per_game": round(total_goals / 1470, 3)  # Career goals per game
                },
                "season": {
                    "goals_this_season": goals_this_season,
                    "games_played": ovechkin_games_played,
                    "games_missed": games_ovie_missed,
                    "total_games": total_season_games,
                    "remaining_games": remaining_games,
                    "goals_per_game": round(goals_per_game, 3)
                },
                "team": {
                    "name": "Washington Capitals",
                    "record": "N/A",
                    "upcoming_games": get_remaining_games()
                },
                "record": {
                    "current_holder": "Wayne Gretzky",
                    "record_goals": GRETZKY_RECORD,
                    "projected_date": projected_date_str,
                    "projected_game": record_game_dict
                },
                "progress": {
                    "percentage": round((total_goals / GRETZKY_RECORD) * 100, 1),
                    "goals_needed": goals_to_beat_gretzky,
                    "goals_per_game_needed": round(goals_to_beat_gretzky / remaining_games, 2) if remaining_games > 0 else "N/A"
                },
                "meta": {
                    "last_updated": now_str,
                    "data_source": "NHL API",
                    "season_end": SEASON_END_DATE
                }
            }
        }
        
        if return_dict:
            return stats
        
        # Print stats in a readable format
        print("Ovechkin Goal Tracker - NHL Record Watch")
        print("===================================\n")
        
        for key, value in stats["flat_stats"].items():
            print(f"{key}: {value}")
            
        return stats
        
    except Exception as e:
        logger.error(f"Error calculating stats: {e}")
        if return_dict:
            return {"error": str(e)}
        else:
            print(f"Error: {e}")
            return None

# ===== Email Functions =====

def prompt_for_parameter(param_name, description=None):
    """Prompt the user to enter a value for a missing parameter
    
    Args:
        param_name: Name of the parameter
        description: Optional description of the parameter
        
    Returns:
        str: User-provided value for the parameter
    """
    prompt_text = f"Enter value for '{param_name}'"
    if description:
        prompt_text += f" ({description})"
    prompt_text += ": "
    
    # Use getpass for sensitive information
    if 'email' in param_name.lower():
        value = input(prompt_text)
    else:
        value = getpass.getpass(prompt_text)
    
    return value


def store_parameter(param_name, param_value, parameter_path='/ovechkin-tracker/'):
    """Store a parameter in AWS Systems Manager Parameter Store as a SecureString
    
    Args:
        param_name: Name of the parameter without the path prefix
        param_value: Value to store
        parameter_path: Path prefix for parameters in Parameter Store
        
    Returns:
        bool: True if parameter was stored successfully, False otherwise
    """
    try:
        # Create a boto3 client for SSM
        ssm = boto3.client('ssm')
        
        # Full parameter name with path
        full_param_name = f"{parameter_path.rstrip('/')}/{param_name}"
        
        # Put the parameter as a SecureString
        ssm.put_parameter(
            Name=full_param_name,
            Value=param_value,
            Type='SecureString',
            Overwrite=True
        )
        
        logger.info(f"Parameter '{param_name}' stored successfully in Parameter Store")
        return True
    except Exception as e:
        logger.error(f"Error storing parameter '{param_name}' in Parameter Store: {e}")
        return False


def get_parameter_store_config(parameter_path='/ovechkin-tracker/'):
    """Get configuration from AWS Systems Manager Parameter Store
    
    Args:
        parameter_path: Path prefix for parameters in Parameter Store
        
    Returns:
        dict: Configuration dictionary with all required parameters
    """
    try:
        # Create an SSM client
        ssm = boto3.client('ssm')
        
        # Get parameters by path
        response = ssm.get_parameters_by_path(
            Path=parameter_path,
            WithDecryption=True
        )
        
        # Extract parameters
        params = {}
        for param in response.get('Parameters', []):
            # Extract the parameter name from the path
            name = param['Name'].split('/')[-1]
            params[name] = param['Value']
        
        # Check required parameters and prompt for missing ones
        required_params = {
            'aws_region': 'AWS region for SES (e.g., us-east-1)',
            'sender_email': 'Email address to send from (must be verified in SES)',
            'recipient_email': 'Default email address to send to'
        }
        
        missing_params = []
        for param, description in required_params.items():
            if param not in params or not params[param].strip():
                missing_params.append((param, description))
        
        # If running in Lambda, we can't prompt for input
        if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ and missing_params:
            logger.error(f"Missing required parameters in Parameter Store: {', '.join([p[0] for p in missing_params])}")
            logger.error("Cannot prompt for parameters in Lambda environment")
            raise ValueError("Missing required parameters in Parameter Store")
        
        # Prompt for missing parameters and store them
        for param_name, description in missing_params:
            logger.info(f"Parameter '{param_name}' not found in Parameter Store or is empty")
            param_value = prompt_for_parameter(param_name, description)
            
            if param_value.strip():
                params[param_name] = param_value
                # Store the parameter for future use
                store_parameter(param_name, param_value, parameter_path)
            else:
                logger.error(f"No value provided for required parameter '{param_name}'")
                raise ValueError(f"Missing required parameter: {param_name}")
        
        logger.info("Using configuration from AWS Parameter Store")
        return params
    except (ClientError) as e:
        logger.warning(f"Error accessing Parameter Store: {e}")
        # If we can't access Parameter Store, prompt for all parameters
        if 'AWS_LAMBDA_FUNCTION_NAME' not in os.environ:
            logger.info("Prompting for all required parameters")
            params = {}
            required_params = {
                'aws_region': 'AWS region for SES (e.g., us-east-1)',
                'sender_email': 'Email address to send from (must be verified in SES)',
                'recipient_email': 'Default email address to send to'
            }
            
            for param_name, description in required_params.items():
                param_value = prompt_for_parameter(param_name, description)
                if param_value.strip():
                    params[param_name] = param_value
                else:
                    logger.error(f"No value provided for required parameter '{param_name}'")
                    raise ValueError(f"Missing required parameter: {param_name}")
            
            return params
        else:
            raise
    except Exception as e:
        logger.error(f"Unexpected error getting parameters: {e}")
        raise


def format_email_html(stats_text):
    """Format the stats as HTML for email"""
    # Convert plain text to HTML
    lines = stats_text.strip().split('\n')
    
    # Extract title and separator
    title = lines[0]
    separator = lines[1]
    
    # Process the stats
    stats_lines = lines[2:]
    stats_dict = {}
    for line in stats_lines:
        if ': ' in line:
            key, value = line.split(': ', 1)
            stats_dict[key] = value
    
    # Create HTML
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #C8102E; text-align: center; }} /* Capitals red */
            .stats-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .stats-table th, .stats-table td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            .stats-table th {{ background-color: #f2f2f2; }}
            .highlight {{ font-weight: bold; color: #C8102E; }}
            .footer {{ margin-top: 30px; text-align: center; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{title}</h1>
            
            <table class="stats-table">
                <tr>
                    <th>Statistic</th>
                    <th>Value</th>
                </tr>
    """
    
    # Add key stats with highlights
    highlight_keys = [
        "Total Number of Goals", 
        "Gretzy Goals Record", 
        "Goals to Beat Gretzy",
        "Projected Date of Record-Breaking Goal",
        "Projected Record-Breaking Game"
    ]
    
    for key, value in stats_dict.items():
        if key in highlight_keys:
            html += f'<tr><td>{key}</td><td class="highlight">{value}</td></tr>\n'
        else:
            html += f'<tr><td>{key}</td><td>{value}</td></tr>\n'
    
    # Add footer
    current_time = datetime.now(pytz.timezone('America/New_York'))
    formatted_time = current_time.strftime('%B %d, %Y %I:%M %p ET')
    
    html += f"""
            </table>
            
            <div class="footer">
                <p>Generated on {formatted_time}</p>
                <p>Ovechkin Tracker - NHL Goal Record Watch</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def send_email_ses(config, subject, text_content, html_content=None):
    """Send an email with Ovechkin stats using Amazon SES"""
    try:
        # Create an SES client
        ses = boto3.client('ses', region_name=config['aws_region'])
        
        # Prepare email content
        email_message = {
            'Subject': {'Data': subject},
            'Body': {
                'Text': {'Data': text_content}
            }
        }
        
        # Add HTML content if provided
        if html_content:
            email_message['Body']['Html'] = {'Data': html_content}
        
        # Send the email
        response = ses.send_email(
            Source=config['sender_email'],
            Destination={
                'ToAddresses': [config['recipient_email']]
            },
            Message=email_message
        )
        
        logger.info(f"Email sent! Message ID: {response['MessageId']}")
        return True
    except ClientError as e:
        logger.error(f"Error sending email: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email: {str(e)}")
        return False

def send_ovechkin_email(recipient_email=None):
    """Send an email with Ovechkin's stats and projected record-breaking date
    
    Args:
        recipient_email: Optional override for the recipient email address
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Get config from Parameter Store
        config = get_parameter_store_config()
        
        # Override recipient email if provided
        if recipient_email:
            config['recipient_email'] = recipient_email
        
        # Get stats from ovechkin_tracker
        stats = calculate_stats(return_dict=True)
        
        # Extract key information
        total_goals = stats.get('flat_stats', {}).get('Total Number of Goals', 'N/A')
        goals_needed = stats.get('flat_stats', {}).get('Goals to Beat Gretzy', 'N/A')
        projected_date = stats.get('flat_stats', {}).get('Projected Date of Record-Breaking Goal', 'N/A')
        projected_game = stats.get('flat_stats', {}).get('Projected Record-Breaking Game', 'N/A')
        
        # Create email subject
        subject = f"Ovechkin Goal Tracker: {total_goals} goals, {goals_needed} to break the record"
        
        # Create plain text content
        text_content = f"""Ovechkin Goal Tracker - NHL Record Watch
===================================

Current Status:
- Total Goals: {total_goals}
- Goals Needed to Break Gretzky's Record: {goals_needed}
- Projected Record-Breaking Date: {projected_date}
- Projected Record-Breaking Game: {projected_game}

This email was automatically generated by the Ovechkin Goal Tracker.
"""
        
        # Create HTML content
        html_content = format_email_html(text_content)
        
        # Send the email
        success = send_email_ses(config, subject, text_content, html_content)
        
        if success:
            logger.info(f"Email sent successfully to {config['recipient_email']}")
        else:
            logger.error(f"Failed to send email to {config['recipient_email']}")
        
        return success
    except Exception as e:
        logger.error(f"Error sending Ovechkin email: {e}")
        return False

# ===== Main Functions =====

def show_stats():
    """Display current Ovechkin stats"""
    calculate_stats()

def main():
    """Main function to handle command-line arguments"""
    if len(sys.argv) < 2:
        print("Usage: python ovechkin.py [stats|email|email-to <address>]")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'stats':
        show_stats()
    elif command == 'email':
        send_ovechkin_email()
    elif command == 'email-to' and len(sys.argv) > 2:
        send_ovechkin_email(sys.argv[2])
    else:
        print("Unknown command. Use 'stats', 'email', or 'email-to <address>'")

if __name__ == "__main__":
    main()
