#!/usr/bin/env python3
"""Email Module for Ovechkin Goal Tracker

This module handles email configuration and sending functionality
using Amazon SES.

Optimized for AWS Lambda with improved Parameter Store integration.
"""

import os
import logging
import boto3
import pytz
import getpass
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError

from ovechkin_tracker.ovechkin_data import OvechkinData

# Set up logging
logger = logging.getLogger(__name__)


def prompt_for_parameter(param_name, description=None):
    """Prompt the user to enter a value for a missing parameter
    
    Args:
        param_name: Name of the parameter
        description: Optional description of the parameter
        
    Returns:
        str: User-provided value for the parameter
    """
    prompt_text = f"Enter value for '{param_name}'"
    if description:
        prompt_text += f" ({description})"
    prompt_text += ": "
    
    # Use getpass for sensitive information
    if 'email' in param_name.lower():
        value = input(prompt_text)
    else:
        value = getpass.getpass(prompt_text)
    
    return value


def store_parameter(param_name, param_value, parameter_path='/ovechkin-tracker/'):
    """Store a parameter in AWS Systems Manager Parameter Store as a SecureString
    
    Args:
        param_name: Name of the parameter without the path prefix
        param_value: Value to store
        parameter_path: Path prefix for parameters in Parameter Store
        
    Returns:
        bool: True if parameter was stored successfully, False otherwise
    """
    try:
        # Create a boto3 client for SSM
        ssm = boto3.client('ssm')
        
        # Full parameter name with path
        full_param_name = f"{parameter_path.rstrip('/')}/{param_name}"
        
        # Put the parameter as a SecureString
        ssm.put_parameter(
            Name=full_param_name,
            Value=param_value,
            Type='SecureString',
            Overwrite=True
        )
        
        logger.info(f"Parameter '{param_name}' stored successfully in Parameter Store")
        return True
    except Exception as e:
        logger.error(f"Error storing parameter '{param_name}' in Parameter Store: {e}")
        return False


def get_parameter_store_config(parameter_path='/ovechkin-tracker/'):
    """Get configuration from AWS Systems Manager Parameter Store
    
    Args:
        parameter_path: Path prefix for parameters in Parameter Store
        
    Returns:
        dict: Configuration dictionary with all required parameters
    """
    try:
        # Create a boto3 client for SSM
        ssm = boto3.client('ssm')
        
        # Get parameters by path
        response = ssm.get_parameters_by_path(
            Path=parameter_path,
            WithDecryption=True
        )
        
        # Extract parameters
        parameters = {}
        for param in response.get('Parameters', []):
            # Extract the parameter name without the path prefix
            name = param['Name'].split('/')[-1]
            parameters[name] = param['Value']
        
        # Check required parameters and prompt for missing ones
        required_params = {
            'aws_region': 'AWS region for SES (e.g., us-east-1)',
            'sender_email': 'Email address to send from (must be verified in SES)',
            'recipient_email': 'Default email address to send to'
        }
        
        missing_params = []
        for param, description in required_params.items():
            if param not in parameters or not parameters[param].strip():
                missing_params.append((param, description))
        
        # If running in Lambda, we can't prompt for input
        if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ and missing_params:
            logger.error(f"Missing required parameters in Parameter Store: {', '.join([p[0] for p in missing_params])}")
            logger.error("Cannot prompt for parameters in Lambda environment")
            raise ValueError("Missing required parameters in Parameter Store")
        
        # Prompt for missing parameters and store them
        for param_name, description in missing_params:
            logger.info(f"Parameter '{param_name}' not found in Parameter Store or is empty")
            param_value = prompt_for_parameter(param_name, description)
            
            if param_value.strip():
                parameters[param_name] = param_value
                # Store the parameter for future use
                store_parameter(param_name, param_value, parameter_path)
            else:
                logger.error(f"No value provided for required parameter '{param_name}'")
                raise ValueError(f"Missing required parameter: {param_name}")
        
        logger.info("Using configuration from AWS Parameter Store")
        return parameters
    except (ClientError, NoCredentialsError) as e:
        logger.warning(f"Error accessing Parameter Store: {e}")
        # If we can't access Parameter Store, prompt for all parameters
        if 'AWS_LAMBDA_FUNCTION_NAME' not in os.environ:
            logger.info("Prompting for all required parameters")
            parameters = {}
            required_params = {
                'aws_region': 'AWS region for SES (e.g., us-east-1)',
                'sender_email': 'Email address to send from (must be verified in SES)',
                'recipient_email': 'Default email address to send to'
            }
            
            for param_name, description in required_params.items():
                param_value = prompt_for_parameter(param_name, description)
                if param_value.strip():
                    parameters[param_name] = param_value
                else:
                    logger.error(f"No value provided for required parameter '{param_name}'")
                    raise ValueError(f"Missing required parameter: {param_name}")
            
            return parameters
        else:
            raise
    except Exception as e:
        logger.error(f"Unexpected error getting parameters: {e}")
        raise


