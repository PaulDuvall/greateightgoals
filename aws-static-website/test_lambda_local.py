#!/usr/bin/env python3
"""
Local test harness for the Lambda function

This script allows testing the Lambda function locally with different event configurations.
"""

import os
import sys
import json
import argparse

# Set environment variables for local testing
os.environ['LOCAL_DEV'] = 'true'

def main():
    """Main function to test the Lambda function locally"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test the Lambda function locally')
    parser.add_argument('--celebrate', action='store_true', help='Activate celebration mode')
    args = parser.parse_args()
    
    # Create a mock event
    event = {
        'source': 'aws.events',
        'celebrate': args.celebrate
    }
    
    # Create a mock context
    class MockContext:
        def __init__(self):
            self.function_name = 'test-function'
            self.aws_request_id = 'test-request-id'
    
    context = MockContext()
    
    # Print the event
    print(f"Event: {json.dumps(event, indent=2)}")
    
    # Import the Lambda handler
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from lambda.update_website_lambda import lambda_handler
    
    # Call the Lambda handler
    response = lambda_handler(event, context)
    
    # Print the response
    print(f"Response: {json.dumps(response, indent=2)}")

if __name__ == '__main__':
    main()
