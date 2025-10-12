#!/usr/bin/env python3
"""
Test Runner Script for Thalamus Testing Suite

Copyright (C) 2025 Mark "Rizzn" Hopkins, Athena Vernal, John Casaretto

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from typing import List, Optional


class TestRunner:
    """Test runner for Thalamus testing suite."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.tests_dir = self.project_root / "tests"
        self.venv_path = self.project_root / "venv"
        self.python_executable = self.venv_path / "Scripts" / "python.exe" if os.name == 'nt' else self.venv_path / "bin" / "python"
    
    def run_command(self, command: List[str], cwd: Optional[str] = None) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        if cwd is None:
            cwd = self.project_root
        
        print(f"Running: {' '.join(command)}")
        print(f"Working directory: {cwd}")
        
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return result
        except subprocess.TimeoutExpired:
            print("Command timed out after 5 minutes")
            return None
        except Exception as e:
            print(f"Error running command: {e}")
            return None
    
    def check_venv(self) -> bool:
        """Check if virtual environment exists and is activated."""
        if not self.python_executable.exists():
            print(f"Virtual environment not found at {self.venv_path}")
            return False
        
        # Check if we're in the virtual environment
        result = self.run_command([str(self.python_executable), "-c", "import sys; print(sys.prefix)"])
        if result and result.returncode == 0:
            venv_prefix = result.stdout.strip()
            if str(self.venv_path) in venv_prefix:
                print("✓ Virtual environment is active")
                return True
        
        print("⚠ Virtual environment may not be active")
        return False
    
    def install_dependencies(self) -> bool:
        """Install test dependencies."""
        print("Installing test dependencies...")
        
        # Install main requirements
        result = self.run_command([
            str(self.python_executable), "-m", "pip", "install", "-r", "requirements.txt"
        ])
        if not result or result.returncode != 0:
            print("Failed to install main requirements")
            if result:
                print(result.stderr)
            return False
        
        # Install test requirements
        result = self.run_command([
            str(self.python_executable), "-m", "pip", "install", "-r", "requirements-testing.txt"
        ])
        if not result or result.returncode != 0:
            print("Failed to install test requirements")
            if result:
                print(result.stderr)
            return False
        
        print("✓ Dependencies installed successfully")
        return True
    
    def run_unit_tests(self, verbose: bool = False) -> bool:
        """Run unit tests."""
        print("\n" + "="*50)
        print("RUNNING UNIT TESTS")
        print("="*50)
        
        command = [str(self.python_executable), "-m", "pytest", "tests/unit/"]
        if verbose:
            command.append("-v")
        
        result = self.run_command(command)
        if not result:
            print("Unit tests failed to run")
            return False
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        print(f"Unit tests {'PASSED' if success else 'FAILED'}")
        return success
    
    def run_integration_tests(self, verbose: bool = False) -> bool:
        """Run integration tests."""
        print("\n" + "="*50)
        print("RUNNING INTEGRATION TESTS")
        print("="*50)
        
        command = [str(self.python_executable), "-m", "pytest", "tests/integration/"]
        if verbose:
            command.append("-v")
        
        result = self.run_command(command)
        if not result:
            print("Integration tests failed to run")
            return False
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        print(f"Integration tests {'PASSED' if success else 'FAILED'}")
        return success
    
    def run_e2e_tests(self, verbose: bool = False) -> bool:
        """Run end-to-end tests."""
        print("\n" + "="*50)
        print("RUNNING END-TO-END TESTS")
        print("="*50)
        
        command = [str(self.python_executable), "-m", "pytest", "tests/e2e/"]
        if verbose:
            command.append("-v")
        
        result = self.run_command(command)
        if not result:
            print("E2E tests failed to run")
            return False
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        print(f"E2E tests {'PASSED' if success else 'FAILED'}")
        return success
    
    def run_all_tests(self, verbose: bool = False) -> bool:
        """Run all tests."""
        print("\n" + "="*50)
        print("RUNNING ALL TESTS")
        print("="*50)
        
        command = [str(self.python_executable), "-m", "pytest", "tests/"]
        if verbose:
            command.append("-v")
        
        result = self.run_command(command)
        if not result:
            print("Tests failed to run")
            return False
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        print(f"All tests {'PASSED' if success else 'FAILED'}")
        return success
    
    def run_coverage_tests(self) -> bool:
        """Run tests with coverage reporting."""
        print("\n" + "="*50)
        print("RUNNING TESTS WITH COVERAGE")
        print("="*50)
        
        command = [
            str(self.python_executable), "-m", "pytest", 
            "--cov=examples", 
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-report=xml:coverage.xml",
            "tests/"
        ]
        
        result = self.run_command(command)
        if not result:
            print("Coverage tests failed to run")
            return False
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        print(f"Coverage tests {'PASSED' if success else 'FAILED'}")
        
        if success:
            print(f"Coverage report generated in htmlcov/index.html")
        
        return success
    
    def run_performance_tests(self) -> bool:
        """Run performance tests."""
        print("\n" + "="*50)
        print("RUNNING PERFORMANCE TESTS")
        print("="*50)
        
        command = [
            str(self.python_executable), "-m", "pytest", 
            "-m", "performance",
            "--benchmark-only",
            "tests/"
        ]
        
        result = self.run_command(command)
        if not result:
            print("Performance tests failed to run")
            return False
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        print(f"Performance tests {'PASSED' if success else 'FAILED'}")
        return success
    
    def run_security_tests(self) -> bool:
        """Run security tests."""
        print("\n" + "="*50)
        print("RUNNING SECURITY TESTS")
        print("="*50)
        
        command = [
            str(self.python_executable), "-m", "pytest", 
            "-m", "security",
            "tests/"
        ]
        
        result = self.run_command(command)
        if not result:
            print("Security tests failed to run")
            return False
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        print(f"Security tests {'PASSED' if success else 'FAILED'}")
        return success
    
    def run_specific_test(self, test_path: str, verbose: bool = False) -> bool:
        """Run a specific test file or test function."""
        print(f"\nRunning specific test: {test_path}")
        
        command = [str(self.python_executable), "-m", "pytest", test_path]
        if verbose:
            command.append("-v")
        
        result = self.run_command(command)
        if not result:
            print("Test failed to run")
            return False
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        print(f"Test {'PASSED' if success else 'FAILED'}")
        return success
    
    def lint_code(self) -> bool:
        """Run code linting."""
        print("\n" + "="*50)
        print("RUNNING CODE LINTING")
        print("="*50)
        
        # Run flake8 if available
        command = [str(self.python_executable), "-m", "flake8", "examples/", "tests/"]
        result = self.run_command(command)
        
        if result and result.returncode == 0:
            print("✓ Code linting passed")
            return True
        elif result:
            print("Code linting issues found:")
            print(result.stdout)
            return False
        else:
            print("Flake8 not available, skipping linting")
            return True
    
    def run_setup(self) -> bool:
        """Run initial setup."""
        print("Setting up Thalamus testing environment...")
        
        # Check virtual environment
        if not self.check_venv():
            print("Please activate the virtual environment first:")
            print("  venv\\Scripts\\Activate.ps1  # Windows PowerShell")
            print("  source venv/bin/activate    # Linux/Mac")
            return False
        
        # Install dependencies
        if not self.install_dependencies():
            return False
        
        # Create tmp directory
        tmp_dir = self.project_root / "tmp"
        tmp_dir.mkdir(exist_ok=True)
        print(f"✓ Created tmp directory: {tmp_dir}")
        
        print("✓ Setup completed successfully")
        return True


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="Thalamus Test Runner")
    parser.add_argument("--setup", action="store_true", help="Run initial setup")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--coverage", action="store_true", help="Run tests with coverage")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--security", action="store_true", help="Run security tests")
    parser.add_argument("--lint", action="store_true", help="Run code linting")
    parser.add_argument("--test", type=str, help="Run specific test file or function")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Run setup if requested
    if args.setup:
        if not runner.run_setup():
            sys.exit(1)
        return
    
    # Run specific test
    if args.test:
        if not runner.run_specific_test(args.test, args.verbose):
            sys.exit(1)
        return
    
    # Run linting
    if args.lint:
        if not runner.lint_code():
            sys.exit(1)
        return
    
    # Run specific test types
    success = True
    
    if args.unit:
        success &= runner.run_unit_tests(args.verbose)
    
    if args.integration:
        success &= runner.run_integration_tests(args.verbose)
    
    if args.e2e:
        success &= runner.run_e2e_tests(args.verbose)
    
    if args.coverage:
        success &= runner.run_coverage_tests()
    
    if args.performance:
        success &= runner.run_performance_tests()
    
    if args.security:
        success &= runner.run_security_tests()
    
    # Run all tests if no specific type specified
    if not any([args.unit, args.integration, args.e2e, args.coverage, args.performance, args.security]):
        success &= runner.run_all_tests(args.verbose)
    
    if not success:
        print("\n❌ Some tests failed!")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")


if __name__ == "__main__":
    main()
