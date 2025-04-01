#!/usr/bin/env python3
"""
Refactoring Analysis Script

This script analyzes Python files in the repository to identify refactoring opportunities
based on Martin Fowler's Refactoring catalog using OpenAI's GPT-4 model.

The script generates individual Markdown reports for each file and a summary report.
"""

import os
import glob
import logging
import openai
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
OUTPUT_DIR = 'refactoring-reports'
MAX_FILE_SIZE = 30000  # Skip files larger than 30KB
MODEL = 'gpt-4'


def setup_openai_client():
    """Configure the OpenAI client with API key from environment variables"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    return openai.OpenAI(api_key=api_key)


def find_python_files():
    """Find all Python files in the repository"""
    # Exclude virtual environments, .git directory, and other non-source directories
    exclude_patterns = [
        '.git/**',
        'venv/**',
        '.venv/**',
        '__pycache__/**',
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '.github/**',  # Skip GitHub workflows and scripts
    ]
    
    # Find all Python files
    python_files = glob.glob('**/*.py', recursive=True)
    
    # Filter out excluded files
    for pattern in exclude_patterns:
        python_files = [f for f in python_files if not Path(f).match(pattern)]
    
    logger.info(f"Found {len(python_files)} Python files to analyze")
    return python_files


def analyze_file(client, file_path):
    """Analyze a single Python file for refactoring opportunities"""
    logger.info(f"Analyzing {file_path}...")
    
    # Read file content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None
    
    # Skip files that are too large
    if len(code_content) > MAX_FILE_SIZE:
        logger.warning(f"Skipping {file_path} - too large ({len(code_content)} bytes)")
        return None
    
    # Skip empty files
    if not code_content.strip():
        logger.warning(f"Skipping {file_path} - empty file")
        return None
    
    # Call OpenAI API
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": """You are a code refactoring expert familiar with Martin Fowler's Refactoring catalog. 
                Analyze Python code to identify refactoring opportunities. For each opportunity:
                1. Identify the specific refactoring pattern from Fowler's catalog
                2. Specify the function name and line numbers
                3. Explain the code smell that indicates the need for refactoring
                4. Provide a clear recommendation with specific next steps
                5. Include a link to the refactoring pattern documentation
                6. Assign a severity level (High, Medium, Low) based on impact
                
                Format your response as Markdown with clear headings and bullet points.
                """},
                {"role": "user", "content": f"Analyze this Python code and identify refactoring opportunities using Martin Fowler's catalog:\n\n```python\n{code_content}\n```"}
            ],
            temperature=0.1,
            max_tokens=1500
        )
        
        # Extract and return results
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error analyzing {file_path}: {e}")
        return None


def save_report(file_path, content):
    """Save analysis results to a Markdown file"""
    if not content:
        return
    
    # Create safe filename
    safe_filename = file_path.replace('/', '_').replace('\\', '_')
    output_file = os.path.join(OUTPUT_DIR, f"{safe_filename}.md")
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Refactoring Analysis for {file_path}\n\n")
        f.write(content)
    
    logger.info(f"Analysis for {file_path} saved to {output_file}")
    return output_file


def create_summary(analyzed_files, output_files):
    """Create a summary report with links to individual file reports"""
    summary_file = os.path.join(OUTPUT_DIR, "SUMMARY.md")
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("# Refactoring Analysis Summary\n\n")
        f.write("## Overview\n\n")
        f.write(f"This report contains refactoring recommendations for {len(analyzed_files)} Python files ")
        f.write("based on Martin Fowler's Refactoring catalog.\n\n")
        f.write("Each file was analyzed using OpenAI's GPT-4 model to identify code smells ")
        f.write("and suggest specific refactoring patterns.\n\n")
        
        f.write("## Files Analyzed\n\n")
        for file_path, output_file in zip(analyzed_files, output_files):
            if output_file:  # Only include files that were successfully analyzed
                relative_path = os.path.relpath(output_file, OUTPUT_DIR)
                f.write(f"- [{file_path}](./{relative_path})\n")
        
        f.write("\n## Next Steps\n\n")
        f.write("1. Review the individual file reports\n")
        f.write("2. Prioritize refactorings based on severity and impact\n")
        f.write("3. Create tickets for implementing the recommended refactorings\n")
        f.write("4. Consider adding automated refactoring checks to your CI/CD pipeline\n")
    
    logger.info(f"Summary report created at {summary_file}")


def main():
    """Main function to orchestrate the analysis process"""
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Setup OpenAI client
    client = setup_openai_client()
    
    # Find Python files
    python_files = find_python_files()
    
    # Analyze each file
    results = []
    output_files = []
    
    for file_path in python_files:
        result = analyze_file(client, file_path)
        results.append(result)
        
        if result:
            output_file = save_report(file_path, result)
            output_files.append(output_file)
        else:
            output_files.append(None)
    
    # Create summary
    create_summary(python_files, output_files)
    
    logger.info(f"Analysis complete. Reports saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
