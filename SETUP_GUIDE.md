# OSRS PvP Reinforcement Learning - Complete Setup Guide

This guide will walk you through setting up the OSRS PvP Reinforcement Learning project from scratch, including all dependencies, environments, and tools needed for training AI agents.

## 📋 Overview

This project trains AI agents to play Old School RuneScape PvP using deep reinforcement learning. The system consists of:

1. **ML Training System** (`pvp-ml`) - Python-based training and model serving
2. **Game Simulation** (`simulation-rsps`) - Java-based RuneScape server simulation
3. **GUI Interface** - User-friendly interface for all operations

## 🔧 Prerequisites

Before starting, ensure you have:

- **Git** - For cloning the repository
- **Internet connection** - For downloading dependencies
- **~5GB free disk space** - For conda environment and models
- **8GB+ RAM recommended** - For training (4GB minimum)

### Operating System Support
- ✅ **Linux** (Ubuntu 18.04+, CentOS 7+, etc.)
- ✅ **macOS** (10.14+)
- ✅ **Windows** (10+)

### Hardware Requirements
- **CPU**: Any modern multi-core processor
- **GPU**: Optional (NVIDIA GPU with CUDA support for faster training)
- **RAM**: 8GB+ recommended, 4GB minimum
- **Storage**: 5GB+ free space

## 🚀 Quick Start (Automated Setup)

### Step 1: Install Conda

If you don't have conda installed:

**Option A: Miniconda (Recommended)**
```bash
# Linux/macOS
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Windows: Download and run from https://docs.conda.io/en/latest/miniconda.html
```

**Option B: Anaconda (Full Distribution)**
Download from: https://www.anaconda.com/products/distribution

### Step 2: Clone the Repository

```bash
git clone https://github.com/ConjureGanja/osrs-pvp-reinforcement-learning.git
cd osrs-pvp-reinforcement-learning
```

### Step 3: Run Automated Setup

```bash
# For systems with GPU support (recommended)
python setup.py

# For CPU-only systems
python setup.py --cpu-only

# To only check prerequisites
python setup.py --check-only
```

The setup script will:
- ✅ Check all prerequisites
- ✅ Create conda environment with all dependencies
- ✅ Install Java 17 (via conda)
- ✅ Install Python packages and CLI tools
- ✅ Validate the installation
- ✅ Create launcher scripts

### Step 4: Launch GUI Interface

After setup completes:

**Linux/macOS:**
```bash
./launch.sh gui
```

**Windows:**
```cmd
launch.bat gui
```

**Or start directly with Python:**
```bash
# Linux/macOS
source pvp-ml/env/bin/activate  # or: conda activate ./pvp-ml/env
python gui.py

# Windows
conda activate .\pvp-ml\env
python gui.py
```

---

## 🎯 Using the System

### GUI Interface

The GUI provides easy access to all functionality:

1. **Setup Tab** - Environment validation and configuration
2. **Training Tab** - Start and monitor training jobs
3. **Evaluation Tab** - Test trained models
4. **API Server Tab** - Serve models for external use
5. **Monitoring Tab** - View training progress with Tensorboard

### Command Line Interface

For advanced users, direct CLI access:

```bash
# Training
train --preset fast_nh_general        # Quick training
train --preset nh_general             # Full training
train --help                          # View all options

# Evaluation
eval --model-path models/GeneralizedNh # Test a model
eval --help                           # View all options

# API Server
serve-api                             # Start model serving API
serve-api --help                      # View all options

# Monitoring
train tensorboard                     # Open Tensorboard
```

---

## 📚 Detailed Workflow

### 1. Training Your First Model

**Option A: Using GUI**
1. Open GUI: `./launch.sh gui`
2. Go to "Training" tab
3. Select a preset (e.g., "fast_nh_general")
4. Click "Start Training"
5. Monitor progress in "Monitoring" tab

**Option B: Using CLI**
```bash
# Quick training session (for testing)
train --preset fast_nh_general

# Full training session
train --preset nh_general

# Distributed training (uses all CPU cores)
train --preset nh_general --distribute

# Custom training with specific parameters
train --preset nh_general --distribute 4 --id my_experiment
```

### 2. Monitoring Training Progress

**Tensorboard (Recommended)**
```bash
train tensorboard
# Opens browser at http://localhost:6006
```

**Command Line Monitoring**
```bash
train show  # View current experiments
```

**GUI Monitoring**
- Use the "Monitoring" tab in the GUI
- Real-time metrics and charts
- Training logs and status

### 3. Evaluating Trained Models

**Prerequisites for Evaluation:**
1. A trained model (in `pvp-ml/models/` directory)
2. Simulation server running

**Start Simulation Server:**

**Option A: GUI**
- Use "Simulation" tab to start/stop server

**Option B: CLI**
```bash
./launch.sh simulation
# or manually:
cd simulation-rsps/ElvargServer
./gradlew run
```

**Evaluate Model:**
```bash
eval --model-path models/GeneralizedNh
```

**Connect Game Client (Optional):**
```bash
# Clone upstream client
git clone https://github.com/RSPSApp/elvarg-rsps.git /tmp/elvarg-client
cd /tmp/elvarg-client/ElvargClient
./gradlew run
# Login and watch the AI play!
```

### 4. Serving Models via API

```bash
serve-api                    # Start on localhost:9999
serve-api --host 0.0.0.0     # Allow external connections
serve-api --port 8080        # Custom port
```

**API Usage Example:**
```python
import socket
import json

# Connect to API
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 9999))

# Send prediction request
request = {
    'model': 'GeneralizedNh',
    'observation': [/* observation data */],
    'action_masks': [/* action mask data */]
}
sock.send(json.dumps(request).encode())
response = json.loads(sock.recv(4096).decode())
print(f"Action: {response['action']}")
```

