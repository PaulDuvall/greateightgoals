#!/usr/bin/env python3
"""
Test the Lambda function locally

This script simulates the Lambda environment locally to test the update_website function
without having to deploy to AWS each time.
"""

import os
import sys
import json
import logging
import argparse
import importlib.util
import tempfile
import shutil
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """
    Check if all required dependencies are installed
    """
    required = ['boto3', 'pytz', 'requests']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            logger.info(f"\u2705 Package {package} is installed")
        except ImportError:
            logger.error(f"\u274c Package {package} is NOT installed")
            missing.append(package)
    
    if missing:
        logger.error(f"Missing dependencies: {', '.join(missing)}")
        logger.info("Install missing dependencies with: pip install -r lambda/requirements-lambda.txt")
        return False
    return True

def check_ovechkin_tracker():
    """
    Check if the ovechkin_tracker module is accessible
    """
    try:
        # Get the directory structure
        script_dir = os.path.dirname(os.path.abspath(__file__))
        aws_static_website_dir = os.path.dirname(script_dir)
        project_root = os.path.dirname(aws_static_website_dir)
        
        # Check if ovechkin_tracker module is accessible
        ovechkin_tracker_path = os.path.join(project_root, 'ovechkin_tracker')
        if os.path.exists(ovechkin_tracker_path):
            logger.info(f"\u2705 ovechkin_tracker module found at: {ovechkin_tracker_path}")
            logger.info(f"Contents: {os.listdir(ovechkin_tracker_path)}")
            
            # Check for __init__.py file
            if os.path.exists(os.path.join(ovechkin_tracker_path, '__init__.py')):
                logger.info("\u2705 __init__.py file exists in ovechkin_tracker module")
            else:
                logger.warning("\u26a0 __init__.py file missing in ovechkin_tracker module")
                logger.info("Creating __init__.py file...")
                with open(os.path.join(ovechkin_tracker_path, '__init__.py'), 'w') as f:
                    f.write("# ovechkin_tracker module\n")
            
            # Try to import the module
            sys.path.insert(0, project_root)
            try:
                from ovechkin_tracker.ovechkin_data import OvechkinData
                logger.info("\u2705 Successfully imported OvechkinData directly")
                return True
            except ImportError as e:
                logger.error(f"\u274c Failed to import OvechkinData: {str(e)}")
                return False
        else:
            logger.error(f"\u274c ovechkin_tracker module not found at: {ovechkin_tracker_path}")
            return False
    except Exception as e:
        logger.error(f"Error checking ovechkin_tracker module: {str(e)}")
        return False

def test_update_website():
    """
    Test the update_website.py script directly
    """
    try:
        # Get the directory structure
        script_dir = os.path.dirname(os.path.abspath(__file__))
        aws_static_website_dir = os.path.dirname(script_dir)
        project_root = os.path.dirname(aws_static_website_dir)
        
        # Add necessary directories to Python path
        sys.path.insert(0, aws_static_website_dir)
        sys.path.insert(0, project_root)
        
        # Import the update_website module
        update_website_path = os.path.join(aws_static_website_dir, "update_website.py")
        logger.info(f"Importing update_website from: {update_website_path}")
        
        if not os.path.exists(update_website_path):
            logger.error(f"\u274c update_website.py not found at {update_website_path}")
            return False
        
        # Import the update_website module
        spec = importlib.util.spec_from_file_location("update_website", update_website_path)
        update_website_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(update_website_module)
        
        # Call the update_website function
        logger.info("Running update_website function")
        result = update_website_module.update_website()
        
        if not result:
            logger.error("\u274c update_website function returned False")
            return False
        
        logger.info("\u2705 Website content updated successfully")
        return True
    except Exception as e:
        logger.error(f"Error testing update_website: {str(e)}")
        return False

