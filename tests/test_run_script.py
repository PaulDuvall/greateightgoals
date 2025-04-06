#!/usr/bin/env python3
"""
Integration tests for the run.sh script functionality.

These tests verify that the run.sh script correctly handles the --celebrate flag
and generates the appropriate website content.
"""

import os
import sys
import unittest
import subprocess
import tempfile
import shutil
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestRunScript(unittest.TestCase):
    """Integration tests for the run.sh script."""

    def setUp(self):
        """Set up test environment."""
        # Store the project root directory
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
        # Create a backup of the static directory if it exists
        self.static_dir = os.path.join(self.project_root, 'aws-static-website', 'static')
        self.backup_dir = None
        
        if os.path.exists(self.static_dir):
            self.backup_dir = tempfile.mkdtemp()
            # Copy the contents to the backup directory
            shutil.copytree(self.static_dir, os.path.join(self.backup_dir, 'static'), dirs_exist_ok=True)

    def tearDown(self):
        """Clean up after tests."""
        # Restore the static directory from backup if it exists
        if self.backup_dir:
            if os.path.exists(self.static_dir):
                shutil.rmtree(self.static_dir)
            shutil.copytree(os.path.join(self.backup_dir, 'static'), self.static_dir, dirs_exist_ok=True)
            shutil.rmtree(self.backup_dir)

    def _run_command(self, command):
        """Run a shell command and return the result."""
        process = subprocess.run(
            command,
            shell=True,
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        return process

    def test_run_script_standard_mode(self):
        """Test that run.sh update-website works correctly."""
        # Run the standard update command
        result = self._run_command('./run.sh update-website')
        
        # Check that the command succeeded
        self.assertEqual(result.returncode, 0, f"Command failed with output: {result.stderr}")
        
        # Verify that the index.html file was created
        index_path = os.path.join(self.static_dir, 'index.html')
        self.assertTrue(os.path.exists(index_path), "index.html was not created")
        
        # Check the content of the index.html file
        with open(index_path, 'r') as f:
            content = f.read()
            
        # Verify it's the standard mode (not celebration)
        self.assertIn('Ovechkin Goal Tracker', content)
        self.assertNotIn('RECORD BROKEN!', content)

    def test_run_script_celebration_mode(self):
        """Test that run.sh update-website --celebrate works correctly."""
        # Run the celebration update command
        result = self._run_command('./run.sh update-website --celebrate')
        
        # Check that the command succeeded
        self.assertEqual(result.returncode, 0, f"Command failed with output: {result.stderr}")
        
        # Verify that the index.html file was created
        index_path = os.path.join(self.static_dir, 'index.html')
        self.assertTrue(os.path.exists(index_path), "index.html was not created")
        
        # Check the content of the index.html file
        with open(index_path, 'r') as f:
            content = f.read()
            
        # Verify it's the celebration mode
        self.assertIn('RECORD BROKEN!', content)
        self.assertIn('Alex Ovechkin has officially surpassed Wayne Gretzky', content)
        self.assertIn('895', content)  # Ovechkin's new record
        self.assertIn('confetti(', content)  # Confetti animation


if __name__ == '__main__':
    unittest.main()
