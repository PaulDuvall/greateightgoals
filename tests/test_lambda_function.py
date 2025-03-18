#!/usr/bin/env python3
"""
Tests for the Lambda Function

This module tests the AWS Lambda function for the Ovechkin Goal Tracker.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
import sys
import os
import importlib.util

# Add the parent directory to the Python path so we can import the lambda module
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import lambda function using importlib to avoid Python keyword conflict
lambda_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lambda')
lambda_file = os.path.join(lambda_dir, 'lambda_function.py')
spec = importlib.util.spec_from_file_location('lambda_function', lambda_file)
lambda_function = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lambda_function)


class TestLambdaFunction:
    """Test cases for the Lambda function"""
    
    def test_lambda_handler_options_request(self):
        """Test the lambda_handler function with an OPTIONS request (CORS preflight)"""
        # Create a test event for an OPTIONS request
        event = {'httpMethod': 'OPTIONS'}
        
        # Call the function
        response = lambda_function.lambda_handler(event, None)
        
        # Verify the response
        assert response['statusCode'] == 200
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert 'Access-Control-Allow-Methods' in response['headers']
        assert 'Access-Control-Allow-Headers' in response['headers']
    
    def test_get_config_from_event_valid(self):
        """Test the get_config_from_event function with valid configuration"""
        # Create a test event with valid configuration
        event = {
            'config': {
                'aws_region': 'us-east-1',
                'sender_email': 'sender@example.com',
                'recipient_email': 'recipient@example.com'
            }
        }
        
        # Call the function
        result = lambda_function.get_config_from_event(event)
        
        # Verify the result
        assert result == {
            'aws_region': 'us-east-1',
            'sender_email': 'sender@example.com',
            'recipient_email': 'recipient@example.com'
        }
    
    def test_get_config_from_event_invalid(self):
        """Test the get_config_from_event function with invalid configuration"""
        # Create a test event with invalid configuration (missing required fields)
        event = {
            'config': {
                'aws_region': 'us-east-1'
                # Missing sender_email and recipient_email
            }
        }
        
        # Call the function
        result = lambda_function.get_config_from_event(event)
        
        # Verify the result is None
        assert result is None
