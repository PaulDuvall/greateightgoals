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
import shutil

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
    formatted_projection = "Record-Breaking Game: "
    
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
        progress_pct_str = str(progress_pct)
    except (ValueError, ZeroDivisionError):
        progress_pct = 0
        progress_pct_str = "0"
    
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
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;900&family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
    
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
            --caps-gold: #FFD700;       /* Celebration gold */
            
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
            --font-massive: 4.5rem;
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
            background-color: var(--caps-red);
            color: var(--caps-white);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            background-image: linear-gradient(135deg, var(--caps-red) 0%, #a00a24 100%);
            position: relative;
            overflow-x: hidden;
        }}
        
        body::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url('https://upload.wikimedia.org/wikipedia/commons/f/f3/Alex_Ovechkin_2018-05-21.jpg');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            opacity: 0.25;
            pointer-events: none;
            z-index: -1;
            filter: contrast(1.2) saturate(1.2);
        }}
        
        /* Hero section with Ovechkin's stats - more compact */
        .hero {{
            background-color: var(--caps-blue);
            color: var(--caps-white);
            padding: var(--spacing-lg) var(--spacing-xl);
            border-radius: 12px;
            margin-bottom: var(--spacing-lg);
            text-align: center;
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.25);
            width: 100%;
            max-width: 1200px;
            background-image: linear-gradient(135deg, var(--caps-blue) 0%, #0a2e5c 100%);
            position: relative;
            overflow: hidden;
            margin-top: var(--spacing-xl);
            border: 5px solid var(--caps-gold);
            animation: pulse 2s infinite alternate;
        }}
        
        @keyframes pulse {{
            0% {{ box-shadow: 0 0 20px var(--caps-gold); }}
            100% {{ box-shadow: 0 0 40px var(--caps-gold); }}
        }}
        
        .hero::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url('https://www.transparenttextures.com/patterns/hockey.png');
            opacity: 0.15;
        }}
        
        .hero h1 {{
            font-size: var(--font-massive);
            margin-bottom: var(--spacing-md);
            font-family: 'Montserrat', sans-serif;
            text-transform: uppercase;
            letter-spacing: 3px;
            text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.4);
            position: relative;
            display: inline-block;
            font-weight: 900;
            color: var(--caps-gold);
            -webkit-text-stroke: 2px var(--caps-blue);
            animation: glow 2s infinite alternate;
        }}
        
        @keyframes glow {{
            0% {{ text-shadow: 0 0 10px var(--caps-gold), 0 0 20px var(--caps-gold); }}
            100% {{ text-shadow: 0 0 20px var(--caps-gold), 0 0 30px var(--caps-gold); }}
        }}
        
        .hero h1::after {{
            content: '';
            position: absolute;
            bottom: -10px;
            left: 50%;
            transform: translateX(-50%);
            width: 100px;
            height: 4px;
            background-color: var(--caps-red);
            border-radius: 3px;
        }}
        
        .hero p {{
            font-size: var(--font-xl);
            opacity: 0.95;
            max-width: 800px;
            margin: var(--spacing-md) auto 0;
            font-weight: 700;
            color: var(--caps-white);
        }}
        
        .projection-banner {{
            background-color: var(--caps-red);
            color: var(--caps-white);
            padding: var(--spacing-md) var(--spacing-lg);
            margin-top: var(--spacing-lg);
            border-radius: 8px;
            font-weight: bold;
            display: inline-block;
            font-size: var(--font-xl);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
            position: relative;
            z-index: 1;
            border: 3px solid var(--caps-gold);
            animation: float 3s ease-in-out infinite;
        }}
        
        @keyframes float {{
            0% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-10px); }}
            100% {{ transform: translateY(0px); }}
        }}
        
        .projection-banner i {{
            margin-right: var(--spacing-xs);
            color: var(--caps-gold);
        }}
        
        /* Top stats and video layout */
        .top-content {{
            display: grid;
            grid-template-columns: 1fr 1fr 2fr;
            gap: var(--spacing-md);
            margin-bottom: var(--spacing-lg);
            width: 100%;
            align-items: stretch;
        }}
        
        .top-content .stat-card {{
            margin: 0;
            min-height: 280px;
        }}
        
        .top-content .video-section {{
            margin: 0;
            grid-column: 3;
            height: 100%;
            display: flex;
            flex-direction: column;
            background-color: var(--caps-white);
            border-radius: 12px;
            padding: var(--spacing-md);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
            border: 4px solid var(--caps-gold);
            min-height: 280px;
        }}
        
        .top-content .video-section h3 {{
            margin-top: 0;
            margin-bottom: var(--spacing-sm);
            color: var(--caps-blue);
            font-size: var(--font-xl);
            font-weight: 700;
            position: relative;
            display: inline-block;
        }}
        
        .top-content .video-section h3::after {{
            content: '';
            position: absolute;
            bottom: -8px;
            left: 0;
            width: 50px;
            height: 3px;
            background-color: var(--caps-red);
            border-radius: 3px;
        }}
        
        .top-content .video-container {{
            flex: 1;
            margin-bottom: 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .top-content .stats-container {{
            display: contents;
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
        
        /* Stats cards styling */
        .stats-container {{
            display: flex;
            justify-content: space-between;
            gap: var(--spacing-md);
            margin-bottom: var(--spacing-lg);
        }}
        
        .stat-card {{
            background-color: var(--caps-white);
            border-radius: 12px;
            padding: var(--spacing-md);
            text-align: center;
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
            flex: 1;
            border: 4px solid var(--caps-gold);
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-height: 280px; /* Fixed height to match video */
        }}
        
        .stat-card h3 {{
            color: var(--caps-blue);
            margin-bottom: var(--spacing-md);
            font-size: var(--font-xl);
            font-family: 'Montserrat', sans-serif;
            position: relative;
            display: inline-block;
            font-weight: 700;
        }}
        
        .stat-card h3::after {{
            content: '';
            position: absolute;
            bottom: -8px;
            left: 0;
            width: 50px;
            height: 3px;
            background-color: var(--caps-red);
            border-radius: 3px;
        }}
        
        .stat-value {{
            font-size: var(--font-huge);
            font-weight: bold;
            color: var(--caps-red);
            margin: var(--spacing-md) 0;
            display: block;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
            font-family: 'Montserrat', sans-serif;
            position: relative;
        }}
        
        .stat-value.record {{
            color: var(--caps-gold);
            font-size: calc(var(--font-huge) * 1.2);
            text-shadow: 2px 2px 4px rgba(200, 16, 46, 0.3);
        }}
        
        .stat-value::before {{
            content: '';
            position: absolute;
            width: 40px;
            height: 40px;
            background-color: rgba(200, 16, 46, 0.1);
            border-radius: 50%;
            z-index: -1;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%) scale(3.5);
        }}
        
        .stat-value.record::before {{
            background-color: rgba(255, 215, 0, 0.15);
        }}
        
        /* Records section - showcases Ovechkin's NHL records */
        .records-section {{
            background-color: var(--caps-white);
            border-radius: 12px;
            padding: var(--spacing-lg);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
            width: 100%;
            grid-column: 1 / -1; /* Spans full width in the grid */
            border: 4px solid var(--caps-gold);
            position: relative;
            overflow: hidden;
            animation: pulse 2s infinite alternate;
        }}
        
        .records-section::before {{
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 150px;
            height: 150px;
            background-image: radial-gradient(circle, rgba(4, 30, 66, 0.05) 0%, transparent 70%);
            border-radius: 50%;
        }}
        
        .records-section h3 {{
            color: var(--caps-blue);
            margin-bottom: var(--spacing-md);
            font-size: var(--font-xl);
            font-family: 'Montserrat', sans-serif;
            position: relative;
            display: inline-block;
            font-weight: 700;
        }}
        
        .records-section h3::after {{
            content: '';
            position: absolute;
            bottom: -8px;
            left: 0;
            width: 50px;
            height: 3px;
            background-color: var(--caps-red);
            border-radius: 3px;
        }}
        
        .records-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: var(--spacing-md);
            margin-top: var(--spacing-md);
        }}
        
        .record-item {{
            background-color: var(--caps-light-gray);
            padding: var(--spacing-md);
            border-radius: 8px;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
            display: flex;
            align-items: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border-left: 4px solid var(--caps-red);
        }}
        
        .record-item:hover {{
            transform: translateY(-5px);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
        }}
        
        .record-icon {{
            font-size: var(--font-huge);
            margin-right: var(--spacing-md);
            color: var(--caps-gold);
            background-color: var(--caps-blue);
            width: 60px;
            height: 60px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }}
        
        .record-details {{
            font-size: var(--font-medium);
        }}
        
        .record-details h4 {{
            font-weight: bold;
            margin-bottom: var(--spacing-xs);
            color: var(--caps-blue);
            font-size: var(--font-large);
        }}
        
        .record-details p {{
            color: var(--caps-dark-gray);
            font-size: var(--font-medium);
        }}
        
        /* Video section styling */
        .video-section {{
            background-color: var(--caps-white);
            border-radius: 12px;
            padding: var(--spacing-lg);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
            width: 100%;
            grid-column: 1 / -1; /* Spans full width in the grid */
            border: 4px solid var(--caps-gold);
            position: relative;
            overflow: hidden;
            margin-top: var(--spacing-lg);
            margin-bottom: var(--spacing-lg);
        }}
        
        .video-section h3 {{
            color: var(--caps-blue);
            margin-bottom: var(--spacing-md);
            font-size: var(--font-xl);
            font-family: 'Montserrat', sans-serif;
            position: relative;
            display: inline-block;
            font-weight: 700;
        }}
        
        .video-section h3::after {{
            content: '';
            position: absolute;
            bottom: -8px;
            left: 0;
            width: 50px;
            height: 3px;
            background-color: var(--caps-red);
            border-radius: 3px;
        }}
        
        .video-container {{
            position: relative;
            width: 100%;
            padding-bottom: 56.25%; /* 16:9 aspect ratio */
            height: 0;
            overflow: hidden;
            max-width: 800px;
            margin: 0 auto;
        }}
        
        .video-container iframe {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            border-radius: 8px;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
            border: none;
        }}
        
        /* Responsive design adjustments */
        @media (max-width: 768px) {{
            .stats-container {{
                flex-direction: column;
                gap: var(--spacing-md);
            }}
            
            .stat-card {{
                width: 100%;
                min-height: 220px;
            }}
            
            .hero h1 {{
                font-size: var(--font-xxl);
            }}
            
            .hero p {{
                font-size: var(--font-large);
            }}
            
            .records-grid {{
                grid-template-columns: 1fr;
            }}
            
            .video-container {{
                padding-bottom: 75%; /* Adjusted aspect ratio for mobile */
            }}
            
            .top-content {{
                grid-template-columns: 1fr;
                grid-template-rows: auto auto auto;
            }}
            
            .top-content .video-section {{
                grid-column: 1;
                margin-top: var(--spacing-md);
                min-height: 220px;
            }}
        }}
        
        /* Animation for page elements */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .hero, .stat-card, .records-section {{
            animation: fadeIn 0.8s ease-out forwards;
        }}
        
        .hero {{ animation-delay: 0s; }}
        .stat-card:nth-child(1) {{ animation-delay: 0.1s; }}
        .stat-card:nth-child(2) {{ animation-delay: 0.2s; }}
        .records-section {{ animation-delay: 0.3s; }}
        
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
            transition: all 0.3s ease;
        }}
        
        .hero-link:hover {{
            text-decoration: underline;
            color: var(--caps-silver);
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
            transition: all 0.3s ease;
        }}
        
        .footer-link:hover {{
            opacity: 1;
            text-decoration: none;
            color: var(--caps-silver);
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
        
        /* Refresh button styling */
        .refresh-button {{
            background-color: var(--caps-blue);
            color: var(--caps-white);
            border: none;
            border-radius: 4px;
            padding: 5px 10px;
            margin-left: 10px;
            cursor: pointer;
            font-size: 0.8rem;
            transition: background-color 0.3s ease;
        }}
        
        .refresh-button:hover {{
            background-color: var(--caps-red);
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
                <li><a href="#records">Ovechkin's NHL Records</a></li>
            </ul>
        </nav>
    </header>
    
    <main>
        <div class="hero">
            <h1>The GR8 Chase</h1>
            <p><a href="https://www.nhl.com/capitals/player/alex-ovechkin-8471214" target="_blank" class="hero-link">Alex Ovechkin</a> has officially surpassed Wayne Gretzky to become the NHL's all-time leading goal scorer!</p>
            <div class="projection-banner">
                <i class="fas fa-calendar-alt"></i> {formatted_projection}
            </div>
        </div>
        
        <div class="top-content">
            <div class="stats-container">
                <div class="stat-card" id="stats" aria-labelledby="current-goals">
                    <h3 id="current-goals">Ovechkin's Goals</h3>
                    <span class="stat-value record" aria-live="polite">{total_goals}</span>
                    <p>Current NHL career goals</p>
                </div>
                
                <div class="stat-card" aria-labelledby="goals-needed">
                    <h3 id="goals-needed">Goals to Break Record</h3>
                    <span class="stat-value" aria-live="polite">{goals_needed}</span>
                    <p>Goals needed to surpass Gretzky</p>
                </div>
            </div>
            
            <div class="video-section">
                <h3>Ovechkin's Record-Breaking Goal</h3>
                <div class="video-container">
                    <iframe src="https://www.youtube.com/embed/pPazSfir7-k" title="Alex Ovechkin Record-Breaking Goal" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
                </div>
            </div>
        </div>
        
        <div class="content-wrapper">
            <div class="records-section" id="records" aria-labelledby="records-heading">
                <h3 id="records-heading">Ovechkin's NHL Records</h3>
                <div class="records-container">
                    <div class="record-item">
                        <div class="record-icon"><i class="fas fa-trophy"></i></div>
                        <div class="record-details">
                            <h4>Most Power Play Goals</h4>
                            <p>All-time NHL leader with 300+ power play goals</p>
                        </div>
                    </div>
                    <div class="record-item">
                        <div class="record-icon"><i class="fas fa-fire"></i></div>
                        <div class="record-details">
                            <h4>Most Goals with One Franchise</h4>
                            <p>All goals scored with the Washington Capitals</p>
                        </div>
                    </div>
                    <div class="record-item">
                        <div class="record-icon"><i class="fas fa-bolt"></i></div>
                        <div class="record-details">
                            <h4>Most Seasons with 50+ Goals</h4>
                            <p>Nine seasons with 50 or more goals</p>
                        </div>
                    </div>
                    <div class="record-item">
                        <div class="record-icon"><i class="fas fa-crown"></i></div>
                        <div class="record-details">
                            <h4>Most Goals by a Left Winger</h4>
                            <p>Surpassed Luc Robitaille's previous record</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>
    
    <footer>
        <p>Last updated: <span class="update-time">{current_time}</span> <button id="refresh-btn" class="refresh-button"><i class="fas fa-sync-alt"></i> Refresh</button></p>
        <p class="built-by">Built by <a href="http://github.com/PaulDuvall/" class="footer-link" target="_blank" rel="noopener">Paul Duvall</a></p>
        <p class="attribution">Background image: <a href="https://commons.wikimedia.org/wiki/File:Alex_Ovechkin_2018-05-21.jpg" class="footer-link">Alex Ovechkin</a> by Michael Miller, <a href="https://creativecommons.org/licenses/by-sa/4.0/" class="footer-link">CC BY-SA 4.0</a></p>
    </footer>
    
    <script>
        // Add cache-busting to ensure fresh data
        document.getElementById('refresh-btn').addEventListener('click', function() {{
            location.reload();
        }});
    </script>
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
