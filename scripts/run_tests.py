"""
AEGIS Test Runner Script
Executes all unit, integration, and research benchmark test suites.
"""

import subprocess
import sys

def main():
    print("=" * 70)
    print("  Running AEGIS Complete Test Suite (Pytest)")
    print("=" * 70)
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"], check=False)
    sys.exit(result.returncode)

if __name__ == '__main__':
    main()
