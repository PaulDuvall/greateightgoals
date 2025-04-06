#!/usr/bin/env python3
"""
Tests for the celebration mode functionality of the Ovechkin Goal Tracker website.

These tests verify that both the standard website update and celebration mode
function correctly, generating the appropriate HTML content.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import tempfile
import shutil

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the modules to test
from aws_static_website.celebrate import generate_celebration_html_content, update_website as update_celebration
from aws_static_website.update_website import generate_html_content, update_website as update_standard


class TestCelebrationMode(unittest.TestCase):
    """Test cases for the celebration mode functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test output
        self.test_dir = tempfile.mkdtemp()
        self.assets_dir = os.path.join(self.test_dir, 'assets')
        os.makedirs(self.assets_dir, exist_ok=True)
        
        # Create a mock SVG file
        self.mock_svg_path = os.path.join(self.assets_dir, 'gr8.svg')
        with open(self.mock_svg_path, 'w') as f:
            f.write('<svg>Test SVG</svg>')

    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def test_generate_celebration_html_content(self):
        """Test that celebration HTML content is generated correctly."""
        # Generate the celebration HTML content
        html_content = generate_celebration_html_content()
        
        # Verify that the HTML contains key celebration elements
        self.assertIn('RECORD BROKEN!', html_content)
        self.assertIn('Alex Ovechkin has officially surpassed Wayne Gretzky', html_content)
        self.assertIn('895', html_content)  # Ovechkin's new record
        self.assertIn('894', html_content)  # Gretzky's record
        self.assertIn('celebration-badge', html_content)
        self.assertIn('confetti(', html_content)  # Confetti animation
        
        # Verify Washington Capitals colors are used
        self.assertIn('#C8102E', html_content)  # Caps red
        self.assertIn('#041E42', html_content)  # Caps blue
        self.assertIn('#FFD700', html_content)  # Gold for celebration

    @patch('aws_static_website.celebrate.os.path')
    @patch('aws_static_website.celebrate.shutil.copy2')
    def test_update_celebration_website(self, mock_copy2, mock_path):
        """Test the update_website function in celebration mode."""
        # Configure mocks
        mock_path.dirname.return_value = self.test_dir
        mock_path.join.side_effect = os.path.join
        mock_path.exists.return_value = True
        
        # Create a mock for open to capture the written HTML
        mock_open = unittest.mock.mock_open()
        with patch('builtins.open', mock_open):
            # Call the update function
            result = update_celebration()
            
            # Verify the function returned True (success)
            self.assertTrue(result)
            
            # Verify that the HTML file was written
            mock_open.assert_called()
            
            # Verify that the SVG file was copied
            mock_copy2.assert_called()
    
    def test_standard_vs_celebration_content(self):
        """Test that standard and celebration HTML content are different."""
        # Mock stats for standard mode
        mock_stats = {
            'flat_stats': {
                'Total Number of Goals': '893',
                'Goals to Beat Gretzy': '2',
                'Projected Date of Record-Breaking Goal': '04/10/2025'
            },
            'nested_stats': {
                'record': {
                    'projected_game': {
                        'date': 'Thursday, 2025-04-10',
                        'time': '7:00 PM ET',
                        'opponent': 'Columbus Blue Jackets',
                        'location': 'Away'
                    }
                }
            }
        }
        
        # Generate both types of content
        standard_html = generate_html_content(mock_stats)
        celebration_html = generate_celebration_html_content()
        
        # Verify they are different
        self.assertNotEqual(standard_html, celebration_html)
        
        # Verify standard HTML has correct stats
        self.assertIn('893', standard_html)  # Current goals
        self.assertIn('2', standard_html)    # Goals needed
        
        # Verify celebration HTML has record-breaking info
        self.assertIn('895', celebration_html)  # New record
        self.assertIn('RECORD BROKEN!', celebration_html)


if __name__ == '__main__':
    unittest.main()
