#!/usr/bin/env python3
"""
Script to run tests for the Graang project.
This script handles activating the virtual environment if needed and
running the tests with the proper Python path.
"""

import os
import sys
import subprocess

def main():
    # Check if we need to activate the virtual environment
    venv_python = os.path.join('venv', 'bin', 'python')
    venv_pytest = os.path.join('venv', 'bin', 'pytest')
    
    if os.path.exists(venv_pytest):
        # Use virtual environment
        print("Using virtual environment pytest...")
        pytest_cmd = venv_pytest
    else:
        # Use system pytest
        print("Using system pytest...")
        pytest_cmd = 'pytest'
    
    # Run the tests
    cmd = [pytest_cmd, '-v', 'tests/']
    result = subprocess.run(cmd)
    
    # Return the exit code
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())