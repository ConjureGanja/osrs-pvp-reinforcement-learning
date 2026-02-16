# OSRS PvP Reinforcement Learning — Complete Setup & Run Walkthrough

This document captures every step taken to successfully set up and run this project from scratch on Windows 11 + WSL2 with an NVIDIA RTX 4060 (8GB). It is structured as a course outline for an AI LLM to expand into a full tutorial.

---

## Part 1: Understanding the Project

### 1.1 What This Project Does
- Trains AI agents to play Old School RuneScape PvP (NH bridding — No Honor combat) using reinforcement learning
- Uses PPO (Proximal Policy Optimization) with self-play to improve through fighting copies of itself
- The AI learns to switch prayers, swap gear, eat food, and time KO combos — all core OSRS PvP mechanics

### 1.2 Architecture Overview
```
┌─────────────────────┐     TCP Socket      ┌──────────────────────┐
│   Python ML System  │◄───────────────────►│   Java Game Server   │
│   (PyTorch + PPO)   │   Port 7070 (RL)    │   (Elvarg RSPS)      │
│                     │   Port 43595 (Game)  │                      │
│   pvp-ml/           │                      │  simulation-rsps/    │
└─────────────────────┘                      └──────────────────────┘
        │                                              │
        ▼                                              ▼
   TensorBoard                                   Game Client
   Port 6006                                    Port 43595
   (metrics)                                 (visual observation)
```

### 1.3 Key Components
| Component | Directory | Language | Purpose |
|-----------|-----------|----------|---------|
| ML Training Pipeline | `pvp-ml/` | Python | PPO training, self-play, model management |
| Game Simulation Server | `simulation-rsps/ElvargServer/` | Java | Simulates OSRS combat mechanics |
| Environment Contracts | `contracts/environments/` | JSON | Define observation/action spaces |
| Model Serving API | `pvp-ml/pvp_ml/api.py` | Python | Serves trained models for inference |
| Game Client | External (ElvargClient) | Java | Visual client to watch/play fights |

### 1.4 Port Map
| Port | Service | Purpose |
|------|---------|---------|
| 7070 | Remote Environment API | Python↔Java training communication |
| 43595 | Game Server | Game client connections |
| 9999 | Model Serving API | Inference for eval bots |
| 6006 | TensorBoard | Training metrics dashboard |

---

## Part 2: Prerequisites & Environment Setup

### 2.1 System Requirements
- **OS**: Windows 11 with WSL2 (Ubuntu)
- **GPU**: NVIDIA GPU with CUDA support (tested: RTX 4060 8GB)
- **RAM**: 16GB+ recommended
- **Disk**: ~10GB free space
- **Software**: Git, WSL2 with Ubuntu

### 2.2 Install Miniconda in WSL2
```bash
# Download and install Miniconda (if not already installed)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Initialize conda for your shell
~/miniconda3/bin/conda init bash
source ~/.bashrc

# Verify
conda --version
```

### 2.3 Accept Conda Terms of Service
This step is required before creating environments with default channels:
```bash
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
```

### 2.4 Clone the Repository
```bash
cd /mnt/c/Users/YOUR_USERNAME
git clone https://github.com/YOUR_REPO/osrs-pvp-reinforcement-learning.git
cd osrs-pvp-reinforcement-learning
```

---

## Part 3: Creating the Conda Environment

### 3.1 Create the Environment
The `environment.yml` installs Python 3.10, Java 17 (OpenJDK), PyTorch 2.1.2 with CUDA 12.1, and all dependencies.
```bash
conda env create -p ./pvp-ml/env -f pvp-ml/environment.yml
```

**Note**: This takes 15-30 minutes on WSL2 due to Windows filesystem overhead. The environment includes Java 17 via conda, so no separate Java installation is needed for the server.

### 3.2 Activate the Environment
```bash
conda activate ./pvp-ml/env
```

### 3.3 Install the Python Package in Editable Mode
```bash
pip install -e pvp-ml/
```

### 3.4 Fix setuptools Compatibility
Ray 2.7.1 requires `pkg_resources` which was removed in setuptools 82+:
```bash
pip install "setuptools<81"
```

### 3.5 Verify the Installation
```bash
# Python
python --version  # Should be 3.10.x

# Java (from conda)
java -version  # Should be openjdk 17.x

# PyTorch with CUDA
python -c "import torch; print(f'PyTorch {torch.__version__}, CUDA available: {torch.cuda.is_available()}')"

# Training CLI registered
which train  # Should point to the conda env
```

---

## Part 4: Fixing WSL2-Specific Issues

