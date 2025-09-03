#!/bin/bash
# OSRS PvP RL - Quick Launcher

export PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export CONDA_ENV_PATH="$PROJECT_ROOT/pvp-ml/env"

echo "🗡️ OSRS PvP Reinforcement Learning - Launcher"
echo "=============================================="
echo ""
echo "Available commands:"
echo "  1. setup         - Run automated setup"
echo "  2. gui           - Launch web GUI interface"  
echo "  3. train         - Start training (requires preset)"
echo "  4. eval          - Evaluate model"
echo "  5. serve-api     - Serve models via API"
echo "  6. tensorboard   - View training progress"
echo "  7. simulation    - Start simulation server"
echo ""

if [ "$1" = "setup" ]; then
    echo "Running automated setup..."
    python "$PROJECT_ROOT/setup.py" "${@:2}"
elif [ "$1" = "gui" ]; then
    echo "Launching web GUI..."
    python "$PROJECT_ROOT/web_gui.py" "${@:2}"
elif [ "$1" = "train" ]; then
    echo "Starting training..."
    if [ -d "$CONDA_ENV_PATH" ]; then
        conda run -p "$CONDA_ENV_PATH" train "${@:2}"
    else
        echo "❌ Conda environment not found. Run './launch.sh setup' first."
    fi
elif [ "$1" = "eval" ]; then
    echo "Starting evaluation..."
    if [ -d "$CONDA_ENV_PATH" ]; then
        conda run -p "$CONDA_ENV_PATH" eval "${@:2}"
    else
        echo "❌ Conda environment not found. Run './launch.sh setup' first."
    fi
elif [ "$1" = "serve-api" ]; then
    echo "Starting API server..."
    if [ -d "$CONDA_ENV_PATH" ]; then
        conda run -p "$CONDA_ENV_PATH" serve-api "${@:2}"
    else
        echo "❌ Conda environment not found. Run './launch.sh setup' first."
    fi
elif [ "$1" = "tensorboard" ]; then
    echo "Starting Tensorboard..."
    if [ -d "$CONDA_ENV_PATH" ]; then
        conda run -p "$CONDA_ENV_PATH" train tensorboard
    else
        echo "❌ Conda environment not found. Run './launch.sh setup' first."
    fi
elif [ "$1" = "simulation" ]; then
    echo "Starting simulation server..."
    cd "$PROJECT_ROOT/simulation-rsps/ElvargServer"
    if [ -f "gradlew" ]; then
        chmod +x gradlew
        ./gradlew run
    else
        echo "❌ Gradle wrapper not found in simulation directory."
    fi
else
    echo "Usage: ./launch.sh <command> [arguments...]"
    echo ""
    echo "Quick Start:"
    echo "  ./launch.sh setup     # First-time setup"
    echo "  ./launch.sh gui       # Launch web interface"
    echo ""
    echo "See SETUP_GUIDE.md for detailed instructions."
fi