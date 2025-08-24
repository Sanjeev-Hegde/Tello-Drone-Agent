#!/usr/bin/env python3
"""
Setup script for Tello Drone AI Agent project.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")


def create_virtual_environment():
    """Create virtual environment if it doesn't exist."""
    venv_path = Path("venv")
    if venv_path.exists():
        print("✓ Virtual environment already exists")
        return
    
    print("Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
    print("✓ Virtual environment created")


def get_venv_python():
    """Get path to Python executable in virtual environment."""
    if os.name == 'nt':  # Windows
        return Path("venv") / "Scripts" / "python.exe"
    else:  # Unix/Linux/macOS
        return Path("venv") / "bin" / "python"


def install_requirements():
    """Install required packages."""
    venv_python = get_venv_python()
    
    print("Installing requirements...")
    subprocess.run([
        str(venv_python), "-m", "pip", "install", "--upgrade", "pip"
    ], check=True)
    
    subprocess.run([
        str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"
    ], check=True)
    
    print("✓ Requirements installed")


def setup_environment_file():
    """Set up environment file from template."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✓ .env file already exists")
        return
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✓ .env file created from template")
        print("⚠  Please edit .env file with your Azure credentials")
    else:
        print("✗ .env.example file not found")


def check_azure_credentials():
    """Check if Azure credentials are configured."""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠  .env file not found - Azure services won't work")
        return
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_AI_VISION_ENDPOINT"
    ]
    
    missing_vars = []
    for var in required_vars:
        if f"{var}=your_" in content or f"{var}=" not in content:
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠  The following environment variables need to be configured:")
        for var in missing_vars:
            print(f"    - {var}")
        print("   Edit .env file with your actual Azure credentials")
    else:
        print("✓ Azure credentials appear to be configured")


def create_run_scripts():
    """Create convenient run scripts."""
    # Unix/Linux/macOS script
    if os.name != 'nt':
        run_script = Path("run.sh")
        with open(run_script, 'w') as f:
            f.write("""#!/bin/bash
# Activate virtual environment and run the application

source venv/bin/activate
python src/main.py "$@"
""")
        run_script.chmod(0o755)
        print("✓ run.sh script created")
    
    # Windows script
    run_script_win = Path("run.bat")
    with open(run_script_win, 'w') as f:
        f.write("""@echo off
REM Activate virtual environment and run the application

call venv\\Scripts\\activate.bat
python src\\main.py %*
""")
    print("✓ run.bat script created")


def run_basic_tests():
    """Run basic tests to verify setup."""
    venv_python = get_venv_python()
    
    print("Running basic tests...")
    try:
        subprocess.run([
            str(venv_python), "tests/test_basic.py"
        ], check=True, cwd=".")
        print("✓ Basic tests passed")
    except subprocess.CalledProcessError:
        print("⚠  Some tests failed - check dependencies")


def main():
    """Main setup function."""
    print("Tello Drone AI Agent Setup")
    print("=" * 40)
    
    try:
        check_python_version()
        create_virtual_environment()
        install_requirements()
        setup_environment_file()
        check_azure_credentials()
        create_run_scripts()
        
        print("\n" + "=" * 40)
        print("Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file with your Azure credentials")
        print("2. Run the application:")
        if os.name == 'nt':
            print("   - Windows: run.bat")
            print("   - Or: venv\\Scripts\\activate && python src\\main.py")
        else:
            print("   - Unix/Linux/macOS: ./run.sh")
            print("   - Or: source venv/bin/activate && python src/main.py")
        print("3. For vision-only mode: add --vision-only flag")
        print("4. For help: add --help flag")
        
    except subprocess.CalledProcessError as e:
        print(f"Setup failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