### 4.1 Fix Gradle Wrapper Permissions
The `gradlew` script needs execute permission:
```bash
chmod +x simulation-rsps/ElvargServer/gradlew
```

### 4.2 Fix CRLF Line Endings
Files cloned on Windows have `\r\n` line endings which break shell scripts in WSL:
```bash
cd simulation-rsps/ElvargServer
tr -d '\r' < gradlew > /tmp/gradlew_fixed && cp /tmp/gradlew_fixed gradlew
chmod +x gradlew
```

### 4.3 Fix Java Source File Formatting
The Java source files may also have CRLF issues. Fix with Spotless:
```bash
cd simulation-rsps/ElvargServer
./gradlew spotlessApply --no-daemon
```

### 4.4 Build the Java Server
Verify everything compiles:
```bash
cd simulation-rsps/ElvargServer
./gradlew build --no-daemon
```
Expected: `BUILD SUCCESSFUL`

---

## Part 5: Running Training

### 5.1 Understanding Training Presets
Training configs are in `pvp-ml/config/nh/`:

| Preset | Network Size | Envs | Batch Size | Use Case |
|--------|-------------|------|------------|----------|
| `test.yml` | 64 units, 1 layer | 10 | 64 | Quick validation (~20 FPS) |
| `baseline.yml` | 512 units, 2 layers | 100 | 2048 | Full training |
| `core.yml` | 512 units, 2 layers | 100 | 2048 | Production base config |
| `pure-self-play.yml` | 512 units | 100 | 2048 | Self-play only |
| `human-like.yml` | 512 units | 100 | 2048 | Human-like behavior |

### 5.2 Start a Test Training Run
```bash
conda activate ./pvp-ml/env
cd pvp-ml

# Clean any previous experiments and start training
python -m pvp_ml.run_train_job cleanup --name all
python -m pvp_ml.run_train_job train --preset Test --id 0 --wait --log
```

**What this does:**
1. Cleans up previous experiment data
2. Starts the Java RSPS server (takes ~75 seconds to load)
3. Launches the PPO training script
4. Starts TensorBoard on port 6006

### 5.3 Known Issue: Orchestrator Crash
The `run_train_job.py` orchestrator may crash with a `queue.Empty` exception in `propagate_logs()`. This is a race condition bug — **the training and RSPS processes continue running independently**. You can safely ignore this crash.

### 5.4 Monitor Training
- **TensorBoard**: Open http://localhost:6006 in your browser
- **Training logs**: `pvp-ml/logs/0-train.log`
- **RSPS logs**: `pvp-ml/logs/0-rsps.log`
- **Model checkpoints**: `pvp-ml/experiments/Test/models/`

### 5.5 Training Metrics to Watch
- **FPS**: Environment steps per second (~17-22 for Test preset)
- **Elo Rating**: Relative skill level against reference agents
- **Win Rate**: Against baseline scripted bots
- **Reward**: Composite reward signal (damage, prayers, food management)
- **Policy Loss / Value Loss**: PPO optimization metrics

### 5.6 Model Checkpoints
Models are saved automatically every rollout to:
```
pvp-ml/experiments/Test/models/main-XXXXX-steps.zip
```

To save the latest model permanently:
```bash
cp pvp-ml/experiments/Test/models/$(ls pvp-ml/experiments/Test/models/ | sort -t- -k2 -n | tail -1) pvp-ml/models/MyTrainedNh.zip
```

---

## Part 6: Watching Fights in the Game Client

### 6.1 Clone the Elvarg Client
The game client is a separate repository:
```bash
# On Windows or from WSL
git clone https://github.com/RSPSApp/elvarg-rsps.git /mnt/c/Users/YOUR_USERNAME/elvarg-client
```

### 6.2 Fix Java 21 Compatibility
The client has an unused import that fails on Java 15+. Remove it:

**File**: `ElvargClient/src/main/java/com/runescape/graphics/Slider.java`
**Remove this line**:
```java
import jdk.nashorn.internal.runtime.regexp.joni.Config;
```

### 6.3 Disable Discord OAuth
For local play, disable the Discord login requirement:

**File**: `ElvargClient/src/main/java/com/runescape/Configuration.java`
**Change**:
```java
public static final boolean ENABLE_DISCORD_OAUTH_LOGIN = false;  // was true
```

### 6.4 Configure Server Address for WSL2
The RSPS runs inside WSL2, which has a different IP than `localhost` from Windows' perspective.

**Find WSL2 IP** (run in WSL):
```bash
hostname -I | awk '{print $1}'
```

