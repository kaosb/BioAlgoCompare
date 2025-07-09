#!/usr/bin/env python3
"""
Setup script for BioAlgoCompare development environment.

This script configures a complete development environment with all
necessary tools, dependencies, and configurations.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
from typing import List, Tuple, Optional
import json


class EnvironmentSetup:
    """Manages the setup of BioAlgoCompare development environment."""
    
    def __init__(self):
        """Initialize setup manager."""
        self.platform = platform.system().lower()
        self.python_version = sys.version_info
        self.project_root = Path(__file__).parent.parent
        self.venv_path = self.project_root / "venv"
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def check_system_requirements(self) -> bool:
        """Check if system meets minimum requirements."""
        print("🔍 Checking system requirements...")
        
        # Check Python version
        if self.python_version < (3, 8):
            self.errors.append(
                f"Python 3.8+ required, found {self.python_version.major}.{self.python_version.minor}"
            )
            return False
        
        # Check Git
        if not shutil.which("git"):
            self.errors.append("Git is not installed or not in PATH")
            return False
        
        # Check available space
        stat = os.statvfs(self.project_root)
        free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
        if free_gb < 2:
            self.warnings.append(f"Low disk space: {free_gb:.1f}GB available")
        
        print("✅ System requirements met")
        return True
    
    def create_virtual_environment(self) -> bool:
        """Create Python virtual environment."""
        print("\n📦 Creating virtual environment...")
        
        if self.venv_path.exists():
            response = input("Virtual environment exists. Recreate? (y/N): ")
            if response.lower() != 'y':
                print("Using existing virtual environment")
                return True
            
            print("Removing existing virtual environment...")
            shutil.rmtree(self.venv_path)
        
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", str(self.venv_path)],
                check=True
            )
            print("✅ Virtual environment created")
            return True
        except subprocess.CalledProcessError as e:
            self.errors.append(f"Failed to create virtual environment: {e}")
            return False
    
    def get_pip_command(self) -> List[str]:
        """Get the pip command for the virtual environment."""
        if self.platform == "windows":
            return [str(self.venv_path / "Scripts" / "pip")]
        else:
            return [str(self.venv_path / "bin" / "pip")]
    
    def install_dependencies(self) -> bool:
        """Install project dependencies."""
        print("\n📚 Installing dependencies...")
        
        pip_cmd = self.get_pip_command()
        
        # Upgrade pip
        try:
            subprocess.run(
                pip_cmd + ["install", "--upgrade", "pip", "setuptools", "wheel"],
                check=True
            )
        except subprocess.CalledProcessError:
            self.warnings.append("Failed to upgrade pip")
        
        # Install main dependencies
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            try:
                subprocess.run(
                    pip_cmd + ["install", "-r", str(requirements_file)],
                    check=True
                )
                print("✅ Main dependencies installed")
            except subprocess.CalledProcessError as e:
                self.errors.append(f"Failed to install requirements: {e}")
                return False
        
        # Install development dependencies
        dev_requirements = self.project_root / "requirements-dev.txt"
        if dev_requirements.exists():
            try:
                subprocess.run(
                    pip_cmd + ["install", "-r", str(dev_requirements)],
                    check=True
                )
                print("✅ Development dependencies installed")
            except subprocess.CalledProcessError:
                self.warnings.append("Some development dependencies failed to install")
        
        # Install project in editable mode
        try:
            subprocess.run(
                pip_cmd + ["install", "-e", str(self.project_root)],
                check=True
            )
            print("✅ Project installed in editable mode")
        except subprocess.CalledProcessError:
            self.warnings.append("Failed to install project in editable mode")
        
        return True
    
    def install_quality_tools(self) -> bool:
        """Install and configure quality assurance tools."""
        print("\n🛠️  Installing quality tools...")
        
        pip_cmd = self.get_pip_command()
        
        tools = [
            "ruff",
            "mypy", 
            "bandit",
            "pytest",
            "pytest-cov",
            "pytest-xdist",
            "pre-commit",
            "interrogate"
        ]
        
        for tool in tools:
            try:
                subprocess.run(
                    pip_cmd + ["install", tool],
                    check=True,
                    capture_output=True
                )
                print(f"  ✅ {tool}")
            except subprocess.CalledProcessError:
                self.warnings.append(f"Failed to install {tool}")
        
        # Install pre-commit hooks
        if self.platform == "windows":
            pre_commit = self.venv_path / "Scripts" / "pre-commit"
        else:
            pre_commit = self.venv_path / "bin" / "pre-commit"
        
        if pre_commit.exists():
            try:
                subprocess.run(
                    [str(pre_commit), "install"],
                    check=True,
                    cwd=self.project_root
                )
                print("✅ Pre-commit hooks installed")
            except subprocess.CalledProcessError:
                self.warnings.append("Failed to install pre-commit hooks")
        
        return True
    
    def setup_environment_files(self) -> bool:
        """Create necessary environment files."""
        print("\n📄 Setting up environment files...")
        
        # Create .env from .env.example
        env_example = self.project_root / ".env.example"
        env_file = self.project_root / ".env"
        
        if env_example.exists() and not env_file.exists():
            shutil.copy(env_example, env_file)
            print("✅ Created .env file from template")
        
        # Create directories
        directories = [
            "results",
            "logs",
            "cache",
            "metadata",
            "checkpoints",
            "quality-reports",
            "docs/_build"
        ]
        
        for dir_name in directories:
            dir_path = self.project_root / dir_name
            dir_path.mkdir(exist_ok=True)
        
        print("✅ Directory structure created")
        
        # Create .gitignore entries
        gitignore_entries = [
            "\n# Environment files",
            ".env",
            "venv/",
            "*.egg-info/",
            "\n# Results and outputs", 
            "results/",
            "logs/",
            "cache/",
            "checkpoints/",
            "quality-reports/",
            "\n# IDE",
            ".vscode/settings.json",
            ".idea/"
        ]
        
        gitignore_path = self.project_root / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, 'a') as f:
                current_content = open(gitignore_path).read()
                for entry in gitignore_entries:
                    if entry not in current_content:
                        f.write(f"{entry}\n")
        
        return True
    
    def configure_ide(self) -> bool:
        """Configure IDE settings."""
        print("\n💻 Configuring IDE...")
        
        # VS Code settings
        vscode_dir = self.project_root / ".vscode"
        vscode_dir.mkdir(exist_ok=True)
        
        vscode_settings = {
            "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
            "python.linting.enabled": True,
            "python.linting.ruffEnabled": True,
            "python.formatting.provider": "ruff",
            "python.testing.pytestEnabled": True,
            "editor.formatOnSave": True,
            "editor.rulers": [88],
            "files.exclude": {
                "**/__pycache__": True,
                "**/*.pyc": True,
                ".pytest_cache": True,
                ".ruff_cache": True,
                ".mypy_cache": True
            }
        }
        
        settings_path = vscode_dir / "settings.json"
        if not settings_path.exists():
            with open(settings_path, 'w') as f:
                json.dump(vscode_settings, f, indent=4)
            print("✅ VS Code settings configured")
        
        # Launch configuration
        launch_config = {
            "version": "0.2.0",
            "configurations": [
                {
                    "name": "Run Algorithm",
                    "type": "python",
                    "request": "launch",
                    "module": "scripts.cli.main",
                    "args": ["run", "--algorithm", "hoa", "--instance", "E-n22-k4"],
                    "console": "integratedTerminal"
                },
                {
                    "name": "Run Tests",
                    "type": "python",
                    "request": "launch",
                    "module": "pytest",
                    "args": ["-v"],
                    "console": "integratedTerminal"
                }
            ]
        }
        
        launch_path = vscode_dir / "launch.json"
        if not launch_path.exists():
            with open(launch_path, 'w') as f:
                json.dump(launch_config, f, indent=4)
            print("✅ VS Code launch configurations created")
        
        return True
    
    def run_initial_checks(self) -> bool:
        """Run initial quality checks."""
        print("\n🧪 Running initial checks...")
        
        if self.platform == "windows":
            python_cmd = self.venv_path / "Scripts" / "python"
        else:
            python_cmd = self.venv_path / "bin" / "python"
        
        # Check imports
        try:
            subprocess.run(
                [str(python_cmd), "-c", "import algorithms, problems, utils"],
                check=True,
                capture_output=True
            )
            print("✅ Package imports working")
        except subprocess.CalledProcessError:
            self.errors.append("Package imports failed")
            return False
        
        # Run quality doctor
        try:
            result = subprocess.run(
                [str(python_cmd), "scripts/cli/main.py", "quality", "doctor"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            print("✅ Quality tools check completed")
            if result.returncode != 0:
                self.warnings.append("Some quality tools may be missing")
        except Exception:
            self.warnings.append("Could not run quality doctor")
        
        return True
    
    def print_summary(self):
        """Print setup summary."""
        print("\n" + "="*60)
        print("🎉 BioAlgoCompare Development Environment Setup")
        print("="*60)
        
        if self.errors:
            print("\n❌ Errors:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if not self.errors:
            print("\n✅ Setup completed successfully!")
            print("\n📚 Next steps:")
            print("  1. Activate virtual environment:")
            if self.platform == "windows":
                print("     .\\venv\\Scripts\\activate")
            else:
                print("     source venv/bin/activate")
            print("  2. Run quality checks:")
            print("     bioalgo quality check")
            print("  3. Run an algorithm:")
            print("     bioalgo run --algorithm hoa --instance E-n22-k4")
            print("  4. View available commands:")
            print("     bioalgo --help")
            print("\n💡 For detailed documentation, see docs/")
    
    def setup(self) -> bool:
        """Run complete setup process."""
        print("🚀 Starting BioAlgoCompare development environment setup...")
        print(f"Platform: {self.platform}")
        print(f"Python: {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}")
        print(f"Project: {self.project_root}")
        
        steps = [
            ("System requirements", self.check_system_requirements),
            ("Virtual environment", self.create_virtual_environment),
            ("Dependencies", self.install_dependencies),
            ("Quality tools", self.install_quality_tools),
            ("Environment files", self.setup_environment_files),
            ("IDE configuration", self.configure_ide),
            ("Initial checks", self.run_initial_checks)
        ]
        
        for step_name, step_func in steps:
            if not step_func():
                print(f"\n❌ Setup failed at: {step_name}")
                self.print_summary()
                return False
        
        self.print_summary()
        return True


def main():
    """Main entry point."""
    setup = EnvironmentSetup()
    success = setup.setup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()