def format_email_html(stats_text):
    """Format the stats as HTML for email
    
    Args:
        stats_text: Plain text stats to format as HTML
        
    Returns:
        str: HTML formatted email content
    """
    # Extract key stats from the text
    lines = stats_text.strip().split('\n')
    stats_dict = {}
    
    for line in lines:
        if line.startswith('- '):
            # Extract key-value pairs from bullet points
            parts = line[2:].split(':', 1)  # Remove the '- ' prefix and split on first colon
            if len(parts) == 2:
                key, value = parts
                stats_dict[key.strip()] = value.strip()
    
    # Get the values we need
    total_goals = stats_dict.get('Total Goals', 'N/A')
    goals_needed = stats_dict.get('Goals Needed to Break Gretzky\'s Record', 'N/A')
    projected_date = stats_dict.get('Projected Record-Breaking Date', 'N/A')
    projected_game = stats_dict.get('Projected Record-Breaking Game', 'N/A')
    
    # Calculate progress percentage
    try:
        progress_pct = round((int(total_goals) / 894) * 100, 1)
    except (ValueError, ZeroDivisionError):
        progress_pct = 0
    
    # Create HTML content with inline styles for email compatibility
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ovechkin Goal Tracker</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #041E42; color: white; padding: 20px; text-align: center; border-radius: 5px;">
            <h1 style="margin: 0;">Ovechkin Goal Tracker</h1>
            <p style="margin: 5px 0 0;">NHL All-Time Goals Record Watch</p>
        </div>
        
        <div style="background-color: #f9f9f9; padding: 20px; margin-top: 20px; border-radius: 5px;">
            <h2 style="color: #041E42; margin-top: 0;">Current Status</h2>
            
            <div style="margin-bottom: 20px;">
                <h3 style="margin-bottom: 5px;">Progress to Gretzky's Record (894)</h3>
                <div style="background-color: #e0e0e0; border-radius: 10px; height: 20px; position: relative;">
                    <div style="background-color: #C8102E; width: {progress_pct}%; height: 100%; border-radius: 10px;"></div>
                    <div style="position: absolute; top: 0; left: 0; right: 0; text-align: center; line-height: 20px; font-size: 12px; color: #000;">
                        {progress_pct}%
                    </div>
                </div>
            </div>
            
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold;">Total Goals:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right; font-size: 18px;">{total_goals}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold;">Goals Needed:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right; font-size: 18px;">{goals_needed}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold;">Projected Date:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">{projected_date}</td>
                </tr>
            </table>
        </div>
        
        <div style="background-color: #041E42; color: white; padding: 15px; margin-top: 20px; border-radius: 5px; text-align: center;">
            <h3 style="margin-top: 0;">Projected Record-Breaking Game</h3>
            <p style="font-size: 16px; margin-bottom: 0;">{projected_game}</p>
        </div>
        
        <div style="text-align: center; margin-top: 20px; font-size: 12px; color: #666;">
            <p>This email was automatically generated by the Ovechkin Goal Tracker.</p>
        </div>
    </body>
    </html>
    """
    
    return html


def send_email_ses(config, subject, text_content, html_content=None):
    """Send an email with Ovechkin stats using Amazon SES
    
    Args:
        config: Email configuration dictionary
        subject: Email subject
        text_content: Plain text email content
        html_content: Optional HTML email content
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Get configuration values
    aws_region = config.get('aws_region')
    sender_email = config.get('sender_email')
    recipient_email = config.get('recipient_email')
    
    # Validate configuration
    if not all([aws_region, sender_email, recipient_email]):
        logger.error("Missing required configuration values for sending email")
        return False
    
    # Create a new SES resource
    try:
        client = boto3.client('ses', region_name=aws_region)
    except Exception as e:
        logger.error(f"Error creating SES client: {e}")
        return False
    
    # Prepare email message
    message = {
        'Subject': {
            'Data': subject,
            'Charset': 'UTF-8'
        },
        'Body': {
            'Text': {
                'Data': text_content,
                'Charset': 'UTF-8'
            }
        }
    }
    
    # Add HTML content if provided
    if html_content:
        message['Body']['Html'] = {
            'Data': html_content,
            'Charset': 'UTF-8'
        }
    
    # Try to send the email
    try:
        response = client.send_email(
            Source=sender_email,
            Destination={
                'ToAddresses': [recipient_email]
            },
            Message=message
        )
        logger.info(f"Email sent! Message ID: {response['MessageId']}")
        return True
    except ClientError as e:
        logger.error(f"Error sending email: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email: {e}")
        return False


