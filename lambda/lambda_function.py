#!/usr/bin/env python3
"""
AWS Lambda Function for Ovechkin Goal Tracker

This Lambda function serves as the main entry point for the Ovechkin Goal Tracker
when deployed to AWS Lambda. It can be triggered by API Gateway or EventBridge.

The function supports two main operations:
1. Retrieving Ovechkin's current stats (GET request or default)
2. Sending an email with Ovechkin's stats (POST request with email parameter)

Configuration is retrieved from AWS Systems Manager Parameter Store with
fallback to event parameters.
"""

import json
import logging
import os
import sys
import time
import boto3
from botocore.exceptions import ClientError

# Add the parent directory to the Python path so we can import ovechkin_tracker
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import ovechkin_tracker modules
from ovechkin_tracker.ovechkin_data import OvechkinData
from ovechkin_tracker.email import send_ovechkin_email, get_parameter_store_config

# Global variables for caching
_stats_cache = None
_stats_cache_time = 0
_CACHE_TTL = 3600  # Cache TTL in seconds (1 hour)


def get_stats_with_cache():
    """Get Ovechkin stats with caching to improve performance
    
    Returns:
        dict: Stats dictionary
    """
    global _stats_cache, _stats_cache_time
    
    current_time = time.time()
    
    # Check if cache is still valid
    if _stats_cache and (current_time - _stats_cache_time) < _CACHE_TTL:
        logger.info("Using cached stats")
        return _stats_cache
    
    # Cache is invalid or not set, fetch new stats
    logger.info("Fetching fresh stats")
    try:
        # Create an instance of OvechkinData and get all stats
        ovechkin_data = OvechkinData()
        flat_stats = ovechkin_data.get_flat_stats()
        nested_stats = ovechkin_data.get_nested_stats() if hasattr(ovechkin_data, 'get_nested_stats') else {}
        
        # Create a complete stats dictionary
        stats = {
            'flat_stats': flat_stats,
            'nested_stats': nested_stats
        }
        
        # Update cache
        _stats_cache = stats
        _stats_cache_time = current_time
        
        return stats
    except Exception as e:
        logger.error(f"Error calculating stats: {e}", exc_info=True)
        return {"error": str(e)}


def get_config_from_event(event):
    """Extract configuration from the Lambda event
    
    Args:
        event: Lambda event dictionary
        
    Returns:
        dict: Configuration dictionary or None if not found
    """
    try:
        # Check if event contains configuration
        if 'config' in event:
            config = event['config']
            
            # Validate required fields
            required_fields = ['aws_region', 'sender_email', 'recipient_email']
            if all(field in config for field in required_fields):
                logger.info("Using configuration from event")
                return config
        
        return None
    except Exception as e:
        logger.error(f"Error extracting config from event: {e}")
        return None


def lambda_handler(event, context):
    """Main Lambda handler function
    
    Args:
        event: Lambda event dictionary
        context: Lambda context object
        
    Returns:
        dict: Response dictionary with status code and body
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Initialize response
    response = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"
        },
        "body": ""
    }
    
    try:
        # Determine request type
        http_method = "GET"
        path_parameters = {}
        query_parameters = {}
        body_parameters = {}
        
        # Extract HTTP method and parameters based on event source
        if 'httpMethod' in event:
            # API Gateway proxy integration
            http_method = event['httpMethod']
            
            # Extract path parameters
            if 'pathParameters' in event and event['pathParameters']:
                path_parameters = event['pathParameters']
            
            # Extract query parameters
            if 'queryStringParameters' in event and event['queryStringParameters']:
                query_parameters = event['queryStringParameters']
            
            # Extract body parameters
            if 'body' in event and event['body']:
                try:
                    body_parameters = json.loads(event['body'])
                except json.JSONDecodeError:
                    logger.warning("Failed to parse request body as JSON")
        
        # Handle OPTIONS request (CORS preflight)
        if http_method == "OPTIONS":
            logger.info("Handling OPTIONS request (CORS preflight)")
            return response
        
        # Handle email request (POST)
        if http_method == "POST":
            logger.info("Handling POST request for email")
            
            # Get recipient email from parameters
            recipient_email = None
            if 'email' in body_parameters:
                recipient_email = body_parameters['email']
            elif 'email' in query_parameters:
                recipient_email = query_parameters['email']
            
            # Get configuration (first from Parameter Store, then from event)
            config = get_parameter_store_config()
            if not config:
                config = get_config_from_event(event)
            
            # Send email
            if recipient_email:
                logger.info(f"Sending email to {recipient_email}")
                success = send_ovechkin_email(recipient_email)
            else:
                logger.info("Sending email to default recipient")
                success = send_ovechkin_email()
            
            # Prepare response
            if success:
                response["body"] = json.dumps({"message": "Email sent successfully"})
            else:
                response["statusCode"] = 500
                response["body"] = json.dumps({"error": "Failed to send email"})
        
        # Handle stats request (GET or default)
        else:
            logger.info("Handling GET request for stats")
            
            # Get stats with caching
            stats = get_stats_with_cache()
            
            # Check for errors
            if "error" in stats:
                response["statusCode"] = 500
                response["body"] = json.dumps({"error": stats["error"]})
            else:
                # Determine response format
                format_param = query_parameters.get("format", "full").lower()
                
                if format_param == "flat":
                    # Return flat stats
                    response["body"] = json.dumps(stats["flat_stats"])
                elif format_param == "nested":
                    # Return nested stats
                    response["body"] = json.dumps(stats["nested_stats"])
                else:
                    # Return full stats
                    response["body"] = json.dumps(stats)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}", exc_info=True)
        response["statusCode"] = 500
        response["body"] = json.dumps({"error": str(e)})
        return response


# For local testing
if __name__ == "__main__":
    # Simulate a GET request
    test_event = {
        "httpMethod": "GET",
        "queryStringParameters": {}
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(json.loads(result["body"]), indent=2))