**Update** `ElvargClient/src/main/java/com/runescape/Configuration.java`:
```java
public static String SERVER_ADDRESS = PRODUCTION_MODE ? "" : "YOUR_WSL2_IP";
// Example: "172.26.95.115"
```

**Note**: The WSL2 IP changes on reboot. Update this value each time.

### 6.5 Build and Run the Client
Create a batch file `C:\Users\YOUR_USERNAME\elvarg-client\run-client.bat`:
```batch
@echo off
cd /d "%~dp0ElvargClient"
echo Building and launching Elvarg Game Client...
call gradlew.bat run
pause
```

Double-click to launch. Log in with any username/password.

### 6.6 Where to Find the Bots
The AI bots fight in the **Wilderness** near coordinates (3093, 3529) — north of Edgeville past the wilderness ditch. During training, you'll see `RemoteEnvironmentPlayerBot` instances fighting each other.

---

## Part 7: Playing Against the AI

### 7.1 Architecture for Eval Mode
```
Game Client (you) ──► RSPS Server (port 43595)
                           │
                     Agent Bots ──► API Server (port 9999)
                                         │
                                    Trained Models
                                    (GeneralizedNh, FineTunedNh, etc.)
```

### 7.2 Start the Model Serving API
```bash
conda activate ./pvp-ml/env
cd pvp-ml
serve-api --device cpu
```
This loads all `.zip` models from `pvp-ml/models/` and serves them on port 9999.

### 7.3 Start the RSPS in Eval Mode
In a separate terminal:
```bash
conda activate ./pvp-ml/env
cd simulation-rsps/ElvargServer

TRAIN=false \
RUN_EVAL_BOTS=true \
SYNC_TRAINING=false \
SHOW_ENV_DEBUGGER=false \
PREDICTION_API_HOST=localhost \
PREDICTION_API_PORT=9999 \
GRADLE_OPTS="-XX:MaxMetaspaceSize=256m -XX:+HeapDumpOnOutOfMemoryError -Xmx512m" \
./gradlew run --no-daemon
```

### 7.4 Environment Variables Reference
| Variable | Default | Purpose |
|----------|---------|---------|
| `TRAIN` | `true` | Enable training mode (RemoteEnvironmentServer) |
| `RUN_EVAL_BOTS` | `true` | Spawn AI agent bots and scripted baselines |
| `SYNC_TRAINING` | `true` | Sync game ticks with trainer (set false for real-time) |
| `SHOW_ENV_DEBUGGER` | `true` | Show environment debugger window |
| `PREDICTION_API_HOST` | `localhost` | API server hostname |
| `PREDICTION_API_PORT` | `9999` | API server port |
| `TICK_RATE` | `600` | Game tick rate in ms (1 for max speed training) |
| `GAME_PORT` | `43595` | Port for game client connections |
| `REMOTE_ENV_PORT` | `7070` | Port for Python training environment |

### 7.5 Bots Spawned in Eval Mode
**AI Agent Bots** (use the GeneralizedNh model via API):
- `NhAgentPure` — Pure build
- `NhAgentZerk` — Zerker build
- `NhAgentMed` — Med level build

**Scripted Baseline Bots** (hardcoded behavior, no model):
- `BaselinePure`, `BaselineZerk`, `BaselineMed`, `BaselineMax`

### 7.6 Connect and Fight
1. Launch the game client (Section 6.5)
2. Log in with any username/password
3. Walk north to the Wilderness
4. Attack any `NhAgent*` bot to fight the AI

### 7.7 In-Game Commands
You can also attach AI control to any player with:
```
::enableagent env=nh model=GeneralizedNh stackFrames=1 deterministic=false
::disableagent
```

---

## Part 8: Model Comparison & Training at Scale

### 8.1 Pre-trained Models
| Model | Parameters | Training Steps | Elo Rating | Network |
|-------|-----------|---------------|------------|---------|
| `FineTunedNh.zip` | 1,774,985 | 238,080,000 | ~1620 | 512 units, 2 layers |
| `GeneralizedNh.zip` | 1,774,985 | 161,792,000 | ~1590 | 512 units, 2 layers |
| Test preset model | 128,393 | ~270,000 | ~713 | 64 units, 1 layer |

### 8.2 Training a Competitive Model
The Test preset is for validation only. For a real model:
```bash
python -m pvp_ml.run_train_job train --preset Baseline --id 0 --wait --log
```

This uses:
- 512-unit networks (2 layers) — 14x more parameters
- 100 environments (vs 10)
- 2048 batch size (vs 64)
- Requires days/weeks of training to reach pre-trained model quality

