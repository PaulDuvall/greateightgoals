#!/usr/bin/env python3
"""
Local Test Script for Ovechkin Tracker Lambda Function

This script allows testing the Lambda function locally with different configurations:
1. Using Parameter Store (requires AWS credentials)
2. Using event parameters (no AWS credentials needed)

Usage:
    python3 test_lambda_local.py [--format=<format>] [--email=<email>] [--method=<method>]

Options:
    --format=<format>    Response format: full, flat, or nested [default: full]
    --email=<email>      Email address to send to (triggers email action)
    --method=<method>    HTTP method to simulate: GET or POST [default: GET]
"""

import json
import argparse
import os
import sys
import boto3
from botocore.exceptions import ClientError

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import the Lambda handler directly
sys.path.append(os.path.join(project_root, 'lambda'))
from lambda_function import lambda_handler


def get_parameter_store_config(parameter_path='/ovechkin-tracker/'):
    """Get configuration from AWS Systems Manager Parameter Store
    
    Args:
        parameter_path: Path prefix for parameters in Parameter Store
        
    Returns:
        dict: Configuration dictionary with all required parameters
    """
    try:
        # Create an SSM client
        ssm = boto3.client('ssm')
        
        # Get parameters by path
        response = ssm.get_parameters_by_path(
            Path=parameter_path,
            WithDecryption=True
        )
        
        # Extract parameters
        params = {}
        for param in response.get('Parameters', []):
            # Extract the parameter name from the path
            name = param['Name'].split('/')[-1]
            params[name] = param['Value']
        
        # Check required parameters
        required_params = ['aws_region', 'sender_email', 'recipient_email']
        missing_params = [param for param in required_params if param not in params]
        
        if missing_params:
            print(f"Warning: Missing required parameters in Parameter Store: {', '.join(missing_params)}")
            print("Using default values for testing purposes")
            
            # Set default values for testing
            if 'aws_region' not in params:
                params['aws_region'] = 'us-east-1'
            if 'sender_email' not in params:
                params['sender_email'] = 'sender@example.com'
            if 'recipient_email' not in params:
                params['recipient_email'] = 'recipient@example.com'
        
        return params
    except Exception as e:
        print(f"Warning: Error getting parameters from Parameter Store: {e}")
        print("Using default values for testing purposes")
        
        # Return default values for testing
        return {
            'aws_region': 'us-east-1',
            'sender_email': 'sender@example.com',
            'recipient_email': 'recipient@example.com'
        }


def create_test_event(args):
    """Create a test event based on command line arguments
    
    Args:
        args: Command line arguments
        
    Returns:
        dict: Test event dictionary
    """
    # Determine HTTP method
    http_method = args.method.upper()
    
    # Create event structure
    event = {
        "httpMethod": http_method,
        "pathParameters": None,
        "queryStringParameters": {},
        "body": None
    }
    
    # Add format parameter for GET requests
    if http_method == "GET" and args.format:
        event["queryStringParameters"]["format"] = args.format
    
    # Add email parameter for POST requests
    if http_method == "POST" and args.email:
        if args.param_location == "query":
            event["queryStringParameters"]["email"] = args.email
        else:  # body
            event["body"] = json.dumps({"email": args.email})
    
    # Add config if using event parameters
    if args.config_source == "event":
        # Get configuration (either from Parameter Store or default values)
        config = get_parameter_store_config()
        
        # Add config to event
        event["config"] = config
    
    return event


def main():
    """Main function to parse arguments and run the test"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test the Ovechkin Tracker Lambda function locally")
    parser.add_argument("--format", choices=["full", "flat", "nested"], default="full",
                        help="Response format: full, flat, or nested")
    parser.add_argument("--email", help="Email address to send to (triggers email action)")
    parser.add_argument("--method", choices=["GET", "POST"], default="GET",
                        help="HTTP method to simulate")
    parser.add_argument("--config-source", choices=["parameter-store", "event"], default="parameter-store",
                        help="Source of configuration: AWS Parameter Store or event parameters")
    parser.add_argument("--param-location", choices=["query", "body"], default="body",
                        help="Location of email parameter: query string or request body")
    
    args = parser.parse_args()
    
    # Create test event
    event = create_test_event(args)
    
    # Print event for debugging
    print("\nTest Event:")
    print(json.dumps(event, indent=2))
    print("\n" + "-" * 80)
    
    # Call the Lambda handler
    print("\nCalling Lambda handler...\n")
    result = lambda_handler(event, None)
    
    # Print the result
    print("\nLambda Response:")
    print(json.dumps(result, indent=2))
    
    # Print the body in a more readable format if it's JSON
    try:
        body = json.loads(result["body"])
        print("\nResponse Body (formatted):")
        print(json.dumps(body, indent=2))
    except (json.JSONDecodeError, KeyError):
        pass


if __name__ == "__main__":
    main()
