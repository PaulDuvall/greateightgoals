#!/usr/bin/env python3
"""
Wrapper module to import the Lambda function from the lambda directory

This module provides access to the Lambda handler function from the lambda directory.
"""

import os
import sys
import importlib.util

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import the Lambda handler using importlib
lambda_function_path = os.path.join(project_root, 'lambda', 'lambda_function.py')

try:
    # First make sure the lambda directory is in the Python path
    lambda_dir = os.path.join(project_root, 'lambda')
    if lambda_dir not in sys.path:
        sys.path.insert(0, lambda_dir)
    
    # Dynamically import the lambda_function module
    spec = importlib.util.spec_from_file_location("lambda_function", lambda_function_path)
    lambda_function = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lambda_function)
    
    # Get the lambda_handler function
    lambda_handler = lambda_function.lambda_handler
except (ImportError, AttributeError) as e:
    print(f"Error: Could not import lambda_handler: {e}")
    print(f"Looking for lambda_function.py at: {lambda_function_path}")
    sys.exit(1)
