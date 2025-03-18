#!/usr/bin/env python3
"""
CLI Module for Ovechkin Goal Tracker

This module provides the command-line interface for the Ovechkin Goal Tracker,
allowing users to display stats and send email notifications.
"""

import sys
import logging

from ovechkin_tracker.ovechkin_data import OvechkinData
from ovechkin_tracker.email import send_ovechkin_email

# Set up logging
logger = logging.getLogger(__name__)

def show_stats():
    """Display current Ovechkin stats using the OvechkinData class"""
    # Create an instance of the OvechkinData class
    ovechkin_data = OvechkinData()
    
    # Display the stats
    ovechkin_data.display_stats()

def main():
    """Main function to handle command-line arguments"""
    if len(sys.argv) < 2:
        print("Usage: python main.py [stats|email|email-to <address>]")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'stats':
        show_stats()
    elif command == 'email':
        success = send_ovechkin_email()
        if not success:
            sys.exit(1)
    elif command == 'email-to' and len(sys.argv) > 2:
        success = send_ovechkin_email(sys.argv[2])
        if not success:
            sys.exit(1)
    else:
        print("Unknown command. Use 'stats', 'email', or 'email-to <address>'")
