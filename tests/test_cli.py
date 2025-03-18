#!/usr/bin/env python3
"""
Tests for the CLI module

This module tests the command-line interface functionality of the Ovechkin Goal Tracker.
"""

import sys
import pytest
from unittest.mock import patch, MagicMock

from ovechkin_tracker.cli import main, show_stats


class TestCLI:
    """Test cases for the CLI module"""
    
    @patch('ovechkin_tracker.cli.OvechkinData')
    def test_show_stats(self, mock_ovechkin_data):
        """Test the show_stats function"""
        # Setup mock
        mock_instance = MagicMock()
        mock_ovechkin_data.return_value = mock_instance
        
        # Call the function
        show_stats()
        
        # Verify the OvechkinData instance was created and display_stats was called
        mock_ovechkin_data.assert_called_once()
        mock_instance.display_stats.assert_called_once()
    
    @patch('ovechkin_tracker.cli.show_stats')
    def test_main_stats(self, mock_show_stats):
        """Test the main function with 'stats' command"""
        # Setup sys.argv
        with patch('sys.argv', ['main.py', 'stats']):
            # Call the function
            main()
            
            # Verify show_stats was called
            mock_show_stats.assert_called_once()
    
    @patch('ovechkin_tracker.cli.send_ovechkin_email')
    def test_main_email(self, mock_send_email):
        """Test the main function with 'email' command"""
        # Setup mock
        mock_send_email.return_value = True
        
        # Setup sys.argv
        with patch('sys.argv', ['main.py', 'email']):
            # Call the function
            main()
            
            # Verify send_ovechkin_email was called with no arguments
            mock_send_email.assert_called_once_with()
    
    @patch('ovechkin_tracker.cli.send_ovechkin_email')
    def test_main_email_to(self, mock_send_email):
        """Test the main function with 'email-to' command"""
        # Setup mock
        mock_send_email.return_value = True
        test_email = 'test@example.com'
        
        # Setup sys.argv
        with patch('sys.argv', ['main.py', 'email-to', test_email]):
            # Call the function
            main()
            
            # Verify send_ovechkin_email was called with the email address
            mock_send_email.assert_called_once_with(test_email)
    
    @patch('ovechkin_tracker.cli.send_ovechkin_email')
    def test_main_email_failure(self, mock_send_email):
        """Test the main function with 'email' command when email fails"""
        # Setup mock to return False (email failed)
        mock_send_email.return_value = False
        
        # Setup sys.argv
        with patch('sys.argv', ['main.py', 'email']):
            # Call the function and check exit code
            with pytest.raises(SystemExit) as excinfo:
                main()
            
            # Verify exit code is 1
            assert excinfo.value.code == 1
    
    @patch('builtins.print')
    def test_main_unknown_command(self, mock_print):
        """Test the main function with an unknown command"""
        # Setup sys.argv
        with patch('sys.argv', ['main.py', 'unknown']):
            # Call the function
            main()
            
            # Verify the error message was printed
            mock_print.assert_called_with("Unknown command. Use 'stats', 'email', or 'email-to <address>'")
    
    @patch('builtins.print')
    def test_main_no_args(self, mock_print):
        """Test the main function with no arguments"""
        # Setup sys.argv
        with patch('sys.argv', ['main.py']):
            # Call the function
            main()
            
            # Verify the usage message was printed
            mock_print.assert_called_with("Usage: python main.py [stats|email|email-to <address>]")
