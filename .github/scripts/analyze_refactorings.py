#!/usr/bin/env python3
"""
Refactoring Analysis Script

This script analyzes Python files in the repository to identify refactoring opportunities
based on Martin Fowler's Refactoring catalog using OpenAI's GPT-4 model.

The script generates a single HTML report with collapsible sections for each file.
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
OUTPUT_HTML = os.path.join(OUTPUT_DIR, 'refactoring-report.html')
MAX_FILE_SIZE = 30000  # Skip files larger than 30KB
MODEL = 'gpt-4'

# HTML Templates
HTML_HEADER = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Refactoring Analysis Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .file-section {
            margin-bottom: 20px;
            border: 1px solid #ddd;
            border-radius: 4px;
            overflow: hidden;
        }
        .file-header {
            background-color: #f5f5f5;
            padding: 10px 15px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .file-header:hover {
            background-color: #e9e9e9;
        }
        .file-name {
            font-weight: bold;
            font-family: monospace;
        }
        .file-content {
            padding: 15px;
            border-top: 1px solid #ddd;
            display: none;
        }
        .toggle-button {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 5px 10px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 14px;
            border-radius: 4px;
            cursor: pointer;
        }
        .toggle-button:hover {
            background-color: #45a049;
        }
        pre {
            background: #f8f8f8;
            padding: 10px;
            overflow-x: auto;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        h1, h2, h3 {
            margin: 0.5em 0;
        }
        .summary {
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f0f8ff;
            border-radius: 4px;
            border: 1px solid #b8daff;
        }
        .toc {
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f5f5f5;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        .toc ul {
            list-style-type: none;
            padding-left: 10px;
        }
        .toc li {
            margin-bottom: 5px;
        }
        .toc a {
            text-decoration: none;
            color: #0366d6;
        }
        .toc a:hover {
            text-decoration: underline;
        }
        .severity-high {
            color: #d73a49;
            font-weight: bold;
        }
        .severity-medium {
            color: #e36209;
            font-weight: bold;
        }
        .severity-low {
            color: #0366d6;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1>Refactoring Analysis Report</h1>
    <div class="summary">
        <p>This report contains refactoring recommendations based on Martin Fowler's catalog, 
        generated by GPT-4.</p>
        <p>Click on each file to expand its refactoring suggestions.</p>
    </div>
"""

HTML_TOC_START = """
    <div class="toc">
        <h2>Table of Contents</h2>
        <ul>
"""

HTML_TOC_END = """
        </ul>
    </div>
"""

HTML_FOOTER = """
    <script>
        function toggleSection(index) {
            const content = document.getElementById(`file-content-${index}`);
            const button = document.querySelector(`#file-header-${index} .toggle-button`);
            
            if (content.style.display === 'block') {
                content.style.display = 'none';
                button.textContent = 'Show';
            } else {
                content.style.display = 'block';
                button.textContent = 'Hide';
            }
        }
        
        // Function to expand all sections
        function expandAll() {
            document.querySelectorAll('.file-content').forEach((content, index) => {
                content.style.display = 'block';
                document.querySelector(`#file-header-${index} .toggle-button`).textContent = 'Hide';
            });
        }
        
        // Function to collapse all sections
        function collapseAll() {
            document.querySelectorAll('.file-content').forEach((content, index) => {
                content.style.display = 'none';
                document.querySelector(`#file-header-${index} .toggle-button`).textContent = 'Show';
            });
        }
    </script>
</body>
</html>
"""


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


def generate_html_report(file_paths, analyses):
    """Generate a single HTML report with collapsible sections for each file"""
    logger.info(f"Generating HTML report: {OUTPUT_HTML}")
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Filter out files with no analysis
    valid_analyses = [(path, analysis) for path, analysis in zip(file_paths, analyses) if analysis]
    
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as report:
        # Write HTML header
        report.write(HTML_HEADER)
        
        # Generate table of contents
        report.write(HTML_TOC_START)
        for i, (path, _) in enumerate(valid_analyses):
            report.write(f'            <li><a href="#file-{i}">{path}</a></li>\n')
        report.write(HTML_TOC_END)
        
        # Add expand/collapse all buttons
        report.write('    <div style="margin-bottom: 20px">\n')
        report.write('        <button onclick="expandAll()" class="toggle-button">Expand All</button>\n')
        report.write('        <button onclick="collapseAll()" class="toggle-button" style="margin-left: 10px">Collapse All</button>\n')
        report.write('    </div>\n')
        
        # Write each file's analysis
        for i, (path, analysis) in enumerate(valid_analyses):
            report.write(f'    <div class="file-section" id="file-{i}">\n')
            report.write(f'        <div class="file-header" id="file-header-{i}" onclick="toggleSection({i})">\n')
            report.write(f'            <span class="file-name">{path}</span>\n')
            report.write(f'            <button class="toggle-button" type="button">Show</button>\n')
            report.write('        </div>\n')
            report.write(f'        <div class="file-content" id="file-content-{i}">\n')
            
            # Convert the Markdown from GPT into HTML-safe content
            safe_analysis = analysis.replace('<', '&lt;').replace('>', '&gt;')
            
            # Add some basic styling for severity levels
            safe_analysis = safe_analysis.replace('Severity: High', '<span class="severity-high">Severity: High</span>')
            safe_analysis = safe_analysis.replace('Severity: Medium', '<span class="severity-medium">Severity: Medium</span>')
            safe_analysis = safe_analysis.replace('Severity: Low', '<span class="severity-low">Severity: Low</span>')
            
            report.write(f'            <pre>{safe_analysis}</pre>\n')
            report.write('        </div>\n')
            report.write('    </div>\n')
        
        # Write HTML footer
        report.write(HTML_FOOTER)
    
    logger.info(f"HTML report generated at {OUTPUT_HTML}")
    return OUTPUT_HTML


def main():
    """Main function to orchestrate the analysis process"""
    # Setup OpenAI client
    client = setup_openai_client()
    
    # Find Python files
    python_files = find_python_files()
    
    # Analyze each file
    results = []
    
    for file_path in python_files:
        result = analyze_file(client, file_path)
        results.append(result)
    
    # Generate HTML report
    generate_html_report(python_files, results)
    
    logger.info(f"Analysis complete. Report saved to {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
