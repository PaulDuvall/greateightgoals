#!/usr/bin/env python3
"""
Celebration Script for Ovechkin Goal Tracker

This script creates a celebratory version of the website to commemorate
Alex Ovechkin breaking Wayne Gretzky's NHL goal record.
"""

import os
import logging
import json
from datetime import datetime
import sys
import shutil

# Try to import pytz, but provide a fallback if not available
try:
    import pytz
    has_pytz = True
except ImportError:
    has_pytz = False

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_celebration_html_content():
    """
    Generate celebratory HTML content for Alex Ovechkin breaking Wayne Gretzky's goal record
    
    Returns:
        str: HTML content for the celebration website
    """
    # Current time in ET for the footer
    if has_pytz:
        current_time = datetime.now(pytz.timezone('America/New_York')).strftime('%Y-%m-%d %I:%M:%S %p ET')
    else:
        current_time = datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')
    
    # Today's date for the record-breaking announcement
    if has_pytz:
        today = datetime.now(pytz.timezone('America/New_York')).strftime('%A, %B %d, %Y')
    else:
        today = datetime.now().strftime('%A, %B %d, %Y')
    
    # Create HTML content with Washington Capitals colors and celebratory design
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Meta tags for proper responsive behavior and character encoding -->
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HISTORY MADE! Ovechkin Breaks Gretzky's Record | Washington Capitals</title>
    
    <!-- SEO Meta Tags -->
    <meta name="description" content="Alex Ovechkin has made history by breaking Wayne Gretzky's all-time NHL goal record of 894 goals. The Great 8 now stands alone with 895 goals!">
    <meta name="keywords" content="Alex Ovechkin, Washington Capitals, NHL, hockey, goal record, Wayne Gretzky, The Great Eight, record breaker">
    <meta name="author" content="Ovechkin Goal Tracker">
    
    <!-- Open Graph / Social Media Meta Tags -->
    <meta property="og:title" content="HISTORY MADE! Ovechkin Breaks Gretzky's Record">
    <meta property="og:description" content="Alex Ovechkin has made history by breaking Wayne Gretzky's all-time NHL goal record with 895 goals!">
    <meta property="og:type" content="website">
    <meta property="og:image" content="https://upload.wikimedia.org/wikipedia/commons/f/f3/Alex_Ovechkin_2018-05-21.jpg">
    
    <!-- Favicon -->
    <link rel="icon" href="assets/gr8.svg" type="image/svg+xml">
    <link rel="alternate icon" href="favicon.ico" type="image/x-icon">
    
    <!-- Google Fonts for clean typography -->
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;900&family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
    
    <!-- Font Awesome for icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <!-- Confetti JS for celebration effects -->
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
    
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
        
        /* Hero section with celebration announcement */
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
        }}
        
        .record-banner {{
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
        
        .record-banner i {{
            margin-right: var(--spacing-xs);
            color: var(--caps-gold);
        }}
        
        /* Main content wrapper */
        .content-wrapper {{
            display: grid;
            grid-template-columns: 1fr;
            gap: var(--spacing-lg);
            width: 100%;
            max-width: 1200px;
            margin-bottom: var(--spacing-lg);
            padding: 0 var(--spacing-md);
        }}
        
        /* Stats cards - celebratory style */
        .stats-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: var(--spacing-lg);
            width: 100%;
        }}
        
        .stat-card {{
            background-color: var(--caps-white);
            border-radius: 12px;
            padding: var(--spacing-lg);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border: 4px solid var(--caps-gold);
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            min-height: 250px;
            transform-style: preserve-3d;
            perspective: 1000px;
            animation: card-entrance 1s ease-out forwards;
        }}
        
        @keyframes card-entrance {{
            from {{ opacity: 0; transform: translateY(50px) rotateX(10deg); }}
            to {{ opacity: 1; transform: translateY(0) rotateX(0); }}
        }}
        
        .stat-card::after {{
            content: '';
            position: absolute;
            bottom: 0;
            right: 0;
            width: 50%;
            height: 50%;
            background-image: linear-gradient(135deg, transparent 50%, rgba(200, 16, 46, 0.1) 50%);
            border-radius: 0 0 12px 0;
        }}
        
        .stat-card:hover {{
            transform: translateY(-10px) scale(1.03);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
        }}
        
        .stat-card h3 {{
            color: var(--caps-blue);
            margin-bottom: var(--spacing-md);
            font-size: var(--font-xl);
            font-family: 'Montserrat', sans-serif;
            display: inline-block;
            position: relative;
            font-weight: 700;
        }}
        
        .stat-card h3::after {{
            content: '';
            position: absolute;
            bottom: -8px;
            left: 0;
            width: 100%;
            height: 3px;
            background-color: var(--caps-red);
            border-radius: 2px;
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
        
        /* Responsive design adjustments */
        @media (max-width: 768px) {{
            .stats-container {{
                grid-template-columns: 1fr;
            }}
            
            .hero h1 {{
                font-size: var(--font-xxl);
            }}
            
            .hero p {{
                font-size: var(--font-large);
            }}
            
            .stat-value {{
                font-size: var(--font-xxl);
            }}
            
            .stat-value.record {{
                font-size: calc(var(--font-xxl) * 1.2);
            }}
        }}
        
        /* Animation for page elements */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .hero, .stat-card {{
            animation: fadeIn 1s ease-out forwards;
        }}
        
        .hero {{ animation-delay: 0.2s; }}
        .stat-card:nth-child(1) {{ animation-delay: 0.4s; }}
        .stat-card:nth-child(2) {{ animation-delay: 0.6s; }}
        
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
            border-top: 4px solid var(--caps-gold);
        }}
        
        .update-time {{
            font-style: italic;
            opacity: 0.9;
        }}
        
        .hero-link {{
            color: var(--caps-gold);
            text-decoration: none;
            font-weight: bold;
            transition: all 0.3s ease;
        }}
        
        .hero-link:hover {{
            text-decoration: underline;
            text-shadow: 0 0 10px var(--caps-gold);
        }}
        
        .footer-link {{
            color: var(--caps-white);
            text-decoration: underline;
            opacity: 0.9;
        }}
        
        .footer-link:hover {{
            opacity: 1;
            text-decoration: none;
            color: var(--caps-gold);
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
        
        /* Celebration elements */
        .celebration-badge {{
            position: absolute;
            top: -25px;
            right: -25px;
            width: 100px;
            height: 100px;
            background-color: var(--caps-gold);
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            font-weight: 900;
            font-size: 1.2rem;
            color: var(--caps-blue);
            transform: rotate(15deg);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            z-index: 10;
            animation: spin 10s linear infinite;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        .celebration-text {{
            font-size: var(--font-xl);
            font-weight: 700;
            color: var(--caps-gold);
            margin-top: var(--spacing-md);
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.3);
            animation: celebrate-pulse 2s infinite alternate;
        }}
        
        @keyframes celebrate-pulse {{
            0% {{ transform: scale(1); }}
            100% {{ transform: scale(1.05); }}
        }}
        
        .celebration-emoji {{
            font-size: 2rem;
            margin: 0 0.3rem;
            display: inline-block;
            animation: bounce 1s infinite alternate;
        }}
        
        @keyframes bounce {{
            0% {{ transform: translateY(0); }}
            100% {{ transform: translateY(-10px); }}
        }}
        
        .celebration-emoji:nth-child(2) {{
            animation-delay: 0.2s;
        }}
        
        .celebration-emoji:nth-child(3) {{
            animation-delay: 0.4s;
        }}
    </style>
</head>
<body>
    <!-- Schema.org structured data for better search engine understanding -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "SportsEvent",
        "name": "Alex Ovechkin Breaks NHL Goal Record",
        "description": "Alex Ovechkin has broken Wayne Gretzky's all-time NHL goal record with 895 goals.",
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
        "startDate": "{today}"
    }}
    </script>
    
    <header>
        <nav aria-label="Main Navigation" style="display: none;">
            <ul>
                <li><a href="#stats">Historic Achievement</a></li>
            </ul>
        </nav>
    </header>
    
    <main>
        <div class="hero">
            <div class="celebration-badge">HISTORY!</div>
            <h1>RECORD BROKEN!</h1>
            <p><a href="https://www.nhl.com/capitals/player/alex-ovechkin-8471214" target="_blank" class="hero-link">Alex Ovechkin</a> has officially surpassed Wayne Gretzky to become the NHL's all-time leading goal scorer!</p>
            <div class="record-banner">
                <i class="fas fa-trophy"></i> Record-Breaking Goal: {today}
            </div>
        </div>
        
        <div class="content-wrapper">
            <div class="stats-container">
                <div class="stat-card" id="stats">
                    <h3>Gretzky's Record</h3>
                    <span class="stat-value">894</span>
                    <p>Wayne Gretzky's previous NHL record</p>
                </div>
                
                <div class="stat-card">
                    <h3>Ovechkin's Goals</h3>
                    <span class="stat-value record">895</span>
                    <p>The new all-time NHL goal record!</p>
                    <div class="celebration-text">
                        <span class="celebration-emoji">🏒</span>
                        <span class="celebration-emoji">🏆</span>
                        <span class="celebration-emoji">🎉</span>
                    </div>
                </div>
            </div>
        </div>
    </main>
    
    <footer>
        <p>Last updated: <span class="update-time">{current_time}</span></p>
        <p class="built-by">Built by <a href="http://github.com/PaulDuvall/" class="footer-link" target="_blank" rel="noopener">Paul Duvall</a></p>
        <p class="attribution">Background image: <a href="https://commons.wikimedia.org/wiki/File:Alex_Ovechkin_2018-05-21.jpg" class="footer-link">Alex Ovechkin</a> by Michael Miller, <a href="https://creativecommons.org/licenses/by-sa/4.0/" class="footer-link">CC BY-SA 4.0</a></p>
    </footer>
    
    <!-- Confetti celebration script -->
    <script>
        // Run confetti when page loads
        window.onload = function() {{
            // Run the confetti animation
            var duration = 8 * 1000;
            var animationEnd = Date.now() + duration;
            var defaults = {{ startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 }};

            function randomInRange(min, max) {{
                return Math.random() * (max - min) + min;
            }}

            var interval = setInterval(function() {{
                var timeLeft = animationEnd - Date.now();

                if (timeLeft <= 0) {{
                    return clearInterval(interval);
                }}

                var particleCount = 50 * (timeLeft / duration);
                // Washington Capitals colors
                confetti(Object.assign({{}}, defaults, {{ 
                    particleCount, 
                    origin: {{ x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 }},
                    colors: ['#C8102E', '#041E42', '#FFFFFF', '#FFD700']
                }}));
                confetti(Object.assign({{}}, defaults, {{ 
                    particleCount, 
                    origin: {{ x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 }},
                    colors: ['#C8102E', '#041E42', '#FFFFFF', '#FFD700']
                }}));
            }}, 250);
            
            // Add click event to trigger more confetti when clicking on the record value
            document.querySelector('.stat-value.record').addEventListener('click', function() {{
                confetti({{
                    particleCount: 150,
                    spread: 70,
                    origin: {{ y: 0.6 }},
                    colors: ['#C8102E', '#041E42', '#FFFFFF', '#FFD700']
                }});
            }});
        }};
    </script>
</body>
</html>
"""
    
    return html


def update_website():
    """
    Generate a new index.html file with the celebration content for Ovechkin breaking Gretzky's record
    
    Returns:
        bool: True if website was updated successfully, False otherwise
    """
    try:
        # Get the project root directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        
        # Check if running in Lambda environment
        is_lambda = 'AWS_LAMBDA_FUNCTION_NAME' in os.environ
        
        # Generate celebration HTML content
        html_content = generate_celebration_html_content()
        
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
            shutil.copy2(source_svg, target_svg)
            logger.info(f"Copied favicon from {source_svg} to {target_svg}")
        else:
            logger.warning(f"Favicon source file not found at {source_svg}")
        
        # Write the HTML content to the file, completely replacing the existing content
        with open(index_path, 'w') as f:
            f.write(html_content)
        
        success_msg = f"Celebration website updated successfully at {index_path}"
        logger.info(success_msg)
        print(success_msg)
        return True
        
    except Exception as e:
        error_msg = f"ERROR: Failed to update celebration website: {str(e)}"
        logger.error(error_msg)
        print(error_msg)
        return False

if __name__ == "__main__":
    update_website()