def send_ovechkin_email(recipient_email=None):
    """Send an email with Ovechkin's stats and projected record-breaking date
    
    Args:
        recipient_email: Optional recipient email address to override the default
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Get configuration from Parameter Store (will prompt for missing parameters)
        config = get_parameter_store_config()

        # If a recipient email is provided as an argument, override the config
        if recipient_email:
            config['recipient_email'] = recipient_email

        # Get stats from ovechkin_tracker
        ovechkin_data = OvechkinData()
        stats = ovechkin_data.get_all_stats()
        
        if 'error' in stats:
            error_msg = f"ERROR: Failed to calculate stats: {stats['error']}"
            logger.error(error_msg)
            print(error_msg)
            return False
        
        # Extract key information
        total_goals = stats.get('flat_stats', {}).get('Total Number of Goals', 'N/A')
        goals_needed = stats.get('flat_stats', {}).get('Goals to Beat Gretzy', 'N/A')
        projected_date = stats.get('flat_stats', {}).get('Projected Date of Record-Breaking Goal', 'N/A')
        projected_game = stats.get('flat_stats', {}).get('Projected Record-Breaking Game', 'N/A')
        
        # Create email subject
        subject = f"Ovechkin Goal Tracker: {total_goals} goals, {goals_needed} to break the record"
        
        # Create plain text content
        text_content = f"""Ovechkin Goal Tracker - NHL Record Watch
===================================

Current Status:
- Total Goals: {total_goals}
- Goals Needed to Break Gretzky's Record: {goals_needed}
- Projected Record-Breaking Date: {projected_date}
- Projected Record-Breaking Game: {projected_game}

This email was automatically generated by the Ovechkin Goal Tracker.
"""
        
        # Create HTML content
        html_content = format_email_html(text_content)
        
        # Send the email
        print(f"Sending email to {config['recipient_email']}")
        success = send_email_ses(config, subject, text_content, html_content)
        
        if success:
            success_msg = f"Email sent successfully to {config['recipient_email']}"
            logger.info(success_msg)
            print(success_msg)
        else:
            error_msg = f"Failed to send email to {config['recipient_email']}"
            logger.error(error_msg)
            print(error_msg)
        
        return success
    except Exception as e:
        logger.error(f"Error in send_ovechkin_email: {e}")
        print(f"Error: {e}")
        return False
