#!/usr/bin/env python3
"""
Update Website Script for Ovechkin Goal Tracker

This script updates the static website's index.html file with the latest
Ovechkin stats data, similar to what is sent in the email notifications.
"""

import os
import logging
import pytz
import subprocess
import json
from datetime import datetime
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_html_content(stats):
    """
    Generate HTML content for the static website based on Ovechkin stats
    
    Args:
        stats: Dictionary containing Ovechkin's stats
        
    Returns:
        str: HTML content for the website
    """
    # Import required modules
    from datetime import datetime
    import re
    
    # Extract key information
    total_goals = stats.get('flat_stats', {}).get('Total Number of Goals', 'N/A')
    goals_needed = stats.get('flat_stats', {}).get('Goals to Beat Gretzy', 'N/A')
    
    # Get the projected game dictionary from nested stats which has structured data
    projected_game_dict = stats.get('nested_stats', {}).get('record', {}).get('projected_game', {})
    
    # Format the projection string exactly as requested: "Saturday, April 12, 2025, 12:30 PM ET vs Columbus Blue Jackets (Away)"
    formatted_projection = "Projected Record-Breaking Game: "
    
    # Extract and format the date properly
    if projected_game_dict:
        # Try to get the raw date from the dictionary and convert it to the proper format
        raw_date = projected_game_dict.get('raw_date', '')
        day_of_week = ''
        
        # If we have a raw date in YYYY-MM-DD format, convert it to "Saturday, April 12, 2025" format
        if raw_date and re.match(r'\d{4}-\d{2}-\d{2}', raw_date):
            try:
                date_obj = datetime.strptime(raw_date, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%A, %B %d, %Y')
                formatted_projection += formatted_date
            except Exception:
                # If date parsing fails, try to use the 'date' field directly
                date_str = projected_game_dict.get('date', '')
                if date_str:
                    # Try to clean up the date string if it has European format in parentheses
                    if '(' in date_str:
                        parts = date_str.split('(')[0].strip()
                        # If it's in YYYY-MM-DD format, convert it
                        if re.match(r'\w+, \d{4}-\d{2}-\d{2}', parts):
                            try:
                                # Extract just the date part
                                date_part = parts.split(', ')[1]
                                date_obj = datetime.strptime(date_part, '%Y-%m-%d')
                                day_of_week = parts.split(',')[0]
                                formatted_date = f"{day_of_week}, {date_obj.strftime('%B %d, %Y')}"
                                formatted_projection += formatted_date
                            except Exception:
                                formatted_projection += parts
                        else:
                            formatted_projection += parts
                    else:
                        formatted_projection += date_str
        else:
            # If no raw_date, use the 'date' field
            date_str = projected_game_dict.get('date', '')
            if date_str:
                # Try to clean up the date string if it has European format in parentheses
                if '(' in date_str:
                    parts = date_str.split('(')[0].strip()
                    # If it's in YYYY-MM-DD format, convert it
                    if re.match(r'\w+, \d{4}-\d{2}-\d{2}', parts):
                        try:
                            # Extract just the date part
                            date_part = parts.split(', ')[1]
                            date_obj = datetime.strptime(date_part, '%Y-%m-%d')
                            day_of_week = parts.split(',')[0]
                            formatted_date = f"{day_of_week}, {date_obj.strftime('%B %d, %Y')}"
                            formatted_projection += formatted_date
                        except Exception:
                            formatted_projection += parts
                    else:
                        formatted_projection += parts
                else:
                    formatted_projection += date_str
    else:
        # Fallback to raw date if structured data isn't available
        projected_date_raw = stats.get('flat_stats', {}).get('Projected Date of Record-Breaking Goal', 'N/A')
        if projected_date_raw and projected_date_raw != 'N/A':
            try:
                date_obj = datetime.strptime(projected_date_raw, '%m/%d/%Y')
                formatted_projection += date_obj.strftime('%A, %B %d, %Y')
            except Exception:
                formatted_projection += projected_date_raw
    
    # Add time if available
    if projected_game_dict and 'time' in projected_game_dict:
        game_time = projected_game_dict['time']
        if game_time:
            formatted_projection += f", {game_time}"
    
    # Add team and location
    if projected_game_dict:
        team = projected_game_dict.get('opponent', '').split(',')[0].strip()
        location = projected_game_dict.get('location', '')
        
        if team:
            formatted_projection += f" vs {team}"
            if location:
                # Make sure location is properly formatted with parentheses
                if location.startswith('(') and location.endswith(')'):
                    formatted_projection += f" {location}"
                else:
                    formatted_projection += f" ({location})"
    else:
        # Fallback to raw game info if structured data isn't available
        projected_game_raw = stats.get('flat_stats', {}).get('Projected Record-Breaking Game', 'N/A')
        if projected_game_raw and projected_game_raw != 'N/A' and 'vs' in projected_game_raw:
            # Try to extract time information
            time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM)\s*ET)', projected_game_raw)
            if time_match and not ", " + time_match.group(1) in formatted_projection:
                formatted_projection += f", {time_match.group(1)}"
            
            team_info = projected_game_raw.split('vs')[1].strip()
            
            # Extract location if present
            if '(Home)' in team_info:
                team = team_info.replace('(Home)', '').strip()
                formatted_projection += f" vs {team} (Home)"
            elif '(Away)' in team_info:
                team = team_info.replace('(Away)', '').strip()
                formatted_projection += f" vs {team} (Away)"
            else:
                formatted_projection += f" vs {team_info}"
    
    # Calculate progress percentage
    try:
        progress_pct = round((int(total_goals) / 894) * 100, 1)
    except (ValueError, ZeroDivisionError):
        progress_pct = 0
    
    # Current time in ET for the footer
    current_time = datetime.now(pytz.timezone('America/New_York')).strftime('%Y-%m-%d %I:%M:%S %p ET')
    
    # Create HTML content with Washington Capitals colors and responsive design
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Meta tags for proper responsive behavior and character encoding -->
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ovechkin Goal Tracker | Washington Capitals</title>
    
    <!-- SEO Meta Tags -->
    <meta name="description" content="Track Alex Ovechkin's pursuit of Wayne Gretzky's all-time NHL goal record of 894 goals. Currently at {total_goals} goals with {goals_needed} to go.">
    <meta name="keywords" content="Alex Ovechkin, Washington Capitals, NHL, hockey, goal record, Wayne Gretzky, The Great Eight">
    <meta name="author" content="Ovechkin Goal Tracker">
    
    <!-- Open Graph / Social Media Meta Tags -->
    <meta property="og:title" content="The GR8 Chase - Ovechkin Goal Tracker">
    <meta property="og:description" content="Alex Ovechkin has scored {total_goals} goals and needs {goals_needed} more to break Wayne Gretzky's NHL record.">
    <meta property="og:type" content="website">
    <meta property="og:image" content="https://upload.wikimedia.org/wikipedia/commons/f/f3/Alex_Ovechkin_2018-05-21.jpg">
    
    <!-- Favicon -->
    <link rel="icon" href="assets/gr8.svg" type="image/svg+xml">
    <link rel="alternate icon" href="favicon.ico" type="image/x-icon">
    
    <!-- Google Fonts for clean typography -->
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
    
    <!-- Font Awesome for icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <style>
        /* CSS Variables for consistent theming and easy updates */
        :root {{
            /* Washington Capitals colors */
            --caps-red: #C8102E;       /* Primary red */
            --caps-blue: #041E42;      /* Navy blue */
            --caps-white: #FFFFFF;     /* White */
            --caps-light-gray: #F5F5F5; /* Light background */
            --caps-dark-gray: #333333;  /* Text color */
            --caps-silver: #A2AAAD;     /* Silver accent */
            
            /* Spacing variables */
            --spacing-xs: 0.25rem;
            --spacing-sm: 0.5rem;
            --spacing-md: 1rem;
            --spacing-lg: 1.5rem;
            --spacing-xl: 2rem;
            
            /* Font sizes */
            --font-small: 0.875rem;
            --font-medium: 1rem;
            --font-large: 1.25rem;
            --font-xl: 1.5rem;
            --font-xxl: 2rem;
            --font-huge: 3rem;
        }}
        
        /* Base styles and CSS Reset */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Roboto', sans-serif;
            line-height: 1.6;
            background-color: var(--caps-light-gray);
            color: var(--caps-dark-gray);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            background-image: linear-gradient(to bottom, #f9f9f9, #e9e9e9);
            position: relative;
        }}
        
        body::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url('https://upload.wikimedia.org/wikipedia/commons/f/f3/Alex_Ovechkin_2018-05-21.jpg');
            background-size: 80% auto;
            background-position: center;
            background-repeat: no-repeat;
            opacity: 0.15;
            pointer-events: none;
            z-index: -1;
            filter: contrast(1.2) saturate(1.2);
        }}
        
        /* Hero section with Ovechkin's stats - more compact */
        .hero {{
            background-color: var(--caps-blue);
            color: var(--caps-white);
            padding: var(--spacing-md) var(--spacing-lg);
            border-radius: 12px;
            margin-bottom: var(--spacing-md);
            text-align: center;
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
            width: 100%;
            max-width: 1200px;
            background-image: linear-gradient(135deg, var(--caps-blue) 0%, #0a2e5c 100%);
            position: relative;
            overflow: hidden;
            margin-top: var(--spacing-lg);
            transform: translateY(0);
            transition: transform 0.3s ease;
        }}
        
        .hero:hover {{
            transform: translateY(-5px);
        }}
        
        .hero::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url('https://www.transparenttextures.com/patterns/hockey.png');
            opacity: 0.1;
        }}
        
        .hero h1 {{
            font-size: var(--font-xxl);
            margin-bottom: var(--spacing-sm);
            font-family: 'Montserrat', sans-serif;
            text-transform: uppercase;
            letter-spacing: 2px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
            position: relative;
            display: inline-block;
        }}
        
        .hero h1::after {{
            content: '';
            position: absolute;
            bottom: -10px;
            left: 50%;
            transform: translateX(-50%);
            width: 80px;
            height: 3px;
            background-color: var(--caps-red);
            border-radius: 3px;
        }}
        
        .hero p {{
            font-size: var(--font-large);
            opacity: 0.9;
            max-width: 800px;
            margin: var(--spacing-md) auto 0;
        }}
        
        .projection-banner {{
            background-color: var(--caps-red);
            color: var(--caps-white);
            padding: var(--spacing-sm) var(--spacing-md);
            margin-top: var(--spacing-md);
            border-radius: 8px;
            font-weight: bold;
            display: inline-block;
            font-size: var(--font-large);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
            position: relative;
            z-index: 1;
        }}
        
        .projection-banner i {{
            margin-right: var(--spacing-xs);
        }}
        
        /* Main content wrapper - centers content and uses grid layout */
        .content-wrapper {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: var(--spacing-md);
            width: 100%;
            max-width: 1200px;
            margin-bottom: var(--spacing-md);
            padding: 0 var(--spacing-md);
        }}
        
        /* Stats cards - more compact and in a grid */
        .stats-container {{
            display: grid;
            grid-template-columns: 1fr;
            gap: var(--spacing-md);
            width: 100%;
        }}
        
        .stat-card {{
            background-color: var(--caps-white);
            border-radius: 12px;
            padding: var(--spacing-md);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border-left: 5px solid var(--caps-red);
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            min-height: 200px;
        }}
        
        .stat-card::after {{
            content: '';
            position: absolute;
            bottom: 0;
            right: 0;
            width: 40%;
            height: 40%;
            background-image: linear-gradient(135deg, transparent 50%, rgba(200, 16, 46, 0.05) 50%);
            border-radius: 0 0 12px 0;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.12);
        }}
        
        .stat-card h3 {{
            color: var(--caps-blue);
            margin-bottom: var(--spacing-sm);
            font-size: var(--font-large);
            font-family: 'Montserrat', sans-serif;
            display: inline-block;
            position: relative;
        }}
        
        .stat-card h3::after {{
            content: '';
            position: absolute;
            bottom: -5px;
            left: 0;
            width: 100%;
            height: 2px;
            background-color: var(--caps-red);
            border-radius: 2px;
        }}
        
        .stat-value {{
            font-size: var(--font-huge);
            font-weight: bold;
            color: var(--caps-red);
            margin: var(--spacing-sm) 0;
            display: block;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
            font-family: 'Montserrat', sans-serif;
            position: relative;
        }}
        
        .stat-value::before {{
            content: '';
            position: absolute;
            width: 30px;
            height: 30px;
            background-color: rgba(200, 16, 46, 0.1);
            border-radius: 50%;
            z-index: -1;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%) scale(3);
        }}
        
        /* Progress bar - full width and more visible */
        .progress-section {{
            background-color: var(--caps-white);
            border-radius: 12px;
            padding: var(--spacing-lg);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
            width: 100%;
            grid-column: 1 / -1; /* Spans full width in the grid */
            border-top: 5px solid var(--caps-blue);
            position: relative;
            overflow: hidden;
        }}
        
        .progress-section::before {{
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 150px;
            height: 150px;
            background-image: radial-gradient(circle, rgba(4, 30, 66, 0.05) 0%, transparent 70%);
            border-radius: 50%;
        }}
        
        .progress-section h3 {{
            color: var(--caps-blue);
            margin-bottom: var(--spacing-md);
            font-size: var(--font-xl);
            font-family: 'Montserrat', sans-serif;
            position: relative;
            display: inline-block;
        }}
        
        .progress-section h3::after {{
            content: '';
            position: absolute;
            bottom: -8px;
            left: 0;
            width: 50px;
            height: 3px;
            background-color: var(--caps-red);
            border-radius: 3px;
        }}
        
        .progress-bar {{
            background-color: #e0e0e0;
            height: 30px;
            border-radius: 15px;
            margin: var(--spacing-md) 0;
            overflow: hidden;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
            position: relative;
        }}
        
        .progress-fill {{
            background-color: var(--caps-red);
            width: {progress_pct}%;
            height: 100%;
            border-radius: 15px;
            transition: width 1.5s ease-in-out;
            position: relative;
            background-image: linear-gradient(45deg, 
                            rgba(255, 255, 255, 0.15) 25%, 
                            transparent 25%, 
                            transparent 50%, 
                            rgba(255, 255, 255, 0.15) 50%, 
                            rgba(255, 255, 255, 0.15) 75%, 
                            transparent 75%, 
                            transparent);
            background-size: 40px 40px;
            animation: progress-animation 2s linear infinite;
        }}
        
        .progress-fill::after {{
            content: '{progress_pct}%';
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            color: white;
            font-weight: bold;
            font-size: var(--font-medium);
            text-shadow: 1px 1px 1px rgba(0, 0, 0, 0.3);
        }}
        
        @keyframes progress-animation {{
            0% {{ background-position: 0 0; }}
            100% {{ background-position: 40px 0; }}
        }}
        
        .progress-text {{
            display: flex;
            justify-content: space-between;
            font-size: var(--font-medium);
            color: var(--caps-dark-gray);
            margin-top: var(--spacing-sm);
            font-weight: 500;
        }}
        
        .progress-text span:first-child {{
            font-weight: bold;
        }}
        
        .progress-text span:last-child {{
            color: var(--caps-blue);
            font-weight: bold;
        }}
        
        /* Responsive design adjustments */
        @media (max-width: 768px) {{
            .content-wrapper {{
                grid-template-columns: 1fr;
            }}
            
            .hero h1 {{
                font-size: var(--font-xl);
            }}
            
            .hero p {{
                font-size: var(--font-medium);
            }}
        }}
        
        /* Animation for page elements */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .hero, .stat-card, .progress-section {{
            animation: fadeIn 0.8s ease-out forwards;
        }}
        
        .hero {{ animation-delay: 0s; }}
        .stat-card:nth-child(1) {{ animation-delay: 0.1s; }}
        .stat-card:nth-child(2) {{ animation-delay: 0.2s; }}
        .progress-section {{ animation-delay: 0.3s; }}
        
        /* Footer with update time */
        footer {{
            background-color: var(--caps-blue);
            color: var(--caps-white);
            padding: var(--spacing-md);
            text-align: center;
            width: 100%;
            margin-top: auto;
            font-size: var(--font-small);
            position: relative;
        }}
        
        footer::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(90deg, var(--caps-white) 0%, var(--caps-white) 30%, var(--caps-red) 30%, var(--caps-red) 100%);
        }}
        
        .update-time {{
            font-style: italic;
            opacity: 0.8;
        }}
        
        .hero-link {{
            color: var(--caps-white);
            text-decoration: none;
        }}
        
        .hero-link:hover {{
            text-decoration: underline;
        }}
        
        /* Accessibility styles */
        .visually-hidden {{
            position: absolute;
            width: 1px;
            height: 1px;
            margin: -1px;
            padding: 0;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            border: 0;
        }}
        
        .footer-link {{
            color: var(--caps-white);
            text-decoration: underline;
            opacity: 0.9;
        }}
        
        .footer-link:hover {{
            opacity: 1;
            text-decoration: none;
        }}
        
        .attribution {{
            margin-top: var(--spacing-sm);
            font-size: 0.8rem;
            opacity: 0.8;
        }}
        
        .built-by {{
            margin-top: var(--spacing-sm);
            font-size: 0.8rem;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <!-- Schema.org structured data for better search engine understanding -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "SportsEvent",
        "name": "Alex Ovechkin's NHL Goal Record Chase",
        "description": "Tracking Alex Ovechkin's pursuit of Wayne Gretzky's all-time NHL goal record of 894 goals.",
        "performer": {{
            "@type": "Person",
            "name": "Alex Ovechkin",
            "affiliation": {{
                "@type": "SportsTeam",
                "name": "Washington Capitals"
            }}
        }},
        "organizer": {{
            "@type": "Organization",
            "name": "National Hockey League",
            "url": "https://www.nhl.com/"
        }},
        "startDate": "{formatted_projection}"
    }}
    </script>
    
    <header>
        <nav aria-label="Main Navigation" class="visually-hidden">
            <ul>
                <li><a href="#stats">Current Stats</a></li>
                <li><a href="#progress">Progress to Record</a></li>
            </ul>
        </nav>
    </header>
    
    <main>
        <div class="hero">
            <h1>The GR8 Chase</h1>
            <p>Tracking <a href="https://www.nhl.com/capitals/player/alex-ovechkin-8471214" target="_blank" class="hero-link">Alex Ovechkin's</a> pursuit of Wayne Gretzky's all-time NHL goal record of 894 goals</p>
            <div class="projection-banner">
                <i class="fas fa-calendar-alt"></i> {formatted_projection}
            </div>
        </div>
        
        <div class="content-wrapper">
            <div class="stats-container">
                <div class="stat-card" id="stats" aria-labelledby="current-goals">
                    <h3 id="current-goals">Current Goals</h3>
                    <span class="stat-value" aria-live="polite">{total_goals}</span>
                    <p>Ovechkin's career NHL goals</p>
                </div>
            </div>
            
            <div class="stats-container">
                <div class="stat-card" aria-labelledby="goals-needed">
                    <h3 id="goals-needed">Goals Needed</h3>
                    <span class="stat-value" aria-live="polite">{goals_needed}</span>
                    <p>Goals remaining to break Gretzky's record</p>
                </div>
            </div>
            
            <div class="progress-section" id="progress" aria-labelledby="progress-heading">
                <h3 id="progress-heading">Progress to Record</h3>
                <div class="progress-bar" role="progressbar" aria-valuenow="{progress_pct}" aria-valuemin="0" aria-valuemax="100">
                    <div class="progress-fill"></div>
                </div>
                <div class="progress-text">
                    <span>Current: {total_goals}</span>
                    <span>Goal: 894</span>
                </div>
            </div>
        </div>
    </main>
    
    <footer>
        <p>Last updated: <span class="update-time">{current_time}</span></p>
        <p class="built-by">Built by <a href="http://github.com/PaulDuvall/" class="footer-link" target="_blank" rel="noopener">Paul Duvall</a></p>
        <p class="attribution">Background image: <a href="https://commons.wikimedia.org/wiki/File:Alex_Ovechkin_2018-05-21.jpg" class="footer-link">Alex Ovechkin</a> by Michael Miller, <a href="https://creativecommons.org/licenses/by-sa/4.0/" class="footer-link">CC BY-SA 4.0</a></p>
    </footer>
