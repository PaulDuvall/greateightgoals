#!/usr/bin/env python3
"""
Lambda function to update the Ovechkin Goal Tracker website

This Lambda function runs the update_website.py script to refresh
the static website content with the latest Ovechkin stats.
"""

import os
import sys
import logging
import boto3
import json
import importlib.util

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_parameter(name):
    """Get a parameter from SSM Parameter Store"""
    try:
        ssm = boto3.client('ssm')
        response = ssm.get_parameter(Name=name, WithDecryption=True)
        return response['Parameter']['Value']
    except Exception as e:
        logger.warning(f"Could not retrieve parameter {name}: {e}")
        return None

def lambda_handler(event, context):
    """
    Lambda handler function that executes the update_website.py script
    and syncs the updated content to S3
    
    Args:
        event: Lambda event data
        context: Lambda context object
        
    Returns:
        dict: Response with status and message
    """
    try:
        logger.info("Starting website update process")
        
        # Get environment variables
        stack_name = os.environ.get('STACK_NAME', 'static-website')
        
        # Get AWS region from Parameter Store or use environment variable as fallback
        region = os.environ.get('AWS_REGION')
        if not region:
            region = get_parameter('/ovechkin-tracker/aws_region')
            if not region:
                region = 'us-east-1'  # Default fallback if all else fails
        
        logger.info(f"Using AWS region: {region}")
        
        # Get the S3 bucket name from CloudFormation outputs
        cf_client = boto3.client('cloudformation', region_name=region)
        response = cf_client.describe_stacks(StackName=stack_name)
        
        bucket_name = None
        for output in response['Stacks'][0]['Outputs']:
            if output['OutputKey'] == 'WebsiteBucketName':
                bucket_name = output['OutputValue']
                break
        
        if not bucket_name:
            raise Exception(f"Could not find WebsiteBucketName in stack {stack_name} outputs")
        
        logger.info(f"Target S3 bucket: {bucket_name}")
        
        # Set up the Python path for imports
        # First, add the Lambda task directory to the path
        task_dir = os.path.dirname(os.path.abspath(__file__))
        if task_dir not in sys.path:
            sys.path.insert(0, task_dir)
        
        # Add the parent directory to the path for the ovechkin_tracker module
        parent_dir = os.path.dirname(task_dir)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
            
        # Print the sys.path for debugging
        logger.info(f"Python sys.path: {sys.path}")
        
        # List directories to debug
        logger.info(f"Contents of task_dir: {os.listdir(task_dir)}")
        
        # Import the update_website function directly
        try:
            # Try to import the update_website module
            update_website_path = os.path.join(task_dir, "update_website.py")
            logger.info(f"Importing update_website from: {update_website_path}")
            
            if not os.path.exists(update_website_path):
                raise FileNotFoundError(f"update_website.py not found at {update_website_path}")
                
            # Check if assets directory exists and log its location
            assets_dir = os.path.join(task_dir, "assets")
            if os.path.exists(assets_dir):
                logger.info(f"Assets directory found at: {assets_dir}")
                logger.info(f"Assets directory contents: {os.listdir(assets_dir)}")
            else:
                logger.warning(f"Assets directory not found at: {assets_dir}")
                
            spec = importlib.util.spec_from_file_location(
                "update_website", 
                update_website_path
            )
            update_website_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(update_website_module)
            
            # Call the update_website function
            logger.info("Running update_website function")
            result = update_website_module.update_website()
            
            if not result:
                raise Exception("update_website function returned False")
                
            logger.info("Website content updated successfully")
        except Exception as e:
            logger.error(f"Error running update_website module: {str(e)}")
            raise
        
        # Get the updated static files
        # In Lambda, the files will be in /tmp/static instead of task_dir/static
        static_dir = '/tmp/static'
        if not os.path.exists(static_dir):
            logger.warning(f"Temporary static directory not found at {static_dir}")
            # Try alternative locations
            alt_static_dir = os.path.join(task_dir, 'static')
            if os.path.exists(alt_static_dir):
                static_dir = alt_static_dir
                logger.info(f"Using alternative static directory: {static_dir}")
            else:
                alt_static_dir = os.path.join(os.path.dirname(task_dir), 'static')
                if os.path.exists(alt_static_dir):
                    static_dir = alt_static_dir
                    logger.info(f"Using alternative static directory: {static_dir}")
                else:
                    raise Exception(f"Static directory not found at {static_dir} or any alternative locations")
        
        logger.info(f"Using static directory: {static_dir}")
        logger.info(f"Static directory contents: {os.listdir(static_dir)}")
        
        # Upload the updated content to S3
        s3_client = boto3.client('s3', region_name=region)
        
        logger.info(f"Uploading content from {static_dir} to S3 bucket {bucket_name}")
        for root, _, files in os.walk(static_dir):
            for file in files:
                file_path = os.path.join(root, file)
                s3_key = os.path.relpath(file_path, static_dir)
                
                logger.info(f"Uploading {file_path} to s3://{bucket_name}/{s3_key}")
                s3_client.upload_file(
                    Filename=file_path,
                    Bucket=bucket_name,
                    Key=s3_key,
                    ExtraArgs={'ContentType': get_content_type(file_path)}
                )
        
        # Invalidate CloudFront cache if distribution exists
        try:
            # Get CloudFront distribution ID
            for output in response['Stacks'][0]['Outputs']:
                if output['OutputKey'] == 'CloudFrontDistributionId':
                    distribution_id = output['OutputValue']
                    
                    # Create CloudFront invalidation
                    cf_client = boto3.client('cloudfront', region_name=region)
                    cf_client.create_invalidation(
                        DistributionId=distribution_id,
                        InvalidationBatch={
                            'Paths': {
                                'Quantity': 1,
                                'Items': ['/*']
                            },
                            'CallerReference': str(context.aws_request_id)
                        }
                    )
                    logger.info(f"Created CloudFront invalidation for distribution {distribution_id}")
                    break
        except Exception as e:
            logger.warning(f"Could not invalidate CloudFront cache: {str(e)}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Website updated successfully',
                'bucket': bucket_name
            })
        }
        
    except Exception as e:
        logger.error(f"Error updating website: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'Error updating website: {str(e)}'
            })
        }

def get_content_type(file_path):
    """
    Determine the content type based on file extension
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: Content type for the file
    """
    extension = os.path.splitext(file_path)[1].lower()
    content_types = {
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.json': 'application/json',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.ico': 'image/x-icon'
    }
    
    return content_types.get(extension, 'application/octet-stream')