---

## 🔧 Advanced Configuration

### Training Presets

Available presets in `pvp-ml/config/`:
- `fast_nh_general` - Quick training for testing (1M steps)
- `nh_general` - Full training session (200M+ steps)
- `nh_general_distributed` - Multi-core distributed training
- Custom presets can be created by copying and modifying existing YAML files

### Environment Variables

```bash
# Custom paths
export PVP_ML_LOG_DIR="/path/to/logs"
export PVP_ML_MODEL_DIR="/path/to/models"

# Training parameters
export CUDA_VISIBLE_DEVICES="0"  # GPU selection
export OMP_NUM_THREADS="4"       # CPU threads for training
```

### GPU Configuration

**NVIDIA GPU Setup:**
```bash
# Check GPU availability
nvidia-smi

# Verify PyTorch can see GPU
python -c "import torch; print(torch.cuda.is_available())"

# For multiple GPUs, specify which to use
export CUDA_VISIBLE_DEVICES="0,1"
```

**AMD GPU (ROCm) Setup:**
```bash
# AMD GPUs require ROCm version of PyTorch
# Manually install: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.7
```

---

## 🐛 Troubleshooting

### Common Issues

**1. "Command 'conda' not found"**
```bash
# Add conda to PATH (adjust path as needed)
export PATH="/home/$USER/miniconda3/bin:$PATH"
# Or restart terminal after conda installation
```

**2. "Java version mismatch"**
```bash
# The conda environment includes Java 17
# Always use conda environment:
conda activate ./pvp-ml/env
java --version  # Should show Java 17
```

**3. "CUDA out of memory" during training**
```bash
# Reduce batch size or use CPU-only
python setup.py --cpu-only  # Reinstall for CPU
# Or modify config YAML files to reduce batch_size
```

**4. "Simulation server won't start"**
```bash
# Check Java version
java --version  # Must be Java 17

# Check port availability
netstat -tulpn | grep 43594  # Default RL port
netstat -tulpn | grep 43595  # Default game port

# Make gradlew executable
chmod +x simulation-rsps/ElvargServer/gradlew
```

**5. "Training stuck or very slow"**
```bash
# Check system resources
htop  # Monitor CPU/RAM usage

# Try distributed training
train --preset fast_nh_general --distribute

# Reduce environment complexity
# Modify config YAML: set parallel_envs to smaller number
```

### Getting Help

1. **Check logs**: Training logs are in `pvp-ml/logs/`
2. **GitHub Issues**: Report bugs at the project repository
3. **Discussions**: Join community discussions for help
4. **Debug mode**: Run with `-v` or `--verbose` flags for detailed output

### Performance Tuning

**For Training:**
```bash
# Use all CPU cores
train --preset nh_general --distribute

# Monitor training efficiency
train tensorboard  # Check samples_per_second metrics

# Optimize hyperparameters
# Edit config/*.yml files to tune:
# - learning_rate
# - batch_size
# - parallel_envs
# - rollout_fragment_length
```

**For Evaluation:**
```bash
# Faster evaluation with multiple agents
eval --model-path models/GeneralizedNh --num-agents 4

# Disable GUI for headless evaluation
eval --model-path models/GeneralizedNh --headless
```

---

## 🔄 Updating and Maintenance

### Update Repository
```bash
git pull origin master
python setup.py  # Re-run setup if needed
```

### Clean Installation
```bash
# Remove existing environment
conda env remove -n pvp
rm -rf pvp-ml/env

# Re-run setup
python setup.py
```

### Backup Important Data
```bash
# Backup trained models
cp -r pvp-ml/models/ ~/backup/models/

# Backup training configs
cp -r pvp-ml/config/ ~/backup/config/

# Backup logs
cp -r pvp-ml/logs/ ~/backup/logs/
```

---

## 🎓 Learning Resources

### Understanding the Code
- **Training Loop**: `pvp-ml/pvp_ml/train.py`
- **Environment Interface**: `pvp-ml/pvp_ml/env/pvp_env.py`
- **Model Architecture**: `pvp-ml/pvp_ml/ppo/policy.py`
- **Simulation Plugin**: `simulation-rsps/ElvargServer/src/main/java/com/github/naton1/rl/`

### Reinforcement Learning Resources
- [Stable Baselines3 Documentation](https://stable-baselines3.readthedocs.io/)
- [PPO Paper](https://arxiv.org/abs/1707.06347)
- [OpenAI Spinning Up](https://spinningup.openai.com/)

### OSRS Game Mechanics
- [OSRS Wiki](https://oldschool.runescape.wiki/)
- [Combat Formulas](https://oldschool.runescape.wiki/w/Combat_formula)
- [PvP Mechanics](https://oldschool.runescape.wiki/w/Player_versus_player)

---

## 🎯 Quick Reference

### Essential Commands
```bash
# Setup
python setup.py

# Launch GUI
./launch.sh gui

# Start training
train --preset fast_nh_general

# Monitor progress
train tensorboard

# Evaluate model
eval --model-path models/GeneralizedNh

# Serve API
serve-api

# Start simulation
./launch.sh simulation
```

### Key Directories
- `pvp-ml/models/` - Trained models
- `pvp-ml/logs/` - Training logs
- `pvp-ml/config/` - Training configurations
- `simulation-rsps/ElvargServer/` - Java simulation server

### Useful Files
- `launch.sh` / `launch.bat` - Quick launcher
- `setup.py` - Automated setup script
- `gui.py` - GUI application
- `SETUP_GUIDE.md` - This guide

---

**🎉 You're ready to train OSRS PvP AI agents! Start with the GUI for the easiest experience, or use the CLI for advanced control.**