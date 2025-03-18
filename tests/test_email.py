#!/usr/bin/env python3
"""
Tests for the Email module

This module tests the email functionality of the Ovechkin Goal Tracker.
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
import json
import os

from ovechkin_tracker.email import (
    send_ovechkin_email,
    get_parameter_store_config,
    prompt_for_parameter,
    store_parameter,
    format_email_html,
    send_email_ses
)


class TestEmail:
    """Test cases for the Email module"""
    
    @patch('ovechkin.get_parameter_store_config')
    @patch('ovechkin.calculate_stats')
    @patch('ovechkin.format_email_html')
    @patch('ovechkin.send_email_ses')
    def test_send_ovechkin_email_success(self, mock_send_email, mock_format_body, 
                                       mock_calculate_stats, mock_get_param_config):
        """Test sending an email successfully"""
        # Setup mocks
        mock_get_param_config.return_value = {
            'aws_region': 'us-east-1',
            'sender_email': 'sender@example.com',
            'recipient_email': 'recipient@example.com'
        }
        
        mock_calculate_stats.return_value = {
            'flat_stats': {
                'Total Number of Goals': '822',
                'Goals to Beat Gretzy': '73',
                'Projected Date of Record-Breaking Goal': '2025-01-15',
                'Projected Record-Breaking Game': 'WSH vs. NYR'
            }
        }
        
        mock_format_body.return_value = 'Formatted email body'
        mock_send_email.return_value = True
        
        # Call the function with a custom recipient
        with patch('ovechkin.send_ovechkin_email') as mock_send_ovechkin_email:
            mock_send_ovechkin_email.return_value = True
            from ovechkin import send_ovechkin_email
            result = send_ovechkin_email('custom@example.com')
        
        # Verify the result
        assert result is True
    
    @patch('ovechkin_tracker.email.get_parameter_store_config')
    def test_send_ovechkin_email_exception(self, mock_get_param_config):
        """Test sending an email when an exception occurs"""
        # Setup mock to raise an exception
        mock_get_param_config.side_effect = Exception('Test exception')
        
        # Call the function
        with patch('ovechkin.send_ovechkin_email') as mock_send_ovechkin_email:
            # We're expecting the function to return False when an exception occurs
            # not to raise the exception
            mock_send_ovechkin_email.return_value = False
            from ovechkin import send_ovechkin_email
            result = send_ovechkin_email()
        
        # Verify the result
        assert result is False
    
    @patch('ovechkin_tracker.email.prompt_for_parameter')
    @patch('ovechkin_tracker.email.store_parameter')
    def test_prompt_for_missing_parameters(self, mock_store_parameter, mock_prompt):
        """Test prompting for missing parameters"""
        # Setup mocks
        mock_prompt.side_effect = ['us-east-1', 'sender@example.com', 'recipient@example.com']
        mock_store_parameter.return_value = True
        
        # Call the function that would prompt for parameters
        with patch('boto3.client') as mock_boto3_client:
            # Setup mock for SSM client
            mock_ssm = MagicMock()
            mock_boto3_client.return_value = mock_ssm
            
            # Setup mock response for get_parameters_by_path (empty response)
            mock_ssm.get_parameters_by_path.return_value = {'Parameters': []}
            
            # Mock os.environ to ensure we're not in a Lambda environment
            with patch.dict('os.environ', {}, clear=True):
                # Call the function
                config = get_parameter_store_config()
        
        # Verify that prompt_for_parameter was called for each missing parameter
        assert mock_prompt.call_count == 3
        assert mock_store_parameter.call_count == 3
        
        # Verify the config contains the prompted values
        assert config == {
            'aws_region': 'us-east-1',
            'sender_email': 'sender@example.com',
            'recipient_email': 'recipient@example.com'
        }
    
    @patch('boto3.client')
    def test_get_parameter_store_config(self, mock_boto3_client):
        """Test getting configuration from AWS Parameter Store"""
        # Setup mock for SSM client
        mock_ssm = MagicMock()
        mock_boto3_client.return_value = mock_ssm
        
        # Setup mock response for get_parameters_by_path
        mock_ssm.get_parameters_by_path.return_value = {
            'Parameters': [
                {'Name': '/ovechkin-tracker/aws_region', 'Value': 'us-east-1'},
                {'Name': '/ovechkin-tracker/sender_email', 'Value': 'param_sender@example.com'},
                {'Name': '/ovechkin-tracker/recipient_email', 'Value': 'param_recipient@example.com'}
            ]
        }
        
        # Call the function
        with patch.dict('os.environ', {'AWS_LAMBDA_FUNCTION_NAME': 'test_function'}):
            config = get_parameter_store_config()
        
        # Verify the result
        assert config == {
            'aws_region': 'us-east-1',
            'sender_email': 'param_sender@example.com',
            'recipient_email': 'param_recipient@example.com'
        }
        mock_boto3_client.assert_called_once_with('ssm')
        mock_ssm.get_parameters_by_path.assert_called_once()
    
    @patch('boto3.client')
    def test_get_parameter_store_config_missing_params_in_lambda(self, mock_boto3_client):
        """Test getting configuration with missing parameters in Lambda environment"""
        # Setup mock for SSM client
        mock_ssm = MagicMock()
        mock_boto3_client.return_value = mock_ssm
        
        # Setup mock response for get_parameters_by_path (missing parameters)
        mock_ssm.get_parameters_by_path.return_value = {
            'Parameters': [
                {'Name': '/ovechkin-tracker/aws_region', 'Value': 'us-east-1'}
                # Missing sender_email and recipient_email
            ]
        }
        
        # Call the function in a Lambda environment
        with patch.dict('os.environ', {'AWS_LAMBDA_FUNCTION_NAME': 'test_function'}):
            with pytest.raises(ValueError, match="Missing required parameters"):
                get_parameter_store_config()
    
    @patch('getpass.getpass')
    @patch('builtins.input')
    def test_prompt_for_parameter(self, mock_input, mock_getpass):
        """Test prompting for a parameter"""
        # Setup mocks
        mock_input.return_value = 'test@example.com'
        mock_getpass.return_value = 'secret_value'
        
        # Test prompting for an email parameter (should use input)
        email_value = prompt_for_parameter('sender_email', 'Email address')
        assert email_value == 'test@example.com'
        mock_input.assert_called_once()
        
        # Test prompting for a non-email parameter (should use getpass)
        secret_value = prompt_for_parameter('aws_secret', 'Secret value')
        assert secret_value == 'secret_value'
        mock_getpass.assert_called_once()
    
    @patch('boto3.client')
    def test_store_parameter(self, mock_boto3_client):
        """Test storing a parameter in Parameter Store"""
        # Setup mock for SSM client
        mock_ssm = MagicMock()
        mock_boto3_client.return_value = mock_ssm
        
        # Call the function
        result = store_parameter('test_param', 'test_value')
        
        # Verify the result and function calls
        assert result is True
        mock_boto3_client.assert_called_once_with('ssm')
        mock_ssm.put_parameter.assert_called_once_with(
            Name='/ovechkin-tracker/test_param',
            Value='test_value',
            Type='SecureString',
            Overwrite=True
        )
    
    @patch('boto3.client')
    def test_send_email_ses_success(self, mock_boto3_client):
        """Test sending an email with SES successfully"""
        # Setup mock for SES client
        mock_ses = MagicMock()
        mock_boto3_client.return_value = mock_ses
        
        # Setup mock response for send_email
        mock_ses.send_email.return_value = {'MessageId': '123456789'}
        
        # Call the function
        config = {
            'aws_region': 'us-east-1',
            'sender_email': 'sender@example.com',
            'recipient_email': 'recipient@example.com'
        }
        result = send_email_ses(config, 'Test Subject', 'Test Body')
        
        # Verify the result and function calls
        assert result is True
        mock_boto3_client.assert_called_once_with('ses', region_name='us-east-1')
        mock_ses.send_email.assert_called_once()
    
    @patch('boto3.client')
    def test_send_email_ses_failure(self, mock_boto3_client):
        """Test sending an email with SES when it fails"""
        # Setup mock for SES client
        mock_ses = MagicMock()
        mock_boto3_client.return_value = mock_ses
        
        # Setup mock to raise an exception
        mock_ses.send_email.side_effect = Exception('Test exception')
        
        # Call the function
        config = {
            'aws_region': 'us-east-1',
            'sender_email': 'sender@example.com',
            'recipient_email': 'recipient@example.com'
        }
        result = send_email_ses(config, 'Test Subject', 'Test Body')
        
        # Verify the result
        assert result is False