### 8.3 Training Strategies
| Config | Strategy | Description |
|--------|----------|-------------|
| `baseline.yml` | Standard PPO | Trains against scripted baselines |
| `pure-self-play.yml` | Self-play | Fights copies of itself |
| `prioritized-past-self-play.yml` | Prioritized self-play | Fights past versions weighted by difficulty |
| `human-like.yml` | Human approximation | Trained to mimic human play patterns |
| `human-like-adversarial.yml` | Adversarial | Exploits human-like opponents |

---

## Part 9: Troubleshooting Reference

### Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `'/usr/bin/env: sh\r'` | CRLF line endings in gradlew | `tr -d '\r' < gradlew > /tmp/fix && cp /tmp/fix gradlew` |
| `gradlew: Permission denied` | Not executable | `chmod +x gradlew` |
| `No module named 'pkg_resources'` | setuptools 82+ removed it | `pip install "setuptools<81"` |
| `Port XXXXX already taken` | Orphaned process | `lsof -ti :PORT \| xargs -r kill -9` |
| `spotlessJavaCheck FAILED` | Java files have CRLF | `./gradlew spotlessApply --no-daemon` |
| `Error connecting to server` (client) | WSL2 networking | Use WSL2 IP instead of localhost in Configuration.java |
| `queue.Empty` crash in orchestrator | Race condition in log propagation | Harmless — training continues running |
| `CANT_ATTACK_IN_AREA` | Game simulation edge case | Restart training — intermittent bug |
| `JAVA_HOME not set` | Env vars override PATH | Activate conda env before running gradlew |
| `jdk.nashorn` import error (client) | Java 15+ removed Nashorn | Remove unused import from Slider.java |

### Useful Diagnostic Commands
```bash
# Check what's running on each port
lsof -ti :43595  # RSPS game server
lsof -ti :7070   # RL training API
lsof -ti :9999   # Model serving API
lsof -ti :6006   # TensorBoard

# Kill all project processes
lsof -ti :43595 -ti :7070 -ti :9999 -ti :6006 | sort -u | xargs -r kill

# Check training progress
tail -20 pvp-ml/logs/0-train.log

# List saved model checkpoints
ls -lht pvp-ml/experiments/Test/models/ | head -10

# Get WSL2 IP (for game client Configuration.java)
hostname -I | awk '{print $1}'
```

---

## Part 10: About RuneLite Export

Per the project README:

> A third component for evaluating the models in the **live game** as a third-party client plugin was developed but is **not publicly available** to prevent affecting the real game.

The RuneLite plugin was intentionally withheld from the repository. It used the same `serve-api` TCP protocol (JSON over port 9999) to drive actions in real OSRS. The observation/action encoding would need to be replicated from the Java `NhEnvironmentDescriptor` class. This is not included for ethical reasons.

---

## Appendix: Quick Start Cheat Sheet

```bash
# === ONE-TIME SETUP ===
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
conda env create -p ./pvp-ml/env -f pvp-ml/environment.yml
conda activate ./pvp-ml/env
pip install -e pvp-ml/
pip install "setuptools<81"
chmod +x simulation-rsps/ElvargServer/gradlew
cd simulation-rsps/ElvargServer && tr -d '\r' < gradlew > /tmp/gw && cp /tmp/gw gradlew && chmod +x gradlew
./gradlew spotlessApply --no-daemon && ./gradlew build --no-daemon
cd ../..

# === TRAIN ===
conda activate ./pvp-ml/env
cd pvp-ml
python -m pvp_ml.run_train_job train --preset Test --id 0 --wait --log
# TensorBoard: http://localhost:6006

# === PLAY AGAINST AI ===
# Terminal 1: API server
conda activate ./pvp-ml/env && cd pvp-ml && serve-api --device cpu

# Terminal 2: RSPS in eval mode
conda activate ./pvp-ml/env && cd simulation-rsps/ElvargServer
TRAIN=false RUN_EVAL_BOTS=true SYNC_TRAINING=false PREDICTION_API_HOST=localhost PREDICTION_API_PORT=9999 ./gradlew run --no-daemon

# Terminal 3 (Windows): Game client
cd C:\Users\YOUR_USERNAME\elvarg-client\ElvargClient
.\gradlew.bat run
# Log in with any username, walk to Wilderness, attack NhAgent bots

# === SHUTDOWN ===
lsof -ti :43595 -ti :7070 -ti :9999 -ti :6006 | sort -u | xargs -r kill
```
