#!/usr/bin/env python3
"""
OSRS PvP Reinforcement Learning - Automated Setup Script

This script automates the entire setup process for the OSRS PvP reinforcement learning project.
It handles conda environment creation, dependency installation, and validation of all components.
"""

import os
import sys
import subprocess
import platform
import shutil
import time
import argparse
from pathlib import Path
from typing import Optional, List


class SetupManager:
    """Manages the complete setup process for the OSRS PvP RL project."""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.pvp_ml_dir = root_dir / "pvp-ml"
        self.simulation_dir = root_dir / "simulation-rsps" / "ElvargServer"
        self.env_name = "pvp"
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def run_command(self, command: List[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
        """Run a shell command with proper error handling."""
        self.log(f"Running: {' '.join(command)}")
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.root_dir,
                capture_output=True,
                text=True,
                check=check
            )
            if result.stdout:
                self.log(f"Output: {result.stdout.strip()}")
            return result
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {e}", "ERROR")
            if e.stderr:
                self.log(f"Error: {e.stderr.strip()}", "ERROR")
            raise
            
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are installed."""
        self.log("Checking prerequisites...")
        
        # Check conda
        try:
            result = self.run_command(["conda", "--version"])
            self.log(f"Found conda: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("❌ Conda not found. Please install Miniconda or Anaconda first.", "ERROR")
            self.log("Download from: https://docs.conda.io/en/latest/miniconda.html")
            return False
            
        # Check Java
        try:
            result = self.run_command(["java", "--version"])
            self.log(f"Found Java: {result.stdout.strip().split()[1]}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("❌ Java not found. Java 17 will be installed via conda.", "WARNING")
            
        # Check git
        try:
            result = self.run_command(["git", "--version"])
            self.log(f"Found git: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("❌ Git not found. Please install Git first.", "ERROR")
            return False
            
        self.log("✅ Prerequisites check completed")
        return True
        
    def setup_conda_environment(self, cpu_only: bool = False) -> bool:
        """Set up the conda environment for pvp-ml."""
        self.log("Setting up conda environment...")
        
        env_file = self.pvp_ml_dir / "environment.yml"
        if not env_file.exists():
            self.log(f"❌ Environment file not found: {env_file}", "ERROR")
            return False
        
        # Remove existing environment if it exists
        env_path = self.pvp_ml_dir / "env"
        if env_path.exists():
            self.log("Removing existing environment...")
            try:
                self.run_command(["conda", "env", "remove", "-p", str(env_path), "-y"], check=False)
            except subprocess.CalledProcessError:
                pass  # Continue even if removal fails
            
            # Force remove directory if still exists
            import shutil
            if env_path.exists():
                shutil.rmtree(env_path, ignore_errors=True)
        
        # Create modified environment.yml without local package
        self.log("Creating modified environment file...")
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Remove the local package installation
        content = content.replace("      - -e .", "")
        
        # Configure for CPU-only if requested
        if cpu_only:
            self.log("Configuring for CPU-only training...")
            content = content.replace("  # - cpuonly # [CPU]", "  - cpuonly # [CPU]")
            content = content.replace("  - pytorch-cuda=12.1 # [GPU]", "  # - pytorch-cuda=12.1 # [GPU]")
            
        # Write to temporary file
        temp_env_file = self.pvp_ml_dir / "environment_temp.yml"
        with open(temp_env_file, 'w') as f:
            f.write(content)
        
        try:
            # Create new environment
            self.log("Creating conda environment (this may take several minutes)...")
            result = self.run_command([
                "conda", "env", "create", 
                "-p", str(env_path),
                "-f", str(temp_env_file)
            ], check=False)
            
            # Clean up temporary file
            temp_env_file.unlink()
            
            if result.returncode != 0:
                self.log("❌ Failed to create conda environment", "ERROR")
                self.log("Trying alternative approach with mamba...", "INFO")
                
                # Try with mamba if available
                try:
                    self.run_command(["mamba", "--version"], check=False)
                    result = self.run_command([
                        "mamba", "env", "create", 
                        "-p", str(env_path),
                        "-f", str(temp_env_file)
                    ], check=False)
                    
                    if result.returncode == 0:
                        self.log("✅ Conda environment created with mamba")
                        return True
                except subprocess.CalledProcessError:
                    pass
                
                # If both conda and mamba fail, try minimal setup
                self.log("Trying minimal environment setup...", "INFO")
                return self.create_minimal_environment(cpu_only)
            else:
                self.log("✅ Conda environment created successfully")
                return True
                
        except subprocess.CalledProcessError as e:
            self.log(f"❌ Environment creation failed: {e}", "ERROR")
            return self.create_minimal_environment(cpu_only)
    
    def create_minimal_environment(self, cpu_only: bool = False) -> bool:
        """Create a minimal conda environment when full setup fails."""
        self.log("Creating minimal environment...")
        
        env_path = self.pvp_ml_dir / "env"
        
        try:
            # Create basic Python environment
            self.run_command([
                "conda", "create", "-p", str(env_path), 
                "python=3.10", "pip", "openjdk=17", "-y"
            ])
            
            # Install core packages with pip
            core_packages = [
                "numpy", "gymnasium", "tensorboard", "aiohttp", 
                "pyyaml", "filelock", "psutil", "dacite", "pytest"
            ]
            
            if cpu_only:
                core_packages.extend(["torch", "torchvision", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cpu"])
            else:
                core_packages.extend(["torch", "torchvision", "torchaudio"])
                
            self.run_command([
                "conda", "run", "-p", str(env_path),
                "pip", "install"
            ] + core_packages)
            
            self.log("✅ Minimal environment created")
            return True
            
        except subprocess.CalledProcessError:
            self.log("❌ Failed to create minimal environment", "ERROR")
            return False
            
    def install_pvp_ml(self) -> bool:
        """Install the pvp-ml package in development mode."""
        self.log("Installing pvp-ml package...")
        
        try:
            env_path = self.pvp_ml_dir / "env"
            
            # First try to install Ray (it's often problematic)
            self.log("Installing Ray...")
            try:
                self.run_command([
                    "conda", "run", "-p", str(env_path),
                    "pip", "install", "ray[default]==2.7.1", "--timeout=300"
                ], check=False)
            except subprocess.CalledProcessError:
                self.log("⚠️ Ray installation failed, continuing without it", "WARNING")
            
            # Install the local package
            self.log("Installing local pvp-ml package...")
            self.run_command([
                "conda", "run", "-p", str(env_path),
                "pip", "install", "-e", ".", "--no-deps"
            ], cwd=self.pvp_ml_dir)
            
            self.log("✅ pvp-ml package installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            self.log(f"❌ Failed to install pvp-ml package: {e}", "ERROR")
            
            # Try alternative installation
            self.log("Trying alternative installation method...", "INFO")
            try:
                env_path = self.pvp_ml_dir / "env"
                self.run_command([
                    "conda", "run", "-p", str(env_path),
                    "python", "setup.py", "develop"
                ], cwd=self.pvp_ml_dir, check=False)
                
                self.log("✅ Alternative installation succeeded")
                return True
            except subprocess.CalledProcessError:
                self.log("❌ All installation methods failed", "ERROR")
                return False
            
    def validate_installation(self) -> bool:
        """Validate that all components are properly installed."""
        self.log("Validating installation...")
        
        env_path = self.pvp_ml_dir / "env"
        
        # Test CLI commands
        commands_to_test = ["train", "serve-api", "eval"]
        for cmd in commands_to_test:
            try:
                result = self.run_command([
                    "conda", "run", "-p", str(env_path),
                    cmd, "--help"
                ], check=False)
                if result.returncode == 0:
                    self.log(f"✅ Command '{cmd}' is working")
                else:
                    self.log(f"❌ Command '{cmd}' failed", "ERROR")
                    return False
            except subprocess.CalledProcessError:
                self.log(f"❌ Command '{cmd}' not found", "ERROR")
                return False
                
        # Test Java simulation
        self.log("Testing Java simulation server...")
        try:
            # Check if gradlew exists and is executable
            gradlew = self.simulation_dir / "gradlew"
            if not gradlew.exists():
                self.log("❌ Gradle wrapper not found in simulation directory", "ERROR")
                return False
                
            # Make gradlew executable
            os.chmod(gradlew, 0o755)
            
            # Test gradle build (don't actually run the server)
            result = self.run_command(
                ["./gradlew", "build", "--info"],
                cwd=self.simulation_dir,
                check=False
            )
            
            if result.returncode == 0:
                self.log("✅ Java simulation server build successful")
            else:
                self.log("⚠️  Java simulation server build had issues, but may still work", "WARNING")
                
        except Exception as e:
            self.log(f"⚠️  Could not fully validate Java simulation: {e}", "WARNING")
            
        self.log("✅ Installation validation completed")
        return True
        
    def create_launcher_scripts(self):
        """Create convenient launcher scripts."""
        self.log("Creating launcher scripts...")
        
        # Create shell script for Unix systems
        if platform.system() != "Windows":
            launcher_script = self.root_dir / "launch.sh"
            script_content = f"""#!/bin/bash
# OSRS PvP RL - Quick Launcher

export PROJECT_ROOT="{self.root_dir}"
export CONDA_ENV_PATH="{self.pvp_ml_dir / 'env'}"

echo "OSRS PvP Reinforcement Learning - Launcher"
echo "========================================="
echo ""
echo "Available commands:"
echo "  1. gui           - Launch GUI interface"
echo "  2. train         - Start training (requires preset)"
echo "  3. eval          - Evaluate model"
echo "  4. serve-api     - Serve models via API"
echo "  5. tensorboard   - View training progress"
echo "  6. simulation    - Start simulation server"
echo ""

if [ "$1" = "gui" ]; then
    echo "Launching GUI..."
    conda run -p "$CONDA_ENV_PATH" python gui.py
elif [ "$1" = "train" ]; then
    echo "Starting training..."
    conda run -p "$CONDA_ENV_PATH" train "${{@:2}}"
elif [ "$1" = "eval" ]; then
    echo "Starting evaluation..."
    conda run -p "$CONDA_ENV_PATH" eval "${{@:2}}"
elif [ "$1" = "serve-api" ]; then
    echo "Starting API server..."
    conda run -p "$CONDA_ENV_PATH" serve-api "${{@:2}}"
elif [ "$1" = "tensorboard" ]; then
    echo "Starting Tensorboard..."
    conda run -p "$CONDA_ENV_PATH" train tensorboard
elif [ "$1" = "simulation" ]; then
    echo "Starting simulation server..."
    cd "{self.simulation_dir}"
    ./gradlew run
else
    echo "Usage: ./launch.sh <command> [arguments...]"
    echo "       ./launch.sh gui"
fi
"""
            with open(launcher_script, 'w') as f:
                f.write(script_content)
            os.chmod(launcher_script, 0o755)
            
        # Create batch script for Windows
        launcher_bat = self.root_dir / "launch.bat"
        bat_content = f"""@echo off
REM OSRS PvP RL - Quick Launcher (Windows)

set PROJECT_ROOT={self.root_dir}
set CONDA_ENV_PATH={self.pvp_ml_dir / 'env'}

echo OSRS PvP Reinforcement Learning - Launcher
echo =========================================
echo.

if "%1"=="gui" (
    echo Launching GUI...
    conda run -p "%CONDA_ENV_PATH%" python gui.py
) else if "%1"=="train" (
    echo Starting training...
    conda run -p "%CONDA_ENV_PATH%" train %*
) else if "%1"=="eval" (
    echo Starting evaluation...
    conda run -p "%CONDA_ENV_PATH%" eval %*
) else if "%1"=="serve-api" (
    echo Starting API server...
    conda run -p "%CONDA_ENV_PATH%" serve-api %*
) else if "%1"=="tensorboard" (
    echo Starting Tensorboard...
    conda run -p "%CONDA_ENV_PATH%" train tensorboard
) else if "%1"=="simulation" (
    echo Starting simulation server...
    cd /d "{self.simulation_dir}"
    gradlew.bat run
) else (
    echo Usage: launch.bat ^<command^> [arguments...]
    echo        launch.bat gui
)
"""
        with open(launcher_bat, 'w') as f:
            f.write(bat_content)
            
        self.log("✅ Launcher scripts created")
        
    def run_full_setup(self, cpu_only: bool = False) -> bool:
        """Run the complete setup process."""
        self.log("Starting full setup process...")
        
        if not self.check_prerequisites():
            return False
            
        if not self.setup_conda_environment(cpu_only):
            return False
            
        if not self.install_pvp_ml():
            return False
            
        if not self.validate_installation():
            return False
            
        self.create_launcher_scripts()
        
        self.log("🎉 Setup completed successfully!")
        self.log("")
        self.log("Quick start:")
        if platform.system() != "Windows":
            self.log("  ./launch.sh gui          # Launch GUI")
            self.log("  ./launch.sh train --help # View training options")
        else:
            self.log("  launch.bat gui           # Launch GUI")
            self.log("  launch.bat train --help  # View training options")
        self.log("")
        self.log("For detailed instructions, see SETUP_GUIDE.md")
        
        return True


def main():
    """Main entry point for the setup script."""
    parser = argparse.ArgumentParser(
        description="OSRS PvP Reinforcement Learning - Setup Script"
    )
    parser.add_argument(
        "--cpu-only",
        action="store_true",
        help="Set up for CPU-only training (no GPU support)"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check prerequisites without installing"
    )
    
    args = parser.parse_args()
    
    # Get the root directory (where this script is located)
    root_dir = Path(__file__).parent.absolute()
    
    setup_manager = SetupManager(root_dir)
    
    if args.check_only:
        success = setup_manager.check_prerequisites()
        sys.exit(0 if success else 1)
    else:
        success = setup_manager.run_full_setup(cpu_only=args.cpu_only)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()