def simulate_lambda_handler():
    """
    Simulate the Lambda handler function locally
    """
    try:
        logger.info("Starting local test of website update process")
        
        # Get the directory structure
        script_dir = os.path.dirname(os.path.abspath(__file__))
        aws_static_website_dir = os.path.dirname(script_dir)
        project_root = os.path.dirname(aws_static_website_dir)
        lambda_dir = os.path.join(aws_static_website_dir, 'lambda')
        
        # Create a temporary directory to simulate the Lambda environment
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temporary directory for Lambda simulation: {temp_dir}")
        
        try:
            # Copy the Lambda function code
            lambda_file = os.path.join(lambda_dir, "update_website_lambda.py")
            if not os.path.exists(lambda_file):
                logger.error(f"\u274c update_website_lambda.py not found at {lambda_file}")
                return False
            
            # Copy update_website.py to the temp directory
            update_website_path = os.path.join(aws_static_website_dir, "update_website.py")
            if not os.path.exists(update_website_path):
                logger.error(f"\u274c update_website.py not found at {update_website_path}")
                return False
            
            # Copy necessary files to the temp directory
            shutil.copy2(lambda_file, os.path.join(temp_dir, "update_website_lambda.py"))
            shutil.copy2(update_website_path, os.path.join(temp_dir, "update_website.py"))
            
            # Create static directory in temp dir
            static_dir = os.path.join(temp_dir, "static")
            os.makedirs(static_dir, exist_ok=True)
            
            # Copy ovechkin_tracker module
            ovechkin_tracker_src = os.path.join(project_root, "ovechkin_tracker")
            ovechkin_tracker_dest = os.path.join(temp_dir, "ovechkin_tracker")
            if os.path.exists(ovechkin_tracker_src):
                shutil.copytree(ovechkin_tracker_src, ovechkin_tracker_dest)
                logger.info(f"\u2705 Copied ovechkin_tracker module to {ovechkin_tracker_dest}")
            else:
                logger.error(f"\u274c ovechkin_tracker module not found at {ovechkin_tracker_src}")
                return False
            
            # Add necessary directories to Python path
            sys.path.insert(0, temp_dir)
            
            # Print the sys.path for debugging
            logger.info(f"Python sys.path: {sys.path}")
            logger.info(f"Contents of temp_dir: {os.listdir(temp_dir)}")
            
            # Import the Lambda handler
            lambda_path = os.path.join(temp_dir, "update_website_lambda.py")
            logger.info(f"Importing Lambda handler from: {lambda_path}")
            spec = importlib.util.spec_from_file_location("update_website_lambda", lambda_path)
            lambda_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(lambda_module)
            
            # Create a mock event and context
            event = {}
            
            class MockContext:
                def __init__(self):
                    self.function_name = "local-test-function"
                    self.memory_limit_in_mb = 128
                    self.invoked_function_arn = "arn:aws:lambda:local:123456789012:function:local-test"  # Mock AWS account ID for testing
                    self.aws_request_id = str(uuid.uuid4())
                    
            context = MockContext()
            
            # Set environment variables
            os.environ['STACK_NAME'] = 'static-website'
            
            # Call the Lambda handler
            logger.info("Calling Lambda handler")
            response = lambda_module.lambda_handler(event, context)
            
            logger.info(f"Lambda handler response: {json.dumps(response, indent=2)}")
            
            if response.get('statusCode') == 200:
                logger.info("\u2705 Lambda handler executed successfully")
                return True
            else:
                logger.error(f"\u274c Lambda handler failed: {response.get('body')}")
                return False
        finally:
            # Clean up the temporary directory
            logger.info(f"Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)
    except Exception as e:
        logger.error(f"Error in local test: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Test the Lambda function locally')
    parser.add_argument('--check-deps', action='store_true', help='Check dependencies')
    parser.add_argument('--check-module', action='store_true', help='Check ovechkin_tracker module')
    parser.add_argument('--test-update', action='store_true', help='Test update_website.py')
    parser.add_argument('--test-lambda', action='store_true', help='Test Lambda handler')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    args = parser.parse_args()
    
    # If no arguments provided, run all tests
    if not any(vars(args).values()):
        args.all = True
    
    success = True
    
    if args.all or args.check_deps:
        logger.info("\n==== Checking dependencies ====")
        if not check_dependencies():
            success = False
    
    if args.all or args.check_module:
        logger.info("\n==== Checking ovechkin_tracker module ====")
        if not check_ovechkin_tracker():
            success = False
    
    if args.all or args.test_update:
        logger.info("\n==== Testing update_website.py ====")
        if not test_update_website():
            success = False
    
    if args.all or args.test_lambda:
        logger.info("\n==== Testing Lambda handler ====")
        if not simulate_lambda_handler():
            success = False
    
    if success:
        logger.info("\n\u2705 All tests completed successfully")
        return 0
    else:
        logger.error("\n\u274c Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