</body>
</html>
"""
    
    return html


def update_website():
    """
    Generate a new index.html file with the latest Ovechkin stats and replace the existing one
    
    Returns:
        bool: True if website was updated successfully, False otherwise
    """
    try:
        # Get the project root directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        
        # Check if running in Lambda environment
        is_lambda = 'AWS_LAMBDA_FUNCTION_NAME' in os.environ
        
        # Try different approaches to get the Ovechkin stats
        # First, try direct import if the module is in the path
        try:
            logger.info("Attempting direct import of OvechkinData...")
            # Add project root to path if not already there
            if project_root not in sys.path and os.path.exists(os.path.join(project_root, 'ovechkin_tracker')):
                sys.path.insert(0, project_root)
                
            # Try direct import
            from ovechkin_tracker.ovechkin_data import OvechkinData
            stats = OvechkinData().get_all_stats()
            logger.info("Successfully imported OvechkinData directly")
        except ImportError as e:
            logger.warning(f"Direct import failed: {str(e)}. Trying subprocess approach...")
            # Fallback to subprocess approach for local environment
            cmd = [
                'python3', '-c',
                'from ovechkin_tracker.ovechkin_data import OvechkinData; import json; stats = OvechkinData().get_all_stats(); print(json.dumps(stats))'
            ]
            
            # Run the command from the project root to ensure proper imports
            result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True, check=True)
            
            # Parse the JSON output
            stats = json.loads(result.stdout)
        
        if 'error' in stats:
            error_msg = f"ERROR: Failed to calculate stats: {stats['error']}"
            logger.error(error_msg)
            print(error_msg)
            return False
        
        # Generate HTML content
        html_content = generate_html_content(stats)
        
        # Define the path to the index.html file
        # Use /tmp directory if running in Lambda environment
        if is_lambda:
            static_dir = os.path.join('/tmp', 'static')
            index_path = os.path.join(static_dir, 'index.html')
            logger.info(f"Running in Lambda environment, using temp directory: {static_dir}")
        else:
            static_dir = os.path.join(script_dir, 'static')
            index_path = os.path.join(static_dir, 'index.html')
            logger.info(f"Running in local environment, using directory: {static_dir}")
        
        # Create the static directory if it doesn't exist
        os.makedirs(static_dir, exist_ok=True)
        
        # Create assets directory in the static directory
        assets_dir = os.path.join(static_dir, 'assets')
        os.makedirs(assets_dir, exist_ok=True)
        
        # Copy the gr8.svg file to the assets directory
        source_svg = os.path.join(script_dir, 'assets', 'gr8.svg')
        target_svg = os.path.join(assets_dir, 'gr8.svg')
        
        if os.path.exists(source_svg):
            import shutil
            shutil.copy2(source_svg, target_svg)
            logger.info(f"Copied favicon from {source_svg} to {target_svg}")
        else:
            logger.warning(f"Favicon source file not found at {source_svg}")
        
        # Write the HTML content to the file, completely replacing the existing content
        with open(index_path, 'w') as f:
            f.write(html_content)
        
        success_msg = f"Website updated successfully at {index_path}"
        logger.info(success_msg)
        print(success_msg)
        return True
        
    except subprocess.CalledProcessError as e:
        error_msg = f"ERROR: Failed to get Ovechkin stats: {e.stderr}"
        logger.error(error_msg)
        print(error_msg)
        return False
    except Exception as e:
        error_msg = f"ERROR: Failed to update website: {str(e)}"
        logger.error(error_msg)
        print(error_msg)
        return False

if __name__ == "__main__":
    update_website